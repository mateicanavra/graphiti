#!/usr/bin/env python3
"""
Generate docker-compose.yml by combining base-compose.yaml with custom server definitions
from custom_servers.yaml using ruamel.yaml to preserve anchors and aliases.
"""

# Use ruamel.yaml instead of pyyaml
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString # For multi-line strings potentially
from ruamel.yaml.comments import CommentedMap # For adding merge keys
import sys
import os

# --- Configuration ---
BASE_COMPOSE_FILE = 'base-compose.yaml'
CUSTOM_SERVERS_CONFIG_FILE = 'custom_servers.yaml'
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

# --- Load Custom Server Configurations ---
# Use safe loader for config data
custom_yaml = YAML(typ='safe')
try:
    with open(CUSTOM_SERVERS_CONFIG_FILE, 'r') as f:
        custom_config = custom_yaml.load(f)
except FileNotFoundError:
    print(f"Error: Custom servers configuration file '{CUSTOM_SERVERS_CONFIG_FILE}' not found.")
    sys.exit(1)
except Exception as e: # Catch ruamel.yaml errors
    print(f"Error parsing custom servers YAML file '{CUSTOM_SERVERS_CONFIG_FILE}': {e}")
    sys.exit(1)

if not custom_config or 'custom_mcp_servers' not in custom_config:
    print(f"Warning: Invalid format or missing 'custom_mcp_servers' key in '{CUSTOM_SERVERS_CONFIG_FILE}'. No custom services will be added.")
    custom_mcp_servers = []
else:
    custom_mcp_servers = custom_config.get('custom_mcp_servers', [])
    if not isinstance(custom_mcp_servers, list):
        print(f"Warning: 'custom_mcp_servers' in '{CUSTOM_SERVERS_CONFIG_FILE}' is not a list. No custom services will be added.")
        custom_mcp_servers = []


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

for n, server_conf in enumerate(custom_mcp_servers):
    if not isinstance(server_conf, dict):
        print(f"Warning: Skipping item at index {n} in 'custom_mcp_servers' as it's not a dictionary: {server_conf}")
        continue

    server_id = server_conf.get('id')
    if not server_id:
        print(f"Warning: Skipping server config at index {n} due to missing required field 'id': {server_conf}")
        continue

    # --- Apply Defaults ---
    container_name_var = server_conf.get('container', f"{server_id.upper().replace('-', '_')}_CONTAINER_NAME") # Ensure valid env var name
    port_var = server_conf.get('port', f"{server_id.upper().replace('-', '_')}_PORT") # Ensure valid env var name
    default_port_value = DEFAULT_PORT_START + n + 1
    entity_type_dir = server_conf.get('dir', f"entity_types/{server_id}")
    mcp_group_id = server_conf.get('group_id', server_id)
    entity_types = server_conf.get('types')
    # --- End Defaults ---

    service_name = f"mcp-{server_id}"
    port_mapping = f"${{{port_var}:-{default_port_value}}}:${{{DEFAULT_MCP_CONTAINER_PORT_VAR}}}"

    # Use CommentedMap for the service definition to allow adding merge key
    new_service = CommentedMap()
    new_service['container_name'] = f"${{{container_name_var}}}"
    new_service['ports'] = [port_mapping] # List of ports

    # Create environment map
    env_vars = CommentedMap()
    env_vars['MCP_GROUP_ID'] = mcp_group_id
    env_vars['MCP_USE_CUSTOM_ENTITIES'] = "true" # Env vars are strings

    if entity_type_dir is not None:
        env_vars['MCP_ENTITY_TYPE_DIR'] = entity_type_dir
    if entity_types is not None:
        # Handle multi-line strings correctly if needed
        if '\n' in entity_types:
             env_vars['MCP_ENTITY_TYPES'] = LiteralScalarString(entity_types)
        else:
             env_vars['MCP_ENTITY_TYPES'] = entity_types

    new_service['environment'] = env_vars

    # IMPORTANT: Add the merge key using ruamel.yaml's merge feature
    # We provide the Python object that was defined with the anchor.
    # The list [(0, custom_base_anchor_obj)] means insert merge at index 0
    new_service.add_yaml_merge([(0, custom_base_anchor_obj)])

    # Add the fully constructed service definition to the services map
    services_map[service_name] = new_service


# --- Write the final combined docker-compose.yml ---
try:
    with open(OUTPUT_COMPOSE_FILE, 'w') as f:
        # Add header comment
        header = [
            "# Generated by generate_compose.py",
            "# Do not edit this file directly. Modify base-compose.yaml or custom_servers.yaml instead.",
            "",
            "# --- Custom MCP Services Info ---",
            "# Default Ports: Assigned sequentially starting from 8001 (8000 + index + 1)",
            "#              Can be overridden by setting the corresponding <ID>_PORT env var",
            "#              or by specifying a different `port` variable in custom_servers.yaml.",
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