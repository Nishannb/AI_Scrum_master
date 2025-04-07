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
                response = requests.get("https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf")
                with open(regular_font, "wb") as f:
                    f.write(response.content)
                
                # Download bold font
                response = requests.get("https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans-Bold.ttf")
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
    
    def _extract_images(self, markdown_content: str) -> List[str]:
        """
        Extract image paths from markdown content.
        
        Args:
            markdown_content: Markdown content to process.
            
        Returns:
            List of image paths.
        """
        images = []
        image_pattern = r'!\[.*?\]\((.+?)\)'
        for match in re.finditer(image_pattern, markdown_content):
            img_path = match.group(1)
            full_path = os.path.join(self.output_dir, img_path)
            if os.path.exists(full_path):
                images.append(full_path)
        
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
        """
        try:
            if not os.path.exists(markdown_file):
                self.logger.error(f"Markdown file not found: {markdown_file}")
                return ""
                
            # Generate output path if not provided
            if not output_pdf:
                output_pdf = markdown_file.replace(".md", ".pdf")
            
            # Ensure output_pdf is a valid path
            output_pdf = os.path.join(self.output_dir, os.path.basename(output_pdf))
            
            # Create PDF object with proper margins
            pdf = FPDF()
            pdf.add_page()
            
            # Set margins
            pdf.set_margins(20, 20, 20)  # Left, Top, Right margins
            pdf.set_auto_page_break(auto=True, margin=15)
            
            # Add DejaVuSans font which supports Unicode
            regular_font = os.path.join(self.font_dir, "DejaVuSans.ttf")
            bold_font = os.path.join(self.font_dir, "DejaVuSans-Bold.ttf")
            
            if not os.path.exists(regular_font) or not os.path.exists(bold_font):
                self.logger.error("Font files not found. Please run _setup_fonts first.")
                return ""
            
            pdf.add_font('DejaVuSans', '', regular_font, uni=True)
            pdf.add_font('DejaVuSans', 'B', bold_font, uni=True)
            
            # Set up fonts
            pdf.set_font('DejaVuSans', '', 12)  # Default font
            
            # Read markdown content
            with open(markdown_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Process markdown content
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    pdf.ln(5)  # Add space for empty lines
                    continue
                    
                if line.startswith('# '):  # Title
                    pdf.set_font('DejaVuSans', 'B', 20)
                    pdf.cell(0, 12, line[2:], ln=True)
                elif line.startswith('## '):  # H1
                    pdf.set_font('DejaVuSans', 'B', 16)
                    pdf.cell(0, 10, line[3:], ln=True)
                elif line.startswith('### '):  # H2
                    pdf.set_font('DejaVuSans', 'B', 14)
                    pdf.cell(0, 8, line[4:], ln=True)
                elif line.startswith('- '):  # Bullet point
                    pdf.set_font('DejaVuSans', '', 12)
                    pdf.cell(5)  # Indent
                    pdf.multi_cell(0, 7, line[2:])
                elif line.strip() == '---':  # Horizontal rule
                    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
                    pdf.ln(5)
                else:  # Regular text
                    pdf.set_font('DejaVuSans', '', 12)
                    # Use multi_cell with proper width
                    pdf.multi_cell(170, 7, line)  # 170mm width (A4 width - margins)
            
            # Save the PDF
            pdf.output(output_pdf)
            self.logger.info(f"PDF generated successfully: {output_pdf}")
            return output_pdf
            
        except Exception as e:
            self.logger.error(f"Error generating PDF: {e}")
            self.logger.exception(e)
            return ""
    
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
                return {**result, "error": "Failed to generate PDF"}
            
            result["pdf_path"] = pdf_path
            
            # Upload to Cloudinary
            upload_result = self.upload_to_cloudinary(pdf_path)
            if not upload_result.get("success", False):
                return {**result, "error": upload_result.get("error", "Failed to upload to Cloudinary")}
            
            # Print report content to terminal
            self._print_report_content(markdown_file)
            
            # Prepare the final result
            final_result = {
                **result,
                "success": True,
                "cloudinary_url": upload_result.get("url"),
                "cloudinary_public_id": upload_result.get("public_id")
            }
            
            # Send Slack notification
            self.notify_completion(final_result)
            
            return final_result
            
        except Exception as e:
            logger.error(f"Error processing report: {e}")
            return {**result, "error": str(e)}
    
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