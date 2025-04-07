import sys
import os
import json
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.reporting_agent import ReportingAgent

# Create sample Trello data based on the pattern seen in logs
def create_sample_data():
    # Create current date for reference
    current_date = datetime.now()
    yesterday = current_date - timedelta(days=1)
    tomorrow = current_date + timedelta(days=1)
    
    # Create list data
    lists = [
        {"id": "list1", "name": "Backlog", "closed": False},
        {"id": "list2", "name": "Planning / Design", "closed": False},
        {"id": "list3", "name": "Ready to Implement", "closed": False},
        {"id": "list4", "name": "In Progress", "closed": False},
        {"id": "list5", "name": "Review", "closed": False},
        {"id": "list6", "name": "Done 🎉", "closed": False}
    ]
    
    # Create member data
    members = [
        {"id": "member1", "fullName": "Nishan Baral", "username": "nishanbaral"},
        {"id": "member2", "fullName": "adamsnb34", "username": "adamsnb34"},
        {"id": "member3", "fullName": "baralnishan987", "username": "baralnishan987"}
    ]
    
    # Create cards data - include both list title cards and task cards
    cards = [
        # List title cards
        {"id": "card1", "name": "Backlog", "desc": "", "idList": "list1", "due": None, 
         "dateLastActivity": yesterday.isoformat(), "labels": [], "members": [], "url": "https://trello.com/c/1"},
        {"id": "card2", "name": "Planning / Design", "desc": "", "idList": "list2", "due": None, 
         "dateLastActivity": yesterday.isoformat(), "labels": [], "members": [], "url": "https://trello.com/c/2"},
        {"id": "card3", "name": "Ready", "desc": "", "idList": "list3", "due": None, 
         "dateLastActivity": yesterday.isoformat(), "labels": [], "members": [], "url": "https://trello.com/c/3"},
        {"id": "card4", "name": "In Progress", "desc": "", "idList": "list4", "due": None, 
         "dateLastActivity": yesterday.isoformat(), "labels": [], "members": [], "url": "https://trello.com/c/4"},
        {"id": "card5", "name": "Review", "desc": "", "idList": "list5", "due": None, 
         "dateLastActivity": yesterday.isoformat(), "labels": [], "members": [], "url": "https://trello.com/c/5"},
        {"id": "card6", "name": "Done", "desc": "", "idList": "list6", "due": None, 
         "dateLastActivity": yesterday.isoformat(), "labels": [], "members": [], "url": "https://trello.com/c/6"},
        
        # Actual task cards
        {"id": "task1", "name": "[Feature] Customer Dashboard Improvements", "desc": "Add new analytics features", 
         "idList": "list1", "due": None, "dateLastActivity": yesterday.isoformat(), 
         "labels": [], "members": [], "url": "https://trello.com/c/task1"},
        
        {"id": "task2", "name": "[Bug] Payment Processing Delay", "desc": "Investigate and fix", 
         "idList": "list2", "due": (current_date + timedelta(days=2)).isoformat(), 
         "dateLastActivity": yesterday.isoformat(), 
         "labels": [{"id": "label1", "name": "", "color": "red"}], "members": ["member1"], "url": "https://trello.com/c/task2"},
        
        {"id": "task3", "name": "Wireframes for Customer Dashboard Redesign", "desc": "", 
         "idList": "list3", "due": yesterday.isoformat(), 
         "dateLastActivity": yesterday.isoformat(), 
         "labels": [], "members": ["member3"], "url": "https://trello.com/c/task3"},
        
        {"id": "task4", "name": "API Design for CRM Syncing", "desc": "", 
         "idList": "list4", "due": yesterday.isoformat(), 
         "dateLastActivity": yesterday.isoformat(), 
         "labels": [], "members": ["member2"], "url": "https://trello.com/c/task4"},
        
        {"id": "task5", "name": "Front-End Development for Dashboard Redesign", "desc": "", 
         "idList": "list5", "due": yesterday.isoformat(), 
         "dateLastActivity": yesterday.isoformat(), 
         "labels": [], "members": [], "url": "https://trello.com/c/task5"},
        
        {"id": "task6", "name": "Server Performance Optimization", "desc": "", 
         "idList": "list6", "due": None, 
         "dateLastActivity": yesterday.isoformat(), 
         "labels": [], "members": [], "url": "https://trello.com/c/task6"},
        
        {"id": "task7", "name": "Custom Pricing Module for Sales Team", "desc": "", 
         "idList": "list6", "due": None, 
         "dateLastActivity": yesterday.isoformat(), 
         "labels": [], "members": [], "url": "https://trello.com/c/task7"},
        
        {"id": "task8", "name": "CRM Integration Development", "desc": "", 
         "idList": "list6", "due": None, 
         "dateLastActivity": yesterday.isoformat(), 
         "labels": [{"id": "label1", "name": "", "color": "red"}], 
         "members": ["member3"], "url": "https://trello.com/c/task8"},
        
        {"id": "task9", "name": "UI Mockups for Dashboard Redesign", "desc": "", 
         "idList": "list3", "due": (current_date + timedelta(days=1)).isoformat(), 
         "dateLastActivity": yesterday.isoformat(), 
         "labels": [], "members": [], "url": "https://trello.com/c/task9"},
        
        {"id": "task10", "name": "Technical Feasibility for HubSpot Integration", "desc": "", 
         "idList": "list3", "due": (current_date + timedelta(days=3)).isoformat(), 
         "dateLastActivity": yesterday.isoformat(), 
         "labels": [], "members": [], "url": "https://trello.com/c/task10"}
    ]
    
    # Combine data into final structure
    return {
        "sprint_id": "TEST-SPRINT-1",
        "board_id": "board1",
        "cards": cards,
        "lists": lists,
        "members": members,
        "velocity": 42.0,
        "timestamp": current_date.isoformat()
    }

def main():
    print("Creating test data...")
    data = create_sample_data()
    
    print(f"Test data contains {len(data['cards'])} cards")
    print(f"Test data contains {len(data['lists'])} lists")
    print(f"Test data contains {len(data['members'])} members")
    
    # Print all task names
    tasks = [card for card in data['cards'] if card["name"] not in ["Backlog", "Planning / Design", "Ready", "In Progress", "Review", "Done"]]
    print(f"Actual tasks: {len(tasks)}")
    for task in tasks:
        print(f"- {task['name']} (List: {task['idList']})")
    
    # Instantiate ReportingAgent
    print("\nInstantiating ReportingAgent...")
    agent = ReportingAgent()
    
    # Generate report
    print("Generating report...")
    report_path = agent.generate_report(data)
    
    print(f"\nReport generated at: {report_path}")
    
    # Print the first few lines of the report
    if report_path and os.path.exists(report_path):
        print("\nReport content (first 20 lines):")
        with open(report_path, 'r') as f:
            content = f.readlines()
            for i, line in enumerate(content[:20]):
                print(f"{i+1}: {line.strip()}")
    else:
        print("Error: Report was not generated!")

if __name__ == "__main__":
    main() 