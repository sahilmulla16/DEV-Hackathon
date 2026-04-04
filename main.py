# main.py
import click

# --- Core Imports ---
# By importing config first, we ensure all environment variables and constants are loaded.
import core.config

# Now, we can safely import other components that might use the config.
from app import app # This import might not be needed if _vectorstore is initialized in config

@click.group()
def cli():
    """AI Agent Platform CLI"""
    pass

@cli.command()
def serve():
    """Starts the Flask web server."""
    app.run(host='0.0.0.0', port=5000, debug=app.config['DEBUG'])

if __name__ == '__main__':
    cli()