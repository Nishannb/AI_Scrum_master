"""
Test script to interact with the Supervisor agent and test the complete agent flow.
"""

# Set up logging first
from src.utils.logging_utils import setup_logging, get_logger
setup_logging(log_file="logs/agent.log", log_level="DEBUG")
logger = get_logger(__name__)

import asyncio
import json
import os
from typing import Dict, Any
from dotenv import load_dotenv
from uagents import Agent, Context, Protocol
from uagents.network import get_ledger
from uagents.crypto import Identity
from uagents.resolver import GlobalResolver
from uagents.config import REGISTRATION_UPDATE_INTERVAL_SECONDS

from src.models.messages import (
    DataRequest, DataResponse,
    AnalysisRequest, AnalysisResponse,
    ReportRequest, ReportResponse
)
from src.config.agentverse import get_agentverse_config
from uagents_core.types import DeliveryStatus, MsgStatus

async def test_agent_flow():
    # Initialize test agent with proper endpoint configuration
    test_agent = Agent(
        name="Test Agent",
        port=8005,  # Changed from 8004 to 8005 to avoid conflicts
        seed="test_agent_seed",
        endpoint=["http://127.0.0.1:8005/submit"],
        mailbox=True
    )
    
    # Create a protocol for message handling
    protocol = Protocol("Test Protocol")
    
    # Load agent addresses
    try:
        with open("agent_addresses.json", "r") as f:
            agent_addresses = json.load(f)
        supervisor_address = agent_addresses["supervisor"]
        logger.info(f"Loaded supervisor address: {supervisor_address}")
    except Exception as e:
        logger.error(f"Failed to load agent addresses: {e}")
        return
    
    # Send a single test request to the supervisor
    @test_agent.on_event("startup")
    async def startup(ctx: Context):
        try:
            # Create the request
            request = DataRequest(
                sprint_id="TEST-SPRINT-1",
                start_date="2024-03-01",
                end_date="2024-03-14"
            )
            
            # Send the request to the supervisor with proper message status handling
            status = await ctx.send(supervisor_address, request)
            if isinstance(status, MsgStatus):
                if status.status == DeliveryStatus.SENT:
                    logger.info(f"Successfully sent test request to supervisor: {request}")
                else:
                    logger.error(f"Failed to send request: {status.detail}")
            else:
                logger.warning(f"Unexpected status type: {type(status)}")
        except Exception as e:
            logger.error(f"Error sending test request: {e}")
    
    # Handle the report response
    @protocol.on_message(ReportResponse)
    async def handle_report(ctx: Context, sender: str, msg: ReportResponse):
        if msg.status == "success":
            logger.info("\nReport received successfully!")
            logger.info(f"Report details: {msg.report}")
            # Stop the agent after receiving the report
            await ctx.stop()
        else:
            logger.error(f"\nError in report generation: {msg.error}")
            # Stop the agent after error
            await ctx.stop()
    
    # Handle data response
    @protocol.on_message(DataResponse)
    async def handle_data_response(ctx: Context, sender: str, msg: DataResponse):
        if msg.status == "success":
            logger.info("\nData received successfully!")
            logger.info(f"Sprint data: {msg.sprint_data}")
            # Print details for debugging
            logger.info(f"Data response type: {type(msg.sprint_data)}")
            logger.info(f"Data response keys: {msg.sprint_data.keys() if isinstance(msg.sprint_data, dict) else 'Not a dict'}")
        else:
            logger.error(f"\nError in data collection: {msg.error}")
            # Stop the agent on error
            await ctx.stop()
    
    # Handle analysis response
    @protocol.on_message(AnalysisResponse)
    async def handle_analysis_response(ctx: Context, sender: str, msg: AnalysisResponse):
        if msg.status == "success":
            logger.info("\nAnalysis received successfully!")
            logger.info(f"Analysis results: {msg.analysis_results}")
            # Print details for debugging
            logger.info(f"Analysis response type: {type(msg.analysis_results)}")
            logger.info(f"Analysis response keys: {msg.analysis_results.keys() if isinstance(msg.analysis_results, dict) else 'Not a dict'}")
        else:
            logger.error(f"\nError in analysis: {msg.error}")
            # Stop the agent on error
            await ctx.stop()
    
    # Include the protocol in the agent
    test_agent.include(protocol)
    
    # Run the agent
    try:
        await test_agent.run_async()
    except Exception as e:
        logger.error(f"Error running test agent: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(test_agent_flow())
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}") 