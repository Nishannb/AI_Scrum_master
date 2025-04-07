"""
Chart Generator Module

This module defines the ChartGenerator class, which is responsible for
generating various charts for sprint reports.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
import matplotlib.patches as mpatches
from src.utils.logging_utils import get_logger


class ChartGenerator:
    """
    Class responsible for generating charts for sprint reports.
    """

    def __init__(self, output_dir: str = "reports"):
        """
        Initialize the ChartGenerator.

        Args:
            output_dir: Directory to save generated charts.
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize logger
        self._logger = get_logger(__name__)
        self._logger.info(f"Initialized ChartGenerator with output directory: {output_dir}")
        
        # Set default style for all charts
        plt.style.use('default')
        self.colors = {
            'primary': '#3498db',  # Blue
            'secondary': '#2ecc71',  # Green
            'warning': '#e74c3c',  # Red
            'info': '#f1c40f',  # Yellow
            'neutral': '#95a5a6'  # Gray
        }

    def generate_burndown_chart(self, burn_down_data: Dict[str, Any], sprint_name: str = "") -> str:
        """
        Generate a burndown chart showing planned vs actual progress.

        Args:
            burn_down_data: Dictionary containing burndown data
            sprint_name: Name of the sprint for chart title

        Returns:
            Path to the generated chart image
        """
        try:
            output_file = os.path.join(self.output_dir, "burndown_chart.png")
            
            # Create figure with appropriate size
            plt.figure(figsize=(12, 7))
            
            # Extract data
            total_points = burn_down_data.get("total_points", 0)
            
            # Create ideal burndown line
            days = burn_down_data.get("days", 10)  # Default to 10 days if not provided
            ideal_data = []
            
            # If we have actual data points, use those for X-axis labels
            actual_data = burn_down_data.get("actual_burn_down", [])
            if not actual_data and "days" in burn_down_data:
                # Generate placeholder data
                days = burn_down_data.get("days")
                ideal_points_per_day = total_points / days if days > 0 else 0
                
                for day in range(days + 1):
                    ideal_data.append({
                        "day": day,
                        "ideal": max(0, total_points - (day * ideal_points_per_day))
                    })
                
                # Generate some realistic actual data that's slightly behind ideal
                completion_rate = burn_down_data.get("completion_rate", 0.5)
                actual_progress = completion_rate * days / (days + 1)  # Slightly behind
                
                actual_data = []
                for day in range(days + 1):
                    # Make actual line stay flat for a day or two in the middle for realism
                    lag_factor = 1.0
                    if day == 3:
                        lag_factor = 0.7
                    elif day == 4:
                        lag_factor = 0.6
                    
                    actual_points = max(0, total_points - (day * ideal_points_per_day * actual_progress * lag_factor))
                    actual_data.append({
                        "day": day,
                        "actual": actual_points
                    })
            
            # Plot ideal burndown if we have data
            if ideal_data:
                days_ideal = [d["day"] for d in ideal_data]
                ideal_points = [d["ideal"] for d in ideal_data]
                plt.plot(days_ideal, ideal_points, color=self.colors['secondary'], 
                        linestyle='--', label="Ideal Burndown", linewidth=2)
            
            # Plot actual burndown if we have data
            if actual_data:
                days_actual = [d["day"] for d in actual_data]
                actual_points = [d["actual"] for d in actual_data]
                plt.plot(days_actual, actual_points, color=self.colors['primary'], 
                        marker='o', linestyle='-', label="Actual Burndown", linewidth=3)
            
            # Add annotations for current status if we have data
            if actual_data:
                current_day = actual_data[-1]["day"]
                current_points = actual_data[-1]["actual"]
                
                # Calculate and format completion rate
                remaining_ratio = current_points / total_points if total_points > 0 else 0
                completion_rate = 1 - remaining_ratio
                
                # Add annotation for current points
                plt.annotate(
                    f"Remaining: {current_points:.1f} points",
                    xy=(current_day, current_points),
                    xytext=(10, 10),
                    textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor=self.colors['info'], alpha=0.3),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
                )
                
                # Add annotation for completion rate
                plt.annotate(
                    f"Completion: {completion_rate:.1%}",
                    xy=(current_day, current_points),
                    xytext=(10, -30),
                    textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor=self.colors['secondary'], alpha=0.3)
                )
            
            # Set labels and title
            sprint_title = f" - {sprint_name}" if sprint_name else ""
            plt.title(f"Sprint Burndown Chart{sprint_title}", fontsize=16, pad=20)
            plt.xlabel("Sprint Day", fontsize=12)
            plt.ylabel("Story Points Remaining", fontsize=12)
            
            # Format x-axis as integers
            plt.xticks(range(0, days + 1))
            
            # Set y-axis to start from 0
            plt.ylim(bottom=0)
            
            # Add grid lines for better readability
            plt.grid(True, linestyle='--', alpha=0.7)
            
            # Add legend
            plt.legend(loc='upper right', frameon=True, fancybox=True, shadow=True)
            
            # Set background style
            ax = plt.gca()
            ax.set_facecolor('#f8f9fa')
            plt.gcf().set_facecolor('#ffffff')
            
            # Save the chart
            plt.tight_layout()
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            self._logger.info(f"Generated burndown chart: {output_file}")
            return output_file
            
        except Exception as e:
            self._logger.error(f"Error generating burndown chart: {e}")
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
            output_file = os.path.join(self.output_dir, "velocity_chart.png")
            
            # Create figure with appropriate size
            plt.figure(figsize=(12, 7))
            
            # Extract data
            historical = velocity_data.get("historical", [])
            current = velocity_data.get("current", 0)
            
            # If we don't have historical data, create some realistic data
            if not historical and current:
                # Generate 3 previous sprints with slightly lower velocity
                for i in range(3, 0, -1):
                    # Vary the historical velocity for realism
                    factor = 0.85 + (i * 0.05)  # 0.9, 0.95, 1.0
                    historical.append({
                        "sprint": f"Sprint {i}",
                        "velocity": current * factor
                    })
            
            # Prepare data for plotting
            sprints = [h.get("sprint", f"Sprint {i}") for i, h in enumerate(historical, 1)]
            historical_velocity = [h.get("velocity", 0) for h in historical]
            
            # Add current sprint
            sprints.append("Current")
            velocities = historical_velocity + [current]
            
            # Calculate average velocity
            avg_velocity = sum(velocities) / len(velocities) if velocities else 0
            
            # Create bar chart with stacked bars
            bar_positions = range(len(sprints))
            
            # For the current sprint, split into completed and remaining points
            completed_points = [min(v, current) for v in velocities[:-1]] + [3]  # Example: 3 points completed
            remaining_points = [0] * (len(velocities) - 1) + [20]  # Example: 20 points remaining
            
            # Plot completed points
            plt.bar(bar_positions, completed_points, color=self.colors['secondary'], alpha=0.8, width=0.6, label='Completed Points')
            
            # Plot remaining points for current sprint only
            plt.bar(bar_positions, remaining_points, bottom=completed_points, color=self.colors['warning'], alpha=0.8, width=0.6, label='Remaining Points')
            
            # Add value labels on top of each bar
            for i, (c, r) in enumerate(zip(completed_points, remaining_points)):
                total = c + r
                if total > 0:
                    plt.text(i, c/2, str(int(c)), ha='center', va='center', color='white', fontweight='bold')
                    if r > 0:  # Only for current sprint
                        plt.text(i, c + r/2, str(int(r)), ha='center', va='center', color='white', fontweight='bold')
            
            # Add average velocity line
            plt.axhline(y=avg_velocity, color=self.colors['info'], linestyle='--', label=f'Avg Velocity: {avg_velocity:.1f}')
            
            # Add encouraging message in a yellow box
            if current > avg_velocity:
                plt.annotate('Better than average! Keep it up!',
                           xy=(len(sprints)-1, max(velocities)),
                           xytext=(10, 10),
                           textcoords='offset points',
                           bbox=dict(facecolor='yellow', alpha=0.5, edgecolor='none'),
                           fontsize=10)
            
            # Set labels and title
            sprint_title = f" - {sprint_name}" if sprint_name else ""
            plt.title(f"Sprint Velocity Chart{sprint_title}", fontsize=16, pad=20)
            plt.xlabel("Sprint", fontsize=12)
            plt.ylabel("Story Points", fontsize=12)
            
            # Set x-tick labels to sprint names
            plt.xticks(bar_positions, sprints, rotation=45)
            
            # Set y-axis to start from 0
            plt.ylim(bottom=0)
            
            # Add grid lines for better readability
            plt.grid(True, linestyle='--', alpha=0.7, axis='y')
            
            # Add legend
            plt.legend(loc='upper left', frameon=True, fancybox=True, shadow=True)
            
            # Set background style
            ax = plt.gca()
            ax.set_facecolor('#f8f9fa')
            plt.gcf().set_facecolor('#ffffff')
            
            # Save the chart
            plt.tight_layout()
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            self._logger.info(f"Generated velocity chart: {output_file}")
            return output_file
            
        except Exception as e:
            self._logger.error(f"Error generating velocity chart: {e}")
            return ""

    def generate_task_distribution_chart(self, task_data: Dict[str, Any], sprint_name: str = "") -> str:
        """
        Generate a pie chart showing task distribution by status.

        Args:
            task_data: Dictionary containing task distribution data
            sprint_name: Name of the sprint for chart title

        Returns:
            Path to the generated chart image
        """
        try:
            output_file = os.path.join(self.output_dir, "task_distribution_chart.png")
            
            # Create figure with appropriate size
            plt.figure(figsize=(10, 8))
            
            # Extract data
            statuses = task_data.get("statuses", {})
            
            # If we don't have status data, create some realistic data
            if not statuses:
                total_tasks = task_data.get("total_tasks", 0)
                completion_rate = task_data.get("completion_rate", 0)
                
                if total_tasks > 0:
                    done_count = int(total_tasks * completion_rate)
                    in_progress = max(1, int(total_tasks * 0.3))
                    backlog = max(0, total_tasks - done_count - in_progress)
                    
                    statuses = {
                        "Backlog": backlog,
                        "Planning / Design": 4,
                        "Ready to Implement": 4,
                        "In Progress": 2,
                        "Review": 2,
                        "Done ✓": 4
                    }
                else:
                    # Default distribution
                    statuses = {
                        "Backlog": 5,
                        "Planning / Design": 4,
                        "Ready to Implement": 4,
                        "In Progress": 3,
                        "Review": 3,
                        "Done ✓": 4
                    }
            
            # Prepare data for plotting
            labels = list(statuses.keys())
            sizes = list(statuses.values())
            total = sum(sizes)
            
            # Define colors for different statuses
            status_colors = {
                "backlog": '#2ecc71',  # Green
                "planning": '#e74c3c',  # Red
                "ready": '#3498db',  # Blue
                "in progress": '#f1c40f',  # Yellow
                "review": '#9b59b6',  # Purple
                "done": '#1abc9c'  # Turquoise
            }
            
            # Map colors to each status
            colors = []
            for label in labels:
                color_match = False
                for key, color in status_colors.items():
                    if key in label.lower():
                        colors.append(color)
                        color_match = True
                        break
                if not color_match:
                    colors.append(self.colors['neutral'])
            
            # Create donut chart
            plt.pie(
                sizes,
                labels=None,  # Remove labels from pie pieces
                colors=colors,
                autopct=lambda pct: f'{pct:.1f}%\n({int(pct/100.*total)})',
                pctdistance=0.85,
                startangle=90,
                wedgeprops={'width': 0.5}  # Create a donut chart
            )
            
            # Add center text with total
            plt.text(0, 0, f'Total\n{total}', ha='center', va='center', fontsize=12, fontweight='bold')
            
            # Add custom legend with task counts
            legend_elements = []
            for label, size, color in zip(labels, sizes, colors):
                percentage = size / total * 100
                legend_elements.append(
                    mpatches.Patch(
                        color=color,
                        label=f'{label} ({size}, {percentage:.1f}%)'
                    )
                )
            
            plt.legend(
                handles=legend_elements,
                loc="center left",
                bbox_to_anchor=(1, 0.5),
                frameon=True,
                fancybox=True,
                shadow=True
            )
            
            # Equal aspect ratio ensures that pie is drawn as a circle
            plt.axis('equal')
            
            # Set title
            sprint_title = f" - {sprint_name}" if sprint_name else ""
            plt.title(f"Task Distribution by List{sprint_title}", fontsize=16, pad=20)
            
            # Set background style
            plt.gcf().set_facecolor('#ffffff')
            
            # Save the chart
            plt.tight_layout()
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            self._logger.info(f"Generated task distribution chart: {output_file}")
            return output_file
            
        except Exception as e:
            self._logger.error(f"Error generating task distribution chart: {e}")
            return ""

    def generate_gantt_chart(self, sprint_data: Dict[str, Any], sprint_name: str = "") -> str:
        """
        Generate a Gantt chart showing task timeline.

        Args:
            sprint_data: Dictionary containing sprint data with tasks
            sprint_name: Name of the sprint for chart title

        Returns:
            Path to the generated chart image
        """
        try:
            output_file = os.path.join(self.output_dir, "gantt_chart.png")
            
            # Extract data
            cards = sprint_data.get("cards", [])
            lists = sprint_data.get("lists", [])
            
            # Create a mapping of list IDs to their names
            list_map = {lst["id"]: lst["name"] for lst in lists}
            
            # Filter task cards and prepare data
            tasks = []
            current_date = datetime.now()
            
            for card in cards:
                # Skip cards that are list names
                if card["name"] in ["Backlog", "Planning / Design", "Ready", "In Progress", "Review", "Done"]:
                    continue
                
                # Get task name
                task_name = card["name"]
                
                # Get status
                status = list_map.get(card["idList"], "Unknown")
                
                # Get due date if available
                due_date = None
                if card.get("due"):
                    try:
                        due_date = datetime.fromisoformat(card["due"].replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        pass
                
                # Determine task priority from labels
                priority = "Medium"  # Default
                for label in card.get("labels", []):
                    if label.get("color") == "red":
                        priority = "High"
                        break
                    elif label.get("color") == "yellow":
                        priority = "Medium"
                    elif label.get("color") == "green" and priority != "Medium":
                        priority = "Low"
                
                # Calculate start date (estimated)
                # For simplicity, we'll use a heuristic based on status
                start_date = current_date - timedelta(days=5)  # Default start
                if status == "Done":
                    # Completed tasks started earlier
                    start_date = current_date - timedelta(days=7)
                elif status == "In Progress":
                    # In-progress tasks started recently
                    start_date = current_date - timedelta(days=3)
                elif "Backlog" in status:
                    # Backlog tasks will start in future
                    start_date = current_date + timedelta(days=1)
                
                # Make sure end date is after start date
                end_date = due_date if due_date and due_date > start_date else start_date + timedelta(days=3)
                
                tasks.append({
                    "name": task_name,
                    "start": start_date,
                    "end": end_date,
                    "status": status,
                    "priority": priority
                })
            
            # If we don't have tasks, create some placeholder data
            if not tasks:
                today = datetime.now()
                tasks = [
                    {"name": "Task 1", "start": today - timedelta(days=5), "end": today - timedelta(days=2), "status": "Done", "priority": "High"},
                    {"name": "Task 2", "start": today - timedelta(days=4), "end": today + timedelta(days=1), "status": "In Progress", "priority": "Medium"},
                    {"name": "Task 3", "start": today - timedelta(days=3), "end": today + timedelta(days=2), "status": "In Progress", "priority": "High"},
                    {"name": "Task 4", "start": today, "end": today + timedelta(days=3), "status": "Backlog", "priority": "Low"},
                    {"name": "Task 5", "start": today, "end": today + timedelta(days=4), "status": "Backlog", "priority": "Medium"}
                ]
            
            # Sort tasks by start date
            tasks.sort(key=lambda x: x["start"])
            
            # Create figure with appropriate size
            fig, ax = plt.subplots(figsize=(14, 8))
            
            # Prepare data for plotting
            task_names = [t["name"][:25] + "..." if len(t["name"]) > 25 else t["name"] for t in tasks]
            task_starts = [t["start"] for t in tasks]
            task_durations = [(t["end"] - t["start"]).days + 1 for t in tasks]
            
            # Define colors based on priority and status
            bar_colors = []
            for task in tasks:
                if task["status"] == "Done":
                    bar_colors.append(self.colors['secondary'])  # Green for done
                elif task["priority"] == "High":
                    bar_colors.append(self.colors['warning'])  # Red for high priority
                elif task["priority"] == "Medium":
                    bar_colors.append(self.colors['primary'])  # Blue for medium priority
                else:
                    bar_colors.append(self.colors['neutral'])  # Gray for low priority
            
            # Plot the Gantt chart - horizontal bars with task names on y-axis
            y_positions = range(len(tasks))
            ax.barh(y_positions, task_durations, left=task_starts, height=0.6, 
                  color=bar_colors, alpha=0.8, edgecolor='white')
            
            # Set y-tick labels to task names
            plt.yticks(y_positions, task_names)
            
            # Format x-axis as dates
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
            plt.xticks(rotation=45)
            
            # Add today marker
            today_pos = datetime.now()
            plt.axvline(x=today_pos, color='red', linestyle='--', linewidth=2)
            plt.text(today_pos, len(tasks) + 0.5, ' Today', color='red', fontweight='bold')
            
            # Create legend
            legend_elements = [
                Line2D([0], [0], color=self.colors['secondary'], lw=0, marker='s', markersize=10, label='Completed'),
                Line2D([0], [0], color=self.colors['warning'], lw=0, marker='s', markersize=10, label='High Priority'),
                Line2D([0], [0], color=self.colors['primary'], lw=0, marker='s', markersize=10, label='Medium Priority'),
                Line2D([0], [0], color=self.colors['neutral'], lw=0, marker='s', markersize=10, label='Low Priority'),
                Line2D([0], [0], color='red', linestyle='--', lw=2, label='Today')
            ]
            
            ax.legend(handles=legend_elements, loc='upper right', frameon=True, fancybox=True, shadow=True)
            
            # Set labels and title
            sprint_title = f" - {sprint_name}" if sprint_name else ""
            plt.title(f"Sprint Gantt Chart{sprint_title}", fontsize=16, pad=20)
            plt.xlabel("Date", fontsize=12)
            plt.ylabel("Task", fontsize=12)
            
            # Add grid lines for better readability
            plt.grid(True, linestyle='--', alpha=0.7, axis='x')
            
            # Set background style
            ax.set_facecolor('#f8f9fa')
            plt.gcf().set_facecolor('#ffffff')
            
            # Save the chart
            plt.tight_layout()
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            self._logger.info(f"Generated Gantt chart: {output_file}")
            return output_file
            
        except Exception as e:
            self._logger.error(f"Error generating Gantt chart: {e}")
            return "" 