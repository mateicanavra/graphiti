#!/usr/bin/env python3
"""
Generate docker-compose.yml by combining base-compose.yaml with custom server definitions
from mcp-projects.yaml using ruamel.yaml to preserve anchors and aliases.
"""

# Use ruamel.yaml instead of pyyaml
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString # For multi-line strings potentially
from ruamel.yaml.comments import CommentedMap # For adding merge keys
import sys
import os

# --- Configuration ---
BASE_COMPOSE_FILE = 'base-compose.yaml'
MCP_PROJECTS_FILE = 'mcp-projects.yaml'
OUTPUT_COMPOSE_FILE = 'docker-compose.yml'
# Default container port used in port mappings for custom servers
DEFAULT_MCP_CONTAINER_PORT_VAR = "MCP_ROOT_CONTAINER_PORT:-8000"
# Starting port number for default calculation
DEFAULT_PORT_START = 8000

# --- Initialize ruamel.yaml ---
# Use the round-trip loader/dumper to preserve structure
yaml = YAML()
yaml.preserve_quotes = True # Optional: Preserve quotes if needed
yaml.indent(mapping=2, sequence=4, offset=2) # Standard Docker Compose indentation

# --- Load Base Docker Compose Structure ---
try:
    with open(BASE_COMPOSE_FILE, 'r') as f:
        # Use ruamel.yaml load
        compose_data = yaml.load(f)
except FileNotFoundError:
    print(f"Error: Base configuration file '{BASE_COMPOSE_FILE}' not found.")
    sys.exit(1)
except Exception as e: # Catch ruamel.yaml errors
    print(f"Error parsing base YAML file '{BASE_COMPOSE_FILE}': {e}")
    sys.exit(1)

if not isinstance(compose_data, dict) or 'services' not in compose_data or not isinstance(compose_data.get('services'), dict):
     print(f"Error: Invalid structure in '{BASE_COMPOSE_FILE}'. Must be a dictionary with a 'services' key.")
     sys.exit(1)

# --- Load Project Registry ---
# Use safe loader for registry data
registry_yaml = YAML(typ='safe')
try:
    with open(MCP_PROJECTS_FILE, 'r') as f:
        projects_registry = registry_yaml.load(f)
except FileNotFoundError:
    print(f"Warning: Project registry file '{MCP_PROJECTS_FILE}' not found. No custom services will be added.")
    projects_registry = {'projects': {}}
except Exception as e: # Catch ruamel.yaml errors
    print(f"Error parsing project registry file '{MCP_PROJECTS_FILE}': {e}")
    sys.exit(1)

if not projects_registry or 'projects' not in projects_registry:
    print(f"Warning: Invalid format or missing 'projects' key in '{MCP_PROJECTS_FILE}'. No custom services will be added.")
    projects_registry = {'projects': {}}


# --- Generate and Add Custom Service Definitions ---
# Ensure 'services' key exists and is a CommentedMap (should be from ruamel load)
if 'services' not in compose_data: compose_data['services'] = CommentedMap()
services_map = compose_data['services']

# Retrieve the object associated with the anchor we want to merge
# We need the actual Python object that &graphiti-mcp-custom-base points to.
# ruamel.yaml stores anchors separately. We need to find the object.
# Let's assume the object is directly accessible via its key in the top-level map.
custom_base_anchor_obj = compose_data.get('x-graphiti-mcp-custom-base')

if not custom_base_anchor_obj:
    print("Error: Could not find the 'x-graphiti-mcp-custom-base' definition in base YAML.")
    sys.exit(1)

