"""
Test script for verifying agent registration and communication.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from src.agents.supervisor_agent import SupervisorAgent
from src.agents.data_collection_agent import DataCollectionAgent
from src.agents.analysis_agent import AnalysisAgent
from src.agents.reporting_agent import ReportingAgent
from src.models.messages import (
    DataRequest,
    DataResponse,
    AnalysisRequest,
    AnalysisResponse,
    ReportRequest,
    ReportResponse,
    StatusRequest,
    StatusResponse
)
from src.utils.logging_utils import get_logger
from src.config.agentverse import get_agentverse_token

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = get_logger(__name__)

async def start_agent(agent, name):
    """Start an agent and handle any startup errors."""
    try:
        logger.info(f"Starting {name}...")
        await agent.run_async()
        logger.info(f"{name} started successfully")
    except Exception as e:
        logger.error(f"Error starting {name}: {str(e)}")
        raise

async def test_agent_registration():
    """Test that all agents can be registered and communicate."""
    try:
        token = get_agentverse_token()
        if not token:
            logger.error("No Agentverse token found. Please set AGENTVERSE_TOKEN environment variable.")
            raise ValueError("No Agentverse token found")

        # Create agents
        supervisor_agent = SupervisorAgent(
            name="AI_ScrumMaster_supervisor_agent",
            port=8100,
            seed="AI_ScrumMaster_supervisor",
            endpoint="http://127.0.0.1:8100"
        )
        data_collection_agent = DataCollectionAgent(
            name="AI_ScrumMaster_data_collection_agent",
            port=8101,
            seed="AI_ScrumMaster_data_collection",
            endpoint="http://127.0.0.1:8101"
        )
        analysis_agent = AnalysisAgent(
            name="AI_ScrumMaster_analysis_agent",
            port=8102,
            seed="AI_ScrumMaster_analysis",
            endpoint="http://127.0.0.1:8102"
        )
        reporting_agent = ReportingAgent(
            name="AI_ScrumMaster_reporting_agent",
            port=8103,
            seed="AI_ScrumMaster_reporting",
            endpoint="http://127.0.0.1:8103"
        )

        # Start agents asynchronously
        agent_tasks = [
            start_agent(supervisor_agent, "AI_ScrumMaster_supervisor_agent"),
            start_agent(data_collection_agent, "AI_ScrumMaster_data_collection_agent"),
            start_agent(analysis_agent, "AI_ScrumMaster_analysis_agent"),
            start_agent(reporting_agent, "AI_ScrumMaster_reporting_agent")
        ]

        # Wait for all agents to start
        logger.info("Waiting for all agents to start...")
        await asyncio.gather(*agent_tasks)

        # Allow time for agent registration
        logger.info("Waiting for agent registration...")
        await asyncio.sleep(10)

        # Trigger workflow
        logger.info("Triggering data collection workflow...")
        data_request = DataRequest(
            sender="test",
            board_id="test_board",
            list_ids=["list1", "list2"],
            start_date="2024-01-01",
            end_date="2024-01-31"
        )
        await data_collection_agent.handle_data_request(data_request)

        # Allow time to observe interactions
        logger.info("Waiting for workflow completion...")
        await asyncio.sleep(15)

        logger.info("Test completed successfully.")

    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        raise
    finally:
        # Cancel all tasks
        logger.info("Cleaning up tasks...")
        for task in asyncio.all_tasks():
            if task is not asyncio.current_task():
                task.cancel()

        try:
            await asyncio.gather(*[task for task in asyncio.all_tasks() if task is not asyncio.current_task()], return_exceptions=True)
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    try:
        asyncio.run(test_agent_registration())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise 