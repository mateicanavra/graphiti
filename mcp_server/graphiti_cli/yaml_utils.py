#!/usr/bin/env python3
"""
YAML utility functions for the Graphiti CLI.
Contains functions for loading/saving YAML files, updating the registry,
and generating the Docker Compose configuration.
"""
import sys
from pathlib import Path
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
import os
from typing import Optional, List, Dict, Any

from .core import get_mcp_server_dir, CONTAINER_ENTITY_PATH, DEFAULT_PORT_START, DEFAULT_MCP_CONTAINER_PORT_VAR, RED, GREEN, YELLOW, CYAN, NC
# Define the distinct path for project-specific entities inside the container
PROJECT_CONTAINER_ENTITY_PATH = "/app/project_entities"

# --- YAML Instances ---
yaml_rt = YAML()  # Round-Trip for preserving structure/comments
yaml_rt.preserve_quotes = True
yaml_rt.indent(mapping=2, sequence=4, offset=2)

yaml_safe = YAML(typ='safe')  # Safe loader for reading untrusted/simple config

# --- File Handling ---
def load_yaml_file(file_path: Path, safe: bool = False) -> Optional[Any]:
    """
    Loads a YAML file, handling errors.
    
    Args:
        file_path (Path): Path to the YAML file
        safe (bool): Whether to use the safe loader (True) or round-trip loader (False)
        
    Returns:
        Optional[Any]: The parsed YAML data, or None if loading failed
    """
    yaml_loader = yaml_safe if safe else yaml_rt
    if not file_path.is_file():
        print(f"Warning: YAML file not found or is not a file: {file_path}")
        return None
    try:
        with file_path.open('r') as f:
            return yaml_loader.load(f)
    except Exception as e:
        print(f"Error parsing YAML file '{file_path}': {e}")
        return None  # Or raise specific exception

def write_yaml_file(data: Any, file_path: Path, header: Optional[List[str]] = None):
    """
    Writes data to a YAML file using round-trip dumper.
    
    Args:
        data (Any): The data to write to the file
        file_path (Path): Path to the output file
        header (Optional[List[str]]): Optional list of comment lines to add at the top of the file
    
    Raises:
        IOError: If the file cannot be written
        Exception: For other errors
    """
    try:
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open('w') as f:
            if header:
                f.write("\n".join(header) + "\n\n")  # Add extra newline
            yaml_rt.dump(data, f)
    except IOError as e:
        print(f"Error writing YAML file '{file_path}': {e}")
        raise  # Re-raise after printing
    except Exception as e:
        print(f"An unexpected error occurred during YAML dumping to '{file_path}': {e}")
        raise

