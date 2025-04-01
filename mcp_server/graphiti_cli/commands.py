#!/usr/bin/env python3
"""
Command implementations for the Graphiti CLI tool.
This module contains the functions that are called by the CLI commands.
"""
import sys
import shutil
from pathlib import Path
import os
import re  # For entity name validation

from . import core
from . import yaml_utils

# --- Docker Commands ---

def docker_up(detached: bool, log_level: str):
    """
    Start all containers using Docker Compose (builds first).
    
    Args:
        detached (bool): Whether to run in detached mode
        log_level (str): Log level to use
    """
    core.ensure_docker_compose_file()
    core.ensure_dist_for_build()
    cmd = ["up", "--build", "--force-recreate"]
    core.run_docker_compose(cmd, log_level, detached)
    print(f"{core.GREEN}Docker compose up completed.{core.NC}")

def docker_down(log_level: str):
    """
    Stop and remove all containers using Docker Compose.
    
    Args:
        log_level (str): Log level to use
    """
    core.ensure_docker_compose_file()  # Needed for compose to find project
    core.run_docker_compose(["down"], log_level)
    print(f"{core.GREEN}Docker compose down completed.{core.NC}")

def docker_restart(detached: bool, log_level: str):
    """
    Restart all containers: runs 'down' then 'up'.
    
    Args:
        detached (bool): Whether to run in detached mode
        log_level (str): Log level to use
    """
    print(f"{core.BOLD}Restarting Graphiti containers: first down, then up...{core.NC}")
    docker_down(log_level)  # Run down first
    docker_up(detached, log_level)  # Then run up
    print(f"{core.GREEN}Restart sequence completed.{core.NC}")

def docker_reload(service_name: str):
    """
    Restart a specific running service container.
    
    Args:
        service_name (str): Name of the service to reload
    """
    core.ensure_docker_compose_file()
    print(f"{core.BOLD}Attempting to restart service '{core.CYAN}{service_name}{core.NC}'...{core.NC}")
    try:
        # Use check=True to let run_command handle the error printing on failure
        core.run_docker_compose(["restart", service_name], check=True)
        print(f"{core.GREEN}Service '{service_name}' restarted successfully.{core.NC}")
    except Exception:
        # Error message already printed by run_command via CalledProcessError handling
        print(f"{core.RED}Failed to restart service '{service_name}'. Check service name and if stack is running.{core.NC}")
        sys.exit(1)

def docker_compose_generate():
    """
    Generate docker-compose.yml from base and project configs.
    """
    print(f"{core.BOLD}Generating docker-compose.yml from templates...{core.NC}")
    mcp_server_dir = core.get_mcp_server_dir()
    try:
        yaml_utils.generate_compose_logic(mcp_server_dir)
        # Success message printed within generate_compose_logic
    except Exception as e:
        print(f"{core.RED}Error: Failed to generate docker-compose.yml file: {e}{core.NC}")
        sys.exit(1)

# --- Project/File Management Commands ---

def init_project(project_name: str, target_dir: Path):
    """
    Initialize a new Graphiti project.
    
    Args:
        project_name (str): Name of the project
        target_dir (Path): Target directory for the project
    """
    # Basic validation
    if not re.fullmatch(r'^[a-zA-Z0-9_-]+$', project_name):
        print(f"{core.RED}Error: Invalid PROJECT_NAME '{project_name}'. Use only letters, numbers, underscores, and hyphens.{core.NC}")
        sys.exit(1)

    print(f"Initializing Graphiti project '{core.CYAN}{project_name}{core.NC}' in '{core.CYAN}{target_dir}{core.NC}'...")

    # Create ai/graph directory structure
    graph_dir = target_dir / "ai" / "graph"
    try:
        graph_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory structure: {core.CYAN}{graph_dir}{core.NC}")
    except OSError as e:
        print(f"{core.RED}Error creating directory structure {graph_dir}: {e}{core.NC}")
        sys.exit(1)

    # Create mcp-config.yaml in ai/graph directory
    config_path = graph_dir / "mcp-config.yaml"
    config_content = f"""# Configuration for project: {project_name}
services:
  - id: {project_name}-main  # Service ID (used for default naming)
    # container_name: "custom-name"  # Optional: Specify custom container name
    # port_default: 8001             # Optional: Specify custom host port
    group_id: "{project_name}"       # Graph group ID
    entity_dir: "entities"           # Relative path to entity definitions within ai/graph
    # environment:                   # Optional: Add non-secret env vars here
    #   MY_FLAG: "true"
"""
    try:
        config_path.write_text(config_content)
        print(f"Created template {core.CYAN}{config_path}{core.NC}")
    except OSError as e:
        print(f"{core.RED}Error creating config file {config_path}: {e}{core.NC}")
        sys.exit(1)

    # Create entities directory within ai/graph
    entities_dir = graph_dir / "entities"
    try:
        entities_dir.mkdir(exist_ok=True)
        (entities_dir / ".gitkeep").touch(exist_ok=True)  # Create or update timestamp
        print(f"Created entities directory: {core.CYAN}{entities_dir}{core.NC}")
    except OSError as e:
        print(f"{core.RED}Error creating entities directory {entities_dir}: {e}{core.NC}")
        sys.exit(1)

    # Set up rules
    setup_rules(project_name, target_dir)  # Call the rules setup logic

    # Update central registry
    mcp_server_dir = core.get_mcp_server_dir()
    registry_path = mcp_server_dir / "mcp-projects.yaml"
    print(f"Updating central project registry: {core.CYAN}{registry_path}{core.NC}")
    try:
        # Ensure paths are absolute before passing
        success = yaml_utils.update_registry_logic(
            registry_file=registry_path,
            project_name=project_name,
            root_dir=target_dir.resolve(),
            config_file=config_path.resolve(),
            enabled=True
        )
        if not success:
            print(f"{core.RED}Error: Failed to update project registry (see previous errors).{core.NC}")
            sys.exit(1)
    except Exception as e:
        print(f"{core.RED}Error updating project registry: {e}{core.NC}")
        sys.exit(1)

    print(f"{core.GREEN}Graphiti project '{project_name}' initialization complete.{core.NC}")
    print(f"You can now create entity definitions in: {core.CYAN}{entities_dir}{core.NC}")


