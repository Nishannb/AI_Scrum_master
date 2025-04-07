"""
Deployment script for all agents to AgentVerse.
"""

# Set up logging first
from src.utils.logging_utils import setup_logging, get_logger
setup_logging(log_file="logs/agent.log", log_level="DEBUG")
logger = get_logger(__name__)

import asyncio
import logging
import json
import os
import signal
from typing import List, Dict
from src.agents.supervisor_agent import SupervisorAgent
from src.agents.data_collection_agent import DataCollectionAgent
from src.agents.analysis_agent import AnalysisAgent
from src.agents.reporting_agent import ReportingAgent
from src.config.agentverse import get_agentverse_config
from src.utils.logging_utils import get_logger
import aiohttp
from dotenv import load_dotenv
from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low
from uagents.resolver import GlobalResolver

# Store agent addresses for later use
AGENT_ADDRESSES = {}

# Store running agents
RUNNING_AGENTS = []

# Agent metadata and documentation
AGENT_METADATA = {
    "supervisor": {
        "name": "Scrum Master Supervisor",
        "description": "Coordinates the AI scrum master system, managing workflow between data collection, analysis, and reporting agents.",
        "readme": """
# Scrum Master Supervisor Agent

## Description
This agent acts as the central coordinator for the AI scrum master system. It manages the workflow between data collection, analysis, and reporting agents to provide comprehensive sprint insights.

## Use Cases
- Coordinate sprint data collection and analysis
- Monitor sprint progress and team performance
- Generate sprint reports and recommendations

## Connected Agents
- Data Collection Specialist: Collects sprint data from various sources
- Sprint Analysis Specialist: Analyzes sprint data and generates insights
- Report Generation Specialist: Creates comprehensive sprint reports

## Message Formats

### DataRequest
```python
{
    "sprint_id": "SPRINT-123",  # Required: Unique identifier for the sprint
    "start_date": "2024-03-01", # Optional: Sprint start date
    "end_date": "2024-03-14"    # Optional: Sprint end date
}
```

### ReportResponse
```python
{
    "status": "success",
    "report": {
        "sprint_id": "SPRINT-123",
        "summary": "Sprint analysis summary",
        "metrics": {
            "velocity": 42,
            "burndown": "good",
            "blockers": ["none"]
        },
        "recommendations": ["Keep up the good work"]
    }
}
```

## How to Use

### Example Code
```python
from uagents import Agent
from src.models.messages import DataRequest

# Initialize your agent
user_agent = Agent(name="User Agent")

# Get the supervisor agent's address from the marketplace
supervisor_address = "agent1qtrpvncrxncy0zeer84xzqz3vz5v90r33mgmlkj9tauqft2wfjmkcelx80x"

# Send a request to analyze a sprint
async def analyze_sprint(sprint_id: str):
    # Create the request
    request = DataRequest(
        sprint_id=sprint_id,
        start_date="2024-03-01",
        end_date="2024-03-14"
    )
    
    # Send the request to the supervisor
    await user_agent.send(supervisor_address, request)
    
    # Wait for and process the response
    @user_agent.on_message(ReportResponse)
    async def handle_report(ctx: Context, sender: str, msg: ReportResponse):
        if msg.status == "success":
            print(f"Report received: {msg.report}")
        else:
            print(f"Error: {msg.error}")

# Run the analysis
asyncio.run(analyze_sprint("SPRINT-123"))
```

## Required Dependencies
- uagents
- aiohttp
- python-dotenv
"""
    },
    "data_collection": {
        "name": "Data Collection Specialist",
        "description": "Collects sprint data from various sources including Trello, Jira, and other project management tools.",
        "readme": """
# Data Collection Specialist Agent

## Description
This agent specializes in collecting sprint data from various project management tools and sources. It normalizes and prepares data for analysis.

## Use Cases
- Collect sprint data from Trello boards
- Gather task completion statistics
- Track team velocity and progress

## Connected Agents
- Scrum Master Supervisor: Receives data requests and sends collected data
- Sprint Analysis Specialist: Receives processed data for analysis

## Message Formats

### DataRequest
```python
{
    "sprint_id": "SPRINT-123",  # Required: Unique identifier for the sprint
    "start_date": "2024-03-01", # Optional: Sprint start date
    "end_date": "2024-03-14"    # Optional: Sprint end date
}
```

### DataResponse
```python
{
    "status": "success",
    "sprint_data": {
        "sprint_id": "SPRINT-123",
        "tasks": [
            {
                "id": "TASK-1",
                "title": "Implement feature X",
                "status": "completed",
                "points": 3
            }
        ],
        "velocity": 42,
        "completion_rate": 0.85
    }
}
```

## How to Use

### Example Code
```python
from uagents import Agent
from src.models.messages import DataRequest

# Initialize your agent
user_agent = Agent(name="User Agent")

# Get the data collection agent's address from the marketplace
data_collector_address = "agent1qfyuheqntdzggaggwhre2902rc6qfmmhl9yyt64a2l7ly69ry8zksjle6rc"

# Send a request to collect sprint data
async def collect_sprint_data(sprint_id: str):
    # Create the request
    request = DataRequest(
        sprint_id=sprint_id,
        start_date="2024-03-01",
        end_date="2024-03-14"
    )
    
    # Send the request to the data collector
    await user_agent.send(data_collector_address, request)
    
    # Wait for and process the response
    @user_agent.on_message(DataResponse)
    async def handle_data(ctx: Context, sender: str, msg: DataResponse):
        if msg.status == "success":
            print(f"Data received: {msg.sprint_data}")
        else:
            print(f"Error: {msg.error}")

# Run the data collection
asyncio.run(collect_sprint_data("SPRINT-123"))
```

## Required Dependencies
- uagents
- aiohttp
- python-dotenv
"""
    },
    "analysis": {
        "name": "Sprint Analysis Specialist",
        "description": "Analyzes sprint data to generate insights about team performance, velocity, and potential blockers.",
        "readme": """
# Sprint Analysis Specialist Agent

## Description
This agent analyzes sprint data to provide insights about team performance, identify bottlenecks, and suggest improvements.

## Use Cases
- Analyze sprint velocity and burndown
- Identify potential blockers and risks
- Generate performance insights

## Connected Agents
- Data Collection Specialist: Receives sprint data for analysis
- Report Generation Specialist: Sends analysis results for reporting

## Message Formats

### AnalysisRequest
```python
{
    "sprint_data": {
        "sprint_id": "SPRINT-123",
        "tasks": [
            {
                "id": "TASK-1",
                "title": "Implement feature X",
                "status": "completed",
                "points": 3
            }
        ],
        "velocity": 42,
        "completion_rate": 0.85
    }
}
```

### AnalysisResponse
```python
{
    "status": "success",
    "analysis_results": {
        "sprint_id": "SPRINT-123",
        "velocity_analysis": {
            "current": 42,
            "trend": "increasing",
            "prediction": 45
        },
        "blockers": ["none"],
        "risks": ["none"],
        "recommendations": ["Keep up the good work"]
    }
}
```

## How to Use

### Example Code
```python
from uagents import Agent
from src.models.messages import AnalysisRequest

# Initialize your agent
user_agent = Agent(name="User Agent")

# Get the analysis agent's address from the marketplace
analyst_address = "agent1q2jmxtc97vsdr8pm4kaqtggdchqh2lygvv5v2zc5w3dncle0n9es67r39la"

# Send a request to analyze sprint data
async def analyze_sprint_data(sprint_data: dict):
    # Create the request
    request = AnalysisRequest(sprint_data=sprint_data)
    
    # Send the request to the analyst
    await user_agent.send(analyst_address, request)
    
    # Wait for and process the response
    @user_agent.on_message(AnalysisResponse)
    async def handle_analysis(ctx: Context, sender: str, msg: AnalysisResponse):
        if msg.status == "success":
            print(f"Analysis received: {msg.analysis_results}")
        else:
            print(f"Error: {msg.error}")

# Run the analysis
sprint_data = {
    "sprint_id": "SPRINT-123",
    "tasks": [
        {
            "id": "TASK-1",
            "title": "Implement feature X",
            "status": "completed",
            "points": 3
        }
    ],
    "velocity": 42,
    "completion_rate": 0.85
}
asyncio.run(analyze_sprint_data(sprint_data))
```

## Required Dependencies
- uagents
- aiohttp
- python-dotenv
"""
    },
    "reporting": {
        "name": "Report Generation Specialist",
        "description": "Generates comprehensive sprint reports based on analysis results, including recommendations and visualizations.",
        "readme": """
# Report Generation Specialist Agent

## Description
This agent creates comprehensive sprint reports based on analysis results, including visualizations and actionable recommendations.

## Use Cases
- Generate sprint reports
- Create visualizations of sprint metrics
- Provide actionable recommendations

## Connected Agents
- Sprint Analysis Specialist: Receives analysis results
- Scrum Master Supervisor: Sends final reports

## Message Formats

### ReportRequest
```python
{
    "analysis_results": {
        "sprint_id": "SPRINT-123",
        "velocity_analysis": {
            "current": 42,
            "trend": "increasing",
            "prediction": 45
        },
        "blockers": ["none"],
        "risks": ["none"],
        "recommendations": ["Keep up the good work"]
    }
}
```

### ReportResponse
```python
{
    "status": "success",
    "report": {
        "sprint_id": "SPRINT-123",
        "summary": "Sprint analysis summary",
        "metrics": {
            "velocity": 42,
            "burndown": "good",
            "blockers": ["none"]
        },
        "recommendations": ["Keep up the good work"],
        "visualizations": {
            "velocity_chart": "base64_encoded_image",
            "burndown_chart": "base64_encoded_image"
        }
    }
}
```

## How to Use

### Example Code
```python
from uagents import Agent
from src.models.messages import ReportRequest

# Initialize your agent
user_agent = Agent(name="User Agent")

# Get the reporting agent's address from the marketplace
reporter_address = "agent1q02veg75zfh3r684nje5hs6nws5x8rvxhhqrzyt5kspk4kk05f2my097exz"

# Send a request to generate a report
async def generate_report(analysis_results: dict):
    # Create the request
    request = ReportRequest(analysis_results=analysis_results)
    
    # Send the request to the reporter
    await user_agent.send(reporter_address, request)
    
    # Wait for and process the response
    @user_agent.on_message(ReportResponse)
    async def handle_report(ctx: Context, sender: str, msg: ReportResponse):
        if msg.status == "success":
            print(f"Report received: {msg.report}")
            # Save visualizations if needed
            if "visualizations" in msg.report:
                for name, data in msg.report["visualizations"].items():
                    with open(f"{name}.png", "wb") as f:
                        f.write(base64.b64decode(data))
        else:
            print(f"Error: {msg.error}")

# Run the report generation
analysis_results = {
    "sprint_id": "SPRINT-123",
    "velocity_analysis": {
        "current": 42,
        "trend": "increasing",
        "prediction": 45
    },
    "blockers": ["none"],
    "risks": ["none"],
    "recommendations": ["Keep up the good work"]
}
asyncio.run(generate_report(analysis_results))
```

## Required Dependencies
- uagents
- aiohttp
- python-dotenv
"""
    }
}

