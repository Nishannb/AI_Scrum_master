# Slack Integration Guide

This guide will help you set up the Slack integration for sending sprint report notifications.

## Prerequisites

- A Slack workspace with permission to create apps
- Admin access or permission to install apps to your workspace

## Setup Steps

### 1. Create a Slack App

1. Visit [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App"
3. Select "From scratch"
4. Enter a name (e.g., "Sprint Report Bot") and select your workspace
5. Click "Create App"

### 2. Add Required Permissions

1. In the left sidebar, click on "OAuth & Permissions"
2. Scroll down to the "Scopes" section
3. Under "Bot Token Scopes", add the following permissions:
   - `chat:write` - For sending messages to channels
   - `chat:write.customize` - For using Block Kit formatting (optional but recommended)

### 3. Install the App to Your Workspace

1. In the left sidebar, click on "Install App"
2. Click "Install to Workspace"
3. Review the permissions and click "Allow"

### 4. Get Bot Token

1. After installation, you'll be redirected to the "OAuth & Permissions" page
2. Copy the "Bot User OAuth Token" (it starts with `xoxb-`)

### 5. Create a Channel for Reports

1. In Slack, create a new channel (e.g., `#sprint-reports`)
2. Invite your bot to the channel by typing `/invite @YourBotName` in the channel

### 6. Configure Environment Variables

Add these variables to your `.env` file:

```
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_DEFAULT_CHANNEL=sprint-reports
```

Replace `xoxb-your-bot-token-here` with the Bot User OAuth Token you copied.
Replace `sprint-reports` with your channel name (without the `#` symbol).

### 7. Install Required Package

Make sure the Slack SDK is installed:

```bash
pip install slack-sdk
```

## Testing the Integration

After setup, run a report generation to test the integration:

```bash
python main.py
```

If everything is configured correctly, you should see a message in your Slack channel with a link to the sprint report.

## Troubleshooting

- **No message appears in Slack**: Check the application logs for errors related to Slack notifications.
- **Authentication errors**: Verify your Bot Token is correct and the app has the required permissions.
- **Channel not found**: Make sure you've invited the bot to the channel and the channel name is correct in your .env file.

## Moving the Integration to a New Project

The Slack integration is designed to be modular. If you want to move it to a new project:

1. Copy the `src/utils/slack_utils.py` file to your new project
2. Update the import for logging utilities as needed
3. Configure the environment variables in your new project
4. Use the `SlackNotifier` class to send notifications from your new project 