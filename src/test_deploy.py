"""
Simple script to test deploying all agents in sequence.
"""

import os
import json
import asyncio
from src.utils.logging_utils import setup_logging, get_logger
from src.agents.supervisor_agent import SupervisorAgent
from src.agents.data_collection_agent import DataCollectionAgent
from src.agents.analysis_agent import AnalysisAgent
from src.agents.reporting_agent import ReportingAgent

# Set up logging
setup_logging(log_file="logs/agent.log", log_level="DEBUG")
logger = get_logger(__name__)

async def deploy_agents():
    """Deploy all agents and save their addresses"""
    addresses = {}
    
    # Deploy supervisor agent
    logger.info("Starting Supervisor agent...")
    supervisor = SupervisorAgent(
        name="Scrum Master Supervisor",
        port=8000,
        endpoint=["http://127.0.0.1:8000/submit"],
        mailbox=True
    )
    await supervisor.setup()
    addresses["supervisor"] = supervisor.address
    logger.info(f"Supervisor agent address: {supervisor.address}")
    
    # Deploy data collection agent
    logger.info("Starting Data Collection agent...")
    data_agent = DataCollectionAgent(
        name="Data Collection Specialist",
        port=8001,
        endpoint=["http://127.0.0.1:8001/submit"],
        mailbox=True
    )
    await data_agent.setup()
    addresses["data_collection"] = data_agent.address
    logger.info(f"Data Collection agent address: {data_agent.address}")
    
    # Deploy analysis agent
    logger.info("Starting Analysis agent...")
    analysis_agent = AnalysisAgent(
        name="Sprint Analysis Specialist",
        port=8002,
        endpoint=["http://127.0.0.1:8002/submit"],
        mailbox=True
    )
    await analysis_agent.setup()
    addresses["analysis"] = analysis_agent.address
    logger.info(f"Analysis agent address: {analysis_agent.address}")
    
    # Deploy reporting agent
    logger.info("Starting Reporting agent...")
    reporting_agent = ReportingAgent(
        name="Report Generation Specialist",
        port=8003,
        endpoint=["http://127.0.0.1:8003/submit"],
        mailbox=True
    )
    await reporting_agent.setup()
    addresses["reporting"] = reporting_agent.address
    logger.info(f"Reporting agent address: {reporting_agent.address}")
    
    # Save addresses to file
    with open("agent_addresses.json", "w") as f:
        json.dump(addresses, f, indent=2)
    logger.info("Saved agent addresses to agent_addresses.json")
    
    # Keep the program running
    logger.info("All agents deployed. Press Ctrl+C to exit.")
    while True:
        await asyncio.sleep(60)  # Keep alive

if __name__ == "__main__":
    try:
        asyncio.run(deploy_agents())
    except KeyboardInterrupt:
        logger.info("Deployment interrupted by user")
    except Exception as e:
        logger.error(f"Error deploying agents: {e}") 