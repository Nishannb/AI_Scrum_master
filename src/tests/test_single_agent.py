"""
Test file for single agent registration and operation.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from src.agents.data_collection_agent import DataCollectionAgent
from src.utils.logging_utils import get_logger
from src.config.agentverse import get_agentverse_token
from typing import Optional, List
import aiohttp

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = get_logger(__name__)

async def test_single_agent():
    """Test a single agent's registration and basic functionality."""
    try:
        # Check for Agentverse token
        token = get_agentverse_token()
        if not token:
            logger.error("No Agentverse token found. Please set AGENTVERSE_TOKEN environment variable.")
            raise ValueError("No Agentverse token found")

        # Create agent with endpoints in array format
        agent = DataCollectionAgent(
            name="data_collection_agent",
            port=8100,
            seed="data_collection_seeds_tests_next",
            endpoint=["http://127.0.0.1:8100/submit"],
            agentverse={
                "url": "https://agentverse.ai",  # or your AgentVerse URL
                "token": token  # get your token from config
            },
            mailbox=True  # Enable mailbox for remote communication
        )

        # Log agent details
        logger.info(f"Agent network address: {agent.wallet.address()}")
        logger.info(f"Agent endpoints: {agent._endpoints}")

        # Start the agent
        logger.info("Starting agent...")
        await agent.run_async()

        # Allow time for registration
        logger.info("Waiting for agent registration...")
        await asyncio.sleep(10)

        # Publish manifest
        await agent.publish_manifest({
            "metadata": {
                "name": agent._name,
                "role": "supervisor",  # or "data_collection", "analysis", etc.
                "version": "1.0.0"
            }
        })

        logger.info("Test completed successfully.")

    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        raise
    finally:
        # Clean up tasks
        logger.info("Cleaning up tasks...")
        for task in asyncio.all_tasks():
            if task is not asyncio.current_task():
                task.cancel()

        try:
            await asyncio.gather(*[task for task in asyncio.all_tasks() if task is not asyncio.current_task()], return_exceptions=True)
        except asyncio.CancelledError:
            pass

async def discover_agents(self, role: str) -> List[str]:
    """Discover agents with a specific role on AgentVerse"""
    try:
        # Query AgentVerse for agents with the specified role
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self._agentverse.url}/v1/agents",
                params={"role": role},
                headers={"Authorization": f"Bearer {self._agentverse.token}"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return [agent["address"] for agent in data["agents"]]
                else:
                    self._logger.error(f"Failed to discover agents: {await response.text()}")
                    return []
    except Exception as e:
        self._logger.error(f"Error discovering agents: {str(e)}")
        return []

async def send_message_to_agent(
    self,
    destination: str,
    message: Model,
    response_type: Optional[type[Model]] = None
) -> MsgStatus:
    """Send a message to another agent through AgentVerse"""
    try:
        return await self.send(
            destination,
            message,
            response_type=response_type,
            sync=True  # Wait for response
        )
    except Exception as e:
        self._logger.error(f"Error sending message: {str(e)}")
        return MsgStatus(
            status=DeliveryStatus.FAILED,
            detail=str(e),
            destination=destination
        )

async def trigger_supervisor(sprint_id: str):
    """Trigger the supervisor agent to start the sprint analysis process"""
    supervisor_address = "your_supervisor_agent_address"  # Get this from AgentVerse
    message = DataRequest(sprint_id=sprint_id)
    
    status = await send_message_to_agent(
        sender=your_identity,  # Your agent's identity
        target=supervisor_address,
        payload=message.model_dump(),
        agentverse_base_url="https://agentverse.ai"  # or your AgentVerse URL
    )
    
    return status

if __name__ == "__main__":
    try:
        asyncio.run(test_single_agent())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise 