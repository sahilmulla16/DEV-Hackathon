import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

def send_slack_message():
    # Load the bot token from environment variable
    token = os.getenv("SLACK_BOT_TOKEN")
    if not token:
        print("Error: SLACK_BOT_TOKEN environment variable not set.")
        return

    # Initialize the Slack client
    client = WebClient(token=token)

    try:
        response = client.chat_postMessage(
            channel="#general",
            text="Hello from the AI Agent!"
        )
        print("Message sent successfully to #general")
    except SlackApiError as e:
        # Handle specific Slack API errors
        error = e.response['error']
        print(f"Error: {error}")
    except Exception as e:
        # Handle other exceptions (e.g., network issues)
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    send_slack_message()