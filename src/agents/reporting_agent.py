"""
Reporting Agent Module

This module defines the ReportingAgent class, which generates
reports from analysis results.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from uagents import Agent, Context, Protocol
from src.models.messages import (
    ReportRequest, ReportResponse,
    StatusRequest, StatusResponse,
    AnalysisRequest
)
from src.config.agentverse import get_agentverse_config
from src.utils.slack_utils import SlackNotifier
from src.utils.pdf_generator import PDFReportGenerator
from src.utils.chart_generator import ChartGenerator
import time
from uagents.setup import fund_agent_if_low
from src.utils.logging_utils import get_logger

class ReportingAgent(Agent):
    """
    Agent responsible for generating reports from analysis results.
    """

    def __init__(
        self,
        name: str = "Report Generation Specialist",
        port: int = 8003,
        seed: Optional[str] = None,
        endpoint: Optional[str] = None,
        agentverse: Optional[Dict[str, Any]] = None,
        mailbox: bool = True
    ):
        """
        Initialize a reporting agent that generates reports from analysis results.
        
        Args:
            name: The name of the agent
            port: The port to run the agent on
            seed: Optional seed for the agent's key pair
            endpoint: Optional endpoint for the agent
            agentverse: Optional AgentVerse configuration
            mailbox: Whether to use a mailbox
        """
        # Track agent start time
        self._start_time = time.time()
        
        # Initialize logger
        self._logger = get_logger(self.__class__.__name__)
        
        super().__init__(
            name=name,
            port=port,
            seed=seed,
            endpoint=endpoint,
            agentverse=agentverse or get_agentverse_config(),
            mailbox=mailbox
        )

        self._logger.info("Initialized ReportingAgent")

        # Initialize PDF generator and Slack notifier
        self._pdf_generator = PDFReportGenerator()
        try:
            self._slack_notifier = SlackNotifier()
            self._logger.info("Slack notifier initialized successfully")
        except Exception as e:
            self._logger.error(f"Failed to initialize Slack notifier: {e}")
            self._slack_notifier = None

        # Register message handlers
        @self.on_message(ReportRequest)
        async def handle_report_request(ctx: Context, sender: str, msg: ReportRequest):
            """Handle requests to generate reports"""
            try:
                self._logger.info(f"Received report request from {sender}")
                await self.process_report(ctx, msg.analysis_results)
            except Exception as e:
                self._logger.error(f"Error processing report: {e}")
                await ctx.send(
                    sender,
                    ReportResponse(
                        status="error",
                        error=str(e)
                    )
                )

        @self.on_message(StatusRequest)
        async def handle_status_request(ctx: Context, sender: str, msg: StatusRequest):
            """Handle status check requests"""
            self._logger.info(f"Received status request from {sender}")
            
            # Just a simple status response
            await ctx.send(
                sender,
                StatusResponse(
                    status="active",
                    uptime=int(time.time() - self._start_time)
                )
            )

        @self.on_message(AnalysisRequest)
        async def handle_analysis_request(ctx: Context, sender: str, msg: AnalysisRequest):
            """Handle analysis request to generate a report"""
            self._logger.info(f"Received report request from {sender}")
            
            # Add debug logging to see the structure of analysis_results
            self._logger.debug(f"Analysis results type: {type(msg.analysis_results)}")
            self._logger.debug(f"Analysis results keys: {msg.analysis_results.keys() if isinstance(msg.analysis_results, dict) else 'Not a dict'}")
            self._logger.debug(f"Analysis results content: {msg.analysis_results}")
            
            # Extract velocity for debug
            velocity_data = msg.analysis_results.get("velocity", None) 
            self._logger.debug(f"Velocity data type: {type(velocity_data)}")
            self._logger.debug(f"Velocity data content: {velocity_data}")
            
            try:
                # Process the report
                await self.process_report(ctx, msg.analysis_results)
            except Exception as e:
                self._logger.error(f"Error processing report: {e}")
                await ctx.send(
                    sender,
                    body={"status": "error", "error": str(e)}
                )

    async def process_report(self, ctx: Context, report_data: Any) -> None:
        """
        Process the report data and generate a PDF report.
        
        Args:
            ctx: Context for the agent's protocol
            report_data: Data to include in the report
        """
        try:
            # Determine the sender based on context type
            sender = None
            if hasattr(ctx, 'message') and hasattr(ctx.message, 'sender'):
                sender = str(ctx.message.sender)
            elif hasattr(ctx, 'sender'):
                sender = str(ctx.sender)
            else:
                # If we can't determine sender, log it but continue
                self._logger.warning("Could not determine sender from context, responses may fail")
                
            # Generate markdown report
            self._logger.info("Generating markdown report...")
            markdown_path = self.generate_report(report_data)
            
            if not markdown_path or not os.path.exists(markdown_path):
                self._logger.error("Failed to generate markdown report")
                if sender:
                    await ctx.send(
                        sender,
                        ReportResponse(
                            status="error",
                            error="Failed to generate markdown report"
                        )
                    )
                return
                
            # Generate PDF from markdown
            self._logger.info("Generating PDF report...")
            pdf_path = await self.generate_pdf(markdown_path)
            
            if not pdf_path or not os.path.exists(pdf_path):
                self._logger.error("Failed to generate PDF report")
                if sender:
                    await ctx.send(
                        sender,
                        ReportResponse(
                            status="error",
                            error="Failed to generate PDF report"
                        )
                    )
                return
                
            # Upload PDF to Cloudinary
            self._logger.info("Uploading PDF to Cloudinary...")
            cloudinary_url = await self.upload_to_cloudinary(pdf_path)
            
            # Track Cloudinary uploads for debugging
            os.makedirs("reports", exist_ok=True)
            uploads_log = "reports/cloudinary_uploads.txt"
            with open(uploads_log, "a") as f:
                f.write(f"{datetime.now(timezone.utc).isoformat()}: {pdf_path} -> {cloudinary_url or 'FAILED'}\n")
            
            # Prepare report result with actual data
            metrics = {}
            
            # Use actual data from the analysis results
            if isinstance(report_data, dict):
                # Get actual velocity data
                metrics["velocity"] = report_data.get("velocity", 0)
                metrics["completion_rate"] = report_data.get("completion_rate", 0)
                metrics["total_tasks"] = report_data.get("total_tasks", 0)
                metrics["completed_tasks"] = report_data.get("completed_tasks", 0)
                metrics["blockers"] = report_data.get("blockers", [])
                metrics["risks"] = report_data.get("risks", [])
                metrics["overdue_tasks"] = report_data.get("overdue_tasks", [])
                metrics["sprint_name"] = report_data.get("sprint_name", "")
                metrics["board_id"] = report_data.get("board_id", "")
                
                # Add debug logging
                self._logger.debug(f"Metrics dictionary: {metrics}")
                self._logger.debug(f"Report data: {report_data}")
            else:
                self._logger.warning(f"Report data is not a dictionary: {type(report_data)}")
                
            # Prepare report result with all details
            report_result = {
                "success": True,
                "status": "success",
                "markdown_path": markdown_path,
                "pdf_path": pdf_path,
                "cloudinary_url": cloudinary_url,
                # Add top-level metrics for easier access by the Slack notifier
                "completion_rate": report_data.get("completion_rate", 0),
                "total_tasks": report_data.get("total_tasks", 0),
                "completed_tasks": report_data.get("completed_tasks", 0),
                "remaining_tasks": report_data.get("total_tasks", 0) - report_data.get("completed_tasks", 0),
                "velocity": report_data.get("velocity", 0),
                "sprint_name": report_data.get("sprint_name", "Current Sprint"),
                "blockers": report_data.get("blockers", []),
                "overdue_tasks": report_data.get("overdue_tasks", []),
                "approaching_deadlines": report_data.get("approaching_deadlines", []),
                "risks": report_data.get("risks", []),
                "status_counts": report_data.get("status_counts", {}),
                "report": {
                    "title": os.path.basename(markdown_path).replace(".md", ""),
                    "pdf_path": pdf_path,
                    "metrics": {
                        "completion_rate": report_data.get("completion_rate", 0),
                        "velocity": report_data.get("velocity", 0),
                        "total_tasks": report_data.get("total_tasks", 0),
                        "completed_tasks": report_data.get("completed_tasks", 0),
                        "overdue_tasks": report_data.get("overdue_tasks", []),
                        "blockers": report_data.get("blockers", []),
                        "risks": report_data.get("risks", []),
                        "status_counts": report_data.get("status_counts", {}),
                        "sprint_name": report_data.get("sprint_name", "Current Sprint")
                    },
                    "sprint_name": report_data.get("sprint_name", "Current Sprint")
                }
            }
            
            # Notify via Slack only if we have actual metrics to report
            if metrics:
                self._logger.info("Sending notification to Slack...")
                try:
                    slack_notifier = SlackNotifier()
                    
                    # Add detailed debug logging for report structure
                    print("\n=== SLACK NOTIFICATION DATA (FROM REPORTING AGENT) ===")
                    print(f"Report data structure keys: {list(report_result.keys())}")
                    print(f"Report path: {report_result.get('markdown_path')}")
                    print(f"Cloudinary URL: {report_result.get('cloudinary_url')}")
                    print(f"Total tasks: {report_result.get('total_tasks')}")
                    print(f"Completed tasks: {report_result.get('completed_tasks')}")
                    print(f"Overdue tasks: {len(report_result.get('overdue_tasks', []))}")
                    print(f"Blockers: {len(report_result.get('blockers', []))}")
                    print(f"Status counts: {report_result.get('status_counts', {})}")
                    print("=== END DEBUG DATA ===\n")
                    
                    self._logger.debug(f"Report result for Slack: {report_result}")
                    slack_success = slack_notifier.notify_report_completion(report_result)
                    
                    if not slack_success:
                        self._logger.warning("Failed to send notification to Slack, but report was generated successfully")
                except Exception as slack_error:
                    self._logger.error(f"Error sending Slack notification: {slack_error}")
                    self._logger.exception(slack_error)  # This will log the full stack trace
            else:
                self._logger.warning("No metrics available, skipping Slack notification")
                
            # Send response back to sender - using proper format based on the context type
            try:
                if sender:
                    # Different message format based on context type
                    if hasattr(ctx, 'message') and hasattr(ctx.message, 'sender'):
                        await ctx.send(
                            sender,
                            ReportResponse(
                                status="success",
                                report_path=pdf_path,
                                cloudinary_url=cloudinary_url
                            )
                        )
                    else:
                        # For ExternalContext or other types
                        await ctx.send(
                            sender,
                            {"status": "success", "report_path": pdf_path, "cloudinary_url": cloudinary_url}
                        )
                else:
                    self._logger.warning("No sender determined, unable to send response")
            except Exception as response_error:
                self._logger.error(f"Error sending response: {response_error}")
            
        except Exception as e:
            self._logger.error(f"Error processing report: {e}")
            self._logger.exception(e)
            
            # Try to send error response with appropriate context handling
            try:
                if sender:
                    # Different message format based on context type
                    if hasattr(ctx, 'message') and hasattr(ctx.message, 'sender'):
                        await ctx.send(
                            sender,
                            ReportResponse(
                                status="error",
                                error=str(e)
                            )
                        )
                    else:
                        # For ExternalContext or other types
                        await ctx.send(
                            sender,
                            {"status": "error", "error": str(e)}
                        )
            except Exception as response_error:
                self._logger.error(f"Error sending error response: {response_error}")

    def generate_report(self, analysis_results: Dict[str, Any]) -> str:
        try:
            # Extract key metrics and data from actual Trello data
            sprint_name = analysis_results.get("sprint_name", "Current Sprint")
            
            # Get all cards from the Trello data
            all_cards = analysis_results.get("cards", [])
            all_lists = analysis_results.get("lists", [])
            
            # Filter out cards that are just list titles
            task_cards = [card for card in all_cards if not card["name"] in ["Backlog", "Planning / Design", "Ready", "In Progress", "Review", "Done"]]
            
            # Calculate tasks counts
            total_tasks = len(task_cards)
            
            # Create a mapping of list IDs to their names
            list_map = {lst["id"]: lst["name"] for lst in all_lists}
            
            # Count completed tasks (those in the "Done" list)
            done_list_ids = [lst["id"] for lst in all_lists if "Done" in lst["name"]]
            completed_tasks = sum(1 for card in task_cards if card["idList"] in done_list_ids)
            
            # Calculate proper completion rate
            completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
            
            # Handle velocity which might be a dict or a number
            velocity_data = analysis_results.get("velocity", 0)
            if isinstance(velocity_data, dict):
                velocity = velocity_data.get("current", 0)
                prev_velocity = velocity_data.get("previous", velocity * 0.9)
                trend = "increasing" if velocity > prev_velocity else "decreasing"
            else:
                velocity = float(velocity_data)
                prev_velocity = velocity * 0.9
                trend = "stable"
            
            # Identify blockers from the data
            blockers = []
            for card in task_cards:
                # Check for red labels which might indicate blockers
                if any(label.get("color", "") == "red" for label in card.get("labels", [])):
                    blockers.append({
                        "name": card["name"],
                        "description": card.get("desc", ""),
                        "members": card.get("members", []),
                        "due": card.get("due")
                    })
                # Check for "blocked" in the name or description
                elif "block" in card.get("name", "").lower() or "block" in card.get("desc", "").lower():
                    if not any(b["name"] == card["name"] for b in blockers):
                        blockers.append({
                            "name": card["name"],
                            "description": card.get("desc", ""),
                            "members": card.get("members", []),
                            "due": card.get("due")
                        })
            
            # Calculate status counts for task distribution chart
            status_counts = {}
            for card in task_cards:
                list_id = card["idList"]
                list_name = list_map.get(list_id, "Unknown")
                if list_name in status_counts:
                    status_counts[list_name] += 1
                else:
                    status_counts[list_name] = 1
            
            # Debug log the status counts
            self._logger.info(f"Status counts for task distribution: {status_counts}")
            self._logger.info(f"Total tasks: {total_tasks}, Completed tasks: {completed_tasks}")
            
            # DEBUGGING - Add print statements that will show in terminal output
            print("\n=== DEBUGGING CHART DATA ===")
            print(f"Status counts: {status_counts}")
            print(f"Total tasks: {total_tasks}, Completed tasks: {completed_tasks}")
            print(f"Completion rate: {completion_rate}")
            print("===========================\n")
            
            # Define overdue_tasks before using it
            overdue_tasks = []
            
            # Generate charts using ChartGenerator
            chart_generator = ChartGenerator(output_dir="reports")
            
            # Prepare burndown data
            burndown_data = {
                "total_points": velocity,
                "days": 14,  # Assuming a 2-week sprint
                "completion_rate": completion_rate
            }
            
            self._logger.info(f"Burndown data being sent to chart generator: {burndown_data}")
            print(f"Burndown data: {burndown_data}")
            
            # Generate burndown chart
            print("Aaba Generating burndown chart with: ", burndown_data);
            burndown_chart = chart_generator.generate_burndown_chart(
                burndown_data,
                sprint_name=sprint_name
            )
            
            # Prepare velocity data
            velocity_chart_data = {
                "current": velocity,
                "historical": [
                    # {"sprint": "Sprint 1", "velocity": velocity * 0.9},
                    # {"sprint": "Sprint 2", "velocity": velocity * 0.95},
                    # {"sprint": "Sprint 3", "velocity": velocity * 0.98}
                ]
            }
            
            self._logger.info(f"Velocity data being sent to chart generator: current={velocity}")
            print(f"Velocity data: current={velocity}")
            
            # Generate velocity chart
            
            velocity_chart = chart_generator.generate_velocity_chart(
                velocity_chart_data,
                sprint_name=sprint_name
            )
            
            # Prepare task distribution data
            print("Aaba Generating task disribution chart with: ", status_counts);
            task_distribution_data = {
                "statuses": status_counts,
                "total_tasks": total_tasks,
                "completion_rate": completion_rate
            }
            
            self._logger.info(f"Task distribution data being sent to chart generator: {task_distribution_data}")
            print(f"Task distribution data: {task_distribution_data}")
            
            # Generate task distribution chart
            distribution_chart = chart_generator.generate_task_distribution_chart(
                task_distribution_data,
                sprint_name=sprint_name
            )
            
            # Generate Gantt chart
            gantt_chart = chart_generator.generate_gantt_chart(
                {
                    "cards": analysis_results.get("cards", []),
                    "lists": analysis_results.get("lists", []),
                    "sprint_name": sprint_name,
                    "metrics": {
                        "completion_rate": completion_rate,
                        "velocity": velocity,
                        "total_tasks": total_tasks,
                        "completed_tasks": completed_tasks,
                        "overdue_tasks": overdue_tasks,
                        "blockers": blockers
                    }
                },
                sprint_name=sprint_name
            )
            
            # Prepare markdown sections
            sections = []
            
            # Title
            sections.append(f"# Scrum Report: {sprint_name}")
            sections.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
            
            # Executive Summary
            sections.append("# Executive Summary")
            sections.append("---\n")
            
            summary = f"The team has completed **{completion_rate:.1%}** of the sprint tasks "
            summary += f"with a velocity of **{velocity:.1f}** story points.\n\n"
            
            if completion_rate < 0.3:
                summary += "⚠️ **CRITICAL**: The completion rate is concerning and requires immediate attention.\n"
            elif completion_rate < 0.5:
                summary += "⚠️ **WARNING**: The completion rate is below target and needs focus.\n"
            else:
                summary += "✅ The completion rate is on track for this sprint.\n"
                
            if blockers:
                summary += f"\n🚫 **BLOCKERS**: There are **{len(blockers)}** active blockers that need immediate attention.\n"
            
            sections.append(summary)
            
            # Key Metrics Box
            sections.append("## Key Metrics")
            sections.append("---\n")
            metrics_text = [
                f"**Sprint**: {sprint_name}",
                f"**Completion Rate**: {completion_rate:.1%}",
                f"**Velocity**: {velocity:.1f} story points ({trend})",
                f"**Tasks**: {completed_tasks}/{total_tasks} completed",
                f"**Remaining**: {total_tasks - completed_tasks} tasks",
                f"**Blockers**: {len(blockers)}",
            ]
            sections.append("\n".join(metrics_text) + "\n")
            
            # Charts Section
            sections.append("# Sprint Progress & Analytics")
            sections.append("---\n")
            
            # Burndown Chart
            sections.append("## Sprint Burndown")
            sections.append("![Burndown Chart](burndown_chart.png)")
            sections.append("*This chart shows the team's progress in completing story points over the sprint duration.*\n")
            
            # Velocity Chart
            sections.append("## Velocity Trend")
            sections.append("![Velocity Chart](velocity_chart.png)")
            sections.append("*This chart displays the team's velocity compared to previous sprints, helping forecast future capacity.*\n")
            
            # Task Distribution Chart
            sections.append("## Task Distribution")
            sections.append("![Task Distribution](task_distribution_chart.png)")
            sections.append("*This chart shows how tasks are distributed across different workflow stages, helping identify bottlenecks.*\n")
            
            # Gantt Chart
            sections.append("## Sprint Timeline")
            sections.append("![Gantt Chart](gantt_chart.png)")
            sections.append("*This timeline shows tasks with dependencies and highlights critical items that need attention.*\n")
            
            # Blockers Section
            if blockers:
                sections.append("# Critical Blockers")
                sections.append("---\n")
                sections.append("🚨 **IMMEDIATE ACTION REQUIRED**\n")
                
                for i, blocker in enumerate(blockers, 1):
                    sections.append(f"### {i}. {blocker['name']}")
                    if blocker.get("description"):
                        sections.append(f"**Details**: {blocker['description']}")
                    sections.append(f"**Impact**: High - Blocking sprint progress")
                    sections.append(f"**Action Required**: Immediate escalation and resolution")
                    if blocker.get("due"):
                        due_date = datetime.fromisoformat(blocker["due"].replace("Z", "+00:00"))
                        sections.append(f"**Due Date**: {due_date.strftime('%Y-%m-%d')}")
                    sections.append("")
            
            # Approaching Deadlines
            sections.append("# Upcoming Deadlines")
            sections.append("---\n")
            sections.append("⏰ **Tasks Due Within 3 Days**\n")
            
            # Find tasks with approaching deadlines
            approaching_deadlines = []
            current_date = datetime.now(timezone.utc)
            for card in task_cards:
                if card.get("due"):
                    try:
                        due_date = datetime.fromisoformat(card["due"].replace("Z", "+00:00"))
                        days_until_due = (due_date - current_date).days
                        if 0 <= days_until_due <= 3:
                            assignee_ids = card.get("members", [])
                            assignees = []
                            for member in analysis_results.get("members", []):
                                if member["id"] in assignee_ids:
                                    assignees.append(member["fullName"] or member["username"])
                            
                            approaching_deadlines.append({
                                "task": card["name"],
                                "due_in_days": days_until_due,
                                "assignee": assignees[0] if assignees else "Unassigned",
                                "priority": "Critical" if days_until_due == 0 else "High" if days_until_due == 1 else "Medium",
                                "status": list_map.get(card["idList"], "Unknown")
                            })
                    except (ValueError, TypeError) as e:
                        self._logger.warning(f"Error parsing due date for card {card['name']}: {e}")
            
            if approaching_deadlines:
                approaching_deadlines.sort(key=lambda x: x["due_in_days"])
                for task in approaching_deadlines:
                    due_text = "Today" if task["due_in_days"] == 0 else "Tomorrow" if task["due_in_days"] == 1 else f"In {task['due_in_days']} days"
                    priority_color = "🔴" if task["priority"] == "Critical" else "🟠" if task["priority"] == "High" else "🟡"
                    
                    sections.append(f"### {task['task']}")
                    sections.append(f"**Due**: {due_text}")
                    sections.append(f"**Priority**: {priority_color} {task['priority']}")
                    sections.append(f"**Assigned**: {task['assignee']}")
                    sections.append(f"**Status**: {task['status']}\n")
            else:
                sections.append("✅ No tasks due within the next 3 days\n")
            
            # Recommendations Section
            sections.append("# Action Items & Recommendations")
            sections.append("---\n")
            
            # Generate specific recommendations based on data
            recommendations = []
            
            if blockers:
                for blocker in blockers:
                    recommendations.append({
                        "priority": "Critical",
                        "action": f"Resolve blocker: {blocker['name']}",
                        "details": blocker.get("description", "No details provided"),
                        "owner": "Team Lead"
                    })
            
            if completion_rate < 0.3:
                recommendations.append({
                    "priority": "High",
                    "action": "Address Low Completion Rate",
                    "details": "Current completion rate is significantly below target (17.6% vs 70% target)",
                    "owner": "Scrum Master"
                })
            
            if approaching_deadlines:
                recommendations.append({
                    "priority": "High",
                    "action": f"Focus on {len(approaching_deadlines)} approaching deadlines",
                    "details": "Multiple tasks due within 3 days need immediate attention",
                    "owner": "Team"
                })
            
            # Sort recommendations by priority
            priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
            recommendations.sort(key=lambda x: priority_order.get(x["priority"], 99))
            
            # Add recommendations to report
            for i, rec in enumerate(recommendations, 1):
                priority_color = "🔴" if rec["priority"] == "Critical" else "🟠" if rec["priority"] == "High" else "🟡"
                sections.append(f"### {i}. {priority_color} {rec['action']}")
                sections.append(f"**Priority**: {rec['priority']}")
                sections.append(f"**Details**: {rec['details']}")
                sections.append(f"**Owner**: {rec['owner']}\n")
            
            # Save markdown to file
            os.makedirs("reports", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            markdown_path = f"reports/sprint_report_{sprint_name.replace(' ', '_')}_{timestamp}.md"
            
            with open(markdown_path, "w", encoding="utf-8") as f:
                f.write("\n".join(sections))
                
            self._logger.info(f"Markdown report generated: {markdown_path}")
            return markdown_path
            
        except Exception as e:
            self._logger.error(f"Error generating markdown report: {e}")
            self._logger.exception(e)
            return ""
            
    def _get_risk_impact(self, risk: str) -> str:
        """Get impact description for a risk"""
        risk_lower = risk.lower()
        
        if "resource" in risk_lower:
            return "Sprint goals may not be met by the end of the sprint"
        elif "availability" in risk_lower:
            return "Tasks may take longer than estimated"
        elif "scope" in risk_lower:
            return "The team may not be able to complete all planned tasks"
        elif "technical" in risk_lower:
            return "Implementation quality may be compromised or delayed"
        else:
            return "May affect sprint deliverables"
            
    def _get_risk_mitigation(self, risk: str) -> str:
        """Get mitigation strategy for a risk"""
        risk_lower = risk.lower()
        
        if "resource" in risk_lower:
            return "Consider reducing sprint scope or requesting additional resources"
        elif "availability" in risk_lower:
            return "Reprioritize tasks and redistribute workload"
        elif "scope" in risk_lower:
            return "Review scope and identify items that can be moved to future sprints"
        elif "technical" in risk_lower:
            return "Schedule technical debt sessions and conduct design reviews"
        else:
            return "Monitor closely and address at daily stand-ups"

    async def generate_pdf(self, markdown_path: str) -> str:
        """
        Generate a PDF from a markdown file
        
        Args:
            markdown_path: Path to the markdown file
            
        Returns:
            str: Path to the generated PDF file
        """
        try:
            if not os.path.exists(markdown_path):
                self._logger.error(f"Markdown file not found: {markdown_path}")
                return ""
                
            # Generate a PDF filename based on the markdown filename
            pdf_path = markdown_path.replace(".md", ".pdf")
            
            # Use the PDFReportGenerator to generate a PDF from the markdown file
            self._logger.info(f"Converting markdown to PDF: {markdown_path} -> {pdf_path}")
            pdf_path = self._pdf_generator.generate_pdf_from_markdown(markdown_path, pdf_path)
            
            if not pdf_path or not os.path.exists(pdf_path):
                self._logger.error("Failed to generate PDF from markdown")
                return ""
                
            self._logger.info(f"PDF generated: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            self._logger.error(f"Error generating PDF: {e}")
            self._logger.exception(e)
            return ""
            
    async def upload_to_cloudinary(self, pdf_path: str) -> str:
        """
        Upload a PDF file to Cloudinary.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            str: Cloudinary URL to the uploaded file
        """
        try:
            if not os.path.exists(pdf_path):
                self._logger.error(f"PDF file not found: {pdf_path}")
                return ""
                
            self._logger.info(f"Uploading PDF to Cloudinary: {pdf_path}")
            
            # Use the already implemented PDFReportGenerator's upload_to_cloudinary
            result = self._pdf_generator.upload_to_cloudinary(pdf_path)
            
            if not result.get("success", False):
                self._logger.error(f"Failed to upload to Cloudinary: {result.get('error', 'Unknown error')}")
                return ""
                
            cloudinary_url = result.get("url", "")
            self._logger.info(f"PDF uploaded to Cloudinary: {cloudinary_url}")
            return cloudinary_url
            
        except Exception as e:
            self._logger.error(f"Error uploading to Cloudinary: {e}")
            self._logger.exception(e)
            return ""