import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Initialize the Slack client with your bot token
client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])

try:
    # Send a message to the #general channel
    response = client.chat_postMessage(
        channel="#general",
        text="Hello from the Slack bot!"
    )
    print("Message sent successfully:", response)
except SlackApiError as e:
    # Print the error if something goes wrong
    print(f"Error sending message: {e.response['error']}")