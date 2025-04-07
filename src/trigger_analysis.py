"""
Script to trigger the agent analysis process.
"""

import asyncio
import json
import logging
from pathlib import Path
from src.models.messages import DataRequest
from src.config.agentverse import get_agentverse_config
from src.utils.logging_utils import get_logger
from uagents_core.identity import Identity
from uagents_core.types import DeliveryStatus, MsgStatus
import aiohttp

logger = get_logger(__name__)

def get_supervisor_address() -> str:
    """Get the supervisor agent's address from the saved file."""
    try:
        with open("agent_addresses.json", "r") as f:
            addresses = json.load(f)
            return addresses.get("supervisor")
    except FileNotFoundError:
        raise ValueError(
            "Agent addresses file not found. Please deploy the agents first."
        )
    except KeyError:
        raise ValueError(
            "Supervisor agent address not found. Please check the deployment."
        )

async def trigger_analysis(sprint_id: str):
    """Trigger the supervisor agent to start the sprint analysis process"""
    try:
        # Get supervisor address
        supervisor_address = get_supervisor_address()
        if not supervisor_address:
            raise ValueError("Supervisor agent address not found")
            
        # Get your agent's identity
        identity = Identity.generate()
        
        # Create the request message
        message = DataRequest(sprint_id=sprint_id)
        
        # Get AgentVerse config
        config = get_agentverse_config()
        
        # Send message to supervisor agent
        status = await send_message_to_agent(
            sender=identity,
            target=supervisor_address,
            payload=message.model_dump(),
            agentverse_base_url=config["url"],
            token=config["token"]
        )
        
        if status.status == DeliveryStatus.SENT:
            logger.info("Successfully triggered analysis process")
        else:
            logger.error(f"Failed to trigger analysis: {status.detail}")
            
        return status
        
    except Exception as e:
        logger.error(f"Error triggering analysis: {str(e)}")
        raise

async def send_message_to_agent(
    sender: Identity,
    target: str,
    payload: dict,
    agentverse_base_url: str,
    token: str
) -> MsgStatus:
    """Send a message to an agent through AgentVerse"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{agentverse_base_url}/v1/messages",
                json={
                    "sender": sender.address,
                    "target": target,
                    "payload": payload
                },
                headers={"Authorization": f"Bearer {token}"}
            ) as response:
                if response.status == 200:
                    return MsgStatus(
                        status=DeliveryStatus.SENT,
                        detail="Message sent successfully",
                        destination=target
                    )
                else:
                    return MsgStatus(
                        status=DeliveryStatus.FAILED,
                        detail=await response.text(),
                        destination=target
                    )
    except Exception as e:
        return MsgStatus(
            status=DeliveryStatus.FAILED,
            detail=str(e),
            destination=target
        )

if __name__ == "__main__":
    try:
        # Example usage
        sprint_id = "SPRINT-123"
        asyncio.run(trigger_analysis(sprint_id))
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Process failed: {str(e)}")
        raise 