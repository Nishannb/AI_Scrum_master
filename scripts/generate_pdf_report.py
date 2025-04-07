#!/usr/bin/env python
"""
PDF Report Generator Script

This script generates a PDF report from a markdown file and uploads it to Cloudinary.
It can be used as a standalone script or imported as a module.
"""

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# Add the parent directory to the system path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.pdf_generator import PDFReportGenerator
from src.utils.logging_utils import get_logger

# Configure logging
logger = get_logger(__name__)

def main():
    """Main function to process command-line arguments and generate the report."""
    parser = argparse.ArgumentParser(description='Generate PDF report and upload to Cloudinary')
    parser.add_argument('--markdown-file', '-m', type=str, 
                        help='Path to the markdown report file',
                        default=None)
    parser.add_argument('--output-dir', '-o', type=str, 
                        help='Output directory for PDF',
                        default='reports')
    parser.add_argument('--print-sections', '-p', action='store_true', 
                        help='Print key sections to the terminal')
    
    args = parser.parse_args()
    
    # Find the most recent report if no file is specified
    markdown_file = args.markdown_file
    if not markdown_file:
        reports_dir = args.output_dir
        if os.path.exists(reports_dir):
            md_files = [f for f in os.listdir(reports_dir) if f.endswith('.md')]
            if md_files:
                # Sort by modification time
                md_files.sort(key=lambda f: os.path.getmtime(os.path.join(reports_dir, f)), reverse=True)
                markdown_file = os.path.join(reports_dir, md_files[0])
                logger.info(f"Using most recent report: {markdown_file}")
            else:
                logger.error(f"No markdown files found in {reports_dir}")
                return 1
        else:
            logger.error(f"Reports directory {reports_dir} not found")
            return 1
    
    # Initialize the PDF generator
    pdf_generator = PDFReportGenerator(output_dir=args.output_dir)
    
    # Process the report
    result = pdf_generator.process_report(markdown_file)
    
    if not result.get('success', False):
        logger.error(f"Error processing report: {result.get('error', 'Unknown error')}")
        return 1
    
    # Print results
    print("\n" + "="*80)
    print(f"REPORT PROCESSING COMPLETED")
    print("="*80)
    print(f"Markdown report: {result['markdown_path']}")
    print(f"PDF report: {result['pdf_path']}")
    print(f"Cloudinary URL: {result['cloudinary_url']}")
    print("="*80 + "\n")
    
    # Print key sections if requested
    if args.print_sections:
        sections = pdf_generator.extract_key_sections(markdown_file)
        
        if 'risk_analysis' in sections:
            print("\n" + "="*80)
            print("RISK ANALYSIS")
            print("="*80)
            print(sections['risk_analysis'])
            print("="*80 + "\n")
        
        if 'overdue_tasks' in sections:
            print("\n" + "="*80)
            print("OVERDUE TASKS")
            print("="*80)
            print(sections['overdue_tasks'])
            print("="*80 + "\n")
        
        if 'goals' in sections:
            print("\n" + "="*80)
            print("GOALS UNTIL NEXT SPRINT MEETING")
            print("="*80)
            print(sections['goals'])
            print("="*80 + "\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 