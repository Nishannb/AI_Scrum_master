"""
Report PDF Agent Module

This module defines the ReportPDFAgent class, which is responsible for
converting markdown reports to PDFs and uploading them to Cloudinary.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low
from src.utils.pdf_report_generator import PDFReportGenerator
from src.utils.logging_utils import get_logger

class ReportPDFAgent(Agent):
    """
    Agent responsible for PDF report generation and upload.

    This agent takes markdown reports, converts them to PDFs, and uploads
    them to Cloudinary within the Fetch.ai Agentverse.
    """

    def __init__(
        self,
        name: str = "PDF Report Specialist",
        port: int = 8004,
        seed: Optional[str] = None,
        endpoint: Optional[str] = None,
        cloudinary_config: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the PDF report agent.

        Args:
            name: The name of the agent
            port: The port to run the agent on
            seed: Optional seed for deterministic agent creation
            endpoint: Optional endpoint for the agent
            cloudinary_config: Optional Cloudinary configuration
        """
        super().__init__(
            name=name,
            port=port,
            seed=seed,
            endpoint=endpoint
        )

        self._logger = get_logger(__name__)
        self.pdf_generator = PDFReportGenerator(cloudinary_config)
        self._logger.info("Initialized ReportPDFAgent")

        # Register message handlers
        @self.on_message("generate_pdf")
        async def handle_pdf_request(ctx: Context, sender: str, msg: Dict[str, Any]):
            """Handle requests to generate PDF reports"""
            try:
                self._logger.info(f"Received PDF generation request from {sender}")
                markdown_path = msg.get("markdown_path")
                if not markdown_path:
                    raise ValueError("No markdown file path provided")

                pdf_url = await self.generate_and_upload_pdf(markdown_path)
                await ctx.send(sender, {
                    "type": "pdf_response",
                    "status": "success",
                    "pdf_url": pdf_url
                })
            except Exception as e:
                self._logger.error(f"Error generating PDF: {str(e)}")
                await ctx.send(sender, {
                    "type": "pdf_response",
                    "status": "error",
                    "error": str(e)
                })

        @self.on_message("status_request")
        async def handle_status_request(ctx: Context, sender: str, msg: Dict[str, Any]):
            """Handle status check requests"""
            await ctx.send(sender, {
                "type": "agent_status",
                "status": "active",
                "last_update": datetime.now().isoformat()
            })

    async def generate_and_upload_pdf(self, markdown_path: str) -> str:
        """
        Generate PDF from markdown and upload to Cloudinary.

        Args:
            markdown_path: Path to the markdown file.

        Returns:
            URL of the uploaded PDF.
        """
        try:
            self._logger.info(f"Generating PDF from {markdown_path}")
            
            # Generate PDF
            pdf_path = self.pdf_generator.generate_pdf(markdown_path)
            if not pdf_path:
                raise ValueError("Failed to generate PDF")
            
            # Upload to Cloudinary
            pdf_url = self.pdf_generator.upload_to_cloudinary(pdf_path)
            if not pdf_url:
                raise ValueError("Failed to upload PDF to Cloudinary")
            
            self._logger.info(f"Successfully generated and uploaded PDF: {pdf_url}")
            return pdf_url
            
        except Exception as e:
            self._logger.error(f"Error in PDF generation and upload: {e}")
            return ""

    def run(self):
        """Run the PDF report agent"""
        self._logger.info("Starting ReportPDFAgent")
        fund_agent_if_low(self.wallet.address())
        super().run() 