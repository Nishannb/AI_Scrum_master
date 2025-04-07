"""
Scrum Master Crew Module

This module defines the ScrumMasterCrew class, which orchestrates the AI agents
responsible for managing and analyzing sprint data.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

from crewai import Crew, Agent, Task
from langchain_openai import ChatOpenAI
from src.agents.analysis_agent import AnalysisAgent
from src.agents.reporting_agent import ReportingAgent
from src.utils.report_generator import ReportGenerator
from src.utils.logging_utils import get_logger
from src.utils.trello_tools import TrelloTools


class ScrumMasterCrew:
    """
    Crew responsible for managing and analyzing sprint data.

    This crew coordinates multiple AI agents to collect, analyze, and report
    on sprint performance using Trello board data.
    """

    def __init__(
        self,
        board_id: str,
        output_file: Optional[str] = None,
        verbose: bool = True
    ):
        """
        Initialize the Scrum Master crew.

        Args:
            board_id: ID of the Trello board to analyze.
            output_file: Optional output file path for the report.
            verbose: Whether to enable verbose logging.
        """
        # Initialize logger using the utility function
        self._std_logger = get_logger(__name__)
        self._std_logger.info("Initializing ScrumMasterCrew")

        self.board_id = board_id
        self.verbose = verbose
        self.output_file = output_file or f"reports/sprint_report_{datetime.now().strftime('%Y%m%d')}.md"
        
        # Initialize the language model
        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            temperature=0.7
        )
        
        # Initialize Trello tools
        self.trello_tools = TrelloTools(
            api_key=os.getenv("TRELLO_API_KEY"),
            api_token=os.getenv("TRELLO_API_TOKEN"),
            board_id=self.board_id
        )
        
        # Initialize agents
        self.analysis_agent = AnalysisAgent(
            trello_tools=self.trello_tools,
            verbose=verbose,
            llm=self.llm
        )
        self.reporting_agent = ReportingAgent(
            verbose=verbose,
            llm=self.llm
        )
        
        # Initialize report generator
        self.report_generator = ReportGenerator()
        
        self._std_logger.info(f"Initialized ScrumMasterCrew with Board ID: {board_id}")

    async def run(self) -> str:
        """
        Run the Scrum Master crew to analyze and report on sprint data.

        Returns:
            Path to the generated report.
        """
        try:
            self._std_logger.info("Starting Scrum Master AI Agent")
            
            # First, fetch the board data
            board_data = await self.trello_tools.get_board_data()
            if not board_data or "error" in board_data:
                raise ValueError(f"Failed to fetch board data: {board_data.get('error', 'Unknown error')}")
            
            # Run analysis task with board data
            analysis_result = await self.analysis_agent.analyze_sprint_data(board_data)
            
            if not analysis_result:
                raise ValueError("Analysis failed: No results returned")
            
            # Generate report using the report generator
            try:
                report_path = self.report_generator.generate_report(
                    sprint_data=board_data,
                    analysis_data=analysis_result,
                    output_file=self.output_file
                )
                
                if not report_path:
                    raise ValueError("Failed to generate report")
                    
                self._std_logger.info(f"Successfully generated report at {report_path}")
                return report_path
                
            except Exception as e:
                self._std_logger.error(f"Error generating report: {e}")
                raise
            
        except Exception as e:
            self._std_logger.error(f"Error running Scrum Master crew: {e}")
            raise