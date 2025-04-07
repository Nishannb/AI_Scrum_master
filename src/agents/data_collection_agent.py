"""
Data Collection Agent Module

This module defines the DataCollectionAgent class, which collects
sprint data from various sources.
"""

import logging
import os
from typing import Dict, Any, Optional, Union, List
from datetime import datetime
from trello import TrelloClient
from uagents import Agent, Context, Protocol
from src.models.messages import (
    StatusRequest, StatusResponse,
    DataRequest, DataResponse
)
from src.config.agentverse import get_agentverse_config

class DataCollectionProtocol(Protocol):
    """Protocol for data collection operations."""
    
    protocol_name = "data_collection"
    protocol_description = "Protocol for collecting sprint data from Trello"
    protocol_version = "0.1.0"

class DataCollectionAgent(Agent):
    """
    Agent responsible for collecting sprint data from various sources.
    """

    def __init__(
        self,
        name: str = "Data Collection Specialist",
        port: int = 8001,
        seed: Optional[str] = None,
        endpoint: Optional[str] = None,
        agentverse: Optional[Dict[str, str]] = None,
        mailbox: bool = True
    ):
        """
        Initialize the data collection agent.

        Args:
            name: The name of the agent
            port: The port to run the agent on
            seed: Optional seed for deterministic agent creation
            endpoint: Optional endpoint(s) for the agent, can be a string or list of strings
            agentverse: Optional agentverse configuration
            mailbox: Whether to use a mailbox for communication
        """
        # Convert single endpoint to list if needed
        if isinstance(endpoint, str):
            endpoint = [endpoint]

        # Ensure HTTPS for production
        if endpoint:
            endpoint = [e.replace("http://", "https://") if e.startswith("http://") else e for e in endpoint]

        super().__init__(
            name=name,
            port=port,
            seed=seed,
            endpoint=endpoint,
            agentverse=agentverse or get_agentverse_config(),
            mailbox=mailbox
        )

        self._logger = logging.getLogger(__name__)
        self._logger.info("Initialized DataCollectionAgent")
        
        # Initialize Trello client if credentials are available
        self._trello_client = None
        self._board_id = None
        try:
            api_key = os.getenv("TRELLO_API_KEY")
            api_token = os.getenv("TRELLO_API_TOKEN")
            board_id = os.getenv("TRELLO_BOARD_ID")
            
            if api_key and api_token and board_id:
                self._trello_client = TrelloClient(
                    api_key=api_key,
                    token=api_token
                )
                self._board_id = board_id
                self._logger.info("Trello client initialized successfully")
            else:
                self._logger.warning("Trello credentials not found in environment variables. Using sample data mode.")
        except Exception as e:
            self._logger.warning(f"Failed to initialize Trello client: {str(e)}. Using sample data mode.")

        # Add the protocol
        self.include(DataCollectionProtocol())

        # This logs the address of the agent when it starts
        @self.on_event("startup")
        async def on_start(ctx: Context):
            self._logger.info(f"Starting DataCollectionAgent {ctx.agent.address}")
            self._logger.info(f"Agent endpoints: {self._endpoints}")

        # Register message handlers
        @self.on_message(DataRequest)
        async def handle_data_request(ctx: Context, sender: str, msg: DataRequest):
            """Handle requests to collect data"""
            try:
                self._logger.info(f"Received data request from {sender}")
                sprint_data = await self.collect_sprint_data(msg.sprint_id)
                await ctx.send(
                    sender,
                    DataResponse(
                        status="success",
                        sprint_data=sprint_data
                    )
                )
            except Exception as e:
                self._logger.error(f"Error collecting data: {str(e)}")
                await ctx.send(
                    sender,
                    DataResponse(
                        status="error",
                        error=str(e)
                    )
                )

        @self.on_message(StatusRequest)
        async def handle_status_request(ctx: Context, sender: str, msg: StatusRequest):
            """Handle status check requests"""
            await ctx.send(
                sender,
                StatusResponse(
                    status="active",
                    details={"last_update": datetime.now().isoformat()}
                )
            )

    async def collect_sprint_data(self, sprint_id: str) -> Dict[str, Any]:
        """Collect sprint data from Trello"""
        try:
            self._logger.info(f"Collecting data for sprint {sprint_id}")
            
            if not self._trello_client or not self._board_id:
                raise ValueError("Trello client not initialized. Please check your environment variables.")
            
            # Get the board
            board = self._trello_client.get_board(self._board_id)
            
            # Fetch all data
            cards = board.open_cards()
            lists = board.open_lists()
            members = board.all_members()
            
            # Convert to dictionary format
            cards_data = [{
                "id": card.id,
                "name": card.name,
                "desc": card.desc,
                "idList": card.idList,
                "due": card.due,
                "dateLastActivity": card.dateLastActivity.isoformat() if card.dateLastActivity else None,
                "labels": [{"id": label.id, "name": label.name, "color": label.color} for label in card.labels],
                "members": [member_id for member_id in card.member_ids],  # Just store member IDs
                "url": card.url
            } for card in cards]
            
            lists_data = [{
                "id": lst.id,
                "name": lst.name,
                "closed": lst.closed
            } for lst in lists]
            
            members_data = []
            for member in members:
                try:
                    members_data.append({
                        "id": member.id,
                        "fullName": member.full_name if hasattr(member, 'full_name') else member.username,
                        "username": member.username if hasattr(member, 'username') else None
                    })
                except Exception as e:
                    self._logger.warning(f"Error processing member data: {str(e)}")
                    continue
            
            # Organize the data
            sprint_data = {
                "sprint_id": sprint_id,
                "board_id": self._board_id,
                "cards": cards_data,
                "lists": lists_data,
                "members": members_data,
                "timestamp": datetime.now().isoformat()
            }
            
            self._logger.info(f"Successfully collected data for sprint {sprint_id}")
            return sprint_data
            
        except Exception as e:
            self._logger.error(f"Error collecting sprint data: {str(e)}")
            raise

    async def run(self) -> None:
        """
        Start the agent.
        """
        try:
            # The agent will automatically register with the Almanac when run() is called
            await super().run()
        except Exception as e:
            self._logger.error(f"Error running agent: {str(e)}")
            raise