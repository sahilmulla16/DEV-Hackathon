import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the Slack bot token
slack_bot_token = os.getenv('SLACK_BOT_TOKEN')

if slack_bot_token:
    print(f"Slack Bot Token loaded successfully: {slack_bot_token}")
else:
    print("Failed to load Slack Bot Token")