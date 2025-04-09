"""
Supervisor Agent Module

This module defines the SupervisorAgent class, which coordinates
the AI scrum master system.
"""

import logging
import aiohttp
from datetime import datetime
from typing import Dict, Any, Optional, List
from uagents import Agent, Context, Protocol
from uagents_core.types import DeliveryStatus, MsgStatus
from src.models.messages import (
    StatusRequest, StatusResponse,
    DataRequest, DataResponse,
    AnalysisRequest, AnalysisResponse,
    ReportRequest, ReportResponse
)
from src.config.agentverse import get_agentverse_config
# from fetchai.registration import register_with_agentverse
import json
import os
import asyncio
from fetchai.registration import AgentverseConnectRequest, AgentUpdates, AgentverseConfig

class SupervisorAgent(Agent):
    """
    Agent responsible for coordinating the AI scrum master system.

    This agent manages the workflow between data collection, analysis,
    and reporting agents.
    """

    def __init__(
        self,
        name: str = "Scrum Master Supervisor",
        port: int = 8000,
        seed: Optional[str] = None,
        endpoint: Optional[str] = None,
        agentverse: Optional[Dict[str, str]] = None,
        mailbox: bool = True
    ):
        """
        Initialize the supervisor agent.

        Args:
            name: The name of the agent
            port: The port to run the agent on
            seed: Optional seed for deterministic agent creation
            endpoint: Optional endpoint for the agent
            agentverse: Optional agentverse configuration
            mailbox: Whether to use a mailbox for communication
        """
        super().__init__(
            name=name,
            port=port,
            seed=seed,
            endpoint=endpoint,
            agentverse=agentverse or get_agentverse_config(),
            mailbox=mailbox
        )

        self._logger = logging.getLogger(__name__)
        self._logger.info("Initialized SupervisorAgent")

        # Store pending requests
        self._pending_requests = {}

        # Register message handlers
        @self.on_message(DataRequest)
        async def handle_data_request(ctx: Context, sender: str, msg: DataRequest):
            """Handle data collection requests"""
            try:
                self._logger.info(f"Received data request from {sender}: {msg}")
                
                # Discover data collection agents
                data_agents = await self.discover_agents("data_collection")
                if not data_agents:
                    self._logger.warning("No data collection agents found")
                    await ctx.send(
                        sender,
                        DataResponse(
                            status="error",
                            error="No data collection agents available"
                        )
                    )
                    return

                # Store the sender for later response
                request_id = f"data_request_{datetime.now().isoformat()}"
                self._pending_requests[request_id] = sender

                # Send request to data collection agents
                for agent_address in data_agents:
                    self._logger.info(f"Forwarding request to data collection agent: {agent_address}")
                    try:
                        status = await ctx.send(agent_address, msg)
                        if isinstance(status, MsgStatus):
                            if status.status == DeliveryStatus.SENT:
                                self._logger.info(f"Request sent successfully to {agent_address}")
                            else:
                                self._logger.error(f"Failed to send request to data collection agent {agent_address}: {status.detail}")
                                await ctx.send(
                                    sender,
                                    DataResponse(
                                        status="error",
                                        error=f"Failed to send request to data collection agent: {status.detail}"
                                    )
                                )
                    except Exception as e:
                        self._logger.error(f"Error sending request to data collection agent: {str(e)}")
                        await ctx.send(
                            sender,
                            DataResponse(
                                status="error",
                                error=f"Error sending request to data collection agent: {str(e)}"
                            )
                        )
            except Exception as e:
                self._logger.error(f"Error handling data request: {str(e)}")
                await ctx.send(
                    sender,
                    DataResponse(
                        status="error",
                        error=str(e)
                    )
                )

        @self.on_message(StatusResponse)
        async def handle_status_response(ctx: Context, sender: str, msg: StatusResponse):
            """Handle status responses from other agents"""
            self._logger.info(f"Received status response from {sender}: {msg.status}")

        @self.on_message(DataResponse)
        async def handle_data_response(ctx: Context, sender: str, msg: DataResponse):
            """Handle data collection responses"""
            try:
                self._logger.info(f"Received data from {sender}")
                
                # Forward the response to the original requester
                for request_id, requester in self._pending_requests.items():
                    if request_id.startswith("data_request_"):
                        try:
                            await ctx.send(
                                requester,
                                msg
                            )
                            del self._pending_requests[request_id]
                            self._logger.info(f"Forwarded data response to {requester}")
                            break
                        except Exception as e:
                            self._logger.error(f"Error forwarding data response: {str(e)}")

                if msg.status == "success":
                    # Discover analysis agents
                    analysis_agents = await self.discover_agents("analysis")
                    if not analysis_agents:
                        self._logger.warning("No analysis agents found")
                        return

                    # Using proper data format - send explicit dict for cross-system compatibility
                    sprint_data = msg.sprint_data
                    self._logger.info(f"Found agent for role analysis: {analysis_agents[0]}")

                    # Send data to analysis agents
                    for agent_address in analysis_agents:
                        try:
                            # Explicitly format as dict when sending across agents
                            analysis_request = AnalysisRequest(sprint_data=sprint_data)
                            
                            # Log the outgoing request for debugging
                            self._logger.debug(f"Sending analysis request to {agent_address}")
                            self._logger.debug(f"Request type: {type(analysis_request)}")
                            self._logger.debug(f"Sprint data type: {type(sprint_data)}")
                            
                            status = await ctx.send(agent_address, analysis_request)
                            
                            if isinstance(status, MsgStatus):
                                if status.status == DeliveryStatus.SENT:
                                    self._logger.info(f"Analysis request sent to {agent_address}")
                                else:
                                    self._logger.error(f"Failed to send data to analysis agent {agent_address}: {status.detail}")
                            else:
                                self._logger.error(f"Unexpected status type: {type(status)}")
                        except Exception as e:
                            self._logger.error(f"Error sending data to analysis agent {agent_address}: {str(e)}")
            except Exception as e:
                self._logger.error(f"Error handling data response: {str(e)}")

        @self.on_message(AnalysisResponse)
        async def handle_analysis_response(ctx: Context, sender: str, msg: AnalysisResponse):
            """Handle analysis responses"""
            try:
                self._logger.info(f"Received analysis from {sender}")
                
                if msg.status == "success":
                    # Discover reporting agents
                    reporting_agents = await self.discover_agents("reporting")
                    if not reporting_agents:
                        self._logger.warning("No reporting agents found")
                        return

                    # Using proper data format
                    analysis_results = msg.analysis_results
                    self._logger.info(f"Found agent for role reporting: {reporting_agents[0]}")

                    # Send analysis to reporting agents
                    for agent_address in reporting_agents:
                        try:
                            # Explicitly format as dict when sending across agents
                            report_request = ReportRequest(analysis_results=analysis_results)
                            
                            # Log the outgoing request for debugging
                            self._logger.debug(f"Sending report request to {agent_address}")
                            self._logger.debug(f"Request type: {type(report_request)}")
                            self._logger.debug(f"Analysis results type: {type(analysis_results)}")
                            
                            status = await ctx.send(agent_address, report_request)
                            
                            if isinstance(status, MsgStatus):
                                if status.status == DeliveryStatus.SENT:
                                    self._logger.info(f"Report request sent to {agent_address}")
                                else:
                                    self._logger.error(f"Failed to send analysis to reporting agent {agent_address}: {status.detail}")
                            else:
                                self._logger.error(f"Unexpected status type: {type(status)}")
                        except Exception as e:
                            self._logger.error(f"Error sending analysis to reporting agent {agent_address}: {str(e)}")
                else:
                    self._logger.error(f"Analysis error: {msg.error if hasattr(msg, 'error') else 'Unknown error'}")
            except Exception as e:
                self._logger.error(f"Error handling analysis response: {str(e)}")

    async def discover_agents(self, role: str) -> List[str]:
        """Discover agents with a specific role from agent_addresses.json"""
        try:
            if not os.path.exists("agent_addresses.json"):
                self._logger.warning("agent_addresses.json not found")
                return []
                
            with open("agent_addresses.json", "r") as f:
                addresses = json.load(f)
                if role in addresses:
                    self._logger.info(f"Found agent for role {role}: {addresses[role]}")
                    return [addresses[role]]
                else:
                    self._logger.warning(f"No agent found for role: {role}")
                    return []
        except Exception as e:
            self._logger.error(f"Error discovering agents: {str(e)}")
            return []

    async def send_message_to_agent(
        self,
        destination: str,
        message: Any,
        response_type: Optional[type] = None,
        ctx: Optional[Context] = None
    ) -> MsgStatus:
        """Send a message to another agent through AgentVerse"""
        try:
            if ctx is None:
                raise ValueError("Context is required for sending messages")
            return await ctx.send(
                destination,
                message,
                response_type=response_type
            )
        except Exception as e:
            self._logger.error(f"Error sending message: {str(e)}")
            return MsgStatus(
                status=DeliveryStatus.FAILED,
                detail=str(e),
                destination=destination
            )

    async def coordinate_workflow(self, ctx: Optional[Context] = None) -> None:
        """
        Coordinate the workflow between agents.

        Args:
            ctx: Optional context for sending messages
        """
        try:
            # Discover collection agents
            collection_agents = await self.discover_agents("collection")
            if not collection_agents:
                self._logger.warning("No collection agents found")
                return

            # Request data collection
            for agent in collection_agents:
                if ctx:
                    await ctx.send(
                        agent,
                        DataRequest(
                            sprint_id=None  # Optional sprint ID
                        )
                    )
                
        except Exception as e:
            self._logger.error(f"Error in workflow coordination: {str(e)}")

    async def run(self) -> None:
        """Start the supervisor agent."""
        try:
            # Register in Agentverse first
            await self.register_in_agentverse()
            
            # Then start the agent
            await super().run()
            
        except Exception as e:
            self._logger.error(f"Error running supervisor agent: {str(e)}")
            raise

    async def register_in_agentverse(self) -> None:
        """
        Register the agent in the Fetch.ai Agentverse.
        """
        try:
            config = get_agentverse_config()
            token = config.get("token")
            if not token:
                self._logger.error("No Agentverse token provided")
                return

            # Define agent details with proper markdown formatting
            readme = """
# Scrum Master Supervisor Agent

## Overview
An intelligent agent that coordinates the AI scrum master system, managing workflow between data collection, analysis, and reporting agents.

## Features
- Coordinates sprint data collection and analysis
- Monitors sprint progress and team performance
- Generates comprehensive sprint reports and recommendations

## Protocols
### Data Collection Protocol
- Receives data collection requests
- Forwards requests to data collection agents
- Handles data collection responses

### Analysis Protocol
- Coordinates data analysis workflow
- Manages analysis requests and responses
- Ensures data quality and completeness

### Reporting Protocol
- Manages report generation workflow
- Coordinates with reporting agents
- Delivers final sprint reports

## Message Types
### DataRequest
```json
{
    "sprint_id": "SPRINT-123",
    "start_date": "2024-03-01",
    "end_date": "2024-03-14"
}
```

### DataResponse
```json
{
    "status": "success",
    "sprint_data": {
        "sprint_id": "SPRINT-123",
        "tasks": [...],
        "metrics": {...}
    }
}
```

## Usage Example
```python
from uagents import Agent, Context
from src.models.messages import DataRequest

async def request_sprint_analysis(ctx: Context):
    request = DataRequest(
        sprint_id="SPRINT-123",
        start_date="2024-03-01",
        end_date="2024-03-14"
    )
    await ctx.send(SUPERVISOR_ADDRESS, request)
```

## Integration
The agent can be integrated with:
- Jira
- Trello
- GitHub Projects
- Custom project management tools

## Requirements
- Python 3.8+
- uAgents framework
- Active AgentVerse registration
"""

            # Get the endpoint URL as string
            endpoint_url = f"http://127.0.0.1:{self._port}/submit"
            self._logger.info(f"Registering agent with endpoint: {endpoint_url}")
            
            # Register with proper agent details
            try:
                # First, ensure we're registered with the Almanac
                await self.register_with_almanac()
                
                # Then register with AgentVerse
                request = AgentverseConnectRequest(
                    user_token=token,
                    agent_type="supervisor",
                    endpoint=endpoint_url
                )
                
                agent_details = AgentUpdates(
                    name="Scrum Master Supervisor",
                    readme=readme,
                    agent_type="supervisor"
                )
                
                # Try registration multiple times
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        response = await register_in_agentverse(
                            request=request,
                            identity=self._identity,
                            prefix="test-agent",
                            agentverse=AgentverseConfig(url="https://agentverse.ai"),
                            agent_details=agent_details
                        )
                        
                        if response.success:
                            self._logger.info("Successfully registered in Agentverse")
                            return
                        else:
                            self._logger.warning(f"Registration attempt {attempt + 1} failed: {response.detail}")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(2)  # Wait before retrying
                            else:
                                self._logger.error("Failed to register with Agentverse after multiple attempts")
                    except Exception as reg_error:
                        self._logger.error(f"Registration attempt {attempt + 1} failed: {str(reg_error)}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2)
                        else:
                            self._logger.error("Failed to register with Agentverse after multiple attempts")
                
            except Exception as e:
                self._logger.error(f"Error during registration: {str(e)}")
                # Continue running even if registration fails
                pass
            
        except Exception as e:
            self._logger.error(f"Error in registration setup: {str(e)}")
            # Continue running even if registration setup fails
            pass

    async def register_with_almanac(self) -> None:
        """Register the agent with the Almanac service"""
        try:
            # Get the endpoint URL as string
            endpoint_url = f"http://127.0.0.1:{self._port}/submit"
            
            # Register with Almanac
            await self._identity.register_with_almanac(
                endpoint_url,
                protocols=[{
                    "name": "data_collection",
                    "description": "Handles sprint data collection workflow"
                }, {
                    "name": "analysis",
                    "description": "Manages sprint data analysis"
                }, {
                    "name": "reporting",
                    "description": "Coordinates sprint report generation"
                }]
            )
            self._logger.info("Successfully registered with Almanac")
        except Exception as e:
            self._logger.error(f"Failed to register with Almanac: {str(e)}")
            # Continue running even if registration fails
            pass 