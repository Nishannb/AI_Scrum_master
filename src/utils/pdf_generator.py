"""
PDF Report Generator and Cloudinary Uploader

This module generates PDF reports from markdown and uploads them to Cloudinary.
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import re
import base64
import tempfile
from datetime import datetime
import shutil
import textwrap

import markdown
from fpdf import FPDF
import cloudinary
import cloudinary.uploader
from src.utils.slack_utils import SlackNotifier
from dotenv import load_dotenv

from src.utils.logging_utils import get_logger

# Configure logging
logger = get_logger(__name__)

class PDFReportGenerator:
    """Class responsible for generating PDF reports and uploading to Cloudinary."""
    
    def __init__(self, output_dir: str = "reports"):
        """
        Initialize the PDFReportGenerator.

        Args:
            output_dir: Directory to save reports and PDFs.
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize logger
        self.logger = get_logger(__name__)
        self.logger.info(f"Initialized PDFReportGenerator with output directory: {output_dir}")
        
        # Load environment variables if not already loaded
        load_dotenv()
        
        # Initialize Cloudinary
        self._setup_cloudinary()
        
        self._setup_fonts()
    
    def _setup_cloudinary(self):
        """Set up Cloudinary with credentials from environment variables."""
        try:
            cloudinary.config(
                cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
                api_key=os.getenv("CLOUDINARY_API_KEY"),
                api_secret=os.getenv("CLOUDINARY_API_SECRET"),
                secure=True
            )
            logger.info("Cloudinary configuration initialized")
        except Exception as e:
            logger.error(f"Error configuring Cloudinary: {e}")
    
    def _setup_fonts(self):
        """Download and set up DejaVuSans fonts if not already present."""
        try:
            font_dir = os.path.join(os.path.dirname(__file__), "fonts")
            os.makedirs(font_dir, exist_ok=True)
            
            regular_font = os.path.join(font_dir, "DejaVuSans.ttf")
            bold_font = os.path.join(font_dir, "DejaVuSans-Bold.ttf")
            
            if not os.path.exists(regular_font) or not os.path.exists(bold_font):
                self.logger.info("Downloading DejaVuSans fonts...")
                import requests
                
                # Download regular font
                response = requests.get("https://raw.githubusercontent.com/dejavu-fonts/dejavu-fonts/master/ttf/DejaVuSans.ttf")
                with open(regular_font, "wb") as f:
                    f.write(response.content)
                
                # Download bold font
                response = requests.get("https://raw.githubusercontent.com/dejavu-fonts/dejavu-fonts/master/ttf/DejaVuSans-Bold.ttf")
                with open(bold_font, "wb") as f:
                    f.write(response.content)
                
                self.logger.info("Fonts downloaded successfully")
            
            self.font_dir = font_dir
            
        except Exception as e:
            self.logger.error(f"Error setting up fonts: {e}")
            self.logger.exception(e)
            raise
    
    def _extract_text_content(self, markdown_content: str) -> str:
        """
        Extract plain text content from markdown, removing special characters.
        
        Args:
            markdown_content: Markdown content to process.
            
        Returns:
            Plain text content.
        """
        # Remove image references
        no_images = re.sub(r'!\[.*?\]\((.+?)\)', '', markdown_content)
        
        # Remove links but keep the text
        no_links = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', no_images)
        
        # We'll handle bold markers separately in the PDF generation
        # Just remove heading markers and other formatting here
        text = no_links
        text = re.sub(r'#{1,6}\s+', '', text)  # Remove heading markers
        text = re.sub(r'`(.*?)`', r'\1', text)  # Remove code markers
        
        # Replace common non-ASCII characters with ASCII
        # Remove emojis and other special characters that might cause issues
        simplified = re.sub(r'[^\x00-\x7F]+', '', text)
        
        return simplified
    
    def _extract_images(self, markdown_content: str) -> List[dict]:
        """
        Extract image paths from markdown content.
        
        Args:
            markdown_content: Markdown content to process.
            
        Returns:
            List of dictionaries with image info including path, alt text and section.
        """
        images = []
        image_pattern = r'!\[(.*?)\]\((.+?)\)'
        lines = markdown_content.split('\n')
        current_section = None
        
        for i, line in enumerate(lines):
            # Track section headers
            if line.startswith('## '):
                current_section = line[3:].strip()
            
            # Find image references
            match = re.search(image_pattern, line)
            if match:
                alt_text = match.group(1)
                img_path = match.group(2)
                
                # Get absolute path
                full_path = os.path.join(self.output_dir, img_path)
                
                # Check if image exists
                if os.path.exists(full_path):
                    # Get description (usually the next line)
                    description = ""
                    if i + 1 < len(lines) and lines[i + 1].startswith('*'):
                        description = lines[i + 1].strip()
                    
                    images.append({
                        'path': full_path,
                        'alt_text': alt_text,
                        'section': current_section,
                        'description': description
                    })
                else:
                    self.logger.warning(f"Image not found: {full_path}")
        
        return images

    def _custom_wrap_text(self, pdf, text, max_width):
        """
        Custom word wrapping function that ensures text doesn't exceed max_width.
        Uses FPDF's string width calculation for better accuracy than textwrap.
        
        Args:
            pdf: FPDF instance
            text: Text to wrap
            max_width: Maximum width in millimeters
            
        Returns:
            List of wrapped lines
        """
        # Split the text into words
        words = text.split()
        if not words:
            return []
            
        lines = []
        current_line = words[0]
        current_width = pdf.get_string_width(current_line)
        
        for word in words[1:]:
            # Check if adding this word exceeds the max width
            word_width = pdf.get_string_width(' ' + word)
            if current_width + word_width <= max_width:
                current_line += ' ' + word
                current_width += word_width
            else:
                # Start a new line
                lines.append(current_line)
                current_line = word
                current_width = pdf.get_string_width(word)
        
        # Add the last line
        if current_line:
            lines.append(current_line)
            
        return lines
        
    def _sanitize_text(self, text: str) -> str:
        """
        Replace Unicode characters with ASCII equivalents.
        
        Args:
            text: Text to sanitize
            
        Returns:
            str: Sanitized text
        """
        replacements = {
            '⚠': '!',  # Warning symbol
            '✓': 'v',  # Checkmark
            '✗': 'x',  # Cross mark
            '→': '->',  # Right arrow
            '←': '<-',  # Left arrow
            '•': '-',  # Bullet point
            '…': '...',  # Ellipsis
            '"': '"',  # Smart quote
            ''': "'",  # Smart quote
            ''': "'",  # Smart quote
            '—': '-',  # Em dash
            '–': '-',  # En dash
            '≈': '~',  # Approximately equal
            '≤': '<=',  # Less than or equal
            '≥': '>=',  # Greater than or equal
            '×': 'x',  # Multiplication
            '÷': '/',  # Division
            '±': '+/-',  # Plus-minus
            '©': '(c)',  # Copyright
            '®': '(R)',  # Registered trademark
            '™': '(TM)',  # Trademark
            '€': 'EUR',  # Euro
            '£': 'GBP',  # Pound
            '¥': 'JPY',  # Yen
            '°': ' degrees',  # Degree
            '²': '^2',  # Superscript 2
            '³': '^3',  # Superscript 3
            '½': '1/2',  # One half
            '¼': '1/4',  # One quarter
            '¾': '3/4',  # Three quarters
            'á': 'a',  # Accented a
            'é': 'e',  # Accented e
            'í': 'i',  # Accented i
            'ó': 'o',  # Accented o
            'ú': 'u',  # Accented u
            'ñ': 'n',  # Spanish n
            'ü': 'u',  # Umlaut u
            'ö': 'o',  # Umlaut o
            'ä': 'a',  # Umlaut a
            # Common emojis
            '🚫': '[X]',  # No entry
            '⚠️': '[!]',  # Warning
            '✅': '[v]',  # Checkmark
            '📊': '[CHART]',  # Chart
            '🎯': '[TARGET]',  # Target
            '⏰': '[CLOCK]',  # Alarm clock
            '🚨': '[ALERT]',  # Alert
            '🔴': '[RED]',  # Red circle
            '🟠': '[ORANGE]',  # Orange circle
            '🟡': '[YELLOW]',  # Yellow circle
            '🟢': '[GREEN]',  # Green circle
            '🔵': '[BLUE]',  # Blue circle
        }
        
        for unicode_char, ascii_char in replacements.items():
            text = text.replace(unicode_char, ascii_char)
            
        # Replace any remaining emojis with empty string
        emoji_pattern = re.compile("["
                                   u"\U0001F600-\U0001F64F"  # emoticons
                                   u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                   u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                   u"\U0001F700-\U0001F77F"  # alchemical symbols
                                   u"\U0001F780-\U0001F7FF"  # Geometric Shapes
                                   u"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
                                   u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
                                   u"\U0001FA00-\U0001FA6F"  # Chess Symbols
                                   u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
                                   u"\U00002702-\U000027B0"  # Dingbats
                                   u"\U000024C2-\U0001F251" 
                                   "]+", flags=re.UNICODE)
        text = emoji_pattern.sub(r'', text)
            
        # Replace any remaining non-ASCII characters with '?'
        return text.encode('ascii', 'replace').decode()

    def generate_pdf_from_markdown(
        self,
        markdown_file: str,
        output_pdf: Optional[str] = None
    ) -> str:
        """
        Generate a PDF from a markdown file.
        
        Args:
            markdown_file: Path to the markdown file
            output_pdf: Optional output path for the PDF
            
        Returns:
            str: Path to the generated PDF file
            
        Raises:
            FileNotFoundError: If markdown file is not found
            Exception: For other errors during PDF generation
        """
        try:
            if not os.path.exists(markdown_file):
                self.logger.error(f"Markdown file not found: {markdown_file}")
                raise FileNotFoundError(f"Markdown file not found: {markdown_file}")
                
            # Generate output path if not provided
            if not output_pdf:
                output_pdf = markdown_file.replace(".md", ".pdf")
            
            # Ensure output_pdf is a valid path
            output_pdf = os.path.join(self.output_dir, os.path.basename(output_pdf))
            
            # Read markdown content
            with open(markdown_file, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Extract all images from markdown
            image_list = self._extract_images(original_content)
            self.logger.info(f"Found {len(image_list)} images in markdown file")
            
            # Create PDF object with proper margins
            pdf = FPDF()
            pdf.add_page()
            
            # Set margins - increase left margin to prevent text from being cut off
            pdf.set_margins(25, 20, 25)  # Left, Top, Right margins (balance for more readable text)
            pdf.set_auto_page_break(auto=True, margin=25)
            
            # Set up fonts - use standard Arial fonts
            pdf.set_font('Arial', '', 11)  # Default font
            
            # Track sections for image insertion
            current_section = None
            in_list = False
            skip_next_lines = 0
            
            # Process markdown content line by line
            lines = original_content.split('\n')
            
            for i, line in enumerate(lines):
                if skip_next_lines > 0:
                    skip_next_lines -= 1
                    continue
                    
                # Sanitize the line to handle non-ASCII characters
                line = self._sanitize_text(line.strip())
                if not line:
                    pdf.ln(5)  # Add space for empty lines
                    continue
                
                # Handle images - we'll add them when we reach their section
                if line.startswith('!['):
                    # We'll process images separately
                    continue
                
                # Handle section headers
                if line.startswith('# '):  # Title
                    current_section = line[2:]
                    pdf.set_font('Arial', 'B', 18)
                    pdf.cell(0, 10, current_section, ln=True)
                    pdf.line(25, pdf.get_y(), 185, pdf.get_y())
                    pdf.ln(5)
                    in_list = False
                elif line.startswith('## '):  # H2
                    current_section = line[3:]
                    pdf.set_font('Arial', 'B', 14)
                    pdf.cell(0, 8, current_section, ln=True)
                    pdf.line(25, pdf.get_y(), 185, pdf.get_y())
                    pdf.ln(5)
                    in_list = False
                    
                    # Find images for this section
                    section_images = [img for img in image_list if img['section'] == current_section]
                    
                    # Add the images for this section
                    for img in section_images:
                        try:
                            # Allow some text to be added before showing the image
                            pass_lines = 0
                            while (i + 1 + pass_lines < len(lines) and 
                                  not lines[i + 1 + pass_lines].startswith('![') and
                                  not lines[i + 1 + pass_lines].startswith('#')):
                                pass_lines += 1
                                if pass_lines >= 2:  # Limit to checking only next 2 lines
                                    break
                            
                            # Add description if it exists
                            if img['description']:
                                pdf.set_font('Arial', 'I', 10)
                                pdf.multi_cell(0, 6, self._sanitize_text(img['description']))
                                pdf.ln(3)
                            
                            # Check if we need a new page based on remaining space
                            if pdf.get_y() > 200:  # If we're close to the bottom
                                pdf.add_page()
                            
                            # Calculate proper width while maintaining aspect ratio
                            # Use a more dynamic width - proportional to page width
                            page_width = pdf.w - pdf.l_margin - pdf.r_margin
                            img_width = min(160, page_width * 0.9)  # 90% of available width
                            
                            # Center the image
                            x_position = (pdf.w - img_width) / 2
                            
                            # Add the image
                            pdf.image(img['path'], x=x_position, y=pdf.get_y(), w=img_width)
                            
                            # Add some space after the image - dynamic based on image
                            pdf.ln(img_width * 0.7)  # Height proportional to width
                            
                            # Add the caption if there is alt text
                            if img['alt_text']:
                                pdf.set_font('Arial', 'I', 10)
                                pdf.cell(0, 6, f"{img['alt_text']}", 0, 1, 'C')
                                pdf.ln(3)
                                
                        except Exception as e:
                            self.logger.error(f"Error adding image {img['path']}: {e}")
                            self.logger.exception(e)
                            
                elif line.startswith('### '):  # H3
                    current_section = line[4:]
                    pdf.set_font('Arial', 'B', 12)
                    pdf.cell(0, 7, current_section, ln=True)
                    pdf.ln(3)
                    in_list = False
                elif line.startswith('- ') or line.startswith('* '):  # Bullet point
                    if not in_list:
                        pdf.ln(2)
                        in_list = True
                    pdf.set_font('Arial', '', 11)
                    bullet_text = line[2:]
                    
                    # Wrap text to prevent it from going off the page
                    # Calculate available width (page width minus margins and bullet indent)
                    available_width = pdf.w - pdf.l_margin - pdf.r_margin - 10  # 10mm for bullet indent
                    
                    # Calculate how many characters can fit in the available width
                    # This is an approximation since proportional fonts vary in width
                    avg_char_width = pdf.get_string_width("m")  # Use 'm' as an average character
                    chars_per_line = int(available_width / avg_char_width)
                    
                    wrapped_lines = textwrap.wrap(bullet_text, width=chars_per_line)
                    pdf.cell(5, 7, "-", 0, 0)
                    if wrapped_lines:
                        pdf.cell(0, 7, wrapped_lines[0], 0, 1)
                        for wrapped_line in wrapped_lines[1:]:
                            pdf.cell(10, 7, wrapped_line, 0, 1)
                    else:
                        pdf.cell(0, 7, "", 0, 1)
                elif line.strip() == '---':  # Horizontal rule
                    pdf.line(25, pdf.get_y(), 185, pdf.get_y())
                    pdf.ln(5)
                    in_list = False
                elif line.startswith('**') and line.endswith('**'):  # Bold text on its own line (often a label)
                    pdf.set_font('Arial', 'B', 11)
                    label_text = line.strip('**')
                    pdf.cell(0, 7, label_text, 0, 1)
                    pdf.set_font('Arial', '', 11)
                    in_list = False
                else:  # Regular text
                    pdf.set_font('Arial', '', 11)
                    
                    # Check if this is a line with bold markers within it
                    if '**' in line:
                        # Handle mixed bold/regular text
                        parts = re.split(r'(\*\*.*?\*\*)', line)
                        x_position = pdf.get_x()
                        line_height = 7
                        
                        # Calculate available width
                        available_width = pdf.w - pdf.l_margin - pdf.r_margin
                        
                        for part in parts:
                            if part.startswith('**') and part.endswith('**'):
                                # Bold text
                                pdf.set_font('Arial', 'B', 11)
                                text = part.strip('**')
                            else:
                                # Regular text
                                pdf.set_font('Arial', '', 11)
                                text = part
                                
                            if not text.strip():
                                continue
                                
                            # Get text width
                            text_width = pdf.get_string_width(text)
                            
                            # Check if we need to wrap to next line
                            remaining_width = available_width - (x_position - pdf.l_margin)
                            if text_width > remaining_width:
                                pdf.ln(line_height)  # Move to next line
                                x_position = pdf.l_margin
                            
                            # Output the text segment
                            pdf.set_x(x_position)
                            pdf.cell(text_width, line_height, text, 0, 0)
                            x_position += text_width
                        
                        pdf.ln(line_height)
                    else:
                        # Regular paragraph text - use multi_cell for automatic wrapping
                        pdf.multi_cell(0, 7, line)
                    
                    in_list = False
            
            # Check if there are any images that weren't displayed with their sections
            # This handles cases where images are in the markdown but not under a clear section
            remaining_images = [img for img in image_list if not any(section_img['path'] == img['path'] 
                                for section_img in [img for img in image_list if img['section'] == img['section']])]
            
            if remaining_images:
                # Add a new section for remaining images if needed
                if not any(img['section'] == 'Charts & Visuals' for img in image_list):
                    pdf.add_page()
                    pdf.set_font('Arial', 'B', 14)
                    pdf.cell(0, 8, "Charts & Visuals", ln=True)
                    pdf.line(25, pdf.get_y(), 185, pdf.get_y())
                    pdf.ln(5)
                
                # Add each remaining image
                for img in remaining_images:
                    try:
                        # Calculate proper width
                        page_width = pdf.w - pdf.l_margin - pdf.r_margin
                        img_width = min(160, page_width * 0.9)
                        
                        # Check if we need a new page
                        if pdf.get_y() > 200:
                            pdf.add_page()
                        
                        # Center the image
                        x_position = (pdf.w - img_width) / 2
                        
                        # Add the image
                        pdf.image(img['path'], x=x_position, y=pdf.get_y(), w=img_width)
                        
                        # Add some space after the image
                        pdf.ln(img_width * 0.7)
                        
                        # Add caption
                        if img['alt_text']:
                            pdf.set_font('Arial', 'I', 10)
                            pdf.cell(0, 6, f"{img['alt_text']}", 0, 1, 'C')
                            pdf.ln(3)
                    except Exception as e:
                        self.logger.error(f"Error adding remaining image {img['path']}: {e}")
            
            # Save the PDF
            pdf.output(output_pdf)
            self.logger.info(f"PDF generated successfully: {output_pdf}")
            return output_pdf
            
        except Exception as e:
            self.logger.error(f"Error generating PDF: {e}")
            self.logger.exception(e)
            raise
    
    def generate_pdf(self, markdown_file: str, output_pdf: Optional[str] = None) -> str:
        """
        Generate a PDF from a markdown file. This is an alias for generate_pdf_from_markdown.
        
        Args:
            markdown_file: Path to the markdown file
            output_pdf: Optional output path for the PDF
            
        Returns:
            str: Path to the generated PDF file
        """
        return self.generate_pdf_from_markdown(markdown_file, output_pdf)
    
    def upload_to_cloudinary(self, file_path: str) -> Dict[str, Any]:
        """
        Upload a file to Cloudinary.
        
        Args:
            file_path: Path to the file to upload.
            
        Returns:
            Dictionary with upload information including URL.
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return {"error": "File not found"}
            
            # Generate a folder name using the current date
            folder = f"sprint_reports/{datetime.now().strftime('%Y%m')}"
            
            # Upload the file
            response = cloudinary.uploader.upload(
                file_path,
                folder=folder,
                resource_type="auto",
                use_filename=True,
                unique_filename=True
            )
            
            logger.info(f"File uploaded to Cloudinary: {response.get('secure_url')}")
            return {
                "success": True,
                "url": response.get("secure_url"),
                "public_id": response.get("public_id"),
                "created_at": response.get("created_at")
            }
            
        except Exception as e:
            logger.error(f"Error uploading to Cloudinary: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def process_report(self, markdown_file: str) -> Dict[str, Any]:
        """
        Process a markdown report: generate PDF and upload to Cloudinary.
        
        Args:
            markdown_file: Path to the markdown report file.
            
        Returns:
            Dictionary with paths and URLs of the processed report.
        """
        result = {
            "markdown_path": markdown_file,
            "success": False
        }
        
        try:
            # Generate PDF
            pdf_path = self.generate_pdf_from_markdown(markdown_file)
            if not pdf_path:
                raise ValueError("PDF generation failed - no path returned")
                
            result["pdf_path"] = pdf_path
            
            # Upload to Cloudinary
            upload_result = self.upload_to_cloudinary(pdf_path)
            if upload_result.get("success"):
                result.update({
                    "success": True,
                    "cloudinary_url": upload_result["url"],
                    "cloudinary_public_id": upload_result["public_id"],
                    "created_at": upload_result["created_at"]
                })
            else:
                result["error"] = f"Failed to upload PDF: {upload_result.get('error')}"
                
        except FileNotFoundError as e:
            result["error"] = str(e)
            self.logger.error(f"File not found error: {e}")
            
        except Exception as e:
            result["error"] = f"Error processing report: {str(e)}"
            self.logger.error(f"Error processing report: {e}")
            self.logger.exception(e)
            
        return result
    
    def _print_report_content(self, markdown_file: str) -> None:
        """
        Print all report content to the terminal.
        
        Args:
            markdown_file: Path to the markdown report file.
        """
        try:
            with open(markdown_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Print the entire report content to the terminal
            print("\n" + "="*80)
            print("SPRINT REPORT - TEXTUAL CONTENT")
            print("="*80)
            
            # Remove image references to clean up the output
            no_images = re.sub(r'!\[.*?\]\((.+?)\)', '', content)
            print(no_images)
            
            print("="*80 + "\n")
                
        except Exception as e:
            logger.error(f"Error printing report content: {e}")
    
    def extract_key_sections(self, markdown_file: str) -> Dict[str, str]:
        """
        Extract key sections from a markdown report.
        
        Args:
            markdown_file: Path to the markdown report file.
            
        Returns:
            Dictionary with key sections as strings.
        """
        try:
            with open(markdown_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            sections = {}
            
            # Extract Risk Analysis section
            risk_match = re.search(r'## Risk Analysis(.*?)(?=##|\Z)', content, re.DOTALL)
            if risk_match:
                sections['risk_analysis'] = risk_match.group(1).strip()
            
            # Extract Overdue Tasks section
            overdue_match = re.search(r'### Overdue Tasks(.*?)(?=###|\Z)', content, re.DOTALL)
            if overdue_match:
                sections['overdue_tasks'] = overdue_match.group(1).strip()
            
            # Extract Goals section
            goals_match = re.search(r'## 🎯 Goals Until Next Sprint Meeting(.*?)(?=##|\Z)', content, re.DOTALL)
            if goals_match:
                sections['goals'] = goals_match.group(1).strip()
            
            return sections
            
        except Exception as e:
            logger.error(f"Error extracting key sections: {e}")
            return {}

    def notify_completion(self, result: Dict[str, Any]) -> bool:
        """
        Notify about report completion via Slack.
        
        Args:
            result: Dictionary with report generation results
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        try:
            from src.utils.slack_utils import SlackNotifier
            # Create Slack notifier with proper SSL certificate handling
            notifier = SlackNotifier()
            return notifier.notify_report_completion(result)
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
            return False 