def setup_rules(project_name: str, target_dir: Path):
    """
    Set up Cursor rules for a project.
    
    Args:
        project_name (str): Name of the project
        target_dir (Path): Target directory for the project
    """
    print(f"Setting up Graphiti Cursor rules for project '{core.CYAN}{project_name}{core.NC}' in {core.CYAN}{target_dir}{core.NC}")
    mcp_server_dir = core.get_mcp_server_dir()
    rules_source_dir = mcp_server_dir / "rules"
    templates_source_dir = rules_source_dir / "templates"
    cursor_rules_dir = target_dir / ".cursor" / "rules" / "graphiti"

    try:
        cursor_rules_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created/verified rules directory: {core.CYAN}{cursor_rules_dir}{core.NC}")

        core_rule_src = rules_source_dir / "graphiti-mcp-core-rules.md"
        maint_rule_src = rules_source_dir / "graphiti-knowledge-graph-maintenance.md"
        schema_template_src = templates_source_dir / "project_schema_template.md"

        core_rule_link = cursor_rules_dir / "graphiti-mcp-core-rules.mdc"
        maint_rule_link = cursor_rules_dir / "graphiti-knowledge-graph-maintenance.mdc"
        target_schema_file = cursor_rules_dir / f"graphiti-{project_name}-schema.mdc"

        # Check source files
        missing_files = []
        if not core_rule_src.is_file(): missing_files.append(core_rule_src)
        if not maint_rule_src.is_file(): missing_files.append(maint_rule_src)
        if not schema_template_src.is_file(): missing_files.append(schema_template_src)
        if missing_files:
            print(f"{core.RED}Error: Source rule/template files not found:{core.NC}")
            for f in missing_files: print(f"  - {f}")
            sys.exit(1)

        # Create/Update symlinks using relative paths for better portability
        try:
            core_rel_path = os.path.relpath(core_rule_src.resolve(), start=cursor_rules_dir.resolve())
            maint_rel_path = os.path.relpath(maint_rule_src.resolve(), start=cursor_rules_dir.resolve())
        except ValueError:
            # Handle case where paths are on different drives (Windows) - fall back to absolute
            print(f"{core.YELLOW}Warning: Cannot create relative symlink paths (different drives?). Using absolute paths.{core.NC}")
            core_rel_path = core_rule_src.resolve()
            maint_rel_path = maint_rule_src.resolve()

        # Unlink if it exists and is not the correct link target
        if core_rule_link.is_symlink():
            if core_rule_link.readlink() != Path(core_rel_path):
                core_rule_link.unlink()
        elif core_rule_link.exists():  # It exists but isn't a symlink
            core_rule_link.unlink()

        if not core_rule_link.exists():
            core_rule_link.symlink_to(core_rel_path)
            print(f"Linking core rule: {core.CYAN}{core_rule_link.name}{core.NC} -> {core.CYAN}{core_rel_path}{core.NC}")
        else:
            print(f"Core rule link already exists: {core.CYAN}{core_rule_link.name}{core.NC}")

        if maint_rule_link.is_symlink():
            if maint_rule_link.readlink() != Path(maint_rel_path):
                maint_rule_link.unlink()
        elif maint_rule_link.exists():
            maint_rule_link.unlink()

        if not maint_rule_link.exists():
            maint_rule_link.symlink_to(maint_rel_path)
            print(f"Linking maintenance rule: {core.CYAN}{maint_rule_link.name}{core.NC} -> {core.CYAN}{maint_rel_path}{core.NC}")
        else:
            print(f"Maintenance rule link already exists: {core.CYAN}{maint_rule_link.name}{core.NC}")

        # Generate schema file from template
        if target_schema_file.exists():
            print(f"{core.YELLOW}Warning: Project schema file already exists, skipping template generation: {target_schema_file}{core.NC}")
        else:
            print(f"Generating template project schema file: {core.CYAN}{target_schema_file}{core.NC}")
            template_content = schema_template_src.read_text()
            schema_content = template_content.replace("__PROJECT_NAME__", project_name)
            target_schema_file.write_text(schema_content)

        print(f"{core.GREEN}Graphiti Cursor rules setup complete for project '{project_name}'.{core.NC}")

    except OSError as e:
        print(f"{core.RED}Error setting up rules: {e}{core.NC}")
        sys.exit(1)
    except Exception as e:
        print(f"{core.RED}An unexpected error occurred during rule setup: {e}{core.NC}")
        sys.exit(1)


