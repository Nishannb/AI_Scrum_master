"""
Report Generator Module

This module defines the ReportGenerator class, which is responsible for
generating sprint reports with metrics and visualizations.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
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
                analysis_data.get("velocity", {})
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

    def generate_velocity_chart(
        self,
        velocity_data: Dict[str, Any],
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate a velocity chart.

        Args:
            velocity_data: Dictionary containing velocity data.
            output_file: Optional output file path for the chart.

        Returns:
            Path to the generated chart.
        """
        try:
            if not output_file:
                output_file = os.path.join(self.output_dir, "velocity_chart.png")

            plt.figure(figsize=(12, 7))
            
            # Set style and use a better color palette
            plt.style.use('default')
            completed_color = '#2ecc71'  # Green
            remaining_color = '#e74c3c'  # Red
            avg_line_color = '#3498db'   # Blue
            
            # Prepare data
            sprints = []
            completed_points = []
            remaining_points = []
            
            # Add historical data
            historical = velocity_data.get("historical", [])
            for sprint in historical:
                # Use sprint number for labeling if available
                sprint_label = f"Sprint {sprint.get('sprint_number', sprint.get('sprint', 'N/A'))}"
                sprints.append(sprint_label)
                completed_points.append(sprint.get("completed_points", 0))
                remaining_points.append(sprint.get("remaining_points", 0))
            
            # Add current sprint
            current_sprint = velocity_data.get("current_sprint", {})
            if current_sprint:
                sprints.append("Current")
                completed_points.append(current_sprint.get("completed_points", 0))
                remaining_points.append(current_sprint.get("remaining_points", 0))
            
            # Create stacked bar chart
            x = range(len(sprints))
            width = 0.8
            
            # Create bar chart with distinct colors
            plt.bar(x, completed_points, width, label='Completed Points', color=completed_color)
            plt.bar(x, remaining_points, width, bottom=completed_points, 
                   label='Remaining Points', color=remaining_color, alpha=0.7)
            
            # Add value labels on bars
            for i in range(len(sprints)):
                # Label for completed points (only if there are points)
                if completed_points[i] > 0:
                    plt.text(i, completed_points[i]/2, str(completed_points[i]),
                            ha='center', va='center', color='white', fontweight='bold', fontsize=11)
                
                # Label for remaining points (only if there are points)
                if remaining_points[i] > 0:
                    plt.text(i, completed_points[i] + remaining_points[i]/2,
                            str(remaining_points[i]), ha='center', va='center',
                            color='white', fontweight='bold', fontsize=11)
            
            # Add styling with larger fonts
            plt.grid(True, linestyle='--', alpha=0.5, color='gray', axis='y')
            plt.title("Sprint Velocity Chart", pad=20, fontsize=16, fontweight='bold')
            plt.xlabel("Sprint", fontsize=14, labelpad=10)
            plt.ylabel("Story Points", fontsize=14, labelpad=10)
            
            # Customize x-axis with better rotation and larger font
            plt.xticks(x, sprints, rotation=30, ha='right', fontsize=12)
            plt.yticks(fontsize=12)
            
            # Add legend with custom styling and larger font
            legend = plt.legend(loc='upper right', frameon=True, fancybox=True, shadow=True, fontsize=12)
            legend.get_frame().set_alpha(0.9)
            
            # Add average velocity line
            if historical:
                avg_velocity = sum(h.get("completed_points", 0) for h in historical) / len(historical)
                plt.axhline(y=avg_velocity, color=avg_line_color, linestyle='--', alpha=0.7,
                           label=f'Avg Velocity: {avg_velocity:.1f}')
                
                # Update legend
                handles, labels = plt.gca().get_legend_handles_labels()
                plt.legend(handles, labels, loc='upper right', frameon=True,
                         fancybox=True, shadow=True, fontsize=12)
                
                # Add emoji based on performance comparison
                if current_sprint:
                    current_points = current_sprint.get("completed_points", 0)
                    # Determine if current performance is better than average
                    is_better = current_points > avg_velocity
                    emoji = "🎉" if is_better else "😟"
                    emoji_x = len(sprints) - 0.5  # Position to the right of the last bar
                    emoji_y = max(max(completed_points), avg_velocity) * 1.1  # Position above the highest bar
                    
                    # Add the emoji with a performance message
                    performance_text = "Better than average! Keep it up!" if is_better else "Below average. Let's improve!"
                    plt.annotate(f"{emoji} {performance_text}", 
                                xy=(len(sprints) - 1, current_points), 
                                xytext=(emoji_x, emoji_y),
                                textcoords='data',
                                ha='center', va='center',
                                fontsize=16,
                                bbox=dict(boxstyle="round,pad=0.5", fc="yellow", alpha=0.7),
                                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2"))
            
            # Set background color and style
            ax = plt.gca()
            ax.set_facecolor('#f8f9fa')
            plt.gcf().set_facecolor('#ffffff')
            
            # Add padding and save
            plt.margins(x=0.05)
            plt.tight_layout()
            plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()

            self._std_logger.info(f"Generated velocity chart at {output_file}")
            return output_file

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
        Prepare the content for the sprint report.

        Args:
            sprint_data: Data collected from the sprint.
            analysis_data: Analysis results.
            burn_down_chart: Path to the burndown chart.
            velocity_chart: Path to the velocity chart.
            task_distribution_chart: Path to the task distribution chart.
            gantt_chart: Path to the Gantt chart.

        Returns:
            The formatted report content.
        """
        try:
            # Get current date
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            # Count completed and remaining tasks
            cards = sprint_data.get('cards', [])
            total_tasks = len(cards)
            completed_tasks = sum(1 for card in cards if card.get('dueComplete', False))
            remaining_tasks = total_tasks - completed_tasks
            
            # Calculate completion rate
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            # Get board name if available
            board_name = sprint_data.get('board', {}).get('name', 'Sprint')
            
            # Create a mapping of members' IDs to their names or usernames
            member_map = {}
            for member in sprint_data.get('members', []):
                member_id = member.get('id')
                member_name = member.get('fullName') or member.get('username') or 'Unknown'
                if member_id:
                    member_map[member_id] = member_name
            
            # Create a mapping of list IDs to names
            list_map = {lst['id']: lst['name'] for lst in sprint_data.get('lists', [])}
            
            # Start building the report content
            content = [
                f"# {board_name} Report - {current_date}\n",
                "## Executive Summary\n",
                f"- **Completion Rate**: {completion_rate:.1f}%",
                f"- **Total Tasks**: {total_tasks}",
                f"- **Completed Tasks**: {completed_tasks}",
                f"- **Remaining Tasks**: {remaining_tasks}\n",
            ]
            
            # Add sprint status summary
            burn_down = analysis_data.get('burn_down', {})
            content.extend([
                "### Sprint Status Summary\n",
                f"The team has completed **{completed_tasks}** out of **{total_tasks}** tasks, achieving a **{completion_rate:.1f}%** completion rate. "
            ])
            
            # Add trend analysis based on the numbers
            if completion_rate < 30:
                content.append(f"The sprint is **significantly behind schedule** and immediate action is required to address blockers and prioritize critical tasks.")
            elif completion_rate < 60:
                content.append(f"The sprint is **somewhat behind schedule**. The team should focus on completing high-priority items and addressing any existing blockers.")
            else:
                content.append(f"The sprint is **progressing well**. The team should continue their momentum while addressing any remaining blockers.")
            
            # Add recently completed tasks for personalization
            completed_cards = [card for card in cards if card.get('dueComplete', False)]
            if completed_cards:
                content.append("\n**Recently Completed Tasks:**")
                for card in completed_cards[:3]:  # Show top 3 completed
                    card_name = card.get('name', 'Unnamed')
                    list_name = list_map.get(card.get('idList', ''), 'Unknown')
                    members = [member_map.get(m_id, 'Unknown') for m_id in card.get('idMembers', [])]
                    members_str = ", ".join(members) if members else "No assignees"
                    content.append(f"- ✅ **{card_name}** in {list_name} (Completed by: {members_str})")
            
            content.append("\n")
                
            # Add Timeline/Gantt Chart Section
            content.extend([
                "## Sprint Timeline\n",
                "### Gantt Chart",
                f"![Gantt Chart]({os.path.basename(gantt_chart)})\n",
                "This chart shows the timeline of all tasks with due dates. Critical tasks (due within 2 days) are highlighted in red with counts by section.\n"
            ])
                
            # Sprint Metrics Section
            content.extend([
                "## Sprint Metrics\n",
                "### Burndown Chart",
                f"![Burndown Chart]({os.path.basename(burn_down_chart)})\n",
                "#### Burndown Analysis\n",
                f"The team has completed **{burn_down.get('completed_points', 0)}** story points with **{burn_down.get('remaining_points', 0)}** points remaining. "
            ])
            
            # Add burndown analysis
            completion_rate = burn_down.get('completion_rate', 0)
            if completion_rate < 30:
                content.append("At the current rate, the team will **not meet the sprint goal**. Immediate action is required to increase velocity.")
            elif completion_rate < 60:
                content.append("The team needs to **increase velocity** to meet the sprint goal.")
            else:
                content.append("The team is on track to **meet the sprint goal**.")
            
            content.append("\n")
            
            # Velocity Analysis
            content.extend([
                "### Velocity Analysis",
                f"![Velocity Chart]({os.path.basename(velocity_chart)})\n",
                "#### Velocity Insights\n",
            ])
            
            # Add velocity insights
            velocity_data = analysis_data.get('velocity', {})
            current_sprint = velocity_data.get('current_sprint', {})
            if current_sprint:
                content.append(f"The team's current velocity is **{current_sprint.get('completed_points', 0)} points** completed out of a commitment of **{current_sprint.get('total_points', 0)} points**. ")
                
                # Compare with historical data if available
                historical = velocity_data.get('historical', [])
                if historical:
                    avg_historical = sum(h.get('completed_points', 0) for h in historical) / len(historical)
                    if current_sprint.get('completed_points', 0) > avg_historical:
                        content.append(f"This represents an **improvement** over the team's average velocity of **{avg_historical:.1f} points** in previous sprints.")
                    elif current_sprint.get('completed_points', 0) < avg_historical:
                        content.append(f"This is **below** the team's average velocity of **{avg_historical:.1f} points** in previous sprints.")
                    else:
                        content.append(f"This is **consistent** with the team's average velocity of **{avg_historical:.1f} points** in previous sprints.")
            
            content.append("\n")
            
            # Task Distribution
            content.extend([
                "### Task Distribution",
                f"![Task Distribution]({os.path.basename(task_distribution_chart)})\n",
                "#### Distribution Analysis\n",
            ])
            
            # Add task distribution insights with specific task mentions
            task_distribution = analysis_data.get('task_distribution', {})
            if task_distribution:
                most_tasks_list = max(task_distribution.items(), key=lambda x: x[1], default=("None", 0))
                content.append(f"The **{most_tasks_list[0]}** list contains the highest number of tasks (**{most_tasks_list[1]}**), which may indicate a bottleneck in the workflow.")
                
                # Add specific tasks in the bottleneck list
                bottleneck_cards = []
                for card in cards:
                    list_name = list_map.get(card.get('idList', ''), 'Unknown')
                    if list_name == most_tasks_list[0]:
                        bottleneck_cards.append(card)
                
                if bottleneck_cards:
                    content.append("\n**Key tasks in this bottleneck:**")
                    for card in bottleneck_cards[:3]:  # Top 3 from the bottleneck
                        card_name = card.get('name', 'Unnamed')
                        members = [member_map.get(m_id, 'Unknown') for m_id in card.get('idMembers', [])]
                        members_str = f" (Assigned to: {', '.join(members)})" if members else " (Unassigned)"
                        due_date = ""
                        if card.get('due'):
                            try:
                                due_date = f", due on {datetime.fromisoformat(card['due'].replace('Z', '+00:00')).strftime('%Y-%m-%d')}"
                            except (ValueError, KeyError):
                                pass
                        content.append(f"- **{card_name}**{members_str}{due_date}")
            
            content.append("\n")
            
            # Risk Analysis Section
            risks = analysis_data.get('risks', [])
            blockers = analysis_data.get('blockers', [])
            
            # Find overdue and approaching deadline cards
            now = datetime.now().replace(tzinfo=None)  # Create timezone-naive now for comparisons
            overdue_cards = []
            approaching_deadline_cards = []
            
            for card in cards:
                if 'due' in card and card['due'] and not card.get('dueComplete', False):
                    try:
                        # Convert to timezone-naive datetime for consistent comparisons
                        due_date = datetime.fromisoformat(card['due'].replace('Z', '+00:00'))
                        due_date = due_date.replace(tzinfo=None)
                        
                        if due_date < now:
                            overdue_cards.append(card)
                        elif (due_date - now).days <= 2:
                            approaching_deadline_cards.append(card)
                    except (ValueError, KeyError):
                        pass
            
            if risks or blockers or overdue_cards or approaching_deadline_cards:
                content.extend([
                    "## Risk Analysis\n",
                    "### Current Risks\n"
                ])
                
                if not risks:
                    content.append("- No significant risks identified in this sprint.\n")
                else:
                    for risk in risks:
                        # Enhanced risk description with impact
                        content.append(f"- **{risk.get('category', 'Unknown').replace('_', ' ').title()}** ({risk.get('severity', 'medium')}): {risk.get('description', '')}")
                        content.append(f"  - **Impact**: {risk.get('impact', 'Unknown impact')}")
                        
                        # Link risks to specific tasks or situations when possible
                        if risk.get('category') == 'completion_rate':
                            content.append(f"  - **Tasks affecting completion rate**: {', '.join([c.get('name', 'Unnamed') for c in overdue_cards + approaching_deadline_cards][:3])}")
                        elif risk.get('category') == 'approaching_deadlines' and approaching_deadline_cards:
                            content.append(f"  - **Critical deadlines**: {', '.join([c.get('name', 'Unnamed') for c in approaching_deadline_cards][:3])}")
                        elif risk.get('category') == 'overdue' and overdue_cards:
                            content.append(f"  - **Overdue tasks**: {', '.join([c.get('name', 'Unnamed') for c in overdue_cards][:3])}")
                    
                    content.append("")
                
                # Add specific section for overdue tasks
                if overdue_cards:
                    content.extend([
                        "### Overdue Tasks\n"
                    ])
                    for card in overdue_cards:
                        card_name = card.get('name', 'Unnamed')
                        due_date = datetime.fromisoformat(card['due'].replace('Z', '+00:00')).replace(tzinfo=None)
                        days_overdue = (now - due_date).days
                        list_name = list_map.get(card.get('idList', ''), 'Unknown')
                        members = [member_map.get(m_id, 'Unknown') for m_id in card.get('idMembers', [])]
                        members_str = f" (Assigned to: {', '.join(members)})" if members else " (Unassigned)"
                        
                        content.append(f"- ⚠️ **{card_name}** - **{days_overdue} days overdue**{members_str}")
                        content.append(f"  - Current status: {list_name}")
                        content.append(f"  - Due date: {due_date.strftime('%Y-%m-%d')}")
                        if card.get('desc'):
                            desc = card['desc'][:100] + '...' if len(card['desc']) > 100 else card['desc']
                            content.append(f"  - Description: {desc}")
                    content.append("")
                
                # Add specific section for approaching deadline tasks
                if approaching_deadline_cards:
                    content.extend([
                        "### Approaching Deadlines\n"
                    ])
                    for card in approaching_deadline_cards:
                        card_name = card.get('name', 'Unnamed')
                        due_date = datetime.fromisoformat(card['due'].replace('Z', '+00:00')).replace(tzinfo=None)
                        days_until_due = (due_date - now).days
                        hours_until_due = int((due_date - now).total_seconds() / 3600) % 24
                        list_name = list_map.get(card.get('idList', ''), 'Unknown')
                        members = [member_map.get(m_id, 'Unknown') for m_id in card.get('idMembers', [])]
                        members_str = f" (Assigned to: {', '.join(members)})" if members else " (Unassigned)"
                        
                        time_str = f"{days_until_due} days" if days_until_due > 0 else f"{hours_until_due} hours"
                        content.append(f"- ⏰ **{card_name}** - **Due in {time_str}**{members_str}")
                        content.append(f"  - Current status: {list_name}")
                        content.append(f"  - Due date: {due_date.strftime('%Y-%m-%d %H:%M')}")
                        if card.get('desc'):
                            desc = card['desc'][:100] + '...' if len(card['desc']) > 100 else card['desc']
                            content.append(f"  - Description: {desc}")
                    content.append("")
                
                # Add specific section for blockers with detailed information
                if blockers:
                    content.extend([
                        "### Active Blockers\n"
                    ])
                    for blocker in blockers:
                        blocker_title = blocker.get('title', 'Unknown Task')
                        blocker_list = blocker.get('list', 'Unknown List')
                        
                        # Find the actual card for this blocker to get more details
                        blocker_card = None
                        for card in cards:
                            if card.get('name') == blocker_title:
                                blocker_card = card
                                break
                        
                        content.append(f"- 🚫 **{blocker_title}** in {blocker_list}")
                        
                        if blocker_card:
                            # Add members assigned to the blocker
                            members = [member_map.get(m_id, 'Unknown') for m_id in blocker_card.get('idMembers', [])]
                            if members:
                                content.append(f"  - **Assigned to**: {', '.join(members)}")
                            
                            # Add due date if available
                            if blocker_card.get('due'):
                                try:
                                    due_date = datetime.fromisoformat(blocker_card['due'].replace('Z', '+00:00'))
                                    content.append(f"  - **Due date**: {due_date.strftime('%Y-%m-%d')}")
                                    
                                    # Check if it's overdue
                                    if due_date.replace(tzinfo=None) < now:
                                        days_overdue = (now - due_date.replace(tzinfo=None)).days
                                        content.append(f"  - **Status**: {days_overdue} days overdue")
                                except (ValueError, KeyError):
                                    pass
                            
                            # Add description if available
                            if blocker_card.get('desc'):
                                desc = blocker_card['desc'][:100] + '...' if len(blocker_card['desc']) > 100 else blocker_card['desc']
                                content.append(f"  - **Description**: {desc}")
                        
                        # Add specific blocker information
                        if 'owner' in blocker:
                            content.append(f"  - **Owner**: {blocker.get('owner', 'Unassigned')}")
                        if 'blocked_since' in blocker:
                            content.append(f"  - **Blocked since**: {blocker.get('blocked_since', 'Unknown')}")
                        if 'impact' in blocker:
                            content.append(f"  - **Impact**: {blocker.get('impact', 'Unknown impact')}")
                        if 'resolution_plan' in blocker:
                            content.append(f"  - **Resolution plan**: {blocker.get('resolution_plan', 'No plan specified')}")
                        
                        # Add dependent tasks if any
                        if 'blocking_tasks' in blocker and blocker['blocking_tasks']:
                            content.append(f"  - **Blocking**: {', '.join(blocker['blocking_tasks'])}")
                    
                    content.append("\n**Action Required**: Blockers should be addressed immediately in the daily stand-up meetings and escalated if necessary. The team should prioritize resolving these blockers before taking on new work.\n")
            
            # Add Goals for the Team section
            content.extend([
                "## 🎯 Goals Until Next Sprint Meeting\n",
                "Based on the analysis above, the team should focus on the following specific action items before the next sprint meeting:\n"
            ])
            
            # Calculate action items based on the analysis data
            goals = []
            goal_count = 1
            
            # Priority 1: Resolve overdue tasks
            if overdue_cards:
                overdue_task_names = [card.get('name', 'Unnamed')[:50] + '...' if len(card.get('name', 'Unnamed')) > 50 else card.get('name', 'Unnamed') for card in overdue_cards[:2]]
                overdue_members = set()
                for card in overdue_cards[:2]:
                    for m_id in card.get('idMembers', []):
                        if m_id in member_map:
                            overdue_members.add(member_map[m_id])
                
                owners = f" ({', '.join(overdue_members)})" if overdue_members else ""
                goal = f"{goal_count}. **URGENT: Complete overdue tasks**{owners}\n   - Focus on: {', '.join(overdue_task_names)}"
                goals.append(goal)
                goal_count += 1
            
            # Priority 2: Address approaching deadlines
            if approaching_deadline_cards:
                approaching_task_names = [card.get('name', 'Unnamed')[:50] + '...' if len(card.get('name', 'Unnamed')) > 50 else card.get('name', 'Unnamed') for card in approaching_deadline_cards[:2]]
                approaching_members = set()
                for card in approaching_deadline_cards[:2]:
                    for m_id in card.get('idMembers', []):
                        if m_id in member_map:
                            approaching_members.add(member_map[m_id])
                
                owners = f" ({', '.join(approaching_members)})" if approaching_members else ""
                goal = f"{goal_count}. **HIGH PRIORITY: Address approaching deadlines**{owners}\n   - Focus on: {', '.join(approaching_task_names)}"
                goals.append(goal)
                goal_count += 1
            
            # Priority 3: Resolve blockers
            if blockers:
                blocker_titles = [blocker.get('title', 'Unknown')[:50] + '...' if len(blocker.get('title', 'Unknown')) > 50 else blocker.get('title', 'Unknown') for blocker in blockers[:2]]
                blocker_owners = set()
                for blocker in blockers[:2]:
                    if 'owner' in blocker:
                        blocker_owners.add(blocker.get('owner'))
                
                owners = f" ({', '.join(blocker_owners)})" if blocker_owners else ""
                goal = f"{goal_count}. **PRIORITY: Resolve blockers**{owners}\n   - Focus on: {', '.join(blocker_titles)}"
                goals.append(goal)
                goal_count += 1
            
            # Priority 4: Address bottlenecks
            if task_distribution and bottleneck_cards:
                bottleneck_task_names = [card.get('name', 'Unnamed')[:50] + '...' if len(card.get('name', 'Unnamed')) > 50 else card.get('name', 'Unnamed') for card in bottleneck_cards[:2]]
                bottleneck_list = most_tasks_list[0]
                goal = f"{goal_count}. **Clear bottleneck in {bottleneck_list}**\n   - Focus on: {', '.join(bottleneck_task_names)}"
                goals.append(goal)
                goal_count += 1
            
            # Priority 5: Daily progress tracking
            goal = f"{goal_count}. **Track daily progress**\n   - Hold daily stand-ups to review progress on critical tasks\n   - Update Trello board with current status and blockers\n   - Escalate any new blockers immediately"
            goals.append(goal)
            goal_count += 1
            
            # Priority 6: Preparation for next sprint
            if completion_rate < 50:
                goal = f"{goal_count}. **Prepare for potential scope adjustment**\n   - Identify tasks that may need to be moved to next sprint\n   - Prioritize remaining work for current sprint completion"
                goals.append(goal)
                goal_count += 1
            
            # Add all goals to content
            content.extend(goals)
            
            # Add a clear call to action
            content.append("\n### Immediate Actions Required")
            content.append("1. **Today**: Review this report in team meeting and assign owners to each goal")
            content.append("2. **Tomorrow**: Report progress on highest priority items in stand-up")
            content.append("3. **This Week**: Complete all overdue tasks and address approaching deadlines")
            content.append("4. **Before Next Sprint**: Prepare sprint retrospective with lessons learned")
            
            # Add footer
            content.extend([
                "\n---\n",
                f"*Report generated on {current_date}*"
            ])
            
            return "\n".join(content)
            
        except Exception as e:
            self._std_logger.error(f"Error preparing report content: {e}")
            return f"# Error Generating Full Report\n\nAn error occurred while preparing the report content: {e}\n\n## Available Charts\n\n![Burndown Chart]({os.path.basename(burn_down_chart)})\n\n![Velocity Chart]({os.path.basename(velocity_chart)})\n\n![Task Distribution]({os.path.basename(task_distribution_chart)})\n\n![Gantt Chart]({os.path.basename(gantt_chart)})"

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