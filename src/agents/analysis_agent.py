"""
Analysis Agent Module

This module defines the AnalysisAgent class, which analyzes
sprint data and generates insights.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from uagents import Agent, Context, Protocol
from src.models.messages import (
    AnalysisRequest, AnalysisResponse,
    StatusRequest, StatusResponse
)
from src.config.agentverse import get_agentverse_config

class AnalysisAgent(Agent):
    """
    Agent responsible for analyzing sprint data and generating insights.
    """

    def __init__(
        self,
        name: str = "Sprint Analysis Specialist",
        port: int = 8002,
        seed: Optional[str] = None,
        endpoint: Optional[str] = None,
        agentverse: Optional[Dict[str, Any]] = None,
        mailbox: bool = True
    ):
        super().__init__(
            name=name,
            port=port,
            seed=seed,
            endpoint=endpoint,
            agentverse=agentverse or get_agentverse_config(),
            mailbox=mailbox
        )

        self._logger = logging.getLogger(__name__)
        self._logger.info("Initialized AnalysisAgent")

        # Register message handlers
        @self.on_message(AnalysisRequest)
        async def handle_analysis_request(ctx: Context, sender: str, msg: AnalysisRequest):
            """Handle requests to analyze sprint data"""
            try:
                self._logger.info(f"Received analysis request from {sender}")
                results = await self.analyze_sprint_data(msg.sprint_data)
                await ctx.send(
                    sender,
                    AnalysisResponse(
                        status="success",
                        analysis_results=results
                    )
                )
            except Exception as e:
                self._logger.error(f"Error analyzing sprint data: {str(e)}")
                await ctx.send(
                    sender,
                    AnalysisResponse(
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

    async def analyze_sprint_data(self, sprint_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sprint data and generate insights"""
        try:
            self._logger.info("Analyzing sprint data for insights")
            
            # Extract basic data from sprint data
            cards = sprint_data.get("cards", [])
            lists = sprint_data.get("lists", [])
            members = sprint_data.get("members", [])
            
            # Log data sizes for debugging
            self._logger.debug(f"Analyzing {len(cards)} cards")
            self._logger.debug(f"Found {len(lists)} lists")
            self._logger.debug(f"Found {len(members)} members")
            
            # Create a mapping of list IDs to their names
            list_map = {lst["id"]: lst["name"] for lst in lists}
            
            # Filter out cards that are just list titles (based on common patterns)
            title_names = ["Backlog", "Planning", "Design", "Ready", "In Progress", "Review", "Done"]
            task_cards = [
                card for card in cards 
                if not any(card["name"] == title for title in title_names) and
                not card["name"].startswith("---") and 
                not card["name"].startswith("===")
            ]
            
            # Count total and completed tasks
            total_tasks = len(task_cards)
            
            # Find the "Done" list IDs
            done_list_ids = [
                lst["id"] for lst in lists 
                if any(done_term in lst["name"].lower() for done_term in ["done", "complete", "completed", "finished"])
            ]
            
            # Count completed tasks
            completed_tasks = sum(1 for card in task_cards if card["idList"] in done_list_ids)
            
            # Calculate completion rate
            completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
            
            # Calculate story points from card data - look for story point indicators in card names or descriptions
            total_points = 0
            for card in task_cards:
                # Look for story point indicators like (3) or [5] or 8sp or similar patterns
                card_name = card.get("name", "")
                card_desc = card.get("desc", "")
                
                # Search for patterns like (3) or [5] or 3sp in name
                name_points = self._extract_story_points(card_name)
                if name_points > 0:
                    total_points += name_points
                    continue
                
                # If not found in name, try description
                desc_points = self._extract_story_points(card_desc)
                if desc_points > 0:
                    total_points += desc_points
                
            # Check if we found story points, otherwise calculate based on task complexity
            if total_points == 0:
                # Assign points based on card descriptions, labels, or approximate estimation
                for card in task_cards:
                    # Assign more points to cards with longer descriptions or more labels
                    desc_length = len(card.get("desc", ""))
                    label_count = len(card.get("labels", []))
                    
                    # Simple heuristic: more complex cards have longer descriptions or more labels
                    if desc_length > 200 or label_count >= 2:
                        points = 5  # Complex task
                    elif desc_length > 50 or label_count >= 1:
                        points = 3  # Medium task
                    else:
                        points = 1  # Simple task
                    
                    total_points += points
            
            # Find overdue tasks
            current_date = datetime.now(timezone.utc)
            overdue_tasks = []
            approaching_deadlines = []
            
            for card in task_cards:
                if card.get("due"):
                    try:
                        # Ensure due_date is timezone-aware
                        due_date = datetime.fromisoformat(card["due"].replace("Z", "+00:00"))
                        
                        # Calculate days difference
                        days_diff = (due_date - current_date).days
                        
                        # Check if overdue
                        if days_diff < 0 and card["idList"] not in done_list_ids:
                            overdue_tasks.append({
                                "name": card["name"],
                                "days_overdue": abs(days_diff),
                                "members": card.get("members", []),
                                "list": list_map.get(card["idList"], "Unknown")
                            })
                        # Check if approaching deadline (within next 3 days)
                        elif 0 <= days_diff <= 3 and card["idList"] not in done_list_ids:
                            approaching_deadlines.append({
                                "name": card["name"],
                                "days_remaining": days_diff,
                                "members": card.get("members", []),
                                "list": list_map.get(card["idList"], "Unknown")
                            })
                    except (ValueError, TypeError) as e:
                        self._logger.warning(f"Error parsing due date for card {card['name']}: {e}")
            
            # Find blocked tasks based on labels or card content
            blocked_tasks = []
            for card in task_cards:
                is_blocked = False
                
                # Check labels for red color or "blocked" text
                for label in card.get("labels", []):
                    if label.get("color", "") == "red" or "block" in label.get("name", "").lower():
                        is_blocked = True
                        break
                
                # Check card name or description for "blocked" or "blocker" text
                card_text = (card.get("name", "") + " " + card.get("desc", "")).lower()
                if "block" in card_text or "impediment" in card_text or "depend" in card_text:
                    is_blocked = True
                
                if is_blocked:
                    blocked_tasks.append({
                        "name": card["name"],
                        "members": card.get("members", []),
                        "list": list_map.get(card["idList"], "Unknown")
                    })
            
            # Identify risks based on actual data analysis
            risks = []
            
            # Risk: Low completion rate
            if completion_rate < 0.3 and total_tasks > 0:
                risks.append("low completion rate")
            
            # Risk: Many overdue tasks
            if len(overdue_tasks) > 2:
                risks.append("multiple overdue tasks")
            
            # Risk: Blocked tasks
            if len(blocked_tasks) > 0:
                risks.append("blocked tasks")
            
            # Risk: Unassigned tasks
            unassigned_count = sum(1 for card in task_cards if not card.get("members"))
            if unassigned_count > total_tasks * 0.3 and total_tasks > 0:  # More than 30% unassigned
                risks.append("many unassigned tasks")
            
            # Get lists breakdown for visualization
            list_breakdown = {}
            for card in task_cards:
                list_id = card["idList"]
                list_name = list_map.get(list_id, "Unknown")
                if list_name in list_breakdown:
                    list_breakdown[list_name] += 1
                else:
                    list_breakdown[list_name] = 1
            
            # Member activity breakdown
            member_activity = {}
            for member in members:
                member_id = member["id"]
                member_name = member.get("fullName") or member.get("username", "Unknown")
                assigned_cards = [card for card in task_cards if member_id in card.get("members", [])]
                
                member_activity[member_name] = {
                    "total_tasks": len(assigned_cards),
                    "completed": sum(1 for card in assigned_cards if card["idList"] in done_list_ids),
                    "overdue": sum(1 for card in assigned_cards if card.get("due") and 
                              self._is_overdue(card["due"]) and card["idList"] not in done_list_ids)
                }
            
            # Task distribution by list/status for chart data
            status_distribution = []
            for list_name, count in list_breakdown.items():
                status_distribution.append({
                    "status": list_name,
                    "count": count,
                    "percentage": count / total_tasks if total_tasks > 0 else 0
                })
            
            # Compile the results - using ONLY data from Trello
            analysis_results = {
                "sprint_id": sprint_data.get("sprint_id", ""),
                "sprint_name": sprint_data.get("sprint_name", ""),
                "board_id": sprint_data.get("board_id", ""),
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "completion_rate": completion_rate,
                "velocity": total_points,  # Based on calculated story points
                "overdue_tasks": overdue_tasks,
                "approaching_deadlines": approaching_deadlines,
                "blockers": blocked_tasks,
                "risks": risks,
                
                # Pass through the original data for the reporting agent to use
                "cards": cards,
                "lists": lists,
                "members": members,
                "timestamp": sprint_data.get("timestamp", ""),
                
                # Add visualization data
                "status_distribution": status_distribution,
                "member_activity": member_activity,
                "list_breakdown": list_breakdown,
            }
            
            self._logger.info(f"Analysis completed: {len(analysis_results)} data points calculated")
            return analysis_results
            
        except Exception as e:
            self._logger.error(f"Error analyzing sprint data: {e}")
            self._logger.exception(e)
            # Return empty data to avoid breaking the workflow but without mock data
            return sprint_data

    def _extract_story_points(self, text: str) -> int:
        """Extract story points from text using common patterns"""
        import re
        
        # Look for patterns like (3) or [5] at the beginning or end of string
        point_patterns = [
            r'\((\d+)\)',  # (3)
            r'\[(\d+)\]',  # [5]
            r'(\d+)\s*sp',  # 8sp
            r'(\d+)\s*points',  # 5 points
            r'(\d+)\s*pts',  # 3 pts
            r'(\d+)p\b'  # 8p
        ]
        
        for pattern in point_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    pass
        
        return 0
    
    def _is_overdue(self, due_date_str: str) -> bool:
        """Check if a due date is overdue, handling timezone differences"""
        try:
            # Ensure due_date is timezone-aware
            due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
            current_date = datetime.now(timezone.utc)
            return due_date < current_date
        except (ValueError, TypeError):
            return False