"""
Slack Integration Utility

This module provides functionality for sending notifications to Slack channels.
"""

import os
import logging
import ssl
import certifi
import re
from typing import Dict, List, Any, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
from datetime import datetime

from src.utils.logging_utils import get_logger

# Configure logging
logger = get_logger(__name__)

class SlackNotifier:
    """Class responsible for sending notifications to Slack."""
    
    def __init__(self):
        """
        Initialize the Slack client with credentials from environment variables.
        """
        # Load environment variables if not already loaded
        load_dotenv()
        
        # Get Slack credentials
        self.token = os.getenv('SLACK_BOT_TOKEN')
        if not self.token:
            logger.error("SLACK_BOT_TOKEN environment variable is not set")
            raise ValueError("SLACK_BOT_TOKEN environment variable is not set")
        
        self.default_channel = os.getenv('SLACK_DEFAULT_CHANNEL')
        if not self.default_channel:
            logger.error("SLACK_DEFAULT_CHANNEL environment variable is not set")
            raise ValueError("SLACK_DEFAULT_CHANNEL environment variable is not set")
            
        # Initialize Slack client with proper SSL certificate handling
        # Use default SSL context which is properly set up for certificate validation
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.client = WebClient(token=self.token, ssl=ssl_context)
        logger.info("Slack client initialized successfully with secure SSL configuration")
        
    def _clean_text_for_slack(self, text: str) -> str:
        """
        Clean text for Slack formatting, removing symbols that don't render well.
        
        Args:
            text: Original text with markdown formatting
            
        Returns:
            Cleaned text safe for Slack
        """
        # Remove separator lines with === or ---
        cleaned = re.sub(r'={3,}|-{3,}', '', text)
        
        # Replace ** bold markers with Slack's *bold* format
        cleaned = re.sub(r'\*\*(.*?)\*\*', r'*\1*', cleaned)
        
        # Remove image references
        cleaned = re.sub(r'!\[.*?\]\((.+?)\)', '', cleaned)
        
        # Replace markdown headings with Slack-formatted headings
        cleaned = re.sub(r'^#{1,2}\s+(.*?)$', r'*\1*', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r'^#{3,6}\s+(.*?)$', r'• *\1*', cleaned, flags=re.MULTILINE)
        
        # Ensure emojis display correctly by removing excessive spaces
        cleaned = re.sub(r'\s+([✅⚠️⏰🎯📊])', r' \1', cleaned)
        
        return cleaned.strip()
        
    def _extract_summary_sections(self, text: str) -> Dict[str, str]:
        """
        Extract key sections from the report text for a condensed summary.
        
        Args:
            text: Full report text
            
        Returns:
            Dictionary with key sections
        """
        sections = {}
        
        # Extract executive summary
        exec_summary_match = re.search(r'## Executive Summary(.*?)(?=##|\Z)', text, re.DOTALL)
        if exec_summary_match:
            sections['executive_summary'] = self._clean_text_for_slack(exec_summary_match.group(1).strip())
        
        # Extract risk analysis (only the most critical parts)
        risks_match = re.search(r'### Current Risks(.*?)(?=###|\Z)', text, re.DOTALL)
        if risks_match:
            sections['risks'] = self._clean_text_for_slack(risks_match.group(1).strip())
        
        # Extract overdue tasks section
        overdue_match = re.search(r'### Overdue Tasks(.*?)(?=###|\Z)', text, re.DOTALL)
        if overdue_match:
            sections['overdue'] = self._clean_text_for_slack(overdue_match.group(1).strip())
        
        # Extract goals section (most important for action items)
        goals_match = re.search(r'## 🎯 Goals Until Next Sprint Meeting(.*?)(?=##|\Z)', text, re.DOTALL)
        if goals_match:
            sections['goals'] = self._clean_text_for_slack(goals_match.group(1).strip())
        
        return sections
        
    def notify_report_completion(self, report_data: Dict[str, Any]) -> bool:
        """
        Send a notification to Slack about the completed sprint report.
        
        Args:
            report_data: Dictionary containing report details and metrics
            
        Returns:
            bool: Whether the notification was sent successfully
        """
        try:
            logger.debug(f"Received report data: {report_data}")
            metrics = report_data.get("report", {}).get("metrics", {})
            logger.debug(f"Extracted metrics: {metrics}")
            sprint_name = metrics.get("sprint_name", "Current Sprint")
            cloudinary_url = report_data.get("cloudinary_url", "")
            
            # Format completion rate and status
            completion_rate = metrics.get("completion_rate", 0)
            logger.debug(f"Completion rate: {completion_rate}")
            completion_status = (
                "🔴 Critical - Needs immediate attention" if completion_rate < 0.3 else 
                "🟠 Warning - Below target" if completion_rate < 0.5 else 
                "✅ On Track - Keep up the good work!"
            )
            
            # Format velocity status
            velocity = metrics.get("velocity", 0)
            velocity_status = (
                "🔴 Below Target - Action needed" if velocity < 20 else 
                "🟡 Near Target - Keep pushing" if velocity < 30 else 
                "✅ On Target - Great pace!"
            )
            
            # Format blockers status
            blockers = metrics.get("blockers", [])
            blocker_status = (
                f"🚫 {len(blockers)} Active blockers need attention" if blockers else 
                "✅ No active blockers - Clear path ahead!"
            )
            
            # Create message blocks
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"📊 Sprint Report: {sprint_name}",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Sprint Status Overview*\n" +
                               f"• Sprint Progress: {completion_rate:.1%} completed ({completion_status})\n" +
                               f"• Team Velocity: {velocity:.1f} points ({velocity_status})\n" +
                               f"• Blockers: {blocker_status}"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Task Progress*\n" +
                               f"• Completed Tasks: {metrics.get('completed_tasks', 0)} of {metrics.get('total_tasks', 0)}\n" +
                               f"• Remaining Work: {metrics.get('total_tasks', 0) - metrics.get('completed_tasks', 0)} tasks to be completed\n" +
                               f"• Identified Risks: {len(metrics.get('risks', []))} potential risks to monitor"
                    }
                }
            ]
            
            # Add critical blockers section if any exist
            if blockers:
                blocker_text = "*Critical Blockers - Action Required*\n"
                for blocker in blockers[:3]:  # Show top 3 blockers
                    blocker_text += f"• 🚫 {blocker.get('name', 'Unknown')}\n"
                if len(blockers) > 3:
                    blocker_text += f"_(+{len(blockers) - 3} more blockers need attention...)_"
                
                blocks.extend([
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": blocker_text
                        }
                    }
                ])
            
            # Add overdue tasks section if any exist
            overdue_tasks = metrics.get("overdue_tasks", [])
            if overdue_tasks:
                overdue_text = "*Overdue Tasks - Needs Attention*\n"
                for task in overdue_tasks[:3]:  # Show top 3 overdue tasks
                    task_name = task.get('name', 'Unknown')
                    days_overdue = task.get('days_overdue', 0)
                    list_name = task.get('list', 'Unknown')
                    overdue_text += f"• ⚠️ {task_name}\n   _(Overdue by {days_overdue} days - Currently in {list_name})_\n"
                if len(overdue_tasks) > 3:
                    overdue_text += f"_(+{len(overdue_tasks) - 3} more overdue tasks...)_"
                
                blocks.extend([
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": overdue_text
                        }
                    }
                ])
            
            # Add report link
            if cloudinary_url:
                blocks.extend([
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "📑 *View Detailed Report*"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"<{cloudinary_url}|Click here to view the complete sprint report with charts and detailed analysis>"
                        }
                    }
                ])
            
            # Send the message
            response = self.client.chat_postMessage(
                channel=self.default_channel,
                blocks=blocks,
                text=f"Sprint Report for {sprint_name} is ready!"  # Fallback text
            )
            
            self.logger.info(f"Sent Slack notification to channel {self.default_channel}")
            return response["ok"]
            
        except Exception as e:
            self.logger.error(f"Error sending Slack notification: {e}")
            return False

    def send_message(self, 
                    text: str, 
                    channel: Optional[str] = None) -> bool:
        """
        Send a simple text message to Slack.
        
        Args:
            text: Message text to send
            channel: Optional channel override (uses default if not specified)
                
        Returns:
            bool: True if successful, False if failed
        """
        try:
            # Use channel override or default
            target_channel = channel or self.default_channel
            
            # Send the message
            response = self.client.chat_postMessage(
                channel=target_channel,
                text=text
            )
            
            logger.info(f"Message sent to Slack channel {target_channel}")
            return response['ok']
            
        except SlackApiError as e:
            logger.error(f"Error sending message to Slack: {e.response['error']}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message to Slack: {str(e)}")
            return False 