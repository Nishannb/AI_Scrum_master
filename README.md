AI Scrum Master Project for Global AI Agents League

4 agents with 1 supervisor agent working together to create scrum report based on information on team trello board data
- Supervisor agent
- Data collection agent: fetches data from trello
- analysis agents: analyzing data from trello
- reporting agent: prepares report along with the pdf with 4 charts (task distribution chart, burndown chart, team velocity chart and gantt chart on task timeline)

The prepared chart will be sent to slack channel and also the pdf will be uploaded to cloudinary as a backup. 
- maybe someone who is using it, might need to make cloudinary pdf view to public on. This is a toggle button in cloudinary settings. 


How to run it locally:
- Add all the required env variable keys in .env
- run python src/deploy_agents.py 
- after deploying, run src/test_agent_flow.py
- You will receive the Scrum Report on your slack channel

Future timeline for the project: 
- Building a bot that automates the process of updating task status and follow thru using slack channels.
- Frontend for client integration


![tag : innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)

