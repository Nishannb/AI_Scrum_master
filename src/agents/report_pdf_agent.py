"""
Report PDF Agent Module

This module defines the ReportPDFAgent class, which is responsible for
converting markdown reports to PDFs and uploading them to Cloudinary.
"""

from typing import Dict, Any, Optional
from src.utils.pdf_generator import PDFReportGenerator
from src.utils.logging_utils import get_logger

class ReportPDFAgent:
    """
    Agent responsible for PDF report generation and upload.

    This agent takes markdown reports, converts them to PDFs, and uploads
    them to Cloudinary.
    """

    def __init__(
        self,
        name: str = "PDF Report Specialist",
        output_dir: str = "reports",
        cloudinary_config: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the PDF report agent.

        Args:
            name: The name of the agent
            output_dir: Directory to save reports and PDFs
            cloudinary_config: Optional Cloudinary configuration
        """
        self._logger = get_logger(__name__)
        self.pdf_generator = PDFReportGenerator(output_dir=output_dir)
        self._logger.info("Initialized ReportPDFAgent")

    def process_specific_report(self, markdown_path: str) -> Dict[str, Any]:
        """
        Process a specific markdown report: generate PDF and upload to Cloudinary.
        
        Args:
            markdown_path: Path to the markdown file.
            
        Returns:
            Dictionary with success status, paths, and URLs.
        """
        try:
            result = self.pdf_generator.process_report(markdown_path)
            self._logger.info(f"Report processing result: {result}")
            return result
            
        except Exception as e:
            self._logger.error(f"Error processing report: {e}")
            return {
                "success": False,
                "error": str(e),
                "markdown_path": markdown_path
            } 