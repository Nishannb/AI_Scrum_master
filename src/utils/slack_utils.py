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
        
    def notify_report_completion(self, result: Dict[str, Any]) -> bool:
        """
        Notify about report completion via Slack.
        
        Args:
            result: Dictionary with report generation results
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        try:
            # DEBUG: Print full result structure
            print("\n=== SLACK NOTIFICATION DATA ===")
            if 'report' in result:
                print("Report structure found in result")
                if 'metrics' in result['report']:
                    print("Metrics found in report structure")
                    print(f"Metrics keys: {result['report']['metrics'].keys()}")
            else:
                print("No report structure found, using top level")
            print("===========================\n")
            
            # Extract key metrics from the result structure
            # First try to access the nested 'report' structure if it exists
            if 'report' in result and 'metrics' in result['report']:
                metrics = result['report']['metrics']
                completion_rate = metrics.get('completion_rate', 0)
                total_tasks = metrics.get('total_tasks', 0)
                completed_tasks = metrics.get('completed_tasks', 0)
                remaining_tasks = total_tasks - completed_tasks
                blockers = metrics.get('blockers', [])
                overdue_tasks = metrics.get('overdue_tasks', [])
                risks = metrics.get('risks', [])
                status_counts = metrics.get('status_counts', {})
                sprint_name = metrics.get('sprint_name', "Current Sprint")
            else:
                # Fallback to the top-level structure
                completion_rate = result.get('completion_rate', 0)
                total_tasks = result.get('total_tasks', 0)
                completed_tasks = result.get('completed_tasks', 0)
                remaining_tasks = total_tasks - completed_tasks
                blockers = result.get('blockers', [])
                overdue_tasks = result.get('overdue_tasks', [])
                risks = result.get('risks', [])
                status_counts = result.get('status_counts', {})
                sprint_name = result.get('sprint_name', "Current Sprint")

            # Get cloudinary URL from the result
            cloudinary_url = result.get('cloudinary_url', 'Not available')
            
            # Format the message
            message = {
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "📊 Scrum Report Available",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"The sprint report for *{sprint_name}* has been generated and is ready for review.\n\n*<{cloudinary_url}|View Full Report>*"
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Executive Summary*\n"
                                f"• Completion Rate: {completion_rate:.1%}\n"
                                f"• Total Tasks: {total_tasks}\n"
                                f"• Completed Tasks: {completed_tasks}\n"
                                f"• Remaining Tasks: {remaining_tasks}"
                        }
                    },
                    {
                        "type": "divider"
                    }
                ]
            }
            
            # Add current risks section
            risks_blocks = []
            
            # Add completion rate risk if low
            if completion_rate < 0.3:
                risk_impact = "Sprint goals may not be met by the end of the sprint"
                tasks_affecting = []
                
                # Include at most 3 non-completed tasks
                non_completed_tasks = []
                if isinstance(overdue_tasks, list):
                    for task in overdue_tasks[:3]:
                        if isinstance(task, dict):
                            non_completed_tasks.append(task.get("title", task.get("name", "Unknown task")))
                
                risk_detail = "*Completion Rate (high)*: Low sprint completion rate" + f" ({completion_rate:.1%})\n"
                risk_detail += f" • Impact: {risk_impact}\n"
                if non_completed_tasks:
                    risk_detail += f" • Tasks affecting completion rate: {', '.join(non_completed_tasks)}."
                
                risks_blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": risk_detail
                    }
                })
            
            # Add blockers risk if any
            if blockers:
                blocker_names = []
                for b in blockers[:3]:  # Show top 3 blockers
                    if isinstance(b, dict):
                        blocker_names.append(b.get("title", b.get("name", "Unknown blocker")))
                    elif isinstance(b, str):
                        blocker_names.append(b)
                
                risks_blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Blockers (high)*: {len(blockers)} blockers identified in the sprint\n"
                            f" • Impact: Blocking issues are preventing team progress\n"
                            + (f" • Blockers: {', '.join(blocker_names)}." if blocker_names else "")
                    }
                })
            
            # Add approaching deadlines risk
            approaching_deadlines = result.get('approaching_deadlines', [])
            if approaching_deadlines:
                deadline_names = []
                for d in approaching_deadlines[:3]:  # Show top 3 approaching deadlines
                    if isinstance(d, dict):
                        deadline_names.append(d.get("title", d.get("name", "Unknown task")))
                    elif isinstance(d, str):
                        deadline_names.append(d)
                
                risks_blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Approaching Deadlines (medium)*: {len(approaching_deadlines)} tasks with approaching deadlines\n"
                            f" • Impact: Tasks may not be completed by their due dates\n"
                            + (f" • Critical deadlines: {', '.join(deadline_names)}." if deadline_names else "")
                    }
                })
            
            # Add overdue tasks risk
            if overdue_tasks:
                overdue_names = []
                for t in overdue_tasks[:3]:  # Show top 3 overdue tasks
                    if isinstance(t, dict):
                        overdue_names.append(t.get("title", t.get("name", "Unknown task")))
                    elif isinstance(t, str):
                        overdue_names.append(t)
                
                risks_blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Overdue (medium)*: {len(overdue_tasks)} overdue tasks\n"
                            f" • Impact: Tasks have already missed their deadlines\n"
                            + (f" • Overdue tasks: {', '.join(overdue_names)}." if overdue_names else "")
                    }
                })
            
            # Add the risks section if any risks were found
            if risks_blocks:
                message["blocks"].append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Current Risks*"
                    }
                })
                message["blocks"].extend(risks_blocks)
                message["blocks"].append({"type": "divider"})
            
            # Add detailed overdue tasks section if there are any
            if overdue_tasks:
                message["blocks"].append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Overdue Tasks*"
                    }
                })
                
                for task in overdue_tasks[:5]:  # Limit to top 5 overdue tasks
                    if isinstance(task, dict):
                        task_name = task.get("title", task.get("name", "Unknown task"))
                        due_date = task.get("due_date", task.get("due", "Unknown"))
                        days_overdue = task.get("days_overdue", 1)  # Default to 1 day if not specified
                        assigned_to = task.get("assigned_to", "Unassigned")
                        status = task.get("status", "Unknown")
                        
                        message["blocks"].append({
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"• :warning: *{task_name}* - {days_overdue} days overdue (Assigned to: {assigned_to})\n"
                                    f" • Current status: {status}\n"
                                    f" • Due date: {due_date}"
                            }
                        })
                
                message["blocks"].append({"type": "divider"})
            
            # Add customized goals section based on the actual data
            goal_text = "*Goals Until Next Sprint Meeting*\n"
            goal_text += "Based on the analysis above, the team should focus on the following specific action items before the next sprint meeting:\n"
            
            goals = []
            
            # Add overdue tasks goal if any
            if overdue_tasks:
                overdue_names = []
                for t in overdue_tasks[:2]:  # Show top 2 overdue tasks in goal
                    if isinstance(t, dict):
                        overdue_names.append(t.get("title", t.get("name", "Unknown task")))
                    elif isinstance(t, str):
                        overdue_names.append(t)
                
                if overdue_names:
                    goals.append(f"1. URGENT: Complete overdue tasks ()\n  • Focus on: {', '.join(overdue_names)}.")
            
            # Add blocker resolution goal if any
            if blockers:
                goals.append(f"2. Address {len(blockers)} blockers to unblock progress")
            
            # Add bottleneck goal based on status counts
            if status_counts:
                # Find the list with the most tasks (potential bottleneck)
                bottleneck = max(status_counts.items(), key=lambda x: x[1], default=("", 0))
                if bottleneck[1] > 0:
                    goals.append(f"3. Clear bottleneck in {bottleneck[0]}\n  • Focus on: {bottleneck[0]}, prioritize critical tasks")
            
            # Add tracking goal
            goals.append("4. Track daily progress\n  • Hold daily stand-ups to review progress on critical tasks\n  • Update Trello board with current status and blockers\n  • Escalate any new blockers immediately")
            
            # Add scope adjustment goal if completion rate is low
            if completion_rate < 0.4:
                goals.append("5. Prepare for potential scope adjustment\n  • Identify tasks that may need to be moved to next sprint\n  • Prioritize remaining work for current sprint completion")
            
            # Number goals properly
            for i, goal in enumerate(goals):
                if i == 0:
                    # First goal already has a number
                    continue
                goal_number = str(i + 1)
                goals[i] = goal.replace(f"{i + 1}. ", f"{goal_number}. ")
            
            goal_text += "\n".join(goals)
            
            message["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": goal_text
                }
            })
            
            # Send the message
            response = self.client.chat_postMessage(
                channel=self.default_channel,
                blocks=message["blocks"]
            )
            
            return response["ok"]
            
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
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