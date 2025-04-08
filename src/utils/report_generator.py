"""
Report Generator Module

This module defines the ReportGenerator class, which is responsible for
generating sprint reports with metrics and visualizations.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, timezone
import matplotlib.pyplot as plt
import seaborn as sns
from src.utils.logging_utils import get_logger
import matplotlib.dates as mdates
from matplotlib.lines import Line2D


class ReportGenerator:
    """
    Class responsible for generating sprint reports with metrics and visualizations.
    """

    def __init__(self, output_dir: str = "reports"):
        """
        Initialize the ReportGenerator.

        Args:
            output_dir: Directory to save reports and charts.
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize logger using the utility function
        self._std_logger = get_logger(__name__)
        self._logger = logging.getLogger(__name__)
        
        # Initialize chart generator
        from src.utils.chart_generator import ChartGenerator
        self.chart_generator = ChartGenerator(output_dir)
        
        self._std_logger.info(f"Initialized ReportGenerator with output directory: {output_dir}")

    def generate_report(
        self,
        sprint_data: Dict[str, Any],
        analysis_data: Dict[str, Any],
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate a complete sprint report with metrics and visualizations.

        Args:
            sprint_data: Data collected from the sprint.
            analysis_data: Analysis results.
            output_file: Optional output file path.

        Returns:
            Path to the generated report.
        """
        try:
            # Generate charts
            burn_down_chart = self.generate_burndown_chart(
                analysis_data.get("burn_down", {})
            )
            velocity_chart = self.generate_velocity_chart(
                analysis_data.get("velocity", 0)
            )
            task_distribution_chart = self.generate_task_distribution_chart(
                analysis_data.get("task_distribution", {})
            )
            gantt_chart = self.generate_gantt_chart(
                sprint_data
            )

            # Prepare report content
            report_content = self._prepare_report_content(
                sprint_data,
                analysis_data,
                burn_down_chart,
                velocity_chart,
                task_distribution_chart,
                gantt_chart
            )

            # Set default output file if not provided
            if not output_file:
                output_file = os.path.join(
                    self.output_dir,
                    f"sprint_report_{datetime.now().strftime('%Y%m%d')}.md"
                )

            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            # Write report to file
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report_content)

            self._std_logger.info(f"Generated report at {output_file}")
            return output_file

        except Exception as e:
            self._std_logger.error(f"Error generating report: {e}")
            return ""

    def generate_burndown_chart(
        self,
        burn_down_data: Dict[str, Any],
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate a burndown chart.

        Args:
            burn_down_data: Dictionary containing burndown data.
            output_file: Optional output file path for the chart.

        Returns:
            Path to the generated chart.
        """
        try:
            if not output_file:
                output_file = os.path.join(self.output_dir, "burndown_chart.png")

            print("Aaba Generating burndown chart with: ", burn_down_data);
            plt.figure(figsize=(12, 7))
            
            # Set style and colors
            plt.style.use('default')
            colors = ['#2ecc71', '#e74c3c', '#3498db', '#f1c40f']
            
            # Plot ideal burndown
            ideal_data = burn_down_data.get("ideal_burn_down", [])
            if ideal_data:
                days = [d["day"] for d in ideal_data]
                ideal_points = [d["ideal"] for d in ideal_data]
                plt.plot(days, ideal_points, color=colors[0], linestyle='--', 
                        label="Ideal Burndown", linewidth=2, alpha=0.7)

            # Plot actual burndown
            actual_data = burn_down_data.get("actual_burn_down", [])
            if actual_data:
                days = [d["day"] for d in actual_data]
                actual_points = [d["actual"] for d in actual_data]
                plt.plot(days, actual_points, color=colors[1], linestyle='-', 
                        label="Actual Burndown", linewidth=3)

            # Add grid and styling
            plt.grid(True, linestyle='--', alpha=0.5, color='gray')
            plt.title("Sprint Burndown Chart", pad=20, fontsize=14, fontweight='bold')
            plt.xlabel("Sprint Day", fontsize=12, labelpad=10)
            plt.ylabel("Story Points Remaining", fontsize=12, labelpad=10)
            
            # Add legend with custom styling
            legend = plt.legend(loc='upper right', frameon=True, fancybox=True, shadow=True)
            legend.get_frame().set_alpha(0.9)
            
            # Add annotations for current status
            if actual_data:
                current_points = actual_data[-1].get("actual", 0)
                total_points = burn_down_data.get("total_points", 0)
                completion_rate = (total_points - current_points) / total_points * 100 if total_points > 0 else 0
                
                # Add completion rate annotation
                plt.annotate(
                    f"Completion Rate: {completion_rate:.1f}%",
                    xy=(days[-1], current_points),
                    xytext=(10, 10),
                    textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.5', fc=colors[2], alpha=0.3),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
                )

                # Add total points annotation
                plt.annotate(
                    f"Total Points: {total_points}",
                    xy=(0, total_points),
                    xytext=(10, 10),
                    textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.5', fc=colors[3], alpha=0.3),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
                )

                # Add remaining points annotation
                plt.annotate(
                    f"Remaining: {current_points}",
                    xy=(days[-1], current_points),
                    xytext=(10, -10),
                    textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.5', fc=colors[0], alpha=0.3),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
                )

            # Set background color and style
            ax = plt.gca()
            ax.set_facecolor('#f8f9fa')
            plt.gcf().set_facecolor('#ffffff')
            
            # Add padding and save
            plt.margins(x=0.05)
            plt.tight_layout()
            plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()

            self._std_logger.info(f"Generated burndown chart at {output_file}")
            return output_file

        except Exception as e:
            self._std_logger.error(f"Error generating burndown chart: {e}")
            return ""

    def generate_velocity_chart(self, velocity_data: Dict[str, Any], sprint_name: str = "") -> str:
        """
        Generate a velocity chart showing historical and current velocity.

        Args:
            velocity_data: Dictionary containing velocity data
            sprint_name: Name of the sprint for chart title

        Returns:
            Path to the generated chart image
        """
        try:
            # Handle velocity data which might be a dict or a number
            if isinstance(velocity_data, dict):
                velocity = velocity_data.get("current", 0)
                historical = velocity_data.get("historical", [])
            else:
                velocity = float(velocity_data)
                # Generate some historical data for visualization
                historical = [
                    {"sprint": f"Sprint {i}", "velocity": velocity * (0.85 + (i * 0.05))}
                    for i in range(1, 4)
                ]
            
            # Create velocity chart data
            velocity_chart_data = {
                "current": velocity,
                "historical": historical,
                "sprint_name": sprint_name
            }
            
            # Generate velocity chart
            return self.chart_generator.generate_velocity_chart(velocity_chart_data, sprint_name)

        except Exception as e:
            self._std_logger.error(f"Error generating velocity chart: {e}")
            return ""

    def generate_task_distribution_chart(
        self,
        task_data: Dict[str, Any],
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate a task distribution pie chart.

        Args:
            task_data: Dictionary containing task distribution data.
            output_file: Optional output file path for the chart.

        Returns:
            Path to the generated chart.
        """
        try:
            if not output_file:
                output_file = os.path.join(self.output_dir, "task_distribution_chart.png")
            print("Aaba Generating task distribution chart with: ", task_data);
            plt.figure(figsize=(10, 8))
            
            # Set style and colors
            plt.style.use('default')
            colors = ['#2ecc71', '#e74c3c', '#3498db', '#f1c40f', '#9b59b6', '#1abc9c', 
                     '#e67e22', '#34495e', '#16a085', '#c0392b']
            
            # Prepare data
            lists = list(task_data.keys())
            counts = list(task_data.values())
            total = sum(counts)
            
            # Create pie chart
            patches, texts, autotexts = plt.pie(
                counts,
                labels=lists,
                colors=colors[:len(lists)],
                autopct=lambda pct: f'{pct:.1f}%\n({int(pct/100.*total)})',
                pctdistance=0.85,
                wedgeprops=dict(width=0.5)  # Create a donut chart
            )
            
            # Customize text properties
            plt.setp(autotexts, size=9, weight="bold", color="white")
            plt.setp(texts, size=10)
            
            # Add title
            plt.title("Task Distribution by List", pad=20, fontsize=14, fontweight='bold')
            
            # Add center text with total
            plt.text(0, 0, f'Total\n{total}', ha='center', va='center', 
                    fontsize=12, fontweight='bold')
            
            # Set background color
            plt.gcf().set_facecolor('#ffffff')
            
            # Add legend with custom styling
            legend = plt.legend(
                [f"{l} ({c})" for l, c in zip(lists, counts)],
                loc='center left',
                bbox_to_anchor=(1, 0, 0.5, 1),
                frameon=True,
                fancybox=True,
                shadow=True
            )
            legend.get_frame().set_alpha(0.9)
            
            # Save chart
            plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()

            self._std_logger.info(f"Generated task distribution chart at {output_file}")
            return output_file

        except Exception as e:
            self._std_logger.error(f"Error generating task distribution chart: {e}")
            return ""

    def generate_gantt_chart(self, sprint_data: Dict[str, Any], output_file: str = 'reports/gantt_chart.png') -> str:
        """
        Generate a Gantt chart to visualize task deadlines by list/section.
        
        Args:
            sprint_data: Data collected from the sprint.
            output_file: Path to save the generated chart.
            
        Returns:
            The path to the generated chart.
        """
        try:
            cards = sprint_data.get('cards', [])
            lists = sprint_data.get('lists', [])
            
            if not cards or not lists:
                self._std_logger.warning("No cards or lists data for Gantt chart")
                return output_file
            
            # Create a mapping of list IDs to names
            list_map = {lst['id']: lst['name'] for lst in lists}
            
            # Filter cards that have due dates
            cards_with_due_dates = []
            now = datetime.now().replace(tzinfo=None)  # Make timezone-naive for consistent comparisons
            
            for card in cards:
                if 'due' in card and card['due']:
                    try:
                        # Convert to timezone-naive datetime for consistent comparisons
                        due_date = datetime.fromisoformat(card['due'].replace('Z', '+00:00'))
                        due_date = due_date.replace(tzinfo=None)
                        
                        list_name = list_map.get(card.get('idList', ''), 'Unknown')
                        is_completed = card.get('dueComplete', False)
                        is_critical = (due_date - now).days <= 2 and not is_completed
                        
                        cards_with_due_dates.append({
                            'name': card.get('name', 'Unnamed'),
                            'due_date': due_date,
                            'list_name': list_name,
                            'is_completed': is_completed,
                            'is_critical': is_critical
                        })
                    except (ValueError, KeyError) as e:
                        self._std_logger.warning(f"Error processing card due date: {e}")
            
            if not cards_with_due_dates:
                self._std_logger.warning("No cards with valid due dates for Gantt chart")
                return output_file
            
            # Sort cards by due date
            cards_with_due_dates.sort(key=lambda x: x['due_date'])
            
            # Determine date range for the chart
            earliest_date = min(card['due_date'] for card in cards_with_due_dates)
            latest_date = max(card['due_date'] for card in cards_with_due_dates)
            
            # Add a buffer to start and end dates
            start_date = earliest_date - timedelta(days=1)
            end_date = latest_date + timedelta(days=1)
            
            # Group cards by list
            cards_by_list = {}
            for card in cards_with_due_dates:
                list_name = card['list_name']
                if list_name not in cards_by_list:
                    cards_by_list[list_name] = []
                cards_by_list[list_name].append(card)
            
            # Set up the figure
            fig, ax = plt.figure(figsize=(12, 8), dpi=100), plt.gca()
            
            # Colors for different list types
            list_colors = {
                'To Do': '#3498db',       # Blue
                'In Progress': '#f39c12', # Orange
                'Done': '#2ecc71',       # Green
                'Backlog': '#95a5a6',    # Gray
                'Design': '#9b59b6',     # Purple
                'Testing': '#e74c3c'      # Red
            }
            
            # Default color for unknown lists
            default_color = '#34495e'  # Dark blue-gray
            
            # Define y-positions for each list
            lists_sorted = sorted(cards_by_list.keys())
            y_positions = {list_name: i for i, list_name in enumerate(lists_sorted)}
            
            # Plot the date range lines
            for i, list_name in enumerate(lists_sorted):
                plt.hlines(
                    y=i, 
                    xmin=start_date, 
                    xmax=end_date, 
                    colors='grey', 
                    linestyles='dashed', 
                    alpha=0.3
                )
            
            # Group critical cards by date and list
            critical_points = {}
            
            # Plot cards as dots at their due dates
            for list_name, cards in cards_by_list.items():
                y_pos = y_positions[list_name]
                
                for card in cards:
                    color = list_colors.get(list_name, default_color)
                    
                    # Use red for critical tasks
                    if card['is_critical']:
                        marker_color = 'red'
                        marker_size = 120
                        edge_color = 'black'
                        zorder = 5
                        
                        # Store critical point coordinates for later annotation
                        date_key = card['due_date'].strftime('%Y-%m-%d')
                        if date_key not in critical_points:
                            critical_points[date_key] = {}
                        if list_name not in critical_points[date_key]:
                            critical_points[date_key][list_name] = {'count': 0, 'position': (card['due_date'], y_pos)}
                        critical_points[date_key][list_name]['count'] += 1
                        
                    elif card['is_completed']:
                        marker_color = '#2ecc71'  # Green for completed
                        marker_size = 80
                        edge_color = color
                        zorder = 3
                    else:
                        marker_color = color
                        marker_size = 80
                        edge_color = 'black'
                        zorder = 4
                    
                    plt.scatter(
                        card['due_date'], 
                        y_pos, 
                        s=marker_size, 
                        color=marker_color, 
                        edgecolors=edge_color,
                        zorder=zorder,
                        alpha=0.8
                    )
            
            # Add count boxes with arrows for critical tasks
            for date_key, list_data in critical_points.items():
                for list_name, data in list_data.items():
                    count = data['count']
                    x_pos, y_pos = data['position']
                    
                    # Create arrow coordinates
                    arrow_dx = 0
                    arrow_dy = -0.3  # Direction of arrow (adjust as needed)
                    
                    # Draw the yellow box with count number
                    bbox_props = dict(boxstyle="round,pad=0.3", fc='yellow', ec='black', alpha=0.8)
                    plt.annotate(
                        f"{count}", 
                        xy=(x_pos, y_pos),
                        xytext=(x_pos, y_pos + arrow_dy),  # Text position above/below the dot
                        textcoords='data',
                        fontsize=10,
                        fontweight='bold',
                        color='black',
                        ha='center',
                        va='center',
                        bbox=bbox_props,
                        arrowprops=dict(
                            arrowstyle="->",
                            connectionstyle="arc3,rad=0",
                            shrinkA=0,
                            shrinkB=5,
                            fc="black", 
                            ec="black"
                        ),
                        zorder=6
                    )
            
            # Group critical tasks by date and list to show counts at the bottom
            critical_task_counts = {}
            for card in cards_with_due_dates:
                if card['is_critical']:
                    date_str = card['due_date'].strftime('%Y-%m-%d')
                    if date_str not in critical_task_counts:
                        critical_task_counts[date_str] = {}
                    
                    list_name = card['list_name']
                    if list_name not in critical_task_counts[date_str]:
                        critical_task_counts[date_str][list_name] = 0
                    
                    critical_task_counts[date_str][list_name] += 1
            
            # Add annotations for critical task counts at the bottom of the chart
            for date_str, list_counts in critical_task_counts.items():
                due_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                # Create combined annotation text
                annotations = []
                for list_name, count in list_counts.items():
                    annotations.append(f"{count} - {list_name}")
                
                annotation_text = ", ".join(annotations)
                
                # Find a good y-position for the annotation (above all the sections)
                y_pos = -0.5  # Default position below the chart
                
                plt.annotate(
                    annotation_text,
                    xy=(due_date, y_pos),
                    xytext=(0, -35),
                    textcoords='offset points',
                    ha='center',
                    fontsize=10,
                    weight='bold',
                    color='red',
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="red", alpha=0.8),
                    zorder=7
                )
            
            # Set labels and title
            plt.yticks(range(len(lists_sorted)), lists_sorted, fontsize=12)
            plt.title('Sprint Task Timeline (Gantt Chart)', fontsize=16, fontweight='bold')
            
            # Format x-axis as dates
            date_format = mdates.DateFormatter('%Y-%m-%d')
            ax.xaxis.set_major_formatter(date_format)
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
            plt.xticks(rotation=45, fontsize=10)
            
            # Add grid
            plt.grid(True, axis='x', alpha=0.3)
            
            # Add legend
            legend_elements = [
                Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=10, label='Critical (due within 2 days)'),
                Line2D([0], [0], marker='o', color='w', markerfacecolor='#2ecc71', markersize=10, label='Completed'),
                Line2D([0], [0], marker='o', color='w', markerfacecolor='#3498db', markersize=10, label='Normal')
            ]
            plt.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3)
            
            # Add a vertical line for current date
            plt.axvline(x=now, color='red', linestyle='--', alpha=0.7, label='Current Date')
            
            # Add annotation for today
            plt.annotate(
                'Today', 
                (now, -0.5), 
                xytext=(0, -25),
                textcoords='offset points',
                fontsize=10,
                weight='bold',
                ha='center'
            )
            
            plt.tight_layout()
            plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            self._std_logger.info(f"Generated Gantt chart at {output_file}")
            return output_file
            
        except Exception as e:
            self._std_logger.error(f"Error generating Gantt chart: {e}")
            return output_file

    def _prepare_report_content(
        self,
        sprint_data: Dict[str, Any],
        analysis_data: Dict[str, Any],
        burn_down_chart: str,
        velocity_chart: str,
        task_distribution_chart: str,
        gantt_chart: str
    ) -> str:
        """
        Prepare the content of the sprint report.

        Args:
            sprint_data: Data collected from the sprint.
            analysis_data: Analysis results.
            burn_down_chart: Path to the burndown chart.
            velocity_chart: Path to the velocity chart.
            task_distribution_chart: Path to the task distribution chart.
            gantt_chart: Path to the Gantt chart.

        Returns:
            Formatted report content.
        """
        try:
            content = []
            
            # Extract detailed data
            sprint_name = sprint_data.get('sprint_name', '')
            cards = sprint_data.get('cards', [])
            lists = sprint_data.get('lists', [])
            members = sprint_data.get('members', [])
            
            # Create a mapping of list IDs to their names
            list_map = {lst["id"]: lst["name"] for lst in lists}
            
            # Create a mapping of member IDs to their names
            member_map = {member["id"]: member.get("fullName", member.get("username", "Unknown")) 
                          for member in members}
            
            # Count tasks by filtering out column headers
            task_cards = [card for card in cards if not card["name"] in ["Backlog", "Planning / Design", "Ready", "In Progress", "Review", "Done"]]
            
            # Count completed tasks (those in the "Done" list)
            done_list_ids = [lst["id"] for lst in lists if "Done" in lst["name"]]
            completed_tasks = sum(1 for card in task_cards if card["idList"] in done_list_ids)
            total_tasks = len(task_cards)
            
            # Calculate proper completion rate
            completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
            
            # Get metrics
            velocity_data = analysis_data.get('velocity', 0)
            velocity = velocity_data.get('current', 0) if isinstance(velocity_data, dict) else float(velocity_data)
            
            # Identify blockers from the data
            blockers = []
            for card in task_cards:
                # Check for red labels which might indicate blockers
                if any(label.get("color", "") == "red" for label in card.get("labels", [])):
                    member_names = [member_map.get(member_id, "Unassigned") 
                                    for member_id in card.get("idMembers", [])]
                    
                    blockers.append({
                        "title": card["name"],
                        "details": card.get("desc", "No details provided"),
                        "due_date": card.get("due", ""),
                        "assigned_to": ", ".join(member_names) if member_names else "Unassigned",
                        "status": list_map.get(card["idList"], "Unknown"),
                        "impact": "High - Blocking sprint progress",
                        "action": "Immediate escalation and resolution",
                        "owner": "Team Lead"
                    })
                # Check for "blocked" in the name or description
                elif "block" in card.get("name", "").lower() or "block" in card.get("desc", "").lower():
                    if not any(b["title"] == card["name"] for b in blockers):
                        member_names = [member_map.get(member_id, "Unassigned") 
                                       for member_id in card.get("idMembers", [])]
                        
                        blockers.append({
                            "title": card["name"],
                            "details": card.get("desc", "No details provided"),
                            "due_date": card.get("due", ""),
                            "assigned_to": ", ".join(member_names) if member_names else "Unassigned",
                            "status": list_map.get(card["idList"], "Unknown"),
                            "impact": "High - Blocking sprint progress",
                            "action": "Immediate escalation and resolution",
                            "owner": "Team Lead"
                        })
            
            # Title and date
            content.extend([
                f"# Scrum Report: {sprint_name}",
                f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
                "# Executive Summary",
                "---\n"
            ])
            
            # Executive summary
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
            
            content.append(summary)
            
            # Key metrics
            content.extend([
                "## Key Metrics",
                "---\n",
                f"**Sprint**: {sprint_name}",
                f"**Completion Rate**: {completion_rate:.1%}",
                f"**Velocity**: {velocity:.1f} story points (stable)",
                f"**Tasks**: {completed_tasks}/{total_tasks} completed",
                f"**Remaining**: {total_tasks - completed_tasks} tasks",
                f"**Blockers**: {len(blockers)}",
                "\n"
            ])
            
            # Charts section
            content.extend([
                "# Sprint Progress & Analytics",
                "---\n",
                "## Sprint Burndown",
                f"![Burndown Chart]({os.path.basename(burn_down_chart)})",
                "*This chart shows the team's progress in completing story points over the sprint duration.*\n",
                "## Velocity Trend",
                f"![Velocity Chart]({os.path.basename(velocity_chart)})",
                "*This chart displays the team's velocity compared to previous sprints, helping forecast future capacity.*\n",
                "## Task Distribution",
                f"![Task Distribution]({os.path.basename(task_distribution_chart)})",
                "*This chart shows how tasks are distributed across different workflow stages, helping identify bottlenecks.*\n",
                "## Sprint Timeline",
                f"![Gantt Chart]({os.path.basename(gantt_chart)})",
                "*This timeline shows tasks with dependencies and highlights critical items that need attention.*\n"
            ])
            
            # Critical blockers section
            if blockers:
                content.extend([
                    "# Critical Blockers",
                    "---\n",
                    "🚨 **IMMEDIATE ACTION REQUIRED**\n"
                ])
                
                for i, blocker in enumerate(blockers, 1):
                    content.extend([
                        f"### {i}. {blocker['title']}",
                        f"**Impact**: {blocker['impact']}",
                        f"**Action Required**: {blocker['action']}",
                        f"**Assigned to**: {blocker['assigned_to']}",
                        f"**Status**: {blocker['status']}"
                    ])
                    
                    if blocker.get('due_date'):
                        due_date = datetime.fromisoformat(blocker["due_date"].replace("Z", "+00:00")) if blocker["due_date"] else None
                        if due_date:
                            content.append(f"**Due Date**: {due_date.strftime('%Y-%m-%d')}")
                    
                    if blocker.get('details') and blocker['details'].strip():
                        content.append(f"**Details**: {blocker['details']}")
                    
                    content.append("")
            
            # Tasks section - show all tasks in progress
            in_progress_lists = [lst["id"] for lst in lists if "Progress" in lst["name"]]
            in_progress_tasks = [card for card in task_cards if card["idList"] in in_progress_lists]
            
            if in_progress_tasks:
                content.extend([
                    "# Tasks In Progress",
                    "---\n"
                ])
                
                for i, task in enumerate(in_progress_tasks, 1):
                    member_names = [member_map.get(member_id, "Unassigned") 
                                   for member_id in task.get("idMembers", [])]
                    assigned_to = ", ".join(member_names) if member_names else "Unassigned"
                    
                    # Get due date if available
                    due_date_text = "No due date"
                    if task.get("due"):
                        try:
                            due_date = datetime.fromisoformat(task["due"].replace("Z", "+00:00"))
                            due_date_text = due_date.strftime('%Y-%m-%d')
                        except:
                            due_date_text = "Invalid date format"
                    
                    # Get labels
                    labels = [label.get("name", "") or label.get("color", "").capitalize() 
                             for label in task.get("labels", [])]
                    labels_text = ", ".join(labels) if labels else "None"
                    
                    content.extend([
                        f"### {i}. {task['name']}",
                        f"**Assigned to**: {assigned_to}",
                        f"**Due Date**: {due_date_text}",
                        f"**Labels**: {labels_text}",
                        f"**Status**: {list_map.get(task['idList'], 'Unknown')}"
                    ])
                    
                    if task.get("desc", "").strip():
                        content.append(f"**Description**: {task['desc'][:100]}...")
                    
                    content.append("")
            
            # Find tasks with approaching deadlines
            approaching_deadlines = []
            current_date = datetime.now(timezone.utc)  # Use timezone-aware datetime
            
            for card in task_cards:
                if card.get("due") and card["idList"] not in done_list_ids:
                    try:
                        # Convert to timezone-aware datetime
                        due_date = datetime.fromisoformat(card["due"].replace("Z", "+00:00"))
                        days_until_due = (due_date - current_date).days
                        
                        if -5 <= days_until_due <= 3:  # Include slightly overdue and approaching
                            member_names = [member_map.get(member_id, "Unassigned") 
                                           for member_id in card.get("idMembers", [])]
                            
                            priority = "Critical" if days_until_due <= 0 else "High" if days_until_due <= 1 else "Medium"
                            priority_emoji = "🔴" if priority == "Critical" else "🟠" if priority == "High" else "🟡"
                            
                            due_text = "Overdue" if days_until_due < 0 else "Today" if days_until_due == 0 else "Tomorrow" if days_until_due == 1 else f"In {days_until_due} days"
                            
                            approaching_deadlines.append({
                                "title": card["name"],
                                "due": due_text,
                                "due_in_days": days_until_due,
                                "assigned_to": ", ".join(member_names) if member_names else "Unassigned",
                                "priority": priority,
                                "priority_emoji": priority_emoji,
                                "status": list_map.get(card["idList"], "Unknown")
                            })
                    except (ValueError, TypeError) as e:
                        self._std_logger.warning(f"Error parsing due date for card {card['name']}: {e}")
            
            # Add upcoming deadlines section
            if approaching_deadlines:
                content.extend([
                    "# Upcoming Deadlines",
                    "---\n",
                    "⏰ **Tasks Due Soon or Overdue**\n"
                ])
                
                # Sort by urgency (overdue first, then by days until due)
                approaching_deadlines.sort(key=lambda x: x["due_in_days"])
                
                for task in approaching_deadlines:
                    content.extend([
                        f"### {task['title']}",
                        f"**Due**: {task['due']}",
                        f"**Priority**: {task['priority_emoji']} {task['priority']}",
                        f"**Assigned**: {task['assigned_to']}",
                        f"**Status**: {task['status']}\n"
                    ])
            
            # Action items section
            content.extend([
                "# Action Items & Recommendations",
                "---\n"
            ])
            
            # Add blocker action items
            for i, blocker in enumerate(blockers, 1):
                content.extend([
                    f"### {i}. 🔴 Resolve blocker: {blocker['title']}",
                    "**Priority**: Critical",
                    f"**Details**: {blocker['details'][:150] if blocker['details'].strip() else 'No details provided'}",
                    f"**Owner**: {blocker['assigned_to']}\n"
                ])
            
            # Add completion rate action item if needed
            if completion_rate < 0.7:  # 70% target
                content.extend([
                    f"### {len(blockers) + 1}. 🟠 Address Low Completion Rate",
                    "**Priority**: High",
                    f"**Details**: Current completion rate is significantly below target ({completion_rate:.1%} vs 70% target)",
                    "**Owner**: Scrum Master\n"
                ])
            
            # Add approaching deadlines action item if needed
            if approaching_deadlines:
                content.extend([
                    f"### {len(blockers) + 2}. 🟠 Focus on approaching deadlines",
                    "**Priority**: High",
                    f"**Details**: {len(approaching_deadlines)} tasks due soon or overdue need immediate attention",
                    "**Owner**: Team\n"
                ])
            
            # Add team section with contributor information
            if members:
                content.extend([
                    "# Team Information",
                    "---\n"
                ])
                
                # Count tasks per member
                member_task_counts = {}
                for card in task_cards:
                    for member_id in card.get("idMembers", []):
                        member_name = member_map.get(member_id, "Unknown")
                        if member_name in member_task_counts:
                            member_task_counts[member_name] += 1
                        else:
                            member_task_counts[member_name] = 1
                
                # Sort by number of tasks
                sorted_members = sorted(member_task_counts.items(), key=lambda x: x[1], reverse=True)
                
                for member_name, task_count in sorted_members:
                    completed_count = sum(1 for card in task_cards 
                                         if card["idList"] in done_list_ids 
                                         and any(member_map.get(m_id) == member_name for m_id in card.get("idMembers", [])))
                    
                    content.extend([
                        f"### {member_name}",
                        f"**Total Tasks**: {task_count}",
                        f"**Completed**: {completed_count}",
                        f"**In Progress**: {task_count - completed_count}",
                    ])
                    
                    # Show active tasks for this member
                    member_active_tasks = [card["name"] for card in task_cards 
                                          if card["idList"] not in done_list_ids 
                                          and any(member_map.get(m_id) == member_name for m_id in card.get("idMembers", []))]
                    
                    if member_active_tasks:
                        content.append("**Active Tasks**:")
                        for task in member_active_tasks[:3]:  # Show up to 3 tasks
                            content.append(f"- {task}")
                        
                        if len(member_active_tasks) > 3:
                            content.append(f"- ...and {len(member_active_tasks) - 3} more")
                    
                    content.append("")
            
            return "\n".join(content)
            
        except Exception as e:
            self._std_logger.error(f"Error preparing report content: {e}")
            self._std_logger.exception(e)
            return ""

    def _format_team_contributions(self, cards_by_member: Dict[str, int]) -> str:
        """
        Format team member contributions.

        Args:
            cards_by_member: Dictionary mapping member names to their card counts.

        Returns:
            Formatted string of team contributions.
        """
        try:
            if not cards_by_member:
                return "- No team member data available"

            contributions = []
            for member, count in cards_by_member.items():
                contributions.append(f"- **{member}**: {count} cards")

            return "\n".join(contributions)

        except Exception as e:
            self._std_logger.error(f"Error formatting team contributions: {e}")
            return "- Error formatting team contributions"

    def _calculate_collaboration_score(self, cards_by_member: Dict[str, int]) -> float:
        """
        Calculate team collaboration score.

        Args:
            cards_by_member: Dictionary mapping member names to their card counts.

        Returns:
            Collaboration score as a percentage.
        """
        try:
            if not cards_by_member:
                return 0.0

            total_cards = sum(cards_by_member.values())
            if total_cards == 0:
                return 0.0

            # Calculate standard deviation of card distribution
            mean = total_cards / len(cards_by_member)
            variance = sum((count - mean) ** 2 for count in cards_by_member.values()) / len(cards_by_member)
            std_dev = variance ** 0.5

            # Convert to percentage (lower std dev = higher collaboration)
            max_std_dev = total_cards * 0.5  # Maximum possible standard deviation
            collaboration_score = 100 * (1 - (std_dev / max_std_dev))
            return max(0, min(100, collaboration_score))

        except Exception as e:
            self._std_logger.error(f"Error calculating collaboration score: {e}")
            return 0.0

    def _identify_skill_opportunities(self, cards_by_member: Dict[str, int]) -> str:
        """
        Identify skill development opportunities.

        Args:
            cards_by_member: Dictionary mapping member names to their card counts.

        Returns:
            Formatted string of skill opportunities.
        """
        try:
            if not cards_by_member:
                return "- No team member data available"

            opportunities = []
            total_cards = sum(cards_by_member.values())
            if total_cards == 0:
                return "- No cards available for analysis"

            # Calculate average cards per member
            avg_cards = total_cards / len(cards_by_member)

            # Identify members with significantly different workloads
            for member, count in cards_by_member.items():
                if count < avg_cards * 0.5:
                    opportunities.append(f"- **{member}** has fewer cards than average. Consider increasing workload or providing support.")
                elif count > avg_cards * 1.5:
                    opportunities.append(f"- **{member}** has more cards than average. Consider knowledge sharing or workload redistribution.")

            return "\n".join(opportunities) if opportunities else "- No significant skill opportunities identified"

        except Exception as e:
            self._std_logger.error(f"Error identifying skill opportunities: {e}")
            return "- Error identifying skill opportunities"

    def _format_recommendations(self, recommendations: List[Dict[str, Any]]) -> str:
        """
        Format recommendations for the report.

        Args:
            recommendations: List of recommendation dictionaries.

        Returns:
            Formatted string of recommendations.
        """
        try:
            if not recommendations:
                return "- No recommendations available"

            formatted_recs = []
            for rec in recommendations:
                formatted_recs.append(f"- **{rec.get('title', 'Recommendation')}**")
                formatted_recs.append(f"  - {rec.get('description', 'No description available')}")
                if rec.get('priority'):
                    formatted_recs.append(f"  - Priority: {rec.get('priority')}")

            return "\n".join(formatted_recs)

        except Exception as e:
            self._std_logger.error(f"Error formatting recommendations: {e}")
            return "- Error formatting recommendations"

    def _format_achievements(self, achievements: List[str]) -> str:
        """
        Format achievements for the report.

        Args:
            achievements: List of achievement strings.

        Returns:
            Formatted string of achievements.
        """
        try:
            if not achievements:
                return "- No achievements recorded"

            return "\n".join(f"- {achievement}" for achievement in achievements)

        except Exception as e:
            self._std_logger.error(f"Error formatting achievements: {e}")
            return "- Error formatting achievements"

    def _format_improvements(self, improvements: List[str]) -> str:
        """
        Format improvements for the report.

        Args:
            improvements: List of improvement strings.

        Returns:
            Formatted string of improvements.
        """
        try:
            if not improvements:
                return "- No improvements identified"

            return "\n".join(f"- {improvement}" for improvement in improvements)

        except Exception as e:
            self._std_logger.error(f"Error formatting improvements: {e}")
            return "- Error formatting improvements"

    def _format_team_feedback(self, feedback: List[str]) -> str:
        """
        Format team feedback for the report.

        Args:
            feedback: List of feedback strings.

        Returns:
            Formatted string of team feedback.
        """
        try:
            if not feedback:
                return "- No team feedback available"

            return "\n".join(f"- {item}" for item in feedback)

        except Exception as e:
            self._std_logger.error(f"Error formatting team feedback: {e}")
            return "- Error formatting team feedback"

    def _generate_sprint_status_analysis(self, sprint_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> str:
        """
        Generate sprint status analysis.

        Args:
            sprint_data: Data collected from the sprint.
            analysis_data: Analysis results.

        Returns:
            Formatted string of sprint status analysis.
        """
        try:
            metrics = analysis_data.get("sprint_metrics", {})
            completion_rate = metrics.get("completion_rate", 0)
            blockers = metrics.get("blockers_count", 0)
            overdue = metrics.get("overdue_count", 0)

            analysis = [
                "### Sprint Status Analysis\n",
                f"- **Overall Progress**: {completion_rate:.1f}% complete",
                f"- **Blockers**: {blockers} items blocking progress",
                f"- **Overdue Items**: {overdue} items past due date"
            ]

            return "\n".join(analysis)

        except Exception as e:
            self._std_logger.error(f"Error generating sprint status analysis: {e}")
            return "### Sprint Status Analysis\n- Error generating analysis"

    def _generate_metrics_analysis(self, metrics: Dict[str, Any]) -> str:
        """
        Generate metrics analysis.

        Args:
            metrics: Dictionary of sprint metrics.

        Returns:
            Formatted string of metrics analysis.
        """
        try:
            analysis = [
                "### Metrics Analysis\n",
                f"- **Total Cards**: {metrics.get('total_cards', 0)}",
                f"- **Completed Cards**: {metrics.get('completed_cards', 0)}",
                f"- **Completion Rate**: {metrics.get('completion_rate', 0):.1f}%",
                f"- **Blockers**: {metrics.get('blockers_count', 0)}",
                f"- **Overdue**: {metrics.get('overdue_count', 0)}",
                f"- **Approaching Deadlines**: {metrics.get('approaching_deadlines_count', 0)}"
            ]

            return "\n".join(analysis)

        except Exception as e:
            self._std_logger.error(f"Error generating metrics analysis: {e}")
            return "### Metrics Analysis\n- Error generating analysis"

    def _generate_team_workload_analysis(self, team_performance: Dict[str, Any]) -> str:
        """
        Generate team workload analysis.

        Args:
            team_performance: Dictionary of team performance data.

        Returns:
            Formatted string of team workload analysis.
        """
        try:
            cards_by_member = team_performance.get("cards_by_member", {})
            avg_cards = team_performance.get("avg_cards_per_member", 0)
            high_workload = team_performance.get("members_with_high_workload", [])

            analysis = [
                "### Team Workload Analysis\n",
                f"- **Average Cards per Member**: {avg_cards:.1f}",
                f"- **Collaboration Score**: {self._calculate_collaboration_score(cards_by_member):.1f}%"
            ]

            if high_workload:
                analysis.append("\n**Members with High Workload**:")
                analysis.extend(f"- {member}" for member in high_workload)

            return "\n".join(analysis)

        except Exception as e:
            self._std_logger.error(f"Error generating team workload analysis: {e}")
            return "### Team Workload Analysis\n- Error generating analysis"

    def _generate_process_health_analysis(self, process_bottlenecks: Dict[str, Any]) -> str:
        """
        Generate process health analysis.

        Args:
            process_bottlenecks: Dictionary of process bottleneck data.

        Returns:
            Formatted string of process health analysis.
        """
        try:
            bottlenecks = process_bottlenecks.get("bottlenecks", [])
            avg_cards = process_bottlenecks.get("avg_cards_per_list", 0)

            analysis = [
                "### Process Health Analysis\n",
                f"- **Process Bottlenecks**: {len(bottlenecks)}",
                f"- **Average Cards per List**: {avg_cards:.1f}"
            ]

            if bottlenecks:
                analysis.append("\n**Identified Bottlenecks**:")
                analysis.extend(f"- {bottleneck}" for bottleneck in bottlenecks)

            return "\n".join(analysis)

        except Exception as e:
            self._std_logger.error(f"Error generating process health analysis: {e}")
            return "### Process Health Analysis\n- Error generating analysis"

    def _generate_burndown_analysis(self, burn_down_data: Dict[str, Any]) -> str:
        """
        Generate burndown analysis.

        Args:
            burn_down_data: Dictionary of burndown data.

        Returns:
            Formatted string of burndown analysis.
        """
        try:
            actual_data = burn_down_data.get("actual_burn_down", [])
            if not actual_data:
                return "### Burndown Analysis\n- No burndown data available"

            current_points = actual_data[-1].get("actual", 0)
            total_points = burn_down_data.get("total_points", 0)
            completion_rate = (total_points - current_points) / total_points * 100 if total_points > 0 else 0

            analysis = [
                "### Burndown Analysis\n",
                f"- **Current Story Points**: {current_points}",
                f"- **Total Story Points**: {total_points}",
                f"- **Completion Rate**: {completion_rate:.1f}%"
            ]

            return "\n".join(analysis)

        except Exception as e:
            self._std_logger.error(f"Error generating burndown analysis: {e}")
            return "### Burndown Analysis\n- Error generating analysis"

    def _generate_velocity_analysis(self, velocity_data: Dict[str, Any]) -> str:
        """
        Generate velocity analysis.

        Args:
            velocity_data: Dictionary of velocity data.

        Returns:
            Formatted string of velocity analysis.
        """
        try:
            current_sprint = velocity_data.get("current_sprint", {})
            historical = velocity_data.get("historical", [])

            if not historical:
                return "### Velocity Analysis\n- No historical velocity data available"

            current_points = current_sprint.get("completed_points", 0)
            avg_historical = sum(h["completed_points"] for h in historical) / len(historical)

            analysis = [
                "### Velocity Analysis\n",
                f"- **Current Sprint Points**: {current_points}",
                f"- **Average Historical Points**: {avg_historical:.1f}",
                f"- **Velocity Trend**: {'Increasing' if current_points > avg_historical else 'Decreasing'}"
            ]

            return "\n".join(analysis)

        except Exception as e:
            self._std_logger.error(f"Error generating velocity analysis: {e}")
            return "### Velocity Analysis\n- Error generating analysis"

    def _generate_task_distribution_analysis(self, task_data: Dict[str, Any]) -> str:
        """
        Generate task distribution analysis.

        Args:
            task_data: Dictionary of task distribution data.

        Returns:
            Formatted string of task distribution analysis.
        """
        try:
            if not task_data:
                return "### Task Distribution Analysis\n- No task distribution data available"

            analysis = ["### Task Distribution Analysis\n"]
            for list_name, count in task_data.items():
                analysis.append(f"- **{list_name}**: {count} cards")

            return "\n".join(analysis)

        except Exception as e:
            self._std_logger.error(f"Error generating task distribution analysis: {e}")
            return "### Task Distribution Analysis\n- Error generating analysis"

    def _generate_management_action_items(self, analysis_data: Dict[str, Any]) -> str:
        """
        Generate management action items.

        Args:
            analysis_data: Dictionary of analysis data.

        Returns:
            Formatted string of management action items.
        """
        try:
            risks = analysis_data.get("risks", [])
            if not risks:
                return "- No management action items identified"

            action_items = []
            for risk in risks:
                action_items.append(f"- **{risk.get('title', 'Action Item')}**")
                action_items.append(f"  - {risk.get('description', 'No description available')}")
                if risk.get('priority'):
                    action_items.append(f"  - Priority: {risk.get('priority')}")

            return "\n".join(action_items)

        except Exception as e:
            self._std_logger.error(f"Error generating management action items: {e}")
            return "- Error generating management action items"

    def _generate_upcoming_focus(self, analysis_data: Dict[str, Any]) -> str:
        """
        Generate upcoming focus areas.

        Args:
            analysis_data: Dictionary of analysis data.

        Returns:
            Formatted string of upcoming focus areas.
        """
        try:
            recommendations = analysis_data.get("recommendations", [])
            improvements = analysis_data.get("improvements", [])
            risks = analysis_data.get("risks", [])

            focus_areas = []
            if recommendations:
                focus_areas.append("**Recommendations**")
                focus_areas.extend(f"- {rec.get('title', '')}" for rec in recommendations[:3])
            
            if improvements:
                focus_areas.append("\n**Areas for Improvement**")
                focus_areas.extend(f"- {improvement}" for improvement in improvements[:3])
            
            if risks:
                focus_areas.append("\n**Risk Mitigation**")
                focus_areas.extend(f"- {risk.get('title', '')}" for risk in risks[:3])

            return "\n".join(focus_areas) if focus_areas else "- No specific focus areas identified"

        except Exception as e:
            self._std_logger.error(f"Error generating upcoming focus: {e}")
            return "- Error generating upcoming focus" 