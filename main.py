# main.py
import os
import shutil
import click
from langchain_chroma import Chroma

# --- Core Imports ---
# By importing config first, we ensure all environment variables and constants are loaded.
import core.config

# Now, we can safely import other components that might use the config.
from app import app
from agent import run_agent_once

@click.group()
def cli():
    """AI Agent Platform CLI"""
    # Initialize the memory vector store and assign it to the global variable in the core config.
    print("🧠 Initializing agent memory vector store...")
    try:
        core.config._vectorstore = Chroma(
            collection_name=core.config.MEM_COLLECTION,
            embedding_function=core.config._embedding_fn,
            persist_directory=core.config.PERSIST_DIR
        )
    except Exception as e:
        print(f"⚠️ ChromaDB loading failed, resetting memory database: {e}")
        shutil.rmtree(core.config.PERSIST_DIR, ignore_errors=True)
        core.config._vectorstore = Chroma(collection_name=core.config.MEM_COLLECTION, embedding_function=core.config._embedding_fn, persist_directory=core.config.PERSIST_DIR)
    print("✅ Agent memory loaded.")

@cli.command()
def serve():
    """Starts the Flask web server."""
    app.run(host='0.0.0.0', port=5000, debug=app.config['DEBUG'])

if __name__ == '__main__':
    cli()