async def deploy_agent(agent_class, name: str, port: int, role: str) -> Dict[str, str]:
    """Deploy a single agent to AgentVerse"""
    try:
        config = get_agentverse_config()
        metadata = AGENT_METADATA[role]
        
        # Create agent with proper endpoint configuration
        agent = agent_class(
            name=metadata["name"],
            port=port,
            seed=f"{name}_seed_{port}",
            endpoint=[f"http://127.0.0.1:{port}/submit"],
            agentverse=config,
            mailbox=True
        )

        logger.info(f"Starting {metadata['name']} agent...")
        
        # Start the agent in a separate task
        agent_task = asyncio.create_task(agent.run_async())
        RUNNING_AGENTS.append(agent_task)
        
        # Wait for the agent to start up
        await asyncio.sleep(5)
        
        # Check if agent is running by querying its endpoint
        try:
            async with aiohttp.ClientSession() as session:
                # Try multiple times to connect to the agent
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        async with session.get(f"http://127.0.0.1:{port}/agent_info") as response:
                            if response.status == 200:
                                agent_info = await response.json()
                                logger.info(f"Agent {metadata['name']} is running with address: {agent_info['address']}")
                                
                                # Store agent address immediately
                                AGENT_ADDRESSES[role] = agent_info["address"]
                                
                                # Save addresses after each successful deployment
                                with open("agent_addresses.json", "w") as f:
                                    json.dump(AGENT_ADDRESSES, f, indent=2)
                                    
                                logger.info(f"Saved agent address for {role} to agent_addresses.json")
                                
                                # Verify agent registration
                                async with session.get(f"https://agentverse.ai/api/v1/agents/{agent_info['address']}") as verify_response:
                                    if verify_response.status == 200:
                                        logger.info(f"Agent {metadata['name']} successfully registered in AgentVerse")
                                    else:
                                        logger.warning(f"Agent {metadata['name']} may not be properly registered in AgentVerse")
                                
                                return {
                                    "name": metadata["name"],
                                    "address": agent_info["address"],
                                    "role": role,
                                    "port": port,
                                    "task": agent_task
                                }
                    except aiohttp.ClientError as e:
                        if attempt < max_retries - 1:
                            logger.warning(f"Attempt {attempt + 1} failed to connect to agent: {str(e)}")
                            await asyncio.sleep(2)  # Wait before retrying
                        else:
                            raise RuntimeError(f"Failed to connect to agent after {max_retries} attempts: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to verify agent {metadata['name']} is running: {str(e)}")
            # Cancel the agent task if it exists
            if agent_task in RUNNING_AGENTS:
                agent_task.cancel()
                try:
                    await agent_task
                except asyncio.CancelledError:
                    pass
            raise
        
    except Exception as e:
        logger.error(f"Failed to deploy agent {metadata['name']}: {str(e)}")
        raise

