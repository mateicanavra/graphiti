#!/usr/bin/env python3
"""
Main entry point for the Graphiti CLI tool.
This module defines the Typer CLI application and command structure.
"""
import typer
from pathlib import Path
from typing_extensions import Annotated  # Preferred for Typer >= 0.9

# Import command functions and core utilities
from . import commands
from .core import LogLevel, get_repo_root

# Initialize Typer app
app = typer.Typer(
    help="CLI for managing Graphiti MCP Server projects and Docker environment.",
    no_args_is_help=True,  # Show help if no command is given
    rich_markup_mode="markdown"  # Nicer help text formatting
)

# --- Callback to ensure repo path is found early ---
@app.callback()
def main_callback(ctx: typer.Context):
    """
    Main callback to perform setup before any command runs.
    Ensures the MCP_GRAPHITI_REPO_PATH is found.
    """
    # Ensure repo root is detected/set early.
    # get_repo_root() will print messages and exit if not found.
    _ = get_repo_root()


# --- Define Commands (delegating to functions in commands.py) ---

@app.command()
def init(
    project_name: Annotated[str, typer.Argument(help="Name of the target project.")],
    target_dir: Annotated[Path, typer.Argument(
        help="Target project root directory.",
        exists=False,  # Allow creating the directory
        file_okay=False,
        dir_okay=True,
        writable=True,
        resolve_path=True  # Convert to absolute path
    )] = Path(".")
):
    """
    Initialize a project: create ai/graph structure with config, entities dir, and rules. ✨
    """
    commands.init_project(project_name, target_dir)

@app.command()
def entity(
    set_name: Annotated[str, typer.Argument(help="Name for the new entity type set (e.g., 'my-entities').")],
    target_dir: Annotated[Path, typer.Argument(
        help="Target project root directory containing ai/graph/mcp-config.yaml.",
        exists=True,  # Must exist for entity creation
        file_okay=False,
        dir_okay=True,
        resolve_path=True
    )] = Path(".")
):
    """
    Create a new entity type set directory and template file within a project's ai/graph/entities directory. 📄
    """
    commands.create_entity_set(set_name, target_dir)

@app.command()
def rules(
    project_name: Annotated[str, typer.Argument(help="Name of the target project for rule setup.")],
    target_dir: Annotated[Path, typer.Argument(
        help="Target project root directory.",
        exists=True,  # Must exist for rules setup
        file_okay=False,
        dir_okay=True,
        resolve_path=True
    )] = Path(".")
):
    """
    Setup/update Cursor rules symlinks and schema template for a project. 🔗
    """
    commands.setup_rules(project_name, target_dir)

@app.command()
def up(
    detached: Annotated[bool, typer.Option("--detached", "-d", help="Run containers in detached mode.")] = False,
    log_level: Annotated[LogLevel, typer.Option("--log-level", help="Set logging level for containers.", case_sensitive=False)] = LogLevel.info
):
    """
    Start all containers using Docker Compose (builds first). 🚀
    """
    commands.docker_up(detached, log_level.value)

@app.command()
def down(
    log_level: Annotated[LogLevel, typer.Option("--log-level", help="Set logging level for Docker Compose execution.", case_sensitive=False)] = LogLevel.info
):
    """
    Stop and remove all containers using Docker Compose. 🛑
    """
    commands.docker_down(log_level.value)

@app.command()
def restart(
    detached: Annotated[bool, typer.Option("--detached", "-d", help="Run 'up' in detached mode after 'down'.")] = False,
    log_level: Annotated[LogLevel, typer.Option("--log-level", help="Set logging level for containers.", case_sensitive=False)] = LogLevel.info
):
    """
    Restart all containers: runs 'down' then 'up'. 🔄
    """
    commands.docker_restart(detached, log_level.value)

@app.command()
def reload(
    service_name: Annotated[str, typer.Argument(help="Name of the service to reload (e.g., 'mcp-test-project-1-main').")]
):
    """
    Restart a specific running service container. ⚡
    """
    commands.docker_reload(service_name)

@app.command()
def compose():
    """
    Generate docker-compose.yml from base and project configs. ⚙️
    """
    commands.docker_compose_generate()


# Allow running the script directly for development/testing
if __name__ == "__main__":
    app()
