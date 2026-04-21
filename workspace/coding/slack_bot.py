import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Initialize the Slack client with the bot token
# Make sure to set the SLACK_BOT_TOKEN environment variable with your bot token
client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])

try:
    # Send a message to the '#general' channel
    response = client.chat_postMessage(
        channel="#general",
        text="Hello from the AI Agent!"
    )
    print("Message sent successfully!")
    print(f"Message timestamp: {response['ts']}")
except SlackApiError as e:
    # Handle errors
    print(f"Error sending message: {e.response['error']}")
except KeyError:
    print("SLACK_BOT_TOKEN environment variable not set. Please set it before running the script.")
