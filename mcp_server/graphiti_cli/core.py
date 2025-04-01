#!/usr/bin/env python3
"""
Core utility functions for the Graphiti CLI tool.
Contains path finding, subprocess execution, and common constants.
"""
import os
import sys
import subprocess
from pathlib import Path
from enum import Enum
import shutil
from typing import List, Optional, Union, Dict, Any

# --- ANSI Color Constants ---
# These match the original bash script for consistency
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[0;33m'
BLUE = '\033[0;34m'
CYAN = '\033[0;36m'
BOLD = '\033[1m'
NC = '\033[0m'  # No Color

# --- Constants ---
DEFAULT_PORT_START = 8000
DEFAULT_MCP_CONTAINER_PORT_VAR = "MCP_PORT"
CONTAINER_ENTITY_PATH = "/app/entity_types"
ENV_REPO_PATH = "MCP_GRAPHITI_REPO_PATH"

# --- Enums ---
class LogLevel(str, Enum):
    """
    Log levels for Docker Compose and container execution.
    """
    debug = "debug"
    info = "info"
    warn = "warn"
    error = "error"
    fatal = "fatal"
    
    def __str__(self) -> str:
        return self.value

# --- Path Finding Functions ---
def _find_repo_root() -> Optional[Path]:
    """
    Internal function to find the repository root directory.
    
    The repository root is identified by the presence of:
    - A mcp_server/ directory
    - Within mcp_server/: entity_types/ directory
    
    Returns:
        Optional[Path]: The absolute path to the repository root, or None if not found.
    """
    # First check environment variable
    if ENV_REPO_PATH in os.environ:
        repo_path = Path(os.environ[ENV_REPO_PATH])
        if _validate_repo_path(repo_path):
            return repo_path.resolve()
        print(f"{YELLOW}Warning: {ENV_REPO_PATH} is set but points to invalid path: {repo_path}{NC}")
    
    # Try to find the repo root automatically based on script location
    # Current script should be in mcp_server/graphiti_cli/core.py
    current_file = Path(__file__).resolve()
    if "mcp_server" in current_file.parts and "graphiti_cli" in current_file.parts:
        # Go up to the 'mcp_server' parent, then one more level to reach repo root
        potential_root = current_file.parents[2]  # Two levels up from core.py
        if _validate_repo_path(potential_root):
            return potential_root
        
    # Check current directory
    current_dir = Path.cwd()
    if _validate_repo_path(current_dir):
        return current_dir
    
    # Check one level up
    parent_dir = current_dir.parent
    if _validate_repo_path(parent_dir):
        return parent_dir
    
    return None

def _validate_repo_path(path: Path) -> bool:
    """
    Validates that a given path is a valid repository root.
    
    Args:
        path (Path): Path to validate
        
    Returns:
        bool: True if the path is a valid repository root, False otherwise
    """
    if not path.is_dir():
        return False
    
    # Check for essential directories
    mcp_server_dir = path / "mcp_server"
    entity_types_dir = mcp_server_dir / "entity_types"
    
    return mcp_server_dir.is_dir() and entity_types_dir.is_dir()

def get_repo_root() -> Path:
    """
    Get the repository root directory, exiting if not found.
    
    Returns:
        Path: The absolute path to the repository root
    """
    repo_root = _find_repo_root()
    if repo_root is None:
        print(f"{RED}Error: Could not find repository root.{NC}")
        print(f"Please set the {CYAN}{ENV_REPO_PATH}{NC} environment variable to the root of your mcp-graphiti repository.")
        print(f"Example: {YELLOW}export {ENV_REPO_PATH}=/path/to/mcp-graphiti{NC}")
        sys.exit(1)
    return repo_root

def get_mcp_server_dir() -> Path:
    """
    Get the mcp_server directory path.
    
    Returns:
        Path: The absolute path to the mcp_server directory
    """
    return get_repo_root() / "mcp_server"

# --- Process Execution Functions ---
def run_command(
    cmd: List[str], 
    check: bool = False, 
    env: Optional[Dict[str, str]] = None,
    cwd: Optional[Union[str, Path]] = None
) -> subprocess.CompletedProcess:
    """
    Run a command in a subprocess with proper error handling.
    Output is streamed to stdout/stderr by default.
    
    Args:
        cmd (List[str]): Command and arguments as a list
        check (bool): If True, check the return code and raise CalledProcessError if non-zero
        env (Optional[Dict[str, str]]): Environment variables to set for the command
        cwd (Optional[Union[str, Path]]): Directory to run the command in
        
    Returns:
        subprocess.CompletedProcess: Result of the command
    """
    cmd_str = " ".join(cmd)
    
    # Use current environment and update with any provided environment variables
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    
    try:
        return subprocess.run(
            cmd,
            check=check,
            env=merged_env,
            cwd=cwd,
            text=True,
            capture_output=False  # Allow output to stream to terminal
        )
    except subprocess.CalledProcessError as e:
        print(f"{RED}Error: Command failed with exit code {e.returncode}:{NC}")
        print(f"Command: {CYAN}{cmd_str}{NC}")
        # Note: with capture_output=False, e.stdout and e.stderr will be None
        # Error output will have been streamed directly to the terminal
        if e.stdout:
            print(f"{YELLOW}--- Command output ---{NC}")
            print(e.stdout)
        if e.stderr:
            print(f"{RED}--- Command error ---{NC}")
            print(e.stderr)
        if check:
            sys.exit(e.returncode)
        raise
    except Exception as e:
        print(f"{RED}Error: Failed to execute command: {cmd_str}{NC}")
        print(f"Error details: {e}")
        if check:
            sys.exit(1)
        raise

def run_docker_compose(
    subcmd: List[str], 
    log_level: str = LogLevel.info.value, 
    detached: bool = False
) -> None:
    """
    Run a docker compose command with consistent environment settings.
    
    Args:
        subcmd (List[str]): Docker compose subcommand and arguments
        log_level (str): Log level to set in environment
        detached (bool): Whether to add the -d flag for detached mode
    """
    mcp_server_dir = get_mcp_server_dir()
    
    # Add -d flag if detached mode is requested
    if detached and subcmd[0] in ["up"]:
        subcmd.append("-d")
    
    # Set environment variables for docker compose
    env_vars = {
        "GRAPHITI_LOG_LEVEL": log_level
    }
    
    # Prepare full command
    cmd = ["docker", "compose"] + subcmd
    
    print(f"Running Docker Compose from: {CYAN}{mcp_server_dir}{NC}")
    print(f"Command: {' '.join(cmd)}")
    if log_level != LogLevel.info.value:
        print(f"Log level: {CYAN}{log_level}{NC}")
    
    # Execute the command
    run_command(cmd, check=True, env=env_vars, cwd=mcp_server_dir)

def ensure_docker_compose_file() -> None:
    """
    Ensure that the docker-compose.yml file exists by generating it if necessary.
    """
    mcp_server_dir = get_mcp_server_dir()
    compose_file = mcp_server_dir / "docker-compose.yml"
    
    print(f"{BOLD}Ensuring docker-compose.yml is up-to-date...{NC}")
    
    # Use our Python utility (to be implemented in yaml_utils.py) instead of the script
    # Will be implemented after yaml_utils.py is created
    from . import yaml_utils
    try:
        yaml_utils.generate_compose_logic(mcp_server_dir)
    except Exception as e:
        print(f"{RED}Warning: Failed to generate docker-compose.yml file: {e}{NC}")
        print(f"{YELLOW}Continuing with existing file if it exists.{NC}")
    
    # Check if the file exists now
    if not compose_file.exists():
        print(f"{RED}Error: docker-compose.yml file does not exist and could not be generated.{NC}")
        sys.exit(1)

def ensure_dist_for_build() -> None:
    """
    Ensure that the dist directory is available for Docker build if needed.
    
    This function checks if the graphiti-core package is configured to use a local wheel.
    If so, it ensures the dist directory exists and copies the wheel files.
    """
    repo_root = get_repo_root()
    mcp_server_dir = get_mcp_server_dir()
    
    print(f"{BOLD}Checking build configuration...{NC}")
    
    # Check pyproject.toml to see if we're using local wheel
    pyproject_path = mcp_server_dir / "pyproject.toml"
    try:
        with open(pyproject_path, 'r') as f:
            pyproject_content = f.read()
            
        # Check if we're using local wheel and not published package
        using_local_wheel = "graphiti-core @ file:///dist/" in pyproject_content
        using_published = any(
            line.strip().startswith("graphiti-core>=") 
            for line in pyproject_content.splitlines()
            if not line.strip().startswith('#')
        )
        
        if not using_local_wheel or using_published:
            print(f"{CYAN}Using published graphiti-core package. Skipping local wheel setup.{NC}")
            return
        
        print(f"{CYAN}Local graphiti-core wheel configuration detected.{NC}")
        
        # Source and target paths
        repo_dist = repo_root / "dist"
        server_dist = mcp_server_dir / "dist"
        
        # Check if source dist exists
        if not repo_dist.is_dir():
            print(f"{RED}Error: dist directory not found at {repo_dist}{NC}")
            print(f"Please build the graphiti-core wheel first.")
            sys.exit(1)
        
        # Find wheel files
        wheel_files = list(repo_dist.glob("*.whl"))
        if not wheel_files:
            print(f"{RED}Error: No wheel files found in {repo_dist}{NC}")
            print(f"Please build the graphiti-core wheel first.")
            sys.exit(1)
        
        # Create target directory if needed
        server_dist.mkdir(exist_ok=True, parents=True)
        
        # Copy wheel files
        print(f"Copying wheel files from {CYAN}{repo_dist}{NC} to {CYAN}{server_dist}{NC}")
        for wheel_file in wheel_files:
            shutil.copy2(wheel_file, server_dist)
        
        print(f"{GREEN}Dist directory prepared for Docker build.{NC}")
    
    except Exception as e:
        print(f"{RED}Error checking build configuration: {e}{NC}")
        print(f"{YELLOW}Please ensure your pyproject.toml is properly configured.{NC}")
        sys.exit(1)
