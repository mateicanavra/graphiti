#!/usr/bin/env python3
"""
YAML Helper for Graphiti MCP Server

This script provides utilities to manage the mcp-projects.yaml registry file.
It preserves comments and formatting while updating the YAML content.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Use ruamel.yaml for round-trip parsing
from ruamel.yaml import YAML


def update_registry(
    registry_file: str,
    project_name: str,
    root_dir: str,
    config_file: str,
    enabled: bool = True
) -> bool:
    """
    Update the central project registry file with a project entry.
    
    Args:
        registry_file: Path to the registry file (mcp-projects.yaml)
        project_name: Name of the project
        root_dir: Absolute path to the project's root directory
        config_file: Absolute path to the project's config file
        enabled: Whether the project should be enabled
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if paths are absolute
        if not os.path.isabs(root_dir):
            print(f"Error: Project root directory '{root_dir}' must be an absolute path")
            return False
            
        if not os.path.isabs(config_file):
            print(f"Error: Project config file '{config_file}' must be an absolute path")
            return False
            
        # Check if config file exists
        if not os.path.exists(config_file):
            print(f"Warning: Project config file '{config_file}' does not exist")
            # Don't return False here, to allow for initialization scenarios where the file is created after
            
        # Create the registry file if it doesn't exist
        registry_path = Path(registry_file)
        if not registry_path.exists():
            # Create directory if needed
            registry_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create a minimal registry file with header comments
            with open(registry_file, 'w') as f:
                f.write("""# !! WARNING: This file is managed by the 'graphiti init' command. !!
# !! Avoid manual edits unless absolutely necessary.                 !!
#
# Maps project names to their configuration details.
# Paths should be absolute for reliability.
projects: {}
""")
            print(f"Created new registry file: {registry_file}")
        
        # Initialize YAML with round-trip mode
        yaml = YAML()
        yaml.preserve_quotes = True
        yaml.indent(mapping=2, sequence=4, offset=2)
        
        # Load the registry file
        with open(registry_file, 'r') as f:
            data = yaml.load(f)
            
        # Validate the YAML structure
        if not isinstance(data, dict) or 'projects' not in data:
            print(f"Error: Invalid registry file format. Missing 'projects' key or not a dictionary.")
            return False
            
        # Create the projects dict if it doesn't exist
        if data['projects'] is None:
            data['projects'] = {}
            
        # Add or update the project entry
        data['projects'][project_name] = {
            'root_dir': root_dir,
            'config_file': config_file,
            'enabled': enabled
        }
        
        # Write back to the registry file
        with open(registry_file, 'w') as f:
            yaml.dump(data, f)
            
        print(f"Successfully updated registry for project '{project_name}'")
        return True
        
    except Exception as e:
        print(f"Error updating registry: {str(e)}")
        return False


def main():
    """Parse command-line arguments and execute the appropriate action."""
    parser = argparse.ArgumentParser(description='YAML Helper for Graphiti MCP Server')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Update registry command
    update_parser = subparsers.add_parser('update-registry', help='Update the central project registry')
    update_parser.add_argument('--registry-file', required=True, help='Path to the registry file (mcp-projects.yaml)')
    update_parser.add_argument('--project-name', required=True, help='Name of the project')
    update_parser.add_argument('--root-dir', required=True, help='Absolute path to the project root directory')
    update_parser.add_argument('--config-file', required=True, help='Absolute path to the project config file')
    update_parser.add_argument('--enabled', action='store_true', default=True, help='Whether the project should be enabled')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute the appropriate command
    if args.command == 'update-registry':
        success = update_registry(
            args.registry_file,
            args.project_name,
            args.root_dir,
            args.config_file,
            args.enabled
        )
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main() 