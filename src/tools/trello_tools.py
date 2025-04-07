"""
Trello Tools Module

This module provides tools for interacting with the Trello API to fetch board and card data.
It includes tools for fetching board data, card data, comments, attachments, and more.
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional, Any, Union
import requests
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

# Set up logging
logger = logging.getLogger(__name__)

# Load constants
try:
    with open(os.path.join("config", "constants.json"), "r") as f:
        CONSTANTS = json.load(f)
except Exception as e:
    logger.error(f"Error loading constants: {e}")
    CONSTANTS = {}


class TrelloAPIError(Exception):
    """Exception raised for errors in the Trello API."""
    pass


class TrelloCardData(BaseModel):
    """Model for Trello card data."""
    id: str
    name: str
    desc: Optional[str] = ""
    idList: Optional[str] = None
    idBoard: Optional[str] = None
    due: Optional[str] = None
    dueComplete: Optional[bool] = False
    dateLastActivity: Optional[str] = None
    labels: Optional[List[Dict[str, Any]]] = []
    url: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = []
    comments: Optional[List[Dict[str, Any]]] = []
    members: Optional[List[Dict[str, Any]]] = []
    customFields: Optional[List[Dict[str, Any]]] = []


def get_board_data(board_id: str, api_key: str, api_token: str) -> List[Dict[str, Any]]:
    """
    Fetch board data from Trello API.

    Args:
        board_id: ID of the Trello board.
        api_key: Trello API key.
        api_token: Trello API token.

    Returns:
        List of dictionaries containing card data.

    Raises:
        TrelloAPIError: If there is an error fetching data from Trello.
    """
    url = f"https://api.trello.com/1/boards/{board_id}/cards"
    query = {
        'key': api_key,
        'token': api_token,
        'fields': 'name,idList,idBoard,desc,due,dueComplete,dateLastActivity,labels,url',
        'attachments': 'true',
        'attachment_fields': 'name,url,date',
        'members': 'true',
        'member_fields': 'fullName,username',
        'actions': 'commentCard',
        'action_fields': 'data,date,type',
        'customFieldItems': 'true'
    }

    try:
        logger.info(f"Fetching board data for board ID: {board_id}")
        response = requests.get(url, params=query)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Successfully fetched data for {len(data)} cards")
        return data
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to fetch data from Trello: {str(e)}"
        logger.error(error_msg)
        raise TrelloAPIError(error_msg)


def get_card_data(card_id: str, api_key: str, api_token: str) -> Dict[str, Any]:
    """
    Fetch detailed card data from Trello API.

    Args:
        card_id: ID of the Trello card.
        api_key: Trello API key.
        api_token: Trello API token.

    Returns:
        Dictionary containing detailed card data.

    Raises:
        TrelloAPIError: If there is an error fetching data from Trello.
    """
    url = f"https://api.trello.com/1/cards/{card_id}"
    query = {
        'key': api_key,
        'token': api_token,
        'fields': 'name,idList,idBoard,desc,due,dueComplete,dateLastActivity,labels,url',
        'attachments': 'true',
        'attachment_fields': 'name,url,date',
        'members': 'true',
        'member_fields': 'fullName,username',
        'actions': 'commentCard',
        'action_fields': 'data,date,type',
        'customFieldItems': 'true'
    }

    try:
        logger.info(f"Fetching detailed data for card ID: {card_id}")
        response = requests.get(url, params=query)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Successfully fetched detailed data for card: {data.get('name', card_id)}")
        return data
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to fetch card data from Trello: {str(e)}"
        logger.error(error_msg)
        raise TrelloAPIError(error_msg)


def get_list_data(board_id: str, api_key: str, api_token: str) -> List[Dict[str, Any]]:
    """
    Fetch lists data from Trello API.

    Args:
        board_id: ID of the Trello board.
        api_key: Trello API key.
        api_token: Trello API token.

    Returns:
        List of dictionaries containing list data.

    Raises:
        TrelloAPIError: If there is an error fetching data from Trello.
    """
    url = f"https://api.trello.com/1/boards/{board_id}/lists"
    query = {
        'key': api_key,
        'token': api_token,
        'fields': 'name,closed,pos'
    }

    try:
        logger.info(f"Fetching lists for board ID: {board_id}")
        response = requests.get(url, params=query)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Successfully fetched {len(data)} lists")
        return data
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to fetch list data from Trello: {str(e)}"
        logger.error(error_msg)
        raise TrelloAPIError(error_msg)


def get_board_members(board_id: str, api_key: str, api_token: str) -> List[Dict[str, Any]]:
    """
    Fetch board members from Trello API.

    Args:
        board_id: ID of the Trello board.
        api_key: Trello API key.
        api_token: Trello API token.

    Returns:
        List of dictionaries containing member data.

    Raises:
        TrelloAPIError: If there is an error fetching data from Trello.
    """
    url = f"https://api.trello.com/1/boards/{board_id}/members"
    query = {
        'key': api_key,
        'token': api_token,
        'fields': 'fullName,username,avatarUrl'
    }

    try:
        logger.info(f"Fetching members for board ID: {board_id}")
        response = requests.get(url, params=query)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Successfully fetched {len(data)} members")
        return data
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to fetch member data from Trello: {str(e)}"
        logger.error(error_msg)
        raise TrelloAPIError(error_msg)


class BoardDataFetcherTool(BaseTool):
    """
    Tool for fetching data from a Trello board.

    This tool fetches all cards, lists, members, and other data from a Trello board.
    """

    name = "Trello Board Data Fetcher"
    description = """
    Fetch all data from a Trello board, including cards, lists, members, and other information.
    This tool requires a board ID, which should be available in the environment variables.
    The tool will return a dictionary containing all the board data.
    """

    def _run(self, **kwargs) -> Dict[str, Any]:
        """
        Run the tool to fetch board data.

        Returns:
            Dictionary containing board data.
        """
        board_id = os.getenv("TRELLO_BOARD_ID")
        api_key = os.getenv("TRELLO_API_KEY")
        api_token = os.getenv("TRELLO_API_TOKEN")

        if not all([board_id, api_key, api_token]):
            raise ValueError("Missing required Trello credentials in environment variables")

        try:
            # Fetch board data
            cards = get_board_data(board_id, api_key, api_token)
            lists = get_list_data(board_id, api_key, api_token)
            members = get_board_members(board_id, api_key, api_token)

            # Organize data
            board_data = {
                "cards": cards,
                "lists": lists,
                "members": members,
                "board_id": board_id,
                "timestamp": time.time()
            }

            return board_data

        except Exception as e:
            error_msg = f"Error fetching board data: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    async def _arun(self, **kwargs) -> Dict[str, Any]:
        """
        Run the tool asynchronously.

        Returns:
            Dictionary containing board data.
        """
        return self._run(**kwargs)


class CardDataFetcherTool(BaseTool):
    """
    Tool for fetching detailed data for a specific Trello card.

    This tool fetches detailed data for a specific card, including comments,
    attachments, members, and custom fields.
    """

    name = "Trello Card Data Fetcher"
    description = """
    Fetch detailed data for a specific Trello card.
    This tool requires a card ID and will return a dictionary containing all the card data.
    """

    def _run(self, card_id: str, **kwargs) -> Dict[str, Any]:
        """
        Run the tool to fetch card data.

        Args:
            card_id: ID of the Trello card.

        Returns:
            Dictionary containing card data.
        """
        api_key = os.getenv("TRELLO_API_KEY")
        api_token = os.getenv("TRELLO_API_TOKEN")

        if not all([api_key, api_token]):
            raise ValueError("Missing required Trello credentials in environment variables")

        try:
            # Fetch card data
            card_data = get_card_data(card_id, api_key, api_token)
            return card_data

        except Exception as e:
            error_msg = f"Error fetching card data: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    async def _arun(self, card_id: str, **kwargs) -> Dict[str, Any]:
        """
        Run the tool asynchronously.

        Args:
            card_id: ID of the Trello card.

        Returns:
            Dictionary containing card data.
        """
        return self._run(card_id, **kwargs)