def _to_pascal_case(snake_str: str) -> str:
    """
    Converts snake_case or kebab-case to PascalCase.
    
    Args:
        snake_str (str): String in snake_case or kebab-case
        
    Returns:
        str: String in PascalCase
    """
    parts = re.split('_|-', snake_str)
    return "".join(part.capitalize() for part in parts)


def create_entity_set(entity_name: str, target_dir: Path):
    """
    Create a new entity file directly in a project's entities directory.
    
    Args:
        entity_name (str): Name for the new entity type
        target_dir (Path): Target project root directory
    """
    # Validate entity_name format
    if not re.fullmatch(r'^[a-zA-Z0-9_-]+$', entity_name):
        print(f"{core.RED}Error: Invalid entity name '{entity_name}'. Use only letters, numbers, underscores, and hyphens.{core.NC}")
        sys.exit(1)
        
    # Load project configuration from ai/graph directory
    graph_dir = target_dir / "ai" / "graph"
    config_path = graph_dir / "mcp-config.yaml"
    if not config_path.is_file():
        print(f"{core.RED}Error: Project configuration file not found: {config_path}{core.NC}")
        print(f"Make sure the project has been initialized with 'graphiti init' first.")
        sys.exit(1)
        
    project_config = yaml_utils.load_yaml_file(config_path, safe=True)
    if project_config is None:
        print(f"{core.RED}Error: Failed to load project configuration from: {config_path}{core.NC}")
        sys.exit(1)
        
    # Validate project config structure
    if 'services' not in project_config or not isinstance(project_config['services'], list) or not project_config['services']:
        print(f"{core.RED}Error: Invalid or missing 'services' section in project configuration: {config_path}{core.NC}")
        sys.exit(1)
        
    # Extract the entity directory name from the first service entry
    entity_dir_name = project_config.get('services', [{}])[0].get('entity_dir', 'entities')
    
    # Calculate paths - entities directory directly in graph_dir
    project_entity_dir = graph_dir / entity_dir_name
    
    # Generate file name with the entity class name (without Entity suffix)
    class_name = _to_pascal_case(entity_name)
    entity_file_path = project_entity_dir / f"{class_name}.py"  # Name file after class
    
    # Check if the entity file already exists
    if entity_file_path.exists():
        print(f"{core.RED}Error: Entity file '{class_name}.py' already exists at: {entity_file_path}{core.NC}")
        sys.exit(1)
        
    # Get path to template file from mcp_server
    mcp_server_dir = core.get_mcp_server_dir()
    example_template_path = mcp_server_dir / "entity_types" / "example" / "custom_entity_example.py"
    
    try:
        # Create the project entity directory if it doesn't exist
        project_entity_dir.mkdir(parents=True, exist_ok=True)

        if not example_template_path.is_file():
            print(f"{core.YELLOW}Warning: Template file not found: {example_template_path}{core.NC}")
            print("Creating a minimal entity file instead.")
            minimal_content = f"""from pydantic import BaseModel, Field

class {class_name}(BaseModel):
    \"\"\"Entity definition for '{entity_name}'.\"\"\"

    example_field: str = Field(
        ...,
        description='An example field.',
    )
"""
            entity_file_path.write_text(minimal_content)
        else:
            template_content = example_template_path.read_text()
            # Perform replacements carefully
            content = template_content.replace("class Product(BaseModel):", f"class {class_name}(BaseModel):")
            # Replace descriptions, trying to be specific
            content = content.replace("A Product represents", f"A {class_name} represents")
            content = content.replace("about Products mentioned", f"about {class_name} entities mentioned")
            content = content.replace("product names", f"{entity_name} names")
            content = content.replace("the product belongs", f"the {entity_name} belongs")
            content = content.replace("description of the product", f"description of the {entity_name}")
            # Add more replacements if needed based on the template content

            entity_file_path.write_text(content)
        
        print(f"Created entity file: {core.CYAN}{entity_file_path}{core.NC}")
        print(f"{core.GREEN}Entity '{entity_name}' successfully created.{core.NC}")
        print(f"You can now edit the entity definition in: {core.CYAN}{entity_file_path}{core.NC}")

    except OSError as e:
        print(f"{core.RED}Error creating entity '{entity_name}': {e}{core.NC}")
        sys.exit(1)
    except Exception as e:
        print(f"{core.RED}An unexpected error occurred creating entity '{entity_name}': {e}{core.NC}")
        sys.exit(1)