# --- Logic from _yaml_helper.py ---
def update_registry_logic(
    registry_file: Path,
    project_name: str,
    root_dir: Path,  # Expecting resolved absolute path
    config_file: Path,  # Expecting resolved absolute path
    enabled: bool = True
) -> bool:
    """
    Updates the central project registry file (mcp-projects.yaml).
    Corresponds to the logic in the old _yaml_helper.py.
    
    Args:
        registry_file (Path): Path to the registry file
        project_name (str): Name of the project
        root_dir (Path): Absolute path to the project root directory
        config_file (Path): Absolute path to the project config file
        enabled (bool): Whether the project should be enabled
        
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"Updating registry '{registry_file}' for project '{project_name}'")
    if not root_dir.is_absolute() or not config_file.is_absolute():
        print("Error: Project root_dir and config_file must be absolute paths.")
        return False

    if not config_file.exists():
        print(f"Warning: Project config file '{config_file}' does not exist.")
        # Allow continuing for init scenarios

    # Create registry file with header if it doesn't exist
    if not registry_file.exists():
        print(f"Creating new registry file: {registry_file}")
        header = [
            "# !! WARNING: This file is managed by the 'graphiti init' command. !!",
            "# !! Avoid manual edits unless absolutely necessary.                 !!",
            "#",
            "# Maps project names to their configuration details.",
            "# Paths should be absolute for reliability.",
        ]
        initial_data = CommentedMap({'projects': CommentedMap()})
        try:
            write_yaml_file(initial_data, registry_file, header=header)
        except Exception:
            return False  # Error handled in write_yaml_file

    # Load existing registry data using round-trip loader
    data = load_yaml_file(registry_file, safe=False)
    if data is None:
        print(f"Error: Could not load registry file {registry_file}")
        return False

    if not isinstance(data, dict) or 'projects' not in data:
        print(f"Error: Invalid registry file format in {registry_file}. Missing 'projects' key.")
        return False

    # Ensure 'projects' key exists and is a map
    if data.get('projects') is None:
        data['projects'] = CommentedMap()
    elif not isinstance(data['projects'], dict):
        print(f"Error: 'projects' key in {registry_file} is not a dictionary.")
        return False

    # Add or update the project entry (convert Paths to strings for YAML)
    project_entry = CommentedMap({
        'root_dir': str(root_dir),
        'config_file': str(config_file),
        'enabled': enabled
    })
    data['projects'][project_name] = project_entry

    # Write back to the registry file
    try:
        # Preserve header by reading first few lines if necessary (complex)
        # Simpler: Assume header is managed manually or re-added if file recreated.
        # We rewrite the whole file here.
        write_yaml_file(data, registry_file)
        print(f"Successfully updated registry for project '{project_name}'")
        return True
    except Exception:
        return False  # Error handled in write_yaml_file

# --- Logic from generate_compose.py ---
def generate_compose_logic(mcp_server_dir: Path):
    """
    Generates the final docker-compose.yml by merging base and project configs.
    Corresponds to the logic in the old generate_compose.py.
    
    Args:
        mcp_server_dir (Path): Path to the mcp_server directory
    """
    print("Generating docker-compose.yml...")
    base_compose_path = mcp_server_dir / 'base-compose.yaml'
    projects_registry_path = mcp_server_dir / 'mcp-projects.yaml'
    output_compose_path = mcp_server_dir / 'docker-compose.yml'

    # Load base compose file
    compose_data = load_yaml_file(base_compose_path, safe=False)
    if compose_data is None or not isinstance(compose_data, dict):
        print(f"Error: Failed to load or parse base compose file: {base_compose_path}")
        sys.exit(1)

    if 'services' not in compose_data or not isinstance(compose_data.get('services'), dict):
        print(f"Error: Invalid structure in '{base_compose_path}'. Missing 'services' dictionary.")
        sys.exit(1)

    # Load project registry safely
    projects_registry = load_yaml_file(projects_registry_path, safe=True)
    if projects_registry is None:
        print(f"Warning: Project registry file '{projects_registry_path}' not found or failed to parse. No custom services will be added.")
        projects_registry = {'projects': {}}
    elif 'projects' not in projects_registry or not isinstance(projects_registry['projects'], dict):
        print(f"Warning: Invalid format or missing 'projects' key in '{projects_registry_path}'. No custom services will be added.")
        projects_registry = {'projects': {}}

    # --- Generate Custom Service Definitions ---
    services_map = compose_data['services']  # Should be CommentedMap

    # Find the anchor object for merging
    custom_base_anchor_obj = compose_data.get('x-graphiti-mcp-custom-base')
    if not custom_base_anchor_obj:
        print(f"{RED}Error: Could not find 'x-graphiti-mcp-custom-base' definition in {base_compose_path}.{NC}")
        sys.exit(1)

    overall_service_index = 0
    # Iterate through projects from the registry
    for project_name, project_data in projects_registry.get('projects', {}).items():
        if not isinstance(project_data, dict) or not project_data.get('enabled', False):
            continue  # Skip disabled or invalid projects

        project_config_path_str = project_data.get('config_file')
        project_root_dir_str = project_data.get('root_dir')

        if not project_config_path_str or not project_root_dir_str:
            print(f"Warning: Skipping project '{project_name}' due to missing 'config_file' or 'root_dir'.")
            continue

        project_config_path = Path(project_config_path_str)
        project_root_dir = Path(project_root_dir_str)

        # Load the project's specific mcp-config.yaml
        project_config = load_yaml_file(project_config_path, safe=True)
        if project_config is None:
            print(f"Warning: Skipping project '{project_name}' because config file '{project_config_path}' could not be loaded.")
            continue

        if 'services' not in project_config or not isinstance(project_config['services'], list):
            print(f"Warning: Skipping project '{project_name}' due to missing or invalid 'services' list in '{project_config_path}'.")
            continue

        # Iterate through services defined in the project's config
        for server_conf in project_config['services']:
            if not isinstance(server_conf, dict):
                print(f"Warning: Skipping invalid service entry in '{project_config_path}': {server_conf}")
                continue

            server_id = server_conf.get('id')
            entity_type_dir = server_conf.get('entity_dir')  # Relative path within project

            if not server_id or not entity_type_dir:
                print(f"Warning: Skipping service in '{project_name}' due to missing 'id' or 'entity_dir': {server_conf}")
                continue

            # --- Determine Service Configuration ---
            service_name = f"mcp-{server_id}"
            container_name = server_conf.get('container_name', service_name)  # Default to service_name
            port_default = server_conf.get('port_default', DEFAULT_PORT_START + overall_service_index + 1)
            port_mapping = f"{port_default}:${{{DEFAULT_MCP_CONTAINER_PORT_VAR}}}"  # Use f-string

            # --- Build Service Definition using CommentedMap ---
            new_service = CommentedMap()
            # Add the merge key first using the anchor object
            new_service.add_yaml_merge([(0, custom_base_anchor_obj)])  # Merge base config

            new_service['container_name'] = container_name
            new_service['ports'] = [port_mapping]  # Ports must be a list

            # --- Environment Variables ---
            env_vars = CommentedMap()  # Use CommentedMap to preserve order if needed
            mcp_group_id = server_conf.get('group_id', project_name)  # Default group_id to project_name
            env_vars['MCP_GROUP_ID'] = mcp_group_id
            env_vars['MCP_USE_CUSTOM_ENTITIES'] = 'true'  # Assume true if defined here

            # Calculate absolute host path for entity volume mount
            abs_host_entity_path = (project_root_dir / entity_type_dir).resolve()
            if not abs_host_entity_path.is_dir():
                print(f"Warning: Entity directory '{abs_host_entity_path}' for service '{service_name}' does not exist. Volume mount might fail.")
                # Continue anyway, Docker will create an empty dir inside container if host path doesn't exist

            # Set container path for entity directory env var
            env_vars['MCP_ENTITY_TYPE_DIR'] = PROJECT_CONTAINER_ENTITY_PATH

            # Add project-specific environment variables from mcp-config.yaml
            project_environment = server_conf.get('environment', {})
            if isinstance(project_environment, dict):
                env_vars.update(project_environment)
            else:
                print(f"Warning: Invalid 'environment' section for service '{service_name}' in '{project_config_path}'. Expected a dictionary.")

            new_service['environment'] = env_vars

            # --- Volumes ---
            # Ensure volumes list exists (might be added by anchor merge, check needed?)
            # setdefault is safer if anchor doesn't guarantee 'volumes'
            if 'volumes' not in new_service:
                new_service['volumes'] = []
            elif not isinstance(new_service['volumes'], list):
                print(f"Warning: 'volumes' merged from anchor for service '{service_name}' is not a list. Overwriting.")
                new_service['volumes'] = []

            # Append the entity volume mount (read-only)
            new_service['volumes'].append(f"{abs_host_entity_path}:{PROJECT_CONTAINER_ENTITY_PATH}:ro")

            # --- Add to Services Map ---
            services_map[service_name] = new_service
            overall_service_index += 1

    # --- Write Output File ---
    header = [
        "# Generated by graphiti CLI",
        "# Do not edit this file directly. Modify base-compose.yaml or project-specific mcp-config.yaml files instead.",
        "",
        "# --- Custom MCP Services Info ---",
        f"# Default Ports: Assigned sequentially starting from {DEFAULT_PORT_START + 1}",
        "#              Can be overridden by specifying 'port_default' in project's mcp-config.yaml.",
    ]
    try:
        write_yaml_file(compose_data, output_compose_path, header=header)
        print(f"Successfully generated '{output_compose_path}'.")
    except Exception:
        # Error already printed by write_yaml_file
        sys.exit(1)
