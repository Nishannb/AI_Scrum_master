"""
Trello Tools Module

This module provides utilities for interacting with the Trello API.
"""

import logging
import ssl
from typing import Dict, List, Any, Optional
import aiohttp
from datetime import datetime, timezone
import certifi

from src.utils.logging_utils import get_logger


class TrelloError(Exception):
    """Base exception for Trello API errors."""
    pass


class TrelloAPIError(TrelloError):
    """Exception for Trello API errors."""
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(f"Trello API error (status {status}): {message}")


class TrelloConnectionError(TrelloError):
    """Exception for Trello connection errors."""
    pass


class TrelloTools:
    """
    Utility class for interacting with the Trello API.
    """

    def __init__(self, api_key: str, api_token: str, board_id: str):
        """
        Initialize the TrelloTools instance.

        Args:
            api_key: Trello API key.
            api_token: Trello API token.
            board_id: ID of the Trello board to analyze.
        """
        if not api_key or not api_token or not board_id:
            raise ValueError("API key, token, and board ID are required")

        self._api_key = api_key
        self._api_token = api_token
        self._board_id = board_id
        self._base_url = "https://api.trello.com/1"
        self._std_logger = get_logger(__name__)

        # Set up SSL context
        self._ssl_context = ssl.create_default_context(cafile=certifi.where())

    async def _make_request(self, url: str, params: Dict[str, Any]) -> Any:
        """
        Make a request to the Trello API.

        Args:
            url: The URL to make the request to.
            params: The parameters to include in the request.

        Returns:
            The JSON response from the API.

        Raises:
            TrelloAPIError: If the API request fails.
            TrelloConnectionError: If there's a connection error.
        """
        try:
            connector = aiohttp.TCPConnector(ssl=self._ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                try:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            error_msg = await response.text()
                            self._std_logger.error(f"API error: {error_msg}")
                            raise TrelloAPIError(response.status, error_msg)
                except aiohttp.ClientError as e:
                    self._std_logger.error(f"Connection error: {e}")
                    raise TrelloConnectionError(f"Failed to connect to Trello API: {e}")

        except Exception as e:
            self._std_logger.error(f"Unexpected error making request: {e}")
            raise

    async def get_cards(self) -> List[Dict[str, Any]]:
        """
        Get all cards from the Trello board.

        Returns:
            List of card objects.

        Raises:
            TrelloAPIError: If the API request fails.
            TrelloConnectionError: If there's a connection error.
        """
        try:
            url = f"{self._base_url}/boards/{self._board_id}/cards"
            params = {
                "key": self._api_key,
                "token": self._api_token,
                "fields": "all",
                "members": "true",
                "member_fields": "all",
                "checklists": "all",
                "checkItemStates": "true",
                "labels": "true",
                "customFieldItems": "true"
            }

            cards = await self._make_request(url, params)
            self._std_logger.info(f"Successfully fetched {len(cards)} cards")
            return cards

        except Exception as e:
            self._std_logger.error(f"Error fetching cards: {e}")
            raise

    async def get_lists(self) -> List[Dict[str, Any]]:
        """
        Get all lists from the Trello board.

        Returns:
            List of list objects.

        Raises:
            TrelloAPIError: If the API request fails.
            TrelloConnectionError: If there's a connection error.
        """
        try:
            url = f"{self._base_url}/boards/{self._board_id}/lists"
            params = {
                "key": self._api_key,
                "token": self._api_token,
                "fields": "all",
                "cards": "none"
            }

            lists = await self._make_request(url, params)
            self._std_logger.info(f"Successfully fetched {len(lists)} lists")
            return lists

        except Exception as e:
            self._std_logger.error(f"Error fetching lists: {e}")
            raise

    async def get_members(self) -> List[Dict[str, Any]]:
        """
        Get all members from the Trello board.

        Returns:
            List of member objects.

        Raises:
            TrelloAPIError: If the API request fails.
            TrelloConnectionError: If there's a connection error.
        """
        try:
            url = f"{self._base_url}/boards/{self._board_id}/members"
            params = {
                "key": self._api_key,
                "token": self._api_token,
                "fields": "all"
            }

            members = await self._make_request(url, params)
            self._std_logger.info(f"Successfully fetched {len(members)} members")
            return members

        except Exception as e:
            self._std_logger.error(f"Error fetching members: {e}")
            raise

    async def get_board_data(self) -> Dict[str, Any]:
        """
        Get all data from the Trello board.

        Returns:
            Dictionary containing board data.

        Raises:
            TrelloAPIError: If any API request fails.
            TrelloConnectionError: If there's a connection error.
        """
        try:
            # Fetch all data concurrently
            cards = await self.get_cards()
            lists = await self.get_lists()
            members = await self.get_members()

            # Validate the data
            if not cards or not lists:
                raise TrelloError("Failed to fetch required board data")

            return {
                "cards": cards,
                "lists": lists,
                "members": members,
                "board_id": self._board_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except (TrelloAPIError, TrelloConnectionError) as e:
            self._std_logger.error(f"Error fetching board data: {e}")
            raise

        except Exception as e:
            self._std_logger.error(f"Unexpected error fetching board data: {e}")
            raise TrelloError(f"Failed to fetch board data: {e}") 