async def deploy_all_agents():
    """Deploy all agents to AgentVerse"""
    try:
        # Remove old addresses file if it exists
        if os.path.exists("agent_addresses.json"):
            os.remove("agent_addresses.json")
            logger.info("Removed old agent_addresses.json")
            
        # Deploy Supervisor Agent
        supervisor = await deploy_agent(
            SupervisorAgent,
            "Scrum Master Supervisor",
            8000,
            "supervisor"
        )
        
        # Wait for supervisor to be fully initialized and registered
        await asyncio.sleep(5)
        
        # Deploy Data Collection Agent
        data_collector = await deploy_agent(
            DataCollectionAgent,
            "Data Collection Specialist",
            8001,
            "data_collection"
        )
        
        # Wait for data collector to be fully initialized and registered
        await asyncio.sleep(5)
        
        # Deploy Analysis Agent
        analyst = await deploy_agent(
            AnalysisAgent,
            "Sprint Analysis Specialist",
            8002,
            "analysis"
        )
        
        # Wait for analyst to be fully initialized and registered
        await asyncio.sleep(5)
        
        # Deploy Reporting Agent
        reporter = await deploy_agent(
            ReportingAgent,
            "Report Generation Specialist",
            8003,
            "reporting"
        )
        
        logger.info("All agents deployed successfully")
        logger.info("Agent addresses saved to agent_addresses.json")
        
        # Keep the agents running
        await asyncio.gather(*RUNNING_AGENTS)
        
    except Exception as e:
        logger.error(f"Failed to deploy agents: {str(e)}")
        raise
    finally:
        # Save addresses even if there's an error
        if AGENT_ADDRESSES:
            with open("agent_addresses.json", "w") as f:
                json.dump(AGENT_ADDRESSES, f, indent=2)
            logger.info("Saved final agent addresses to agent_addresses.json")

def handle_interrupt(signum, frame):
    """Handle interrupt signal"""
    logger.info("Received interrupt signal. Shutting down agents...")
    for task in RUNNING_AGENTS:
        task.cancel()
    logger.info("All agents stopped")

if __name__ == "__main__":
    try:
        # Set up signal handlers
        signal.signal(signal.SIGINT, handle_interrupt)
        signal.signal(signal.SIGTERM, handle_interrupt)
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the deployment
        loop.run_until_complete(deploy_all_agents())
    except KeyboardInterrupt:
        logger.info("Deployment interrupted by user")
    except Exception as e:
        logger.error(f"Deployment failed: {str(e)}")
        raise
    finally:
        loop.close() 