overall_service_index = 0
for project_name, project_data in projects_registry.get('projects', {}).items():
    if not project_data.get('enabled', False):
        continue
    
    project_config_path = project_data.get('config_file')
    if not project_config_path:
        print(f"Warning: Skipping project '{project_name}' due to missing config_file path.")
        continue
    
    # Load project config file
    try:
        with open(project_config_path, 'r') as f:
            project_config = registry_yaml.load(f)
    except FileNotFoundError:
        print(f"Warning: Project config file '{project_config_path}' not found for project '{project_name}'. Skipping.")
        continue
    except Exception as e:
        print(f"Error parsing project config file '{project_config_path}' for project '{project_name}': {e}. Skipping.")
        continue
    
    if not project_config or 'services' not in project_config:
        print(f"Warning: Invalid format or missing 'services' key in '{project_config_path}'. No services will be added for project '{project_name}'.")
        continue
    
    for server_conf in project_config.get('services', []):
        if not isinstance(server_conf, dict):
            print(f"Warning: Skipping service in project '{project_name}' as it's not a dictionary: {server_conf}")
            continue

        server_id = server_conf.get('id')
        if not server_id:
            print(f"Warning: Skipping service in project '{project_name}' due to missing required field 'id': {server_conf}")
            continue

        # --- Apply Defaults ---
        entity_type_dir = server_conf.get('entity_dir')
        if not entity_type_dir:
            print(f"Warning: Skipping service '{server_id}' in project '{project_name}' due to missing required field 'entity_dir'.")
            continue
        
        project_root_dir = project_data.get('root_dir')
        if not project_root_dir:
            print(f"Warning: Skipping service '{server_id}' in project '{project_name}' due to missing project root_dir.")
            continue
        
        # --- End Defaults ---

        service_name = f"mcp-{server_id}"
        
        # Get container name from config or use default
        container_name = server_conf.get('container_name')
        if container_name is None:
            container_name = f"mcp-{server_id}"
        
        # Get port from config or use default
        port_default = server_conf.get('port_default')
        if port_default is None:
            port_default = DEFAULT_PORT_START + overall_service_index + 1
        port_mapping = f"{port_default}:${{{DEFAULT_MCP_CONTAINER_PORT_VAR}}}"

        # Use CommentedMap for the service definition to allow adding merge key
        new_service = CommentedMap()
        new_service['container_name'] = container_name
        new_service['ports'] = [port_mapping] # List of ports

        # Create environment map
        env_vars = CommentedMap()
        mcp_group_id = server_conf.get('group_id', server_id)
        env_vars['MCP_GROUP_ID'] = mcp_group_id
        env_vars['MCP_USE_CUSTOM_ENTITIES'] = "true" # Env vars are strings
        
        # Calculate absolute path for entity directory
        abs_host_entity_path = os.path.abspath(os.path.join(project_root_dir, entity_type_dir))
        
        # Define container entity path constant
        CONTAINER_ENTITY_PATH = "/app/project_entities"
        
        # Add volume mount for entity directory
        new_service.setdefault('volumes', []).append(f"{abs_host_entity_path}:{CONTAINER_ENTITY_PATH}:ro")
        
        # Set MCP_ENTITY_TYPE_DIR to container path
        env_vars['MCP_ENTITY_TYPE_DIR'] = CONTAINER_ENTITY_PATH
        
        # Add any project-specific environment variables
        project_environment = server_conf.get('environment', {})
        env_vars.update(project_environment)

        new_service['environment'] = env_vars

        # IMPORTANT: Add the merge key using ruamel.yaml's merge feature
        # We provide the Python object that was defined with the anchor.
        # The list [(0, custom_base_anchor_obj)] means insert merge at index 0
        new_service.add_yaml_merge([(0, custom_base_anchor_obj)])

        # Add the fully constructed service definition to the services map
        services_map[service_name] = new_service
        
        # Increment the overall service index
        overall_service_index += 1


# --- Write the final combined docker-compose.yml ---
try:
    with open(OUTPUT_COMPOSE_FILE, 'w') as f:
        # Add header comment
        header = [
            "# Generated by generate_compose.py",
            "# Do not edit this file directly. Modify base-compose.yaml or project-specific mcp-config.yaml files instead.",
            "",
            "# --- Custom MCP Services Info ---",
            "# Default Ports: Assigned sequentially starting from 8001 (8000 + index + 1)",
            "#              Can be overridden by specifying 'port_default' in project's mcp-config.yaml.",
            "\n" # Add extra newline before YAML content
        ]
        f.write("\n".join(header))

        # Dump the compose data using ruamel.yaml
        yaml.dump(compose_data, f)

    print(f"Successfully generated '{OUTPUT_COMPOSE_FILE}' using ruamel.yaml.")
    print(f"Note: Default ports for custom services start at {DEFAULT_PORT_START + 1} and increment.")
except IOError as e:
    print(f"Error writing output file '{OUTPUT_COMPOSE_FILE}': {e}")
    sys.exit(1)
except Exception as e:
    print(f"An unexpected error occurred during YAML dumping: {e}")
    sys.exit(1)