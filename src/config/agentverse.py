"""
AgentVerse configuration settings.
"""

import os
from typing import Dict

def get_agentverse_token() -> str:
    """Get the AgentVerse API token from environment variables."""
    token = os.getenv("AGENTVERSE_TOKEN")
    if not token:
        raise ValueError(
            "AGENTVERSE_TOKEN environment variable not set. "
            "Please set it with your AgentVerse API token."
        )
    return token

def get_agentverse_config() -> Dict[str, str]:
    """Get the AgentVerse configuration."""
    return {
        "url": os.getenv("AGENTVERSE_URL", "https://agentverse.ai"),
        "token": get_agentverse_token()
    }

def get_ssl_verify() -> bool:
    """Get whether to verify SSL certificates."""
    return os.getenv("AGENTVERSE_SSL_VERIFY", "0") == "1" 