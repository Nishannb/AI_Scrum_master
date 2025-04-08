# #!/usr/bin/env python
# """
# Main entry point for the Scrum Master AI application.

# This script initializes and runs the AI Scrum Master system, which analyzes
# Trello board data and generates sprint reports with metrics and visualizations.
# """

# # Set up logging first, before any other imports
# from src.utils.logging_utils import setup_logging, get_logger
# setup_logging(log_file="./logs/scrum_master_ai.log")
# logger = get_logger(__name__)

# import os
# import logging
# import asyncio
# from datetime import datetime
# from typing import Optional, Dict, Any
# from dotenv import load_dotenv

# # Now import the rest of the modules
# from src.crew.scrum_master_crew import ScrumMasterCrew
# from src.agents.report_pdf_agent import ReportPDFAgent


# def setup_environment() -> bool:
#     """
#     Set up the environment variables and validate them.

#     Returns:
#         bool: True if setup was successful, False otherwise.
#     """
#     try:
#         # Load environment variables from .env file
#         env_path = os.path.join(os.path.dirname(__file__), ".env")
#         load_dotenv(env_path, override=True)
        
#         # Print the path from which we're loading the .env file
#         print(f"Loading environment variables from: {env_path}")
        
#         # Check required environment variables
#         required_vars = [
#             "OPENAI_API_KEY",
#             "TRELLO_API_KEY",
#             "TRELLO_API_TOKEN",
#             "TRELLO_BOARD_ID",
#             "CLOUDINARY_CLOUD_NAME",
#             "CLOUDINARY_API_KEY",
#             "CLOUDINARY_API_SECRET"
#         ]
        
#         for var in required_vars:
#             value = os.getenv(var)
#             if not value:
#                 logger.error(f"Missing required environment variable: {var}")
#                 return False
#             # Print first few characters of the value for debugging
#             # print(f"from here, {var}: {'*' * len(value[:4])}{value[4:8]}...")
            
#         return True
        
#     except Exception as e:
#         logger.error(f"Error setting up environment: {e}")
#         return False


# async def generate_report(
#     board_id: Optional[str] = None,
#     output_file: Optional[str] = None,
#     verbose: bool = True,
#     generate_pdf: bool = True
# ) -> Dict[str, Any]:
#     """
#     Generate a sprint report with metrics and visualizations.

#     Args:
#         board_id: Optional Trello board ID. If not provided, uses the one from .env.
#         output_file: Optional output file path for the report.
#         verbose: Whether to enable verbose logging.
#         generate_pdf: Whether to generate a PDF version and upload to Cloudinary.

#     Returns:
#         Dict[str, Any]: Dictionary with paths to generated reports and Cloudinary URL.
#     """
#     result = {
#         "success": False,
#         "markdown_path": None,
#         "pdf_path": None,
#         "cloudinary_url": None,
#         "error": None
#     }
    
#     try:
#         # Use provided board ID or get from environment
#         board_id = board_id or os.getenv("TRELLO_BOARD_ID")
#         if not board_id:
#             logger.error("No Trello board ID provided")
#             result["error"] = "No Trello board ID provided"
#             return result
            
#         # Create output file path if not provided
#         if not output_file:
#             date_str = datetime.now().strftime("%Y%m%d")
#             output_file = f"reports/sprint_report_{date_str}.md"
            
#         # Create output directory if it doesn't exist
#         os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
#         # Initialize and run the Scrum Master crew
#         crew = ScrumMasterCrew(
#             board_id=board_id,
#             output_file=output_file,
#             verbose=verbose
#         )
        
#         markdown_path = await crew.run()
        
#         if not markdown_path:
#             logger.error("Failed to generate report")
#             result["error"] = "Failed to generate report"
#             return result
            
#         result["success"] = True
#         result["markdown_path"] = markdown_path
        
#         # Generate PDF and upload to Cloudinary if requested
#         if generate_pdf:
#             # Initialize the PDF agent
#             pdf_agent = ReportPDFAgent(
#                 name="PDF Report Specialist",
#                 output_dir="reports"
#             )
#             # Process the report
#             pdf_result = pdf_agent.process_specific_report(markdown_path)
            
#             if pdf_result.get("success", False):
#                 result["pdf_path"] = pdf_result.get("pdf_path")
#                 result["cloudinary_url"] = pdf_result.get("cloudinary_url")
#                 logger.info(f"PDF report uploaded to Cloudinary: {result['cloudinary_url']}")
#             else:
#                 error_msg = pdf_result.get("error", "Unknown error")
#                 logger.error(f"Failed to generate PDF: {error_msg}")
#                 result["error"] = f"Failed to generate PDF: {error_msg}"
#                 result["success"] = False
        
#         logger.info(f"Successfully generated report at {markdown_path}")
#         return result
        
#     except Exception as e:
#         logger.error(f"Error generating report: {e}")
#         result["error"] = str(e)
#         return result


# async def main():
#     """
#     Main entry point for the application.
#     """
#     try:
#         # Set up environment
#         if not setup_environment():
#             logger.error("Failed to set up environment")
#             return 1

#         # Get board ID from environment
#         board_id = os.getenv("TRELLO_BOARD_ID")
#         if not board_id:
#             logger.error("TRELLO_BOARD_ID not found in environment variables")
#             return 1

#         # Create output directory if it doesn't exist
#         os.makedirs("reports", exist_ok=True)
#         os.makedirs("logs", exist_ok=True)

#         # Initialize and run the Scrum Master crew and PDF generator
#         try:
#             logger.info("Starting report generation...")
#             result = await generate_report(board_id=board_id, generate_pdf=True)

#             if not result.get("success", False):
#                 logger.error("Report generation failed")
#                 return 1

#             # Print report summary and Cloudinary URL
#             print("\n" + "="*80)
#             print("SPRINT REPORT GENERATION COMPLETED")
#             print("="*80)
#             print(f"Markdown report: {result['markdown_path']}")
            
#             if result.get("pdf_path"):
#                 print(f"PDF report: {result['pdf_path']}")
            
#             if result.get("cloudinary_url"):
#                 print(f"Cloudinary URL: {result['cloudinary_url']}")
#                 print("\nShare this link with your team to access the report:")
#                 print(f"📊 {result['cloudinary_url']}")
            
#             print("="*80 + "\n")
            
#             # All done
#             logger.info(f"Report generation completed successfully")
#             return 0

#         except Exception as e:
#             logger.error(f"Error during report generation: {str(e)}")
#             import traceback
#             logger.error(f"Traceback: {traceback.format_exc()}")
#             return 1

#     except Exception as e:
#         logger.error(f"Unexpected error in main: {str(e)}")
#         import traceback
#         logger.error(f"Traceback: {traceback.format_exc()}")
#         return 1


# if __name__ == "__main__":
#     exit(asyncio.run(main()))