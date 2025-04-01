This file is a merged representation of a subset of the codebase, containing files not matching ignore patterns, combined into a single document by Repomix.

# File Summary

## Purpose
This file contains a packed representation of the entire repository's contents.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching these patterns are excluded: .venv/**, uv.lock, dist/**, .ai/.archive/**, llm_cache/**, scripts/README.md, README.md, docs/**
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)

## Additional Info

# Directory Structure
```
.ai/
  plans/
    refactor-cli-architecture.md
    refactor-cli-plan.md
entity_types/
  base/
    preferences.py
    procedures.py
    requirements.py
  candidates/
    Candidate.py
    Certification.py
    Education.py
    Insight.py
    Skill.py
    WorkExperience.py
  example/
    company_entity.py
    custom_entity_example.py
  graphiti/
    ArchitecturalPattern.py
    DataPipeline.py
    IntegrationPattern.py
    RetrievalMethod.py
    TemporalModel.py
  __init__.py
  entity_registry.py
graphiti_cli/
  commands.py
  core.py
  main.py
  yaml_utils.py
mcp_server.egg-info/
  dependency_links.txt
  entry_points.txt
  PKG-INFO
  requires.txt
  SOURCES.txt
  top_level.txt
rules/
  examples/
    graphiti-example-schema.md
  templates/
    project_schema_template.md
  graphiti-knowledge-graph-maintenance.md
  graphiti-mcp-core-rules.md
.env.example
.python-version
.repomixignore
base-compose.yaml
custom_servers.yaml
docker-compose.yml
Dockerfile
entrypoint.sh
graphiti_mcp_server.py
mcp_config_sse_example.json
mcp_config_stdio_example.json
mcp-projects.yaml
pyproject.toml
repomix.config.json
```

# Files

## File: .ai/plans/refactor-cli-architecture.md
````markdown
Okay, let's refine the architecture proposal for migrating the `graphiti` Bash script to Python, integrating existing Python helpers (`_yaml_helper.py`, `generate_compose.py`), and ensuring it aligns well with your current setup.

We'll aim for a clean, maintainable Python CLI tool using **Typer** for the interface, **ruamel.yaml** for config file handling (as already established), and standard Python libraries (`subprocess`, `pathlib`, `os`, `shutil`) for orchestration.

**Consolidation Strategy:**

1.  **Integrate YAML Logic:** The core logic from `generate_compose.py` (@LINE:1-191) and `_yaml_helper.py` (@LINE:1-111) will be moved into functions within a dedicated `yaml_utils.py` module as part of the new CLI tool package. This eliminates executing them as separate scripts.
2.  **Retain Server Logic:** `graphiti_mcp_server.py` (@LINE:1-780) remains the server application. Its `argparse` logic handles arguments passed _inside_ the container (via `entrypoint.sh`). The new Python CLI tool will _not_ replicate this internal server argument parsing; it focuses on orchestrating Docker and project setup from the host.
3.  **Entity Registry:** `entity_registry.py` (@LINE:1-41) remains part of the server's domain, used during entity loading within the server runtime. The CLI tool doesn't interact with it directly.

**Proposed Python CLI Architecture:**

1.  **New Package Structure (Example):**
    We'll create a dedicated package for the CLI tool. This could live at the repository root or within the existing `scripts/` directory. Let's assume we create `graphiti_cli/` at the root for clarity.

    ```
    mcp-graphiti/
    ├── mcp_server/
    │   ├── entity_types/
    │   ├── rules/
    │   ├── Dockerfile
    │   ├── entrypoint.sh
    │   ├── base-compose.yaml
    │   ├── mcp-projects.yaml
    │   ├── docker-compose.yml  # (Generated)
    │   ├── graphiti_mcp_server.py
    │   ├── entity_registry.py
    │   └── ... (other server files)
    ├── graphiti_cli/           # <--- NEW CLI Package
    │   ├── __init__.py
    │   ├── main.py             # Typer app definition, command entry points
    │   ├── core.py             # Core logic: finding paths, running subprocesses
    │   ├── commands.py         # Command implementations (init, up, down, etc.)
    │   └── yaml_utils.py       # Integrated YAML handling logic
    ├── pyproject.toml          # <--- Modified
    ├── .env.example
    └── ... (other repo files)
    ```

2.  **`pyproject.toml` Modifications:**
    Update your main `pyproject.toml` (@LINE:1-16) (or create one at the root if it doesn't exist there) to include the CLI tool dependencies and define the script entry point.

    ```toml
    # pyproject.toml

    [build-system]
    requires = ["setuptools>=61.0"]
    build-backend = "setuptools.build_meta"

    [project]
    name = "graphiti-mcp-tools" # Name for the installable package containing the CLI
    version = "0.1.0" # Consider syncing with server version or managing independently
    description = "CLI Tools for Graphiti MCP Server Management"
    readme = "README.md"
    requires-python = ">=3.10"
    dependencies = [
        # CLI specific dependencies:
        "typer[all]>=0.9.0", # [all] includes rich for better tracebacks/output
        "ruamel.yaml>=0.17.21",
        "python-dotenv>=1.0.0", # Useful for potentially reading .env in CLI too
        # Add other CLI-specific needs here
    ]
    # Note: Dependencies for the *server* itself (mcp, openai, graphiti-core)
    # might be listed here if you install both server and CLI from the same
    # pyproject.toml, or they could remain separate if the server has its own.
    # For simplicity now, assuming they might be installed together.
    # If separating, remove server deps from here.

    [project.scripts]
    # This makes the 'graphiti' command available after 'pip install .'
    graphiti = "graphiti_cli.main:app"
    ```

    _(Self-correction: Added `build-system` section for modern packaging)_

3.  **`graphiti_cli/main.py` (Entry Point & Typer App):**

    ```python
    # graphiti_cli/main.py
    import typer
    from pathlib import Path
    from typing_extensions import Annotated # Preferred for Typer >= 0.9

    # Import command functions and core utilities
    from . import commands
    from .core import LogLevel, get_repo_root

    # Initialize Typer app
    app = typer.Typer(
        help="CLI for managing Graphiti MCP Server projects and Docker environment.",
        no_args_is_help=True, # Show help if no command is given
        rich_markup_mode="markdown" # Nicer help text formatting
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
            ".", # Default to current directory
            help="Target project root directory.",
            exists=False, # Allow creating the directory
            file_okay=False,
            dir_okay=True,
            writable=True,
            resolve_path=True # Convert to absolute path
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
            ".",
            help="Target project root directory containing ai/graph/mcp-config.yaml.",
            exists=True, # Must exist for entity creation
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
            ".",
            help="Target project root directory.",
            exists=True, # Must exist for rules setup
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
    ```

    _(Self-correction: Using `Annotated` for Typer arguments/options as it's the modern approach. Added `no_args_is_help=True`. Added emojis for fun.)_

4.  **`graphiti_cli/core.py` (Core Utilities):**
    (Similar to the previous proposal, containing `get_repo_root`, `get_mcp_server_dir`, `run_command`, `LogLevel` enum, ANSI colors, etc. No major changes needed here from the previous draft.)

5.  **`graphiti_cli/yaml_utils.py` (Consolidated YAML Logic):**

    ```python
    # graphiti_cli/yaml_utils.py
    import sys
    from pathlib import Path
    from ruamel.yaml import YAML
    from ruamel.yaml.comments import CommentedMap
    import os
    from typing import Optional, List, Dict, Any

    from .core import get_mcp_server_dir, CONTAINER_ENTITY_PATH, DEFAULT_PORT_START, DEFAULT_MCP_CONTAINER_PORT_VAR # Import constants

    # --- YAML Instances ---
    yaml_rt = YAML() # Round-Trip for preserving structure/comments
    yaml_rt.preserve_quotes = True
    yaml_rt.indent(mapping=2, sequence=4, offset=2)

    yaml_safe = YAML(typ='safe') # Safe loader for reading untrusted/simple config

    # --- File Handling ---
    def load_yaml_file(file_path: Path, safe: bool = False) -> Optional[Any]:
        """Loads a YAML file, handling errors."""
        yaml_loader = yaml_safe if safe else yaml_rt
        if not file_path.is_file():
            print(f"Warning: YAML file not found or is not a file: {file_path}")
            return None
        try:
            with file_path.open('r') as f:
                return yaml_loader.load(f)
        except Exception as e:
            print(f"Error parsing YAML file '{file_path}': {e}")
            return None # Or raise specific exception

    def write_yaml_file(data: Any, file_path: Path, header: Optional[List[str]] = None):
         """Writes data to a YAML file using round-trip dumper."""
         try:
             # Ensure parent directory exists
             file_path.parent.mkdir(parents=True, exist_ok=True)
             with file_path.open('w') as f:
                 if header:
                     f.write("\n".join(header) + "\n\n") # Add extra newline
                 yaml_rt.dump(data, f)
         except IOError as e:
             print(f"Error writing YAML file '{file_path}': {e}")
             raise # Re-raise after printing
         except Exception as e:
             print(f"An unexpected error occurred during YAML dumping to '{file_path}': {e}")
             raise

    # --- Logic from _yaml_helper.py ---
    def update_registry_logic(
        registry_file: Path,
        project_name: str,
        root_dir: Path, # Expecting resolved absolute path
        config_file: Path, # Expecting resolved absolute path
        enabled: bool = True
    ) -> bool:
        """
        Updates the central project registry file (mcp-projects.yaml).
        Corresponds to the logic in the old _yaml_helper.py.
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
                 return False # Error handled in write_yaml_file

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
             return False # Error handled in write_yaml_file


    # --- Logic from generate_compose.py ---
    def generate_compose_logic(mcp_server_dir: Path):
        """
        Generates the final docker-compose.yml by merging base and project configs.
        Corresponds to the logic in the old generate_compose.py.
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
        services_map = compose_data['services'] # Should be CommentedMap

        # Find the anchor object for merging
        custom_base_anchor_obj = compose_data.get('x-graphiti-mcp-custom-base')
        if not custom_base_anchor_obj:
            print(f"{RED}Error: Could not find 'x-graphiti-mcp-custom-base' definition in {base_compose_path}.{NC}")
            sys.exit(1)

        overall_service_index = 0
        # Iterate through projects from the registry
        for project_name, project_data in projects_registry.get('projects', {}).items():
            if not isinstance(project_data, dict) or not project_data.get('enabled', False):
                continue # Skip disabled or invalid projects

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
                entity_type_dir = server_conf.get('entity_dir') # Relative path within project

                if not server_id or not entity_type_dir:
                    print(f"Warning: Skipping service in '{project_name}' due to missing 'id' or 'entity_dir': {server_conf}")
                    continue

                # --- Determine Service Configuration ---
                service_name = f"mcp-{server_id}"
                container_name = server_conf.get('container_name', service_name) # Default to service_name
                port_default = server_conf.get('port_default', DEFAULT_PORT_START + overall_service_index + 1)
                port_mapping = f"{port_default}:${{{DEFAULT_MCP_CONTAINER_PORT_VAR}}}" # Use f-string

                # --- Build Service Definition using CommentedMap ---
                new_service = CommentedMap()
                # Add the merge key first using the anchor object
                new_service.add_yaml_merge([(0, custom_base_anchor_obj)]) # Merge base config

                new_service['container_name'] = container_name
                new_service['ports'] = [port_mapping] # Ports must be a list

                # --- Environment Variables ---
                env_vars = CommentedMap() # Use CommentedMap to preserve order if needed
                mcp_group_id = server_conf.get('group_id', project_name) # Default group_id to project_name
                env_vars['MCP_GROUP_ID'] = mcp_group_id
                env_vars['MCP_USE_CUSTOM_ENTITIES'] = 'true' # Assume true if defined here

                # Calculate absolute host path for entity volume mount
                abs_host_entity_path = (project_root_dir / entity_type_dir).resolve()
                if not abs_host_entity_path.is_dir():
                     print(f"Warning: Entity directory '{abs_host_entity_path}' for service '{service_name}' does not exist. Volume mount might fail.")
                     # Continue anyway, Docker will create an empty dir inside container if host path doesn't exist

                # Set container path for entity directory env var
                env_vars['MCP_ENTITY_TYPE_DIR'] = CONTAINER_ENTITY_PATH

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
                new_service['volumes'].append(f"{abs_host_entity_path}:{CONTAINER_ENTITY_PATH}:ro")

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

    ```

    _(Self-correction: Added explicit checks for file existence and type before loading YAML. Ensured paths passed to `update_registry_logic` are absolute. Handled potential non-existence of 'volumes' key after merge. Defaulted `group_id` to `project_name`.)_

6.  **`graphiti_cli/commands.py` (Command Implementations):**
    (This file contains the actual logic called by `main.py`. It imports helpers from `core.py` and `yaml_utils.py`).

        ```python
        # graphiti_cli/commands.py
        import sys
        import shutil
        from pathlib import Path
        import os
        import re # For entity name validation

        from . import core
        from . import yaml_utils

        # --- Docker Commands ---

        def docker_up(detached: bool, log_level: str):
        	core.ensure_docker_compose_file()
        	core.ensure_dist_for_build()
        	cmd = ["up", "--build", "--force-recreate"]
        	core.run_docker_compose(cmd, log_level, detached)
        	print(f"{core.GREEN}Docker compose up completed.{core.NC}")

        def docker_down(log_level: str):
        	core.ensure_docker_compose_file() # Needed for compose to find project
        	core.run_docker_compose(["down"], log_level)
        	print(f"{core.GREEN}Docker compose down completed.{core.NC}")

        def docker_restart(detached: bool, log_level: str):
        	print(f"{core.BOLD}Restarting Graphiti containers: first down, then up...{core.NC}")
        	docker_down(log_level) # Run down first
        	docker_up(detached, log_level) # Then run up
        	print(f"{core.GREEN}Restart sequence completed.{core.NC}")

        def docker_reload(service_name: str):
        	core.ensure_docker_compose_file()
        	print(f"{core.BOLD}Attempting to restart service '{core.CYAN}{service_name}{core.NC}'...{core.NC}")
        	try:
        		# Use check=True to let run_command handle the error printing on failure
        		core.run_docker_compose(["restart", service_name], check=True)
        		print(f"{core.GREEN}Service '{service_name}' restarted successfully.{core.NC}")
        	except SystemExit: # run_command exits on error if check=True
        		# Error message already printed by run_command via CalledProcessError handling
        		print(f"{core.RED}Failed to restart service '{service_name}'. Check service name and if stack is running.{core.NC}")
        		# No need to exit again, run_command already did

        def docker_compose_generate():
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
            Initialize a Graphiti project.

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
      - id: {project_name}-main  # Service ID (used for default naming) # container_name: "custom-name" # Optional: Specify custom container name # port_default: 8001 # Optional: Specify custom host port
        group_id: "{project_name}"  # Graph group ID
        entity_dir: "entities"  # Relative path to entity definitions within ai/graph # environment: # Optional: Add non-secret env vars here # MY_FLAG: "true"
    """
    try:
    target_dir.mkdir(parents=True, exist_ok=True) # Ensure target dir exists
    config_path.write_text(config_content)
    print(f"Created template {core.CYAN}{config_path}{core.NC}")
    except OSError as e:
    print(f"{core.RED}Error creating config file {config_path}: {e}{core.NC}")
    sys.exit(1)

            # Create entities directory within ai/graph
            entities_dir = graph_dir / "entities"
            try:
                entities_dir.mkdir(exist_ok=True)
                (entities_dir / ".gitkeep").touch(exist_ok=True) # Create or update timestamp
                print(f"Created entities directory: {core.CYAN}{entities_dir}{core.NC}")
            except OSError as e:
                print(f"{core.RED}Error creating entities directory {entities_dir}: {e}{core.NC}")
                sys.exit(1)

            # Set up rules
            setup_rules(project_name, target_dir) # Call the rules setup logic

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


        def setup_rules(project_name: str, target_dir: Path):
        	"""Sets up the .cursor/rules directory and symlinks."""
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
        		elif core_rule_link.exists(): # It exists but isn't a symlink
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
        	"""Converts snake_case or kebab-case to PascalCase."""
        	parts = re.split('_|-', snake_str)
        	return "".join(part.capitalize() for part in parts)

        def create_entity_set(set_name: str, target_dir: Path):
            """Creates a new directory and example entity file for an entity set within a project's ai/graph directory."""
            # Validate SET_NAME format
            if not re.fullmatch(r'^[a-zA-Z0-9_-]+$', set_name):
                print(f"{core.RED}Error: Invalid SET_NAME '{set_name}'. Use only letters, numbers, underscores, and hyphens.{core.NC}")
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

            # Calculate paths - use graph_dir as base
            project_entity_base_dir = graph_dir / entity_dir_name
            new_set_dir = project_entity_base_dir / set_name

            if new_set_dir.exists():
                print(f"{core.RED}Error: Entity type set '{set_name}' already exists at: {new_set_dir}{core.NC}")
                sys.exit(1)

            try:
                new_set_dir.mkdir(parents=True)
                print(f"Created entity type set directory: {core.CYAN}{new_set_dir}{core.NC}")

                class_name = _to_pascal_case(set_name) + "Entity" # Add suffix convention
                # Use set_name for lowercase replacements, class_name for class definition
                entity_file_path = new_set_dir / f"{class_name}.py" # Name file after class

                if not example_template_path.is_file():
                    print(f"{core.YELLOW}Warning: Template file not found: {example_template_path}{core.NC}")
                    print("Creating a minimal entity file instead.")
                    minimal_content = f"""from pydantic import BaseModel, Field

        class {class_name}(BaseModel):
        	\"\"\"Example entity for the '{set_name}' set.\"\"\"

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
                    content = content.replace("product names", f"{set_name} names")
                    content = content.replace("the product belongs", f"the {set_name} belongs")
                    content = content.replace("description of the product", f"description of the {set_name}")
                    # Add more replacements if needed based on the template content

                    entity_file_path.write_text(content)
                    print(f"Created entity file using template: {core.CYAN}{entity_file_path}{core.NC}")

                print(f"{core.GREEN}Entity set '{set_name}' successfully created.{core.NC}")

            except OSError as e:
                print(f"{core.RED}Error creating entity set '{set_name}': {e}{core.NC}")
                sys.exit(1)
            except Exception as e:
                print(f"{core.RED}An unexpected error occurred creating entity set '{set_name}': {e}{core.NC}")
                sys.exit(1)

        ```

This completes the `commands.py` file, providing the implementation logic for all the commands defined in `main.py`. Each function orchestrates the necessary steps, calling helpers from `core.py` for process execution and path management, and `yaml_utils.py` for configuration file handling. Error handling is included using `try...except` blocks and checking subprocess results.
````

## File: .ai/plans/refactor-cli-plan.md
````markdown
Okay, here is a step-by-step implementation plan for migrating the `graphiti` Bash script to a Python CLI tool, based on the agreed-upon architecture using Typer. This plan is designed for execution by an expert AI implementation agent.

**Objective:** Replace the existing `scripts/graphiti` Bash script with a new Python-based CLI tool located in `graphiti_cli/`, managed via `pyproject.toml` and using Typer, `ruamel.yaml`, `subprocess`, and `pathlib`. The new tool should replicate the functionality and command-line interface of the original script while integrating the logic of `_yaml_helper.py` and `generate_compose.py`.

**Assumptions:**

1.  The execution agent has write access to the filesystem within the repository.
2.  Python 3.10+ and `pip` (or `uv`) are available in the execution environment.
3.  Docker and Docker Compose V2 are installed and accessible.
4.  The existing code provided (including the proposed Python architecture snippets) is accurate and complete for the migration task.
5.  The agent understands how to install Python packages using `pip install -e .` based on `pyproject.toml`.

**Potential Risks:**

1.  **Subtle Behavioral Differences:** Differences in how subprocesses are handled or paths are resolved between Bash and Python could lead to subtle behavioral changes. Thorough testing is crucial.
2.  **Error Handling:** Python's error handling might expose issues previously masked in the Bash script, or new error conditions might arise.
3.  **Dependency Conflicts:** Ensure CLI dependencies in `pyproject.toml` don't conflict with server dependencies if installed in the same environment.
4.  **Path Resolution:** Consistency in handling absolute vs. relative paths, especially for symlinks and configuration files, needs careful implementation.

**Implementation Plan:**

**Phase 1: Setup and Project Structure** ✅ COMPLETED

1.  **Create CLI Package Directory:** ✅ COMPLETED
    *   Action: Create a new directory named `graphiti_cli` within the `mcp_server` directory (not at the repository root as initially planned).
    *   Files Involved: N/A (creates `mcp_server/graphiti_cli/`)
    *   Acceptance: The `mcp_server/graphiti_cli/` directory exists.
2.  **Create Initial Python Files:** ✅ COMPLETED
    *   Action: Create the following empty Python files within the `mcp_server/graphiti_cli/` directory:
        *   `__init__.py`
        *   `main.py`
        *   `core.py`
        *   `commands.py`
        *   `yaml_utils.py`
    *   Files Involved: `mcp_server/graphiti_cli/__init__.py`, `mcp_server/graphiti_cli/main.py`, `mcp_server/graphiti_cli/core.py`, `mcp_server/graphiti_cli/commands.py`, `mcp_server/graphiti_cli/yaml_utils.py`
    *   Acceptance: All five specified Python files exist within `mcp_server/graphiti_cli/` and are initially empty.
3.  **Update `pyproject.toml`:** ✅ COMPLETED
    *   Action: Modify the `mcp_server/pyproject.toml` file.
        *   Add `typer[all]>=0.9.0` and `python-dotenv>=1.0.0` to the `[project.dependencies]` list.
        *   Add the `[project.scripts]` section as defined in the architecture proposal (`graphiti = "graphiti_cli.main:app"`).
        *   Add the `[build-system]` section.
        *   Add the `[tool.setuptools.packages.find]` section to explicitly include only the `graphiti_cli` package.
    *   Files Involved: `mcp_server/pyproject.toml`
    *   Acceptance: `pyproject.toml` contains the new dependencies, the `[project.scripts]` entry point, and proper package configuration.
4.  **Install Dependencies:** ✅ COMPLETED
    *   Action: Run `pip install -e .` in the `mcp_server` directory. This installs the necessary dependencies (Typer, etc.) and makes the `graphiti` command (defined in `project.scripts`) available in the environment based on the (currently empty) `graphiti_cli` package.
    *   Files Involved: `mcp_server/pyproject.toml`, Python environment `site-packages`.
    *   Acceptance: The command runs without errors. The package is successfully installed in development mode with all dependencies.
    *   Notes: The `graphiti` command currently still points to the original Bash script since our Python implementation files are empty.

**Phase 2: Implement Core and YAML Utilities** ✅ COMPLETED

5.  **Implement Core Utilities (`core.py`):** ✅ COMPLETED
    *   Action: Populate `mcp_server/graphiti_cli/core.py` with the Python code provided in the architecture proposal. This includes:
        *   ANSI color constants.
        *   `LogLevel` enum.
        *   `_find_repo_root()`, `get_repo_root()`, `get_mcp_server_dir()` functions (ensure robust path finding).
        *   `run_command()` function for executing subprocesses reliably.
        *   Additional utilities like `run_docker_compose()`, `ensure_docker_compose_file()`, and `ensure_dist_for_build()`.
    *   Files Involved: `mcp_server/graphiti_cli/core.py`
    *   Acceptance: The file contains the specified functions and constants. Implemented with proper type hints, docstrings, and error handling.
6.  **Implement YAML Utilities (`yaml_utils.py`):** ✅ COMPLETED
    *   Action: Populate `mcp_server/graphiti_cli/yaml_utils.py` with the Python code provided in the architecture proposal. This integrates logic from the old helper scripts:
        *   YAML instance initializations (`yaml_rt`, `yaml_safe`).
        *   `load_yaml_file()`, `write_yaml_file()` helper functions.
        *   `update_registry_logic()` function (ported from `_yaml_helper.py`).
        *   `generate_compose_logic()` function (ported from `generate_compose.py`). Ensure it uses constants/helpers from `core.py` where appropriate.
    *   Files Involved: `mcp_server/graphiti_cli/yaml_utils.py`
    *   Acceptance: The file contains the specified functions. Implemented with proper type hints, docstrings, and error handling.

**Phase 3: Implement Command Logic** ✅ COMPLETED

7.  **Implement Command Logic (`commands.py`):** ✅ COMPLETED
    *   Action: Populate `mcp_server/graphiti_cli/commands.py` with the Python functions corresponding to each CLI command (`docker_up`, `docker_down`, `docker_restart`, `docker_reload`, `docker_compose_generate`, `init_project`, `setup_rules`, `create_entity_set`). Use the provided code from the architecture proposal.
        *   Ensure these functions correctly import and call helpers from `core.py` and `yaml_utils.py`.
        *   Carefully translate file system operations (symlinking in `setup_rules`, directory/file creation in `init_project` and `create_entity_set`) using `pathlib` and `shutil`.
        *   Implement the `ensure_docker_compose_file()` and `ensure_dist_for_build()` logic by calling the relevant functions in `core.py`.
    *   Files Involved: `mcp_server/graphiti_cli/commands.py`, `mcp_server/graphiti_cli/core.py`, `mcp_server/graphiti_cli/yaml_utils.py`
    *   Acceptance: The file contains functions for each command. Code compiles and logical structure matches the Bash script's intent for each command.

**Phase 4: Define CLI Interface** ✅ COMPLETED

8.  **Define Typer App (`main.py`):** ✅ COMPLETED
    *   Action: Populate `mcp_server/graphiti_cli/main.py` with the Typer application setup, callback, and command definitions as provided in the architecture proposal.
        *   Instantiate `typer.Typer()`.
        *   Define the `main_callback` to find the repo root.
        *   Define each command (`@app.command()`) with appropriate arguments (`typer.Argument`) and options (`typer.Option`) using `Annotated`.
        *   Ensure each command function in `main.py` calls the corresponding implementation function in `commands.py`.
    *   Files Involved: `mcp_server/graphiti_cli/main.py`, `mcp_server/graphiti_cli/commands.py`
    *   Acceptance: The file contains the Typer app definition. Running `graphiti --help` should display the list of commands and their options, matching the interface of the old script.

**Phase 5: Cleanup** 🕒 PENDING

9.  **Remove Old Scripts:**
    *   Action: Delete the following files:
        *   `mcp_server/scripts/graphiti` (The original Bash script)
        *   `mcp_server/scripts/_yaml_helper.py`
        *   `mcp_server/generate_compose.py`
    *   Files Involved: `mcp_server/scripts/graphiti`, `mcp_server/scripts/_yaml_helper.py`, `mcp_server/generate_compose.py`
    *   Acceptance: The specified files no longer exist in the repository.

10. **Verify Global Command Path:** (NEW STEP) ✅ COMPLETED
    *   Action: Ensure the `graphiti` command executed from the terminal correctly points to the new Python CLI entry point installed by `pip install -e .` (or equivalent).
        *   Run `which graphiti` (or `type graphiti` depending on shell) to identify the exact script being executed.
        *   Verify this path corresponds to the Python environment where the `mcp-server` package was installed editable.
        *   Check common `PATH` directories (e.g., `/usr/local/bin`, `~/.local/bin`, `~/bin`) for any older conflicting `graphiti` files or symlinks and remove them if found.
    *   Files Involved: Files/symlinks in system `PATH` directories, Python environment's `bin` directory.
    *   Acceptance: The `which graphiti` command resolves to the correct entry point script created by the package installation. No conflicting executables are found earlier in the `PATH`.

**Phase 6: Verification and Testing** 🔄 IN PROGRESS (Requires Re-verification After Cleanup)

11. **Functional Testing (Using Global Command):** (REVISED STEP)
    *   Action: Execute the *globally installed* `graphiti` command (verified in Step 10) for each subcommand and option combination. Verify the outputs and side effects are correct and match the behavior tested previously via `python -m ...`. Re-run key tests:
        *   `graphiti --help` (Verify Python CLI help output)
        *   `graphiti compose` -> Check `docker-compose.yml` generation.
        *   `graphiti up --log-level debug` -> Check build configuration message (should now correctly detect published package), check container logs for DEBUG level.
        *   `graphiti down`
        *   `graphiti init test-py-proj-global ./temp_test_py_proj_global`
        *   `graphiti entity my-global-set ./temp_test_py_proj_global`
        *   `graphiti rules test-py-proj-global ./temp_test_py_proj_global`
        *   `graphiti restart`
        *   `graphiti reload <service_name>`
    *   Files Involved: All CLI files, `mcp-projects.yaml`, `docker-compose.yml`, Docker environment, test project directories.
    *   Acceptance Criteria:
        *   All commands execute using the *global* `graphiti` entry point without Python errors.
        *   The build configuration check (`ensure_dist_for_build`) now correctly identifies the published package based on the saved `pyproject.toml`.
        *   File system and Docker operations are successful and produce the expected results.
        *   Outputs match those observed during module-based testing.

**Next Steps:**
1. Execute Phase 5: Cleanup (Steps 9 & 10).
2. Re-run Phase 6: Verification and Testing (Step 11) using the global command.

## Latest Progress Update

- Successfully tested the `compose` command:
  - The command generated a new `docker-compose.yml` file based on `base-compose.yaml` and `mcp-projects.yaml`.
  - MD5 checksum comparisons confirm that the generated file is identical to previous outputs.
  - Error handling was validated by simulating scenarios with a missing and corrupted `base-compose.yaml` file.
- This progress is part of Phase 6: Verification and Testing of the new Python CLI tool.
- Next planned action: Test the `up` command to start Docker containers.

## Docker Environment Management Progress (April 2025)

- Successfully tested the Docker environment management commands:
  - Fixed a critical environment variable issue by adding `MCP_PORT=8000` to the `.env` file
  - Tested the `down` command to ensure it properly stops and removes all containers
  - Tested the `up` command with the following variants:
    - Basic usage to start containers with default settings
    - Detached mode (`-d` flag) to run containers in the background
    - Custom logging with `--log-level debug` option
  - Verified that the Docker Compose environment variables are correctly passed
  - Confirmed that the build preparation logic works as expected with local wheel files
  
- Findings and observations:
  - The CLI successfully regenerates the `docker-compose.yml` file before each operation
  - Proper error handling is in place for warnings about missing configuration files
  - Environment variable management works correctly for both CLI and container settings
  - The commands match the intended behavior from the original Bash script

- Next steps:
  - Test the `restart` command (combines `down` and `up` operations)
  - Test the `reload` command (for restarting individual services)
  - Complete Phase 6: Verification and Testing
  - Proceed to Phase 5: Cleanup to remove the original scripts
````

## File: entity_types/base/preferences.py
````python
"""Preference entity type for Graphiti MCP Server."""

from pydantic import BaseModel, Field


class Preference(BaseModel):
    """A Preference represents a user's expressed like, dislike, or preference for something.

    Instructions for identifying and extracting preferences:
    1. Look for explicit statements of preference such as "I like/love/enjoy/prefer X" or "I don't like/hate/dislike X"
    2. Pay attention to comparative statements ("I prefer X over Y")
    3. Consider the emotional tone when users mention certain topics
    4. Extract only preferences that are clearly expressed, not assumptions
    5. Categorize the preference appropriately based on its domain (food, music, brands, etc.)
    6. Include relevant qualifiers (e.g., "likes spicy food" rather than just "likes food")
    7. Only extract preferences directly stated by the user, not preferences of others they mention
    8. Provide a concise but specific description that captures the nature of the preference
    """

    category: str = Field(
        ...,
        description="The category of the preference. (e.g., 'Brands', 'Food', 'Music')",
    )
    description: str = Field(
        ...,
        description='Brief description of the preference. Only use information mentioned in the context to write this description.',
    )
````

## File: entity_types/base/procedures.py
````python
"""Procedure entity type for Graphiti MCP Server."""

from pydantic import BaseModel, Field


class Procedure(BaseModel):
    """A Procedure informing the agent what actions to take or how to perform in certain scenarios. Procedures are typically composed of several steps.

    Instructions for identifying and extracting procedures:
    1. Look for sequential instructions or steps ("First do X, then do Y")
    2. Identify explicit directives or commands ("Always do X when Y happens")
    3. Pay attention to conditional statements ("If X occurs, then do Y")
    4. Extract procedures that have clear beginning and end points
    5. Focus on actionable instructions rather than general information
    6. Preserve the original sequence and dependencies between steps
    7. Include any specified conditions or triggers for the procedure
    8. Capture any stated purpose or goal of the procedure
    9. Summarize complex procedures while maintaining critical details
    """

    description: str = Field(
        ...,
        description='Brief description of the procedure. Only use information mentioned in the context to write this description.',
    )
````

## File: entity_types/base/requirements.py
````python
"""Requirement entity type for Graphiti MCP Server."""

from pydantic import BaseModel, Field


class Requirement(BaseModel):
    """A Requirement represents a specific need, feature, or functionality that a product or service must fulfill.

    Always ensure an edge is created between the requirement and the project it belongs to, and clearly indicate on the
    edge that the requirement is a requirement.

    Instructions for identifying and extracting requirements:
    1. Look for explicit statements of needs or necessities ("We need X", "X is required", "X must have Y")
    2. Identify functional specifications that describe what the system should do
    3. Pay attention to non-functional requirements like performance, security, or usability criteria
    4. Extract constraints or limitations that must be adhered to
    5. Focus on clear, specific, and measurable requirements rather than vague wishes
    6. Capture the priority or importance if mentioned ("critical", "high priority", etc.)
    7. Include any dependencies between requirements when explicitly stated
    8. Preserve the original intent and scope of the requirement
    9. Categorize requirements appropriately based on their domain or function
    """

    project_name: str = Field(
        ...,
        description='The name of the project to which the requirement belongs.',
    )
    description: str = Field(
        ...,
        description='Description of the requirement. Only use information mentioned in the context to write this description.',
    )

# No need for explicit registration - will be auto-registered
````

## File: entity_types/candidates/Candidate.py
````python
"""Candidate entity type for Graphiti MCP Server."""

from typing import List, Optional
from pydantic import BaseModel, Field

class Candidate(BaseModel):
    """
    ## AI Persona
    You are a knowledgeable recruitment specialist who extracts candidate profile information from text.
    
    ## Task Definition
    Extract core information about a candidate from the provided text, including their name, 
    contact details, current position, location, and a high-level summary of their background.
    
    ## Context
    This entity represents a job candidate in the recruitment process. It captures the essential 
    identifying and contact information for a person applying for jobs or being considered for 
    positions. This information is typically found in resumes, LinkedIn profiles, or candidate 
    databases.
    
    ## Instructions
    1. Extract the candidate's full name as it appears in the text.
    2. Identify all contact information (email, phone, LinkedIn URL).
    3. Extract their current role/title and company if available.
    4. Note their current location (city, state, country).
    5. Capture years of experience if explicitly mentioned.
    6. Create a brief summary of their professional background.
    7. If information for any field is not present, leave it as None.
    8. Do not fabricate or infer information that is not stated or strongly implied in the text.
    
    ## Output Format
    A Candidate entity with the extracted fields populated according to the information available.
    """
    
    name: str = Field(
        ...,
        description="The candidate's full name (first and last name, and middle name if available)."
    )
    
    email: Optional[str] = Field(
        None, 
        description="The candidate's email address for contact purposes."
    )
    
    phone: Optional[str] = Field(
        None, 
        description="The candidate's phone number for contact purposes."
    )
    
    linkedin_url: Optional[str] = Field(
        None, 
        description="URL to the candidate's LinkedIn profile."
    )
    
    current_title: Optional[str] = Field(
        None, 
        description="The candidate's current job title or position."
    )
    
    current_company: Optional[str] = Field(
        None, 
        description="The company where the candidate is currently employed."
    )
    
    location: Optional[str] = Field(
        None, 
        description="The candidate's current location, typically city and state/country."
    )
    
    years_of_experience: Optional[int] = Field(
        None, 
        description="Total years of professional experience the candidate has, if explicitly stated."
    )
    
    headline: Optional[str] = Field(
        None, 
        description="A short professional headline or title the candidate uses to describe themselves."
    )
    
    summary: Optional[str] = Field(
        None, 
        description="A brief summary of the candidate's background, expertise, and key qualifications."
    ) 

# No need for explicit registration - will be auto-registered
````

## File: entity_types/candidates/Certification.py
````python
"""Certification entity type for Graphiti MCP Server."""

from typing import List, Optional
from pydantic import BaseModel, Field

class Certification(BaseModel):
    """
    ## AI Persona
    You are a professional certification analyst who specializes in identifying and validating industry credentials.
    
    ## Task Definition
    Extract information about professional certifications, licenses, or credentials mentioned in the text, 
    including the certification name, issuing organization, date, and validity status.
    
    ## Context
    This entity represents a professional certification, license, or credential that a candidate has earned. 
    Each certification should be captured as a separate entity. These are typically found in dedicated 
    "Certifications" or "Professional Development" sections of resumes, but may also appear in summaries 
    or alongside education details.
    
    ## Instructions
    1. Extract the full, official name of the certification or credential.
    2. Identify the organization or body that issued the certification.
    3. Determine when the certification was earned or issued.
    4. Note the expiration date or validity period if mentioned.
    5. Capture any identification numbers, versions, or specific levels of the certification.
    6. Record related skills or technologies associated with the certification if mentioned.
    7. Note if the certification is highlighted as particularly significant or relevant.
    8. If information for any field is not present, leave it as None.
    9. Create a separate Certification entity for each distinct credential mentioned.
    
    ## Output Format
    A Certification entity with all available fields populated based on the information provided in the text.
    """
    
    name: str = Field(
        ...,
        description="The full, official name of the certification or credential."
    )
    
    issuing_organization: Optional[str] = Field(
        None, 
        description="The name of the organization or body that issued the certification."
    )
    
    issue_date: Optional[str] = Field(
        None, 
        description="When the certification was earned or issued (format: YYYY-MM or YYYY)."
    )
    
    expiration_date: Optional[str] = Field(
        None, 
        description="When the certification expires, if applicable (format: YYYY-MM or YYYY)."
    )
    
    is_active: Optional[bool] = Field(
        None, 
        description="Whether the certification is currently active/valid (True) or expired (False)."
    )
    
    credential_id: Optional[str] = Field(
        None, 
        description="Any identification number, version, or specific identifier for the certification."
    )
    
    credential_url: Optional[str] = Field(
        None, 
        description="URL to verify or view the certification if mentioned."
    )
    
    related_skills: Optional[List[str]] = Field(
        None, 
        description="Skills or technologies directly associated with this certification."
    )
    
    description: Optional[str] = Field(
        None, 
        description="Any additional details or context about the certification as provided in the source text."
    )

# No need for explicit registration - will be auto-registered
````

## File: entity_types/candidates/Education.py
````python
"""Education entity type for Graphiti MCP Server."""

from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum

class DegreeLevel(str, Enum):
    HIGH_SCHOOL = "high_school"
    ASSOCIATE = "associate"
    BACHELOR = "bachelor"
    MASTER = "master"
    DOCTORATE = "doctorate"
    CERTIFICATE = "certificate"
    DIPLOMA = "diploma"
    OTHER = "other"

class Education(BaseModel):
    """
    ## AI Persona
    You are an educational background analyst who specializes in academic credential verification.
    
    ## Task Definition
    Extract and organize information about a candidate's educational background, including institutions attended, 
    degrees earned, areas of study, and relevant academic achievements.
    
    ## Context
    This entity represents a single educational qualification or program completed by a candidate. Each degree, 
    certificate, or formal educational program should be captured as a separate Education entity. These entries 
    typically appear in the "Education" section of resumes, CVs, or professional profiles.
    
    ## Instructions
    1. Extract the name of the educational institution (university, college, school).
    2. Identify the degree level and type (Bachelor's, Master's, PhD, Certificate, etc.).
    3. Determine the field of study, major, or specialization.
    4. Extract the start and completion dates (year is typically sufficient).
    5. Note any academic achievements mentioned (GPA, honors, class rank, etc.).
    6. Capture relevant coursework if it's highlighted and relevant to the candidate's career goals.
    7. Record any notable projects, thesis topics, or research work if mentioned.
    8. If information for any field is not present, leave it as None.
    9. Create a separate Education entity for each degree or educational program mentioned.
    
    ## Output Format
    An Education entity with all available fields populated based on the information in the text.
    """
    
    institution: str = Field(
        ...,
        description="The name of the educational institution (university, college, school)."
    )
    
    degree_level: DegreeLevel = Field(
        ...,
        description="The level of the degree or educational qualification."
    )
    
    degree_name: Optional[str] = Field(
        None, 
        description="The specific name of the degree (e.g., 'Bachelor of Science', 'Master of Business Administration')."
    )
    
    field_of_study: Optional[str] = Field(
        None, 
        description="The major, specialization, or field of study."
    )
    
    start_date: Optional[str] = Field(
        None, 
        description="When the candidate started this educational program (typically just the year)."
    )
    
    end_date: Optional[str] = Field(
        None, 
        description="When the candidate completed this educational program (or expected completion date)."
    )
    
    is_completed: Optional[bool] = Field(
        None, 
        description="Whether the education has been completed (True) or is still in progress (False)."
    )
    
    gpa: Optional[str] = Field(
        None, 
        description="The Grade Point Average or academic score achieved, if mentioned."
    )
    
    honors: Optional[List[str]] = Field(
        None, 
        description="Any academic honors, distinctions, or awards received during this education."
    )
    
    relevant_coursework: Optional[List[str]] = Field(
        None, 
        description="Specific courses highlighted as relevant to the candidate's career goals."
    )
    
    projects: Optional[List[str]] = Field(
        None, 
        description="Notable academic projects, research, or thesis work completed during this education."
    )
    
    location: Optional[str] = Field(
        None, 
        description="The location (city, state, country) of the educational institution."
    )
    
    summary: str = Field(
        default="Education at an institution",
        description="A brief summary of this education record for entity node representation."
    )

# No need for explicit registration - will be auto-registered
````

## File: entity_types/candidates/Insight.py
````python
"""Insight entity type for Graphiti MCP Server."""

from typing import List, Optional
# Remove datetime import since we'll use string representation instead
# from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class InsightType(str, Enum):
    BEHAVIORAL = "behavioral"
    TECHNICAL = "technical"
    CULTURAL = "cultural"
    COMMUNICATION = "communication"
    MOTIVATION = "motivation"
    LEADERSHIP = "leadership"
    GROWTH = "growth"
    OTHER = "other"

class InsightSource(str, Enum):
    INTERVIEW = "interview"
    RESUME_ANALYSIS = "resume_analysis"
    PORTFOLIO_REVIEW = "portfolio_review"
    REFERENCE_CHECK = "reference_check"
    SKILL_ASSESSMENT = "skill_assessment"
    CONVERSATION = "conversation"
    OTHER = "other"

class Insight(BaseModel):
    """
    ## AI Persona
    You are a perceptive talent evaluator who identifies unique insights about candidates beyond what's explicitly stated in their resume or profile.
    
    ## Task Definition
    Extract or document meaningful insights about candidates that provide deeper understanding of their abilities, potential fit, strengths, or areas for development.
    
    ## Context
    This entity represents a unique insight discovered about a candidate during the recruitment process. Insights go beyond explicit resume data and capture observations, patterns, 
    or conclusions that might influence hiring decisions. These could come from interviews, conversations, resume analysis, or other interactions with the candidate.
    
    ## Instructions
    1. Identify meaningful insights that provide deeper understanding about the candidate.
    2. Categorize the insight by type (behavioral, technical, cultural, etc.).
    3. Specify the source of the insight (interview, resume analysis, conversation, etc.).
    4. Provide a clear, specific description of the insight with supporting context.
    5. Note the date when the insight was observed or identified.
    6. Assess the relevance of this insight to specific roles or positions if applicable.
    7. Record any recommendations or actions that should be taken based on this insight.
    8. If information for any field is not present, leave it as None or use the appropriate default.
    9. Do not fabricate insights; only record observations with sufficient supporting evidence.
    
    ## Output Format
    An Insight entity with description, type, source, and other available attributes populated based on the information observed.
    """
    
    candidate_name: str = Field(
        ...,
        description="The name of the candidate this insight is about."
    )
    
    description: str = Field(
        ...,
        description="A clear, specific description of the insight discovered about the candidate."
    )
    
    insight_type: InsightType = Field(
        ...,
        description="The category or type of insight (behavioral, technical, cultural, communication, motivation, leadership, growth, other)."
    )
    
    source: InsightSource = Field(
        ...,
        description="The source or context where this insight was observed or identified."
    )
    
    date_observed: Optional[str] = Field(
        None, 
        description="The date when this insight was observed or identified (format: YYYY-MM-DD)."
    )
    
    supporting_evidence: Optional[str] = Field(
        None, 
        description="Specific examples, quotes, or observations that support this insight."
    )
    
    relevance_to_roles: Optional[List[str]] = Field(
        None, 
        description="Specific roles or positions for which this insight is particularly relevant."
    )
    
    recommendations: Optional[str] = Field(
        None, 
        description="Any recommendations or actions that should be taken based on this insight."
    )
    
    confidence_level: Optional[int] = Field(
        None, 
        description="Subjective confidence in this insight on a scale of 1-5, with 5 being highest confidence."
    )
    
    tags: Optional[List[str]] = Field(
        None, 
        description="Keywords or tags that can be used to categorize or search for this insight."
    )

# No need for explicit registration - will be auto-registered
````

## File: entity_types/candidates/Skill.py
````python
"""Skill entity type for Graphiti MCP Server."""

from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum

class SkillType(str, Enum):
    TECHNICAL = "technical"
    SOFT = "soft"
    LANGUAGE = "language"
    TOOL = "tool"
    PLATFORM = "platform"
    METHODOLOGY = "methodology"
    DOMAIN = "domain"
    OTHER = "other"

class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    UNKNOWN = "unknown"

class Skill(BaseModel):
    """
    ## AI Persona
    You are a skills assessment specialist who identifies and categorizes professional skills from candidate information.
    
    ## Task Definition
    Extract skills mentioned in the text, categorize them by type, and assess proficiency level when possible.
    
    ## Context
    This entity represents a specific professional skill possessed by a candidate. Skills can include technical abilities 
    (programming languages, tools, platforms), soft skills (communication, leadership), language proficiencies, methodologies, 
    and domain expertise. Skills are typically listed in dedicated "Skills" sections of resumes, but may also be mentioned 
    throughout work experience descriptions, summaries, or project sections.
    
    ## Instructions
    1. Identify distinct skills mentioned in the text.
    2. Categorize each skill by its type (technical, soft, language, tool, platform, methodology, domain, other).
    3. Determine the proficiency level if explicitly stated or strongly implied.
    4. Extract any years of experience with the skill if mentioned.
    5. Note if the skill is explicitly highlighted as a core or key skill.
    6. For technical skills, identify related technologies or platforms if mentioned.
    7. Create a separate Skill entity for each distinct skill identified.
    8. Do not infer skills that aren't explicitly mentioned or strongly implied.
    9. If information for any field is not present, leave it as None or use the appropriate default.
    
    ## Output Format
    A Skill entity with name, type, and other available attributes populated based on the information in the text.
    """
    
    name: str = Field(
        ...,
        description="The name of the skill (e.g., 'Python', 'Project Management', 'Data Analysis')."
    )
    
    skill_type: SkillType = Field(
        ...,
        description="The category or type of skill (technical, soft, language, tool, platform, methodology, domain, other)."
    )
    
    level: Optional[SkillLevel] = Field(
        None, 
        description="The candidate's proficiency level with this skill if mentioned."
    )
    
    years_experience: Optional[int] = Field(
        None, 
        description="Number of years of experience with this skill, if explicitly stated."
    )
    
    is_core_skill: Optional[bool] = Field(
        None, 
        description="Whether this is highlighted as a core or key skill for the candidate."
    )
    
    related_technologies: Optional[List[str]] = Field(
        None, 
        description="For technical skills, other technologies, tools, or platforms mentioned in connection with this skill."
    )
    
    description: Optional[str] = Field(
        None, 
        description="Any additional descriptions or context about the skill as provided in the source text."
    )

# No need for explicit registration - will be auto-registered
````

## File: entity_types/candidates/WorkExperience.py
````python
"""WorkExperience entity type for Graphiti MCP Server."""

from typing import List, Optional
from pydantic import BaseModel, Field

class WorkExperience(BaseModel):
    """
    ## AI Persona
    You are a career history analyst who specializes in extracting work experience details.
    
    ## Task Definition
    Extract comprehensive information about a candidate's work experience from the provided text, 
    including job details, responsibilities, achievements, and technologies used.
    
    ## Context
    This entity represents a single job position or role held by a candidate. Each work experience
    should be captured as a separate entity. This information is typically found in the "Work Experience"
    or "Professional Experience" sections of resumes, CVs, or professional profiles.
    
    ## Instructions
    1. Extract the job title or position held by the candidate.
    2. Identify the name of the company or organization where they worked.
    3. Determine the start and end dates of employment (current position may not have an end date).
    4. Note the location where they worked (city, state, country).
    5. Capture key responsibilities and duties performed in the role.
    6. Extract notable achievements, projects, or accomplishments.
    7. Identify technologies, tools, or methodologies used, if mentioned.
    8. Note any promotions or role changes within the same company, if applicable.
    9. If information for any field is not present, leave it as None.
    10. Create a separate WorkExperience entity for each position mentioned.
    
    ## Output Format
    A WorkExperience entity with all available fields populated based on the information in the text.
    """
    
    job_title: str = Field(
        ...,
        description="The title or position held by the candidate."
    )
    
    company_name: str = Field(
        ...,
        description="The name of the company or organization where the candidate worked."
    )
    
    start_date: Optional[str] = Field(
        None, 
        description="When the candidate started this role (e.g., 'Jan 2020', 'March 2018', '2015')."
    )
    
    end_date: Optional[str] = Field(
        None, 
        description="When the candidate ended this role (e.g., 'Present', 'Current', 'Dec 2022')."
    )
    
    is_current: Optional[bool] = Field(
        None, 
        description="Whether this is the candidate's current position."
    )
    
    location: Optional[str] = Field(
        None, 
        description="Where the job was located (city, state, country)."
    )
    
    responsibilities: Optional[List[str]] = Field(
        None, 
        description="Key responsibilities, duties, or tasks performed in this role."
    )
    
    achievements: Optional[List[str]] = Field(
        None, 
        description="Notable achievements, accomplishments, or successful projects in this role."
    )
    
    technologies_used: Optional[List[str]] = Field(
        None, 
        description="Technologies, tools, frameworks, languages, or methodologies used in this role."
    )
    
    description: Optional[str] = Field(
        None, 
        description="A general description or summary of the role as provided in the source text."
    )
    
    summary: str = Field(
        default="Work experience at a company",
        description="A brief summary of this work experience for entity node representation."
    )

# No need for explicit registration - will be auto-registered
````

## File: entity_types/example/company_entity.py
````python
"""Definition for a Company entity type."""

from pydantic import BaseModel, Field


class Company(BaseModel):
    """
    **AI Persona:** You are an expert entity extraction assistant.
    
    **Task:** Identify and extract information about Companies mentioned in the provided text context.
    A Company represents a business organization.

    **Context:** The user will provide text containing potential mentions of companies.

    **Extraction Instructions:**
    Your goal is to accurately populate the fields (`name`, `industry`) 
    based *only* on information explicitly or implicitly stated in the text.

    1.  **Identify Core Mentions:** Look for explicit mentions of business organizations, corporations, startups, etc.
    2.  **Extract Name:** Identify company names, often proper nouns or capitalized sequences.
    3.  **Extract Industry:** Determine the company's industry (e.g., "Technology", "Retail", "Finance") based on context or explicit mentions.
    4.  **Handle Ambiguity:** If information for a field is missing or unclear, indicate that.

    **Output Format:** Respond with the extracted data structured according to this Pydantic model.
    """

    name: str = Field(
        ...,
        description='The specific name of the company as mentioned in the text.',
    )
    industry: str | None = Field(
        default=None,
        description='The industry the company operates in (e.g., "Technology", "Finance"), if mentioned.',
    )
````

## File: entity_types/example/custom_entity_example.py
````python
"""Example of how to create a custom entity type for Graphiti MCP Server."""

from pydantic import BaseModel, Field


class Product(BaseModel):
    """
    **AI Persona:** You are an expert entity extraction assistant.
    
    **Task:** Identify and extract information about Products mentioned in the provided text context.
    A Product represents a specific good or service that a company offers.

    **Context:** The user will provide text containing potential mentions of products.

    **Extraction Instructions:**
    Your goal is to accurately populate the fields (`name`, `description`, `category`) 
    based *only* on information explicitly or implicitly stated in the text.

    1.  **Identify Core Mentions:** Look for explicit mentions of commercial goods or services.
    2.  **Extract Name:** Identify product names, especially proper nouns, capitalized words, or terms near trademark symbols (™, ®).
    3.  **Extract Description:** Synthesize a concise description using details about features, purpose, pricing, or availability found *only* in the text.
    4.  **Extract Category:** Determine the product category (e.g., "Software", "Hardware", "Service") based on the description or explicit mentions.
    5.  **Refine Details:** Pay attention to specifications, technical details, stated benefits, unique selling points, variations, or models mentioned, and incorporate relevant details into the description.
    6.  **Handle Ambiguity:** If information for a field is missing or unclear in the text, indicate that rather than making assumptions.

    **Output Format:** Respond with the extracted data structured according to this Pydantic model.
    """

    name: str = Field(
        ...,
        description='The specific name of the product as mentioned in the text.',
    )
    description: str = Field(
        ...,
        description='A concise description of the product, synthesized *only* from information present in the provided text context.',
    )
    category: str = Field(
        ...,
        description='The category the product belongs to (e.g., "Electronics", "Software", "Service") based on the text.',
    )
````

## File: entity_types/graphiti/ArchitecturalPattern.py
````python
"""Definition of the ArchitecturalPattern entity type for Graphiti."""

from pydantic import BaseModel, Field
from typing import List, Optional


class ArchitecturalPatternEntity(BaseModel):
    """
    **AI Persona:** You are an expert software architecture analyst.
    
    **Task:** Identify and extract information about architectural patterns used in the Graphiti framework.
    ArchitecturalPatternEntity represents a high-level design pattern, principle, or architectural approach used in the system.

    **Context:** The text will contain descriptions of system architecture, code organization, or design principles.

    **Extraction Instructions:**
    Your goal is to accurately populate the fields about architectural patterns based *only* on information explicitly or implicitly stated in the text.

    1.  **Identify Pattern Mentions:** Look for explicit references to design patterns, architectural styles, or structural organization approaches.
    2.  **Extract Name:** Identify the specific pattern name (e.g., "Dependency Inversion", "Plugin Architecture", "Modular Design").
    3.  **Extract Description:** Synthesize a concise description explaining what the pattern is and how it's used in Graphiti.
    4.  **Extract Benefits:** Note any explicit or implicit benefits mentioned about why this pattern was chosen.
    5.  **Extract Implementation Details:** Capture how the pattern is implemented in the codebase, including key classes or components.
    6.  **Extract Related Components:** Identify which system components or modules implement or are affected by this pattern.
    7.  **Handle Ambiguity:** If information for a field is missing or unclear in the text, leave the optional fields empty.

    **Output Format:** Respond with the extracted data structured according to this Pydantic model.
    """

    name: str = Field(
        ...,
        description='The specific name of the architectural pattern (e.g., "Dependency Inversion", "Plugin Architecture").',
    )
    description: str = Field(
        ...,
        description='A concise description of what the pattern is and how it functions in the system architecture.',
    )
    benefits: Optional[List[str]] = Field(
        None,
        description='The advantages or benefits this pattern provides to the system (e.g., "extensibility", "maintainability").',
    )
    implementation_details: Optional[str] = Field(
        None,
        description='How the pattern is implemented in the codebase, including key classes, interfaces, or components.',
    )
    related_components: Optional[List[str]] = Field(
        None,
        description='System components or modules that implement or are directly affected by this pattern.',
    )
````

## File: entity_types/graphiti/DataPipeline.py
````python
"""Definition of the DataPipeline entity type for Graphiti."""

from pydantic import BaseModel, Field
from typing import List, Optional


class DataPipelineEntity(BaseModel):
    """
    **AI Persona:** You are an expert data engineer and systems analyst.
    
    **Task:** Identify and extract information about data processing pipelines in the Graphiti framework.
    DataPipelineEntity represents a workflow or sequence of operations that transform, process, or move data within the system.

    **Context:** The text will contain descriptions of data flows, ETL processes, or information processing sequences.

    **Extraction Instructions:**
    Your goal is to accurately populate the fields about data pipelines based *only* on information explicitly or implicitly stated in the text.

    1.  **Identify Pipeline Mentions:** Look for descriptions of sequential data processing, transformations, or workflows.
    2.  **Extract Name:** Identify the specific pipeline name or purpose (e.g., "Entity Extraction Pipeline", "Knowledge Graph Update Pipeline").
    3.  **Extract Description:** Synthesize a concise description of the pipeline's overall purpose and function.
    4.  **Extract Stages:** Identify the discrete steps or stages in the pipeline process.
    5.  **Extract Input/Output:** Determine what data enters the pipeline and what results from it.
    6.  **Extract Components:** Note which system components are involved in implementing this pipeline.
    7.  **Handle Ambiguity:** If information for a field is missing or unclear in the text, leave the optional fields empty.

    **Output Format:** Respond with the extracted data structured according to this Pydantic model.
    """

    name: str = Field(
        ...,
        description='The specific name or purpose of the data pipeline (e.g., "Entity Extraction Pipeline").',
    )
    description: str = Field(
        ...,
        description='A concise description of the pipeline\'s overall purpose and function in the system.',
    )
    stages: Optional[List[str]] = Field(
        None,
        description='The discrete steps or stages in the pipeline process, in sequential order.',
    )
    input_data: Optional[str] = Field(
        None,
        description='The type or source of data that enters the pipeline for processing.',
    )
    output_data: Optional[str] = Field(
        None,
        description='The resulting data or artifacts produced by the pipeline.',
    )
    components: Optional[List[str]] = Field(
        None,
        description='System components or modules involved in implementing this pipeline.',
    )
````

## File: entity_types/graphiti/IntegrationPattern.py
````python
"""Definition of the IntegrationPattern entity type for Graphiti."""

from pydantic import BaseModel, Field
from typing import List, Optional


class IntegrationPatternEntity(BaseModel):
    """
    **AI Persona:** You are an expert in systems integration and API design.
    
    **Task:** Identify and extract information about integration patterns used in the Graphiti framework.
    IntegrationPatternEntity represents an approach or technique for connecting Graphiti with external systems, databases, or services.

    **Context:** The text will contain descriptions of how Graphiti interfaces with external components, APIs, or data sources.

    **Extraction Instructions:**
    Your goal is to accurately populate the fields about integration patterns based *only* on information explicitly or implicitly stated in the text.

    1.  **Identify Integration Pattern Mentions:** Look for descriptions of how Graphiti connects to external systems or services.
    2.  **Extract Name:** Identify the specific integration pattern name (e.g., "Plugin Architecture", "API Abstraction Layer").
    3.  **Extract Description:** Synthesize a concise description of how the integration pattern works and what integration need it addresses.
    4.  **Extract Interfaces:** Identify the specific interfaces, APIs, or protocols used by this integration pattern.
    5.  **Extract External Systems:** Note which external systems, services, or databases are integrated using this pattern.
    6.  **Extract Implementation Details:** Capture how the integration is technically implemented in the codebase.
    7.  **Extract Benefits:** Identify the benefits or advantages this integration pattern provides.
    8.  **Handle Ambiguity:** If information for a field is missing or unclear in the text, leave the optional fields empty.

    **Output Format:** Respond with the extracted data structured according to this Pydantic model.
    """

    name: str = Field(
        ...,
        description='The specific name of the integration pattern (e.g., "Plugin Architecture", "API Abstraction Layer").',
    )
    description: str = Field(
        ...,
        description='A concise description of how the integration pattern works and what integration need it addresses.',
    )
    interfaces: Optional[List[str]] = Field(
        None,
        description='The specific interfaces, APIs, or protocols used by this integration pattern.',
    )
    external_systems: Optional[List[str]] = Field(
        None,
        description='External systems, services, or databases that are integrated using this pattern.',
    )
    implementation_details: Optional[str] = Field(
        None,
        description='How the integration is technically implemented in the codebase.',
    )
    benefits: Optional[List[str]] = Field(
        None,
        description='The benefits or advantages this integration pattern provides.',
    )
````

## File: entity_types/graphiti/RetrievalMethod.py
````python
"""Definition of the RetrievalMethod entity type for Graphiti."""

from pydantic import BaseModel, Field
from typing import List, Optional


class RetrievalMethodEntity(BaseModel):
    """
    **AI Persona:** You are an expert in information retrieval and search systems.
    
    **Task:** Identify and extract information about data retrieval methods used in the Graphiti framework.
    RetrievalMethodEntity represents an approach or technique for finding and retrieving information from the knowledge graph.

    **Context:** The text will contain descriptions of search mechanisms, query approaches, or information access methods.

    **Extraction Instructions:**
    Your goal is to accurately populate the fields about retrieval methods based *only* on information explicitly or implicitly stated in the text.

    1.  **Identify Retrieval Method Mentions:** Look for descriptions of search algorithms, querying approaches, or information access techniques.
    2.  **Extract Name:** Identify the specific retrieval method name (e.g., "Semantic Search", "Graph Traversal", "Keyword Matching").
    3.  **Extract Description:** Synthesize a concise description of how the retrieval method works and what problem it solves.
    4.  **Extract Algorithms:** Identify the specific algorithms or techniques employed by this retrieval method.
    5.  **Extract Strengths:** Note any stated advantages or strengths of this retrieval approach.
    6.  **Extract Limitations:** Capture any described limitations or constraints of this method.
    7.  **Extract Use Cases:** Identify specific use cases where this retrieval method is particularly effective.
    8.  **Handle Ambiguity:** If information for a field is missing or unclear in the text, leave the optional fields empty.

    **Output Format:** Respond with the extracted data structured according to this Pydantic model.
    """

    name: str = Field(
        ...,
        description='The specific name of the retrieval method (e.g., "Semantic Search", "Graph Traversal").',
    )
    description: str = Field(
        ...,
        description='A concise description of how the retrieval method works and what information access need it addresses.',
    )
    algorithms: Optional[List[str]] = Field(
        None,
        description='The specific algorithms or techniques employed by this retrieval method.',
    )
    strengths: Optional[List[str]] = Field(
        None,
        description='The advantages or strengths of this retrieval approach.',
    )
    limitations: Optional[List[str]] = Field(
        None,
        description='The limitations or constraints of this retrieval method.',
    )
    use_cases: Optional[List[str]] = Field(
        None,
        description='Specific scenarios or use cases where this retrieval method is particularly effective.',
    )
````

## File: entity_types/graphiti/TemporalModel.py
````python
"""Definition of the TemporalModel entity type for Graphiti."""

from pydantic import BaseModel, Field
from typing import List, Optional


class TemporalModelEntity(BaseModel):
    """
    **AI Persona:** You are an expert in temporal data modeling and time-aware databases.
    
    **Task:** Identify and extract information about temporal data models used in the Graphiti framework.
    TemporalModelEntity represents an approach to modeling data that incorporates time dimensions.

    **Context:** The text will contain descriptions of how time is represented, tracked, and queried in the system.

    **Extraction Instructions:**
    Your goal is to accurately populate the fields about temporal data models based *only* on information explicitly or implicitly stated in the text.

    1.  **Identify Temporal Model Mentions:** Look for descriptions of how time is represented in data structures.
    2.  **Extract Name:** Identify the specific temporal model approach (e.g., "Bi-temporal Model", "Valid-time Tracking").
    3.  **Extract Description:** Synthesize a concise description of how the temporal model works and what problem it solves.
    4.  **Extract Time Dimensions:** Identify which dimensions of time are captured (e.g., system time, valid time, transaction time).
    5.  **Extract Query Capabilities:** Note any information about how temporal data can be queried or retrieved.
    6.  **Extract Implementation:** Capture details about how the temporal model is implemented in the database.
    7.  **Extract Use Cases:** Identify specific use cases or scenarios where this temporal model provides value.
    8.  **Handle Ambiguity:** If information for a field is missing or unclear in the text, leave the optional fields empty.

    **Output Format:** Respond with the extracted data structured according to this Pydantic model.
    """

    name: str = Field(
        ...,
        description='The specific name or type of the temporal model (e.g., "Bi-temporal Model", "Valid-time Tracking").',
    )
    description: str = Field(
        ...,
        description='A concise description of how the temporal model works and what problem it solves.',
    )
    time_dimensions: Optional[List[str]] = Field(
        None,
        description='The dimensions of time that are captured (e.g., "system time", "valid time", "transaction time").',
    )
    query_capabilities: Optional[str] = Field(
        None,
        description='How temporal data can be queried or retrieved, including any special query features.',
    )
    implementation: Optional[str] = Field(
        None,
        description='How the temporal model is implemented in the database or data structures.',
    )
    use_cases: Optional[List[str]] = Field(
        None,
        description='Specific use cases or scenarios where this temporal model provides value.',
    )
````

## File: entity_types/__init__.py
````python
"""Entity Types package.

This package contains entity type definitions for Graphiti MCP Server.
"""

from entity_types.entity_registry import (
    register_entity_type,
    get_entity_types,
    get_entity_type_subset,
)
````

## File: entity_types/entity_registry.py
````python
"""Entity Types Registry for Graphiti MCP Server.

This module provides a registry to manage entity types in a modular way.
"""

from typing import Dict, Type

from pydantic import BaseModel

# Global registry to store entity types
_ENTITY_REGISTRY: Dict[str, Type[BaseModel]] = {}


def register_entity_type(name: str, entity_class: Type[BaseModel]) -> None:
    """Register an entity type with the registry.

    Args:
        name: The name of the entity type
        entity_class: The Pydantic model class for the entity type
    """
    _ENTITY_REGISTRY[name] = entity_class


def get_entity_types() -> Dict[str, Type[BaseModel]]:
    """Get all registered entity types.

    Returns:
        A dictionary mapping entity type names to their Pydantic model classes
    """
    # Return the actual registry reference, not a copy
    return _ENTITY_REGISTRY


def get_entity_type_subset(names: list[str]) -> Dict[str, Type[BaseModel]]:
    """Get a subset of registered entity types.

    Args:
        names: List of entity type names to include

    Returns:
        A dictionary containing only the specified entity types
    """
    return {name: _ENTITY_REGISTRY[name] for name in names if name in _ENTITY_REGISTRY}
````

## File: graphiti_cli/commands.py
````python
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
    core.ensure_docker_compose_file()  # Ensure docker-compose.yml exists before the restart sequence
    core.run_docker_compose(["down"], log_level)
    docker_up(detached, log_level)
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
        core.run_docker_compose(["restart", service_name], log_level=core.LogLevel.info.value)
        print(f"{core.GREEN}Service '{service_name}' restarted successfully.{core.NC}")
    except Exception:
        print(f"{core.RED}Failed to restart service '{service_name}'. Check service name and if stack is running.{core.NC}")
        sys.exit(1)

def docker_compose_generate():
    """
    Generate docker-compose.yml from base and project configs.
    """
    print(f"{core.BOLD}Generating docker-compose.yml from templates...{core.NC}")
    mcp_server_dir = core.get_mcp_server_dir()
    try:
        yaml_utils.generate_compose_logic(mcp_server_dir)  # Generate with default level
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
````

## File: graphiti_cli/core.py
````python
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
    
    # Ensure the docker-compose.yml file exists
    ensure_docker_compose_file()
    
    # Add -d flag if detached mode is requested
    if detached and subcmd[0] in ["up", "restart"]:  # Add restart for consistency
        subcmd.append("-d")
    
    # Prepare full command
    cmd = ["docker", "compose"] + subcmd
    
    print(f"Running Docker Compose from: {CYAN}{mcp_server_dir}{NC}")
    print(f"Command: {' '.join(cmd)}")
    if log_level != LogLevel.info.value:
        print(f"Log level: {CYAN}{log_level}{NC}")
    
    # Execute the command - Pass the log level as an environment variable
    env = {"GRAPHITI_LOG_LEVEL": log_level}
    run_command(cmd, check=True, env=env, cwd=mcp_server_dir)

def ensure_docker_compose_file() -> None:
    """
    Ensure that the docker-compose.yml file exists by generating it if necessary.
    """
    mcp_server_dir = get_mcp_server_dir()
    compose_file = mcp_server_dir / "docker-compose.yml"
    
    # Use our Python utility (to be implemented in yaml_utils.py) instead of the script
    # Will be implemented after yaml_utils.py is created
    from . import yaml_utils
    try:
        yaml_utils.generate_compose_logic(mcp_server_dir)  # Generate with default log level initially
    except Exception as e:
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
````

## File: graphiti_cli/main.py
````python
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
````

## File: graphiti_cli/yaml_utils.py
````python
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
from .core import LogLevel

# Define the distinct path for project-specific entities inside the container
PROJECT_CONTAINER_ENTITY_PATH = "/app/project_entities"

# --- File and Path Constants ---
BASE_COMPOSE_FILENAME = "base-compose.yaml"
PROJECTS_REGISTRY_FILENAME = "mcp-projects.yaml"
DOCKER_COMPOSE_OUTPUT_FILENAME = "docker-compose.yml"

# --- YAML Key Constants ---
# Registry file keys
REGISTRY_PROJECTS_KEY = "projects"
REGISTRY_ROOT_DIR_KEY = "root_dir"
REGISTRY_CONFIG_FILE_KEY = "config_file"
REGISTRY_ENABLED_KEY = "enabled"

# Compose file keys
COMPOSE_SERVICES_KEY = "services"
COMPOSE_CUSTOM_BASE_ANCHOR_KEY = "x-graphiti-mcp-custom-base"
COMPOSE_CONTAINER_NAME_KEY = "container_name"
COMPOSE_PORTS_KEY = "ports"
COMPOSE_ENVIRONMENT_KEY = "environment"
COMPOSE_VOLUMES_KEY = "volumes"

# Project config keys
PROJECT_SERVICES_KEY = "services"
PROJECT_SERVER_ID_KEY = "id"
PROJECT_ENTITY_DIR_KEY = "entity_dir"
PROJECT_CONTAINER_NAME_KEY = "container_name"
PROJECT_PORT_DEFAULT_KEY = "port_default"
PROJECT_GROUP_ID_KEY = "group_id"
PROJECT_ENVIRONMENT_KEY = "environment"

# --- Environment Variable Constants ---
ENV_MCP_GROUP_ID = "MCP_GROUP_ID"
ENV_MCP_USE_CUSTOM_ENTITIES = "MCP_USE_CUSTOM_ENTITIES"
ENV_MCP_USE_CUSTOM_ENTITIES_VALUE = "true"
ENV_MCP_ENTITY_TYPE_DIR = "MCP_ENTITY_TYPE_DIR"

# --- Other Constants ---
SERVICE_NAME_PREFIX = "mcp-"

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
        initial_data = CommentedMap({REGISTRY_PROJECTS_KEY: CommentedMap()})
        try:
            write_yaml_file(initial_data, registry_file, header=header)
        except Exception:
            return False  # Error handled in write_yaml_file

    # Load existing registry data using round-trip loader
    data = load_yaml_file(registry_file, safe=False)
    if data is None:
        print(f"Error: Could not load registry file {registry_file}")
        return False

    if not isinstance(data, dict) or REGISTRY_PROJECTS_KEY not in data:
        print(f"Error: Invalid registry file format in {registry_file}. Missing '{REGISTRY_PROJECTS_KEY}' key.")
        return False

    # Ensure 'projects' key exists and is a map
    if data.get(REGISTRY_PROJECTS_KEY) is None:
        data[REGISTRY_PROJECTS_KEY] = CommentedMap()
    elif not isinstance(data[REGISTRY_PROJECTS_KEY], dict):
        print(f"Error: '{REGISTRY_PROJECTS_KEY}' key in {registry_file} is not a dictionary.")
        return False

    # Add or update the project entry (convert Paths to strings for YAML)
    project_entry = CommentedMap({
        REGISTRY_ROOT_DIR_KEY: str(root_dir),
        REGISTRY_CONFIG_FILE_KEY: str(config_file),
        REGISTRY_ENABLED_KEY: enabled
    })
    data[REGISTRY_PROJECTS_KEY][project_name] = project_entry

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
def generate_compose_logic(
    mcp_server_dir: Path
):
    """
    Generates the final docker-compose.yml by merging base and project configs.
    Corresponds to the logic in the old generate_compose.py.
    
    Args:
        mcp_server_dir (Path): Path to the mcp_server directory
    """
    print("Generating docker-compose.yml...")
    base_compose_path = mcp_server_dir / BASE_COMPOSE_FILENAME
    projects_registry_path = mcp_server_dir / PROJECTS_REGISTRY_FILENAME
    output_compose_path = mcp_server_dir / DOCKER_COMPOSE_OUTPUT_FILENAME

    # Load base compose file
    compose_data = load_yaml_file(base_compose_path, safe=False)
    if compose_data is None or not isinstance(compose_data, dict):
        print(f"Error: Failed to load or parse base compose file: {base_compose_path}")
        sys.exit(1)

    if COMPOSE_SERVICES_KEY not in compose_data or not isinstance(compose_data.get(COMPOSE_SERVICES_KEY), dict):
        print(f"Error: Invalid structure in '{base_compose_path}'. Missing '{COMPOSE_SERVICES_KEY}' dictionary.")
        sys.exit(1)

    # Load project registry safely
    projects_registry = load_yaml_file(projects_registry_path, safe=True)
    if projects_registry is None:
        print(f"Warning: Project registry file '{projects_registry_path}' not found or failed to parse. No custom services will be added.")
        projects_registry = {REGISTRY_PROJECTS_KEY: {}}
    elif REGISTRY_PROJECTS_KEY not in projects_registry or not isinstance(projects_registry[REGISTRY_PROJECTS_KEY], dict):
        print(f"Warning: Invalid format or missing '{REGISTRY_PROJECTS_KEY}' key in '{projects_registry_path}'. No custom services will be added.")
        projects_registry = {REGISTRY_PROJECTS_KEY: {}}

    # --- Generate Custom Service Definitions ---
    services_map = compose_data[COMPOSE_SERVICES_KEY]  # Should be CommentedMap

    # Find the anchor object for merging
    custom_base_anchor_obj = compose_data.get(COMPOSE_CUSTOM_BASE_ANCHOR_KEY)
    if not custom_base_anchor_obj:
        print(f"{RED}Error: Could not find '{COMPOSE_CUSTOM_BASE_ANCHOR_KEY}' definition in {base_compose_path}.{NC}")
        sys.exit(1)

    overall_service_index = 0
    # Iterate through projects from the registry
    for project_name, project_data in projects_registry.get(REGISTRY_PROJECTS_KEY, {}).items():
        if not isinstance(project_data, dict) or not project_data.get(REGISTRY_ENABLED_KEY, False):
            continue  # Skip disabled or invalid projects

        project_config_path_str = project_data.get(REGISTRY_CONFIG_FILE_KEY)
        project_root_dir_str = project_data.get(REGISTRY_ROOT_DIR_KEY)

        if not project_config_path_str or not project_root_dir_str:
            print(f"Warning: Skipping project '{project_name}' due to missing '{REGISTRY_CONFIG_FILE_KEY}' or '{REGISTRY_ROOT_DIR_KEY}'.")
            continue

        project_config_path = Path(project_config_path_str)
        project_root_dir = Path(project_root_dir_str)

        # Load the project's specific mcp-config.yaml
        project_config = load_yaml_file(project_config_path, safe=True)
        if project_config is None:
            print(f"Warning: Skipping project '{project_name}' because config file '{project_config_path}' could not be loaded.")
            continue

        if PROJECT_SERVICES_KEY not in project_config or not isinstance(project_config[PROJECT_SERVICES_KEY], list):
            print(f"Warning: Skipping project '{project_name}' due to missing or invalid '{PROJECT_SERVICES_KEY}' list in '{project_config_path}'.")
            continue

        # Iterate through services defined in the project's config
        for server_conf in project_config[PROJECT_SERVICES_KEY]:
            if not isinstance(server_conf, dict):
                print(f"Warning: Skipping invalid service entry in '{project_config_path}': {server_conf}")
                continue

            server_id = server_conf.get(PROJECT_SERVER_ID_KEY)
            entity_type_dir = server_conf.get(PROJECT_ENTITY_DIR_KEY)  # Relative path within project

            if not server_id or not entity_type_dir:
                print(f"Warning: Skipping service in '{project_name}' due to missing '{PROJECT_SERVER_ID_KEY}' or '{PROJECT_ENTITY_DIR_KEY}': {server_conf}")
                continue

            # --- Determine Service Configuration ---
            service_name = f"{SERVICE_NAME_PREFIX}{server_id}"
            container_name = server_conf.get(PROJECT_CONTAINER_NAME_KEY, service_name)  # Default to service_name
            port_default = server_conf.get(PROJECT_PORT_DEFAULT_KEY, DEFAULT_PORT_START + overall_service_index + 1)
            port_mapping = f"{port_default}:${{{DEFAULT_MCP_CONTAINER_PORT_VAR}}}"  # Use f-string

            # --- Build Service Definition using CommentedMap ---
            new_service = CommentedMap()
            # Add the merge key first using the anchor object
            new_service.add_yaml_merge([(0, custom_base_anchor_obj)])  # Merge base config

            new_service[COMPOSE_CONTAINER_NAME_KEY] = container_name
            new_service[COMPOSE_PORTS_KEY] = [port_mapping]  # Ports must be a list

            # --- Environment Variables ---
            env_vars = CommentedMap()  # Use CommentedMap to preserve order if needed
            mcp_group_id = server_conf.get(PROJECT_GROUP_ID_KEY, project_name)  # Default group_id to project_name
            env_vars[ENV_MCP_GROUP_ID] = mcp_group_id
            env_vars[ENV_MCP_USE_CUSTOM_ENTITIES] = ENV_MCP_USE_CUSTOM_ENTITIES_VALUE  # Assume true if defined here

            # Calculate absolute host path for entity volume mount
            abs_host_entity_path = (project_root_dir / entity_type_dir).resolve()
            if not abs_host_entity_path.is_dir():
                print(f"Warning: Entity directory '{abs_host_entity_path}' for service '{service_name}' does not exist. Volume mount might fail.")
                # Continue anyway, Docker will create an empty dir inside container if host path doesn't exist

            # Set container path for entity directory env var
            env_vars[ENV_MCP_ENTITY_TYPE_DIR] = PROJECT_CONTAINER_ENTITY_PATH

            # Add project-specific environment variables from mcp-config.yaml
            project_environment = server_conf.get(PROJECT_ENVIRONMENT_KEY, {})
            if isinstance(project_environment, dict):
                env_vars.update(project_environment)
            else:
                print(f"Warning: Invalid '{PROJECT_ENVIRONMENT_KEY}' section for service '{service_name}' in '{project_config_path}'. Expected a dictionary.")

            new_service[COMPOSE_ENVIRONMENT_KEY] = env_vars

            # --- Volumes ---
            # Ensure volumes list exists (might be added by anchor merge, check needed?)
            # setdefault is safer if anchor doesn't guarantee 'volumes'
            if COMPOSE_VOLUMES_KEY not in new_service:
                new_service[COMPOSE_VOLUMES_KEY] = []
            elif not isinstance(new_service[COMPOSE_VOLUMES_KEY], list):
                print(f"Warning: '{COMPOSE_VOLUMES_KEY}' merged from anchor for service '{service_name}' is not a list. Overwriting.")
                new_service[COMPOSE_VOLUMES_KEY] = []

            # Append the entity volume mount (read-only)
            new_service[COMPOSE_VOLUMES_KEY].append(f"{abs_host_entity_path}:{PROJECT_CONTAINER_ENTITY_PATH}:ro")

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
````

## File: mcp_server.egg-info/dependency_links.txt
````

````

## File: mcp_server.egg-info/entry_points.txt
````
[console_scripts]
graphiti = graphiti_cli.main:app
````

## File: mcp_server.egg-info/PKG-INFO
````
Metadata-Version: 2.4
Name: mcp-server
Version: 0.1.0
Summary: Graphiti MCP Server
Requires-Python: >=3.10
Description-Content-Type: text/markdown
Requires-Dist: mcp>=1.5.0
Requires-Dist: openai>=1.68.2
Requires-Dist: graphiti-core>=0.8.5
Requires-Dist: ruamel.yaml>=0.17.21
Requires-Dist: typer[all]>=0.9.0
Requires-Dist: python-dotenv>=1.0.0

# Graphiti MCP Server

Graphiti is a framework for building and querying temporally-aware knowledge graphs, specifically tailored for AI agents operating in dynamic environments. Unlike traditional retrieval-augmented generation (RAG) methods, Graphiti continuously integrates user interactions, structured and unstructured enterprise data, and external information into a coherent, queryable graph. The framework supports incremental data updates, efficient retrieval, and precise historical queries without requiring complete graph recomputation, making it suitable for developing interactive, context-aware AI applications.

This is an experimental Model Context Protocol (MCP) server implementation for Graphiti. The MCP server exposes Graphiti's key functionality through the MCP protocol, allowing AI assistants to interact with Graphiti's knowledge graph capabilities.

## Features

The Graphiti MCP server exposes the following key high-level functions of Graphiti:

- **Episode Management**: Add, retrieve, and delete episodes (text, messages, or JSON data)
- **Entity Management**: Search and manage entity nodes and relationships in the knowledge graph
- **Search Capabilities**: Search for facts (edges) and node summaries using semantic and hybrid search
- **Group Management**: Organize and manage groups of related data with group_id filtering
- **Graph Maintenance**: Clear the graph and rebuild indices

## Installation

### Prerequisites

1. Ensure you have Python 3.10 or higher installed.
2. A running Neo4j database (version 5.26 or later required)
3. OpenAI API key for LLM operations

### Setup

1. Clone the repository and navigate to the mcp_server directory
2. Use `uv` to create a virtual environment and install dependencies:

```bash
# Install uv if you don't have it already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create a virtual environment and install dependencies in one step
uv sync
```

## Configuration

The server uses the following environment variables:

- `NEO4J_URI`: URI for the Neo4j database (default: `bolt://localhost:7687`)
- `NEO4J_USER`: Neo4j username (default: `neo4j`)
- `NEO4J_PASSWORD`: Neo4j password (default: `demodemo`)
- `OPENAI_API_KEY`: OpenAI API key (required for LLM operations)
- `OPENAI_BASE_URL`: Optional base URL for OpenAI API
- `MODEL_NAME`: Optional model name to use for LLM inference

You can set these variables in a `.env` file in the project directory.

## Running the Server

To run the Graphiti MCP server directly using `uv`:

```bash
uv run graphiti_mcp_server.py
```

With options:

```bash
uv run graphiti_mcp_server.py --model gpt-4o --transport sse
```

Available arguments:

- `--model`: Specify the model name to use with the LLM client
- `--transport`: Choose the transport method (sse or stdio, default: sse)
- `--group-id`: Set a namespace for the graph (optional)
- `--destroy-graph`: Destroy all Graphiti graphs (use with caution)
- `--use-custom-entities`: Enable entity extraction using the predefined ENTITY_TYPES

## Docker Deployment

The Graphiti MCP server can be deployed using Docker. The Dockerfile uses `uv` for package management, ensuring consistent dependency installation.

### Environment Configuration

Before running the Docker Compose setup, you need to configure the environment variables. You have two options:

1. **Using a .env file** (recommended):

   - Copy the provided `.env.example` file to create a `.env` file:
     ```bash
     cp .env.example .env
     ```
   - Edit the `.env` file to set your OpenAI API key and other configuration options:
     ```
     # Required for LLM operations
     OPENAI_API_KEY=your_openai_api_key_here
     MODEL_NAME=gpt-4o
     # Optional: OPENAI_BASE_URL only needed for non-standard OpenAI endpoints
     # OPENAI_BASE_URL=https://api.openai.com/v1
     ```
   - The Docker Compose setup is configured to use this file if it exists (it's optional)

2. **Using environment variables directly**:
   - You can also set the environment variables when running the Docker Compose command:
     ```bash
     OPENAI_API_KEY=your_key MODEL_NAME=gpt-4o docker compose up
     ```

### Neo4j Configuration

The Docker Compose setup includes a Neo4j container with the following default configuration:

- Username: `neo4j`
- Password: `demodemo`
- URI: `bolt://neo4j:7687` (from within the Docker network)
- Memory settings optimized for development use

## Project-Based Architecture

The Graphiti MCP server uses a centralized, project-based architecture that allows different projects to define their own custom MCP servers while sharing a single Neo4j instance and core server.

### Project Configuration

Each project defines its custom MCP server configuration in an `mcp-config.yaml` file:

```yaml
# Configuration for project: project-name
services:
  - id: project-main         # Service ID (used for default naming)
    # container_name: "custom-name" # Optional: Specify custom container name
    # port_default: 8001           # Optional: Specify custom host port
    group_id: "project-name"     # Graph group ID
    entity_dir: "entities"       # Relative path to entity definitions within project
    # environment:                 # Optional: Add non-secret env vars here
    #   MY_FLAG: "true"
```

### Central Registry

All projects are registered in a central `mcp-projects.yaml` file in the `mcp-server` repository:

```yaml
# Maps project names to their configuration details
projects:
  project-name:
    config_file: /absolute/path/to/project-name/mcp-config.yaml
    root_dir: /absolute/path/to/project-name
    enabled: true
```

### Docker Compose Generation

The system automatically generates a `docker-compose.yml` file based on:
- A base configuration (`base-compose.yaml`)
- All enabled projects in the central registry

This allows multiple projects to share a single Neo4j instance and core MCP server while maintaining isolation between different projects' entity types and data.

### Project Setup

To set up a new project:

```bash
cd /path/to/your/project
/path/to/mcp-server/scripts/graphiti init project-name .
```

This will:
1. Create a template `mcp-config.yaml` in your project directory
2. Create an `entities/` directory for your custom entity definitions
3. Register your project in the central `mcp-projects.yaml` with absolute paths
4. Set up cursor rules in your project

### Running Services

All services are managed centrally from the `mcp-server` directory:

```bash
cd /path/to/mcp-server
./scripts/graphiti compose   # Generate the docker-compose.yml
./scripts/graphiti up -d     # Start all services
./scripts/graphiti down      # Stop all services
./scripts/graphiti restart   # Restart all services
```

### Running Services

To run the Graphiti MCP server with Docker Compose:

```bash
docker compose up
```

Or if you're using an older version of Docker Compose:

```bash
docker-compose up
```

This will start both the Neo4j database and the Graphiti MCP server. The Docker setup:

- Uses `uv` for package management and running the server
- Installs dependencies from the `pyproject.toml` file
- Connects to the Neo4j container using the environment variables
- Exposes the server on port 8000 for HTTP-based SSE transport
- Includes a healthcheck for Neo4j to ensure it's fully operational before starting the MCP server

## Integrating with MCP Clients

### Configuration

To use the Graphiti MCP server with an MCP-compatible client, configure it to connect to the server:

```json
{
  "mcpServers": {
    "graphiti": {
      "transport": "stdio",
      "command": "uv",
      "args": [
        "run",
        "/ABSOLUTE/PATH/TO/graphiti_mcp_server.py",
        "--transport",
        "stdio"
      ],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "demodemo",
        "OPENAI_API_KEY": "${OPENAI_API_KEY}",
        "MODEL_NAME": "gpt-4o"
      }
    }
  }
}
```

For SSE transport (HTTP-based), you can use this configuration:

```json
{
  "mcpServers": {
    "graphiti": {
      "transport": "sse",
      "url": "http://localhost:8000/sse"
    }
  }
}
```

Or start the server with uv and connect to it:

```json
{
  "mcpServers": {
    "graphiti": {
      "command": "uv",
      "args": [
        "run",
        "/ABSOLUTE/PATH/TO/graphiti_mcp_server.py",
        "--transport",
        "sse"
      ],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "demodemo",
        "OPENAI_API_KEY": "${OPENAI_API_KEY}",
        "MODEL_NAME": "gpt-4o"
      }
    }
  }
}
```

## Available Tools

The Graphiti MCP server exposes the following tools:

- `add_episode`: Add an episode to the knowledge graph (supports text, JSON, and message formats)
- `search_nodes`: Search the knowledge graph for relevant node summaries
- `search_facts`: Search the knowledge graph for relevant facts (edges between entities)
- `delete_entity_edge`: Delete an entity edge from the knowledge graph
- `delete_episode`: Delete an episode from the knowledge graph
- `get_entity_edge`: Get an entity edge by its UUID
- `get_episodes`: Get the most recent episodes for a specific group
- `clear_graph`: Clear all data from the knowledge graph and rebuild indices
- `get_status`: Get the status of the Graphiti MCP server and Neo4j connection

For detailed usage instructions, known issues, and best practices, see the [MCP Tools Usage Guide](./docs/MCP_TOOLS_USAGE.md).

## Working with JSON Data

The Graphiti MCP server can process structured JSON data through the `add_episode` tool with `source="json"`. This allows you to automatically extract entities and relationships from structured data:

```
add_episode(
    name="Customer Profile",
    episode_body="{\"company\": {\"name\": \"Acme Technologies\"}, \"products\": [{\"id\": \"P001\", \"name\": \"CloudSync\"}, {\"id\": \"P002\", \"name\": \"DataMiner\"}]}",
    source="json",
    source_description="CRM data"
)
```

## Integrating with the Cursor IDE

To integrate the Graphiti MCP Server with the Cursor IDE, follow these steps:

1. Run the Graphiti MCP server using the SSE transport:

```bash
python graphiti_mcp_server.py --transport sse --use-custom-entities --group-id <your_group_id>
```

Hint: specify a `group_id` to retain prior graph data. If you do not specify a `group_id`, the server will create a new graph

2. Configure Cursor to connect to the Graphiti MCP server.

```json
{
  "mcpServers": {
    "Graphiti": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

3. Add the Graphiti rules to Cursor's User Rules. See [cursor_rules.md](cursor_rules.md) for details.

4. Kick off an agent session in Cursor.

The integration enables AI assistants in Cursor to maintain persistent memory through Graphiti's knowledge graph capabilities.

## Requirements

- Python 3.10 or higher
- Neo4j database (version 5.26 or later required)
- OpenAI API key (for LLM operations and embeddings)
- MCP-compatible client

## License

This project is licensed under the same license as the Graphiti project.
````

## File: mcp_server.egg-info/requires.txt
````
mcp>=1.5.0
openai>=1.68.2
graphiti-core>=0.8.5
ruamel.yaml>=0.17.21
typer[all]>=0.9.0
python-dotenv>=1.0.0
````

## File: mcp_server.egg-info/SOURCES.txt
````
README.md
pyproject.toml
graphiti_cli/__init__.py
graphiti_cli/commands.py
graphiti_cli/core.py
graphiti_cli/main.py
graphiti_cli/yaml_utils.py
mcp_server.egg-info/PKG-INFO
mcp_server.egg-info/SOURCES.txt
mcp_server.egg-info/dependency_links.txt
mcp_server.egg-info/entry_points.txt
mcp_server.egg-info/requires.txt
mcp_server.egg-info/top_level.txt
````

## File: mcp_server.egg-info/top_level.txt
````
graphiti_cli
````

## File: rules/examples/graphiti-example-schema.md
````markdown
---
description: Use this rule when working specifically within the 'example' project context to understand its unique entities (Product, Company), relationships (PRODUCES), and extraction guidelines.
globs: mcp_server/entity_types/example/*.py
alwaysApply: false
---

# Graphiti Schema: Example Project

This document outlines the specific knowledge graph schema for the 'example' project.

**Core Rules Reference:** For general Graphiti tool usage and foundational entity extraction principles, refer to `@graphiti-mcp-core-rules.md`.

**Maintenance:** For rules on how to update *this* schema file, refer to `@graphiti-knowledge-graph-maintenance.md`.

## 1. Defined Entity Types

The following entity types are defined for this project:

*   **`Product`**: Represents a specific good or service offered.
    *   Reference: `@mcp_server/entity_types/example/custom_entity_example.py`
    *   Fields: `name` (str), `description` (str), `category` (str)
*   **`Company`**: Represents a business organization.
    *   Reference: `@mcp_server/entity_types/example/company_entity.py`
    *   Fields: `name` (str), `industry` (str | None)

## 2. Defined Relationships (Facts)

The primary relationship captured in this project is:

*   **Subject:** `Company`
*   **Predicate:** `PRODUCES`
*   **Object:** `Product`

    *Example Fact:* `(Company: 'Acme Corp') --[PRODUCES]-> (Product: 'Widget Pro')`

**Extraction Rule:** When extracting facts of this type, ensure both the Company and Product entities are identified according to their definitions.

## 3. Project-Specific Extraction Guidelines

These guidelines supplement or specialize the instructions within the entity definitions and core rules:

*   **Product Category Inference:** If a `Product`'s category is not explicitly stated but its producing `Company`'s `industry` is known, you *may* infer the category from the industry if it's a direct match (e.g., a Tech company likely produces Software/Hardware). State the inference basis in the extraction reasoning.
*   **Disambiguation:** If multiple companies could produce a mentioned product, prioritize the company most recently discussed or most closely associated with the product description in the context.

## 4. Future Evolution

This schema may be expanded to include other entities (e.g., `Customer`, `Review`) and relationships (e.g., `SELLS`, `REVIEWS`) as the project needs evolve. Follow the process in `@graphiti-knowledge-graph-maintenance.md` to propose changes.
````

## File: rules/templates/project_schema_template.md
````markdown
---
description: Use this rule when working specifically within the '__PROJECT_NAME__' project context to understand its unique entities, relationships, and extraction guidelines.
globs: # Add relevant globs for your project files, e.g., src/**/*.py
alwaysApply: false
---

# Graphiti Schema: __PROJECT_NAME__ Project

This document outlines the specific knowledge graph schema for the '__PROJECT_NAME__' project.

**Core Rules Reference:** For general Graphiti tool usage and foundational entity extraction principles, refer to `@graphiti-mcp-core-rules.mdc`.

**Maintenance:** For rules on how to update *this* schema file, refer to `@graphiti-knowledge-graph-maintenance.mdc`.

---

## 1. Defined Entity Types

*Add definitions for entities specific to the '__PROJECT_NAME__' project here.*
*Reference the entity definition files (e.g., Python classes) if applicable.*

Example:
*   **`MyEntity`**: Description of what this entity represents.
    *   Reference: `@path/to/your/entity/definition.py` (if applicable)
    *   Fields: `field1` (type), `field2` (type)

---

## 2. Defined Relationships (Facts)

*Define the key relationships (subject-predicate-object triples) specific to '__PROJECT_NAME__'.*

Example:
*   **Subject:** `MyEntity`
*   **Predicate:** `RELATED_TO`
*   **Object:** `AnotherEntity`

    *Example Fact:* `(MyEntity: 'Instance A') --[RELATED_TO]-> (AnotherEntity: 'Instance B')`
    *Extraction Rule:* Briefly describe how to identify this relationship.

---

## 3. Project-Specific Extraction Guidelines

*Add any extraction rules or nuances unique to the '__PROJECT_NAME__' project.*
*These guidelines supplement or specialize instructions in entity definitions and core rules.*

Example:
*   **Handling Ambiguity:** How to resolve conflicts when multiple potential entities match.
*   **Inference Rules:** Conditions under which properties can be inferred.

---

## 4. Future Evolution

*Briefly mention potential future directions or areas for schema expansion.*
````

## File: rules/graphiti-knowledge-graph-maintenance.md
````markdown
---
description: Use this rule when you need to propose changes (additions, modifications) to a project's specific knowledge graph schema file (`graphiti-[project-name]-schema.md`).
globs: 
alwaysApply: false
---

# Graphiti Knowledge Graph Maintenance Rules

## 1. Purpose and Scope

This document provides rules for AI agents on how to maintain and update the **project-specific knowledge graph schema file**, typically named `graphiti-[project-name]-schema.md`.

**Goal:** Ensure consistency between the defined project schema, the agent's entity extraction behavior for this project, and the actual structure of the project's knowledge graph over time.

**Key Distinctions:**
- This rule governs the *maintenance* of the project schema.
- For general rules on using Graphiti tools, refer to `@graphiti-mcp-core-rules.md`.
- For the specific entities and relationships of *this* project, refer to `graphiti-[project-name]-schema.md`.

**Scope Limitation:** These rules apply *only* to proposing changes to the project-specific `graphiti-[project-name]-schema.md` file. Do not use these rules to modify `@graphiti-mcp-core-rules.md` or this file itself.

## 2. Primacy of the Project Schema

- The `graphiti-[project-name]-schema.md` file is the **single source of truth** for this project's unique knowledge structure (entities, relationships, properties).
- Specific rules within the project schema **override or specialize** the general guidelines found in `@graphiti-mcp-core-rules.md`.

## 3. When to Consult the Project Schema

You **must** consult the relevant `graphiti-[project-name]-schema.md` file **before**:
- Defining any new entity type or relationship that appears specific to the current project.
- Extracting entities, facts, or relationships based on project-specific requirements mentioned by the user or discovered in project context.
- Answering user questions about the project's established knowledge structure, entities, or relationships.

## 4. Consistency Verification

- Before adding any new entity instance, fact, or relationship that seems specific to the project, **verify** that it conforms to the existing definitions and relationship rules documented in `graphiti-[project-name]-schema.md`.
- If the information doesn't fit the existing schema, proceed to Section 5 (Schema Evolution).

## 5. Schema Evolution and Update Process

Project knowledge schemas are expected to evolve. If you identify a need for a **new** entity type, relationship, property, or a **modification** to an existing one based on user interaction or task requirements:

1.  **Identify the Need:** Clearly determine the required change (e.g., "Need a 'SoftwareComponent' entity type," "Need to add a 'dependency' relationship between 'SoftwareComponent' entities," "Need to add a 'version' property to 'SoftwareComponent'").
2.  **Consult Existing Schema:** Double-check `graphiti-[project-name]-schema.md` to confirm the element truly doesn't exist or needs modification.
3.  **Propose Schema Update:**
    - Formulate a proposed change to the `graphiti-[project-name]-schema.md` file.
    - Define the new/modified element clearly, following the structural best practices (like those derived from the entity templates mentioned in `@graphiti-mcp-core-rules.md`).
    - Format the proposed edit for the `.md` file itself according to the guidelines in `@creating-cursor-rules.mdc`.
    - Include a justification (see Section 6).
    - Use the appropriate tool (e.g., `edit_file`) to propose this change to the `graphiti-[project-name]-schema.md` file.
4.  **Await Outcome:** Wait for the schema update proposal to be accepted or rejected.
5.  **Proceed Based on Outcome:**
    - **If Accepted:** You can now proceed with the original task (e.g., entity extraction, graph update) using the newly defined/modified schema element.
    - **If Rejected:** Do not proceed with adding graph data that violates the established schema. Inform the user if necessary, explaining that the required structure is not defined in the project schema.

## 6. Justification for Schema Changes

- When proposing any change to the `graphiti-[project-name]-schema.md`, provide a brief, clear justification.
- Link the justification directly to the user request, conversation context, or specific information encountered that necessitates the schema change. Example: "Justification: User requested tracking software components and their dependencies, which requires adding a 'SoftwareComponent' entity and a 'dependency' relationship to the project schema."

## 7. Schema Validation (Best Practice)

- Before finalizing a schema change proposal, briefly consider its potential impact:
    - Does the change conflict with existing data in the knowledge graph?
    - Does it align with the overall goals of the project as understood?
    - Does it maintain the clarity and usefulness of the schema?
- Mention any potential conflicts or considerations in your justification if significant.

**Remember:** Maintaining an accurate and consistent project schema is crucial for reliable knowledge management and effective AI assistance within the project context.
````

## File: rules/graphiti-mcp-core-rules.md
````markdown
---
description: Use this rule first for general guidance on using Graphiti MCP server tools (entity extraction, memory). It explains the overall rule structure and links to project-specific schemas and maintenance procedures.
globs: 
alwaysApply: false
---

# Graphiti MCP Tools Guide for AI Agents

## Understanding Graphiti Rule Structure

This document provides the **core, foundational guidelines** for using the Graphiti MCP server tools, including entity extraction and agent memory management via the knowledge graph. These rules apply generally across projects.

For effective project work, be aware of the three key types of Graphiti rules:

1.  **This Core Rule (`@graphiti-mcp-core-rules.md`):** Your starting point for general tool usage and best practices.
2.  **Project-Specific Schema (`graphiti-[project-name]-schema.md`):** Defines the unique entities, relationships, and extraction nuances for a *specific* project. **Always consult the relevant project schema** when working on project-specific tasks. Example: `@graphiti-example-schema.md`.
3.  **Schema Maintenance (`@graphiti-knowledge-graph-maintenance.md`):** Explains the *process* for proposing updates or changes to a project-specific schema file.

**Always prioritize rules in the project-specific schema** if they conflict with these general core rules.

## Entity Extraction Principles

- **Use structured extraction patterns:** Follow the AI persona, task, context, and instructions format in entity definitions.
- **Maintain entity type integrity:** Each entity type should have a clear, unique purpose with non-overlapping definitions.
- **Prefer explicit information:** Extract only what is explicitly or strongly implied in the text; avoid assumptions.
- **Handle ambiguity properly:** If information is missing or uncertain, acknowledge the ambiguity rather than fabricating details.
- **Follow field definitions strictly:** Respect the description and constraints defined for each field in the entity model.

## Creating New Entity Types

- **Utilize the `graphiti add-entities` command:** Create new entity type sets with proper scaffolding.
- **Follow the template pattern:** Use the comprehensive docstring format from `custom_entity_example.py` when defining new entity types.
- **Structure entity classes clearly:** Include AI persona, task definition, context explanation, detailed extraction instructions, and output format.
- **Use descriptive field definitions:** Each field should have clear descriptions using the Field annotations.
- **Document extraction logic:** Include specific instructions for identifying and extracting each required field.

## Agent Memory Management

### Before Starting Any Task

- **Always search first:** Use the `search_nodes` tool to look for relevant preferences and procedures before beginning work.
- **Search for facts too:** Use the `search_facts` tool to discover relationships and factual information that may be relevant to your task.
- **Filter by entity type:** Specify `Preference`, `Procedure`, `Requirement`, or other relevant entity types in your node search to get targeted results.
- **Review all matches:** Carefully examine any preferences, procedures, or facts that match your current task.

### Always Save New or Updated Information

- **Capture requirements and preferences immediately:** When a user expresses a requirement or preference, use `add_episode` to store it right away.
  - _Best practice:_ Split very long requirements into shorter, logical chunks.
- **Be explicit if something is an update to existing knowledge.** Only add what's changed or new to the graph.
- **Document procedures clearly:** When you discover how a user wants things done, record it as a procedure.
- **Record factual relationships:** When you learn about connections between entities, store these as facts.
- **Be specific with categories:** Label entities with clear categories for better retrieval later.

### During Your Work

- **Respect discovered preferences:** Align your work with any preferences you've found.
- **Follow procedures exactly:** If you find a procedure for your current task, follow it step by step.
- **Apply relevant facts:** Use factual information to inform your decisions and recommendations.
- **Stay consistent:** Maintain consistency with previously identified entities, preferences, procedures, and facts.

## Best Practices for Tool Usage

- **Search before suggesting:** Always check if there's established knowledge before making recommendations.
- **Combine node and fact searches:** For complex tasks, search both nodes and facts to build a complete picture.
- **Use `center_node_uuid`:** When exploring related information, center your search around a specific node.
- **Prioritize specific matches:** More specific information takes precedence over general information.
- **Be proactive:** If you notice patterns in user behavior, consider storing them as preferences or procedures.
- **Document your reasoning:** When making extraction or classification decisions, briefly note your reasoning.
- **Handle edge cases gracefully:** Plan for anomalies and develop consistent strategies for handling them.
- **Validate entity coherence:** Ensure extracted entities form a coherent, logically consistent set.
- **Understand parameter behavior:** Be aware of specific tool parameter nuances:
  - For `mcp_graphiti_core_add_episode`, avoid explicitly providing `group_id` as a string—let the system use defaults from command line configuration or generate one automatically.
  - Use episode source types appropriately: 'text' for plain content, 'json' for structured data that should automatically extract entities and relationships, and 'message' for conversation-style content.
- **Leverage advanced search capabilities:** When using search tools:
  - Use hybrid search combining vector similarity, full-text search, and graph traversal.
  - Set appropriate `max_nodes` and `max_facts` to control result volume.
  - Apply `entity` parameter when filtering for specific entity types (e.g., "Preference", "Procedure").
  - Use advanced re-ranking strategies for more contextually relevant results.

## MCP Server Codebase Organization

- **Prefer flat directory structures:** Use consolidated, shallow directory hierarchies over deeply nested ones.
- **Group similar entity types:** Place related entity types within a single directory (e.g., `entity_types/graphiti/`).
- **Follow semantic naming:** Name entity type files according to their semantic type (e.g., `ArchitecturalPattern.py`) rather than using generic names.
- **Remove redundant files:** Keep the codebase clean by removing unnecessary `__init__.py` files in auto-loaded directories.
- **Clean up after reorganization:** Systematically remove empty directories after file restructuring.
- **Maintain proper entity structure:** Ensure all entity types follow the Pydantic model pattern with well-defined fields, descriptions, and extraction instructions.

## Maintaining Context and Continuity

- **Track conversation history:** Reference relevant prior exchanges when making decisions.
- **Build knowledge incrementally:** Add to the graph progressively as new information emerges.
- **Preserve important context:** Identify and retain critical contextual information across sessions.
- **Connect related entities:** Create explicit links between related entities to build a rich knowledge graph.
- **Support iterative refinement:** Allow for progressive improvement of entity definitions and instances.

**Remember:** The knowledge graph is your memory. Use it consistently, respecting the rules outlined here and, more importantly, the specific definitions and guidelines within the relevant `graphiti-[project-name]-schema.md` file for your current project context. Entity extraction should be precise, consistent, and aligned with the structured models defined in the codebase and the project schema.

---

## Background & References

Maintaining a knowledge graph requires diligence. The goal is not just to store data, but to create a useful, accurate, and evolving representation of knowledge.

*   **Graphiti Project:** This MCP server leverages the Graphiti framework. Understanding its core concepts is beneficial.
    *   [Graphiti GitHub Repository](mdc:https:/github.com/getzep/Graphiti)
    *   [Graphiti Documentation & Guides](mdc:https:/help.getzep.com/graphiti)
    *   Graphiti powers [Zep Agent Memory](mdc:https:/www.getzep.com), detailed in the paper: [Zep: A Temporal Knowledge Graph Architecture for Agent Memory](mdc:https:/arxiv.org/abs/2501.13956).
*   **Neo4j Database:** Graphiti uses Neo4j (v5.26+) as its backend storage.
    *   [Neo4j Developer Documentation](mdc:https:/neo4j.com/docs/getting-started/current)
    *   [Neo4j Desktop](mdc:https:/neo4j.com/download) (Recommended for local development)
*   **Knowledge Graph Principles:** Building and maintaining knowledge graphs involves careful planning and iteration.
    *   **Defining Scope & Entities:** Clearly define the purpose, scope, entities, and relationships for your graph. ([Source: pageon.ai](mdc:https:/www.pageon.ai/blog/how-to-build-a-knowledge-graph), [Source: smythos.com](mdc:https:/smythos.com/ai-agents/ai-tutorials/knowledge-graph-tutorial))
    *   **Maintenance & Validation:** Regularly assess the graph's accuracy and usefulness. Ensure data validity and consistency. Schemas evolve, so plan for iteration. ([Source: stardog.com](mdc:https:/www.stardog.com/building-a-knowledge-graph))

Use the specific rules defined in `@graphiti-knowledge-graph-maintenance.md` when proposing changes to project schemas.
````

## File: .env.example
````
# Graphiti MCP Server Environment Configuration

# --- Required Secrets ---
# Neo4j Database Configuration
# These settings are used to connect to your Neo4j database
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_strong_neo4j_password_here

# OpenAI API Configuration
# Required for LLM operations
OPENAI_API_KEY=your_openai_api_key_here
MODEL_NAME=gpt-4o

# --- Optional Configuration ---
# OpenAI Base URL (if not using the standard OpenAI API endpoint)
# OPENAI_BASE_URL=https://api.openai.com/v1

# --- Neo4j Connection Configuration ---
# Host ports - ports exposed on your local machine
NEO4J_HOST_HTTP_PORT=7474
NEO4J_HOST_BOLT_PORT=7687

# Container ports - ports used inside the container (rarely need to change)
# NEO4J_CONTAINER_HTTP_PORT=7474
# NEO4J_CONTAINER_BOLT_PORT=7687

# Neo4j Memory Settings
# NEO4J_HEAP_INITIAL=512m # Initial heap size for Neo4j
# NEO4J_HEAP_MAX=1G # Maximum heap size for Neo4j
# NEO4J_PAGECACHE=512m # Page cache size for Neo4j

# --- MCP Server Configuration ---
# Default internal port used by all MCP servers
MCP_ROOT_CONTAINER_PORT=8000

# Root MCP Server (Required)
MCP_ROOT_CONTAINER_NAME=graphiti-mcp-root
MCP_ROOT_HOST_PORT=8000

# --- Custom MCP Servers (Required if uncommented in docker-compose.yml) ---
# Civilization 7 MCP Server
CIV7_CONTAINER_NAME=mcp-civ7
CIV7_PORT=8001

# Filesystem MCP Server
FILESYSTEM_CONTAINER_NAME=mcp-filesystem
FILESYSTEM_PORT=8002

# Magic Candidates MCP Server
CANDIDATES_CONTAINER_NAME=mcp-candidates
CANDIDATES_PORT=8004

# --- Neo4j Container Name ---
NEO4J_CONTAINER_NAME=graphiti-mcp-neo4j

# --- Logging Configuration ---
GRAPHITI_LOG_LEVEL=info

# --- DANGER ZONE ---
# !!! WARNING !!! UNCOMMENTING AND SETTING THE FOLLOWING VARIABLE TO "true" WILL:
# - PERMANENTLY DELETE ALL DATA in the Neo4j database
# - Affect ALL knowledge graphs, not just a specific group
# - Cannot be undone once executed
# Only uncomment and set to "true" when you specifically need to clear all data
# Always comment out or set back to "false" immediately after use
# NEO4J_DESTROY_ENTIRE_GRAPH=true
````

## File: .python-version
````
3.10
````

## File: .repomixignore
````
# Add patterns to ignore here, one per line
# Example:
# *.log
# tmp/
````

## File: base-compose.yaml
````yaml
# base-compose.yaml
# Base structure for the Docker Compose configuration, including static services and anchors.

version: "3.8"

# --- Base Definitions (Anchors) ---
# Anchors are defined here and will be loaded by the Python script.

x-mcp-healthcheck: &mcp-healthcheck
  test:
    [
      "CMD-SHELL",
      "curl -s -I --max-time 1 http://localhost:${MCP_ROOT_CONTAINER_PORT:-8000}/sse | grep -q 'text/event-stream' || exit 1",
    ]
  interval: 30s
  timeout: 10s
  retries: 5
  start_period: 5s

x-neo4j-connection: &neo4j-connection
  NEO4J_URI: "bolt://neo4j:${NEO4J_CONTAINER_BOLT_PORT:-7687}"
  NEO4J_USER: "${NEO4J_USER}"
  NEO4J_PASSWORD: "${NEO4J_PASSWORD}"

x-mcp-env: &mcp-env
  MODEL_NAME: "${MODEL_NAME:-gpt-4o}"
  OPENAI_API_KEY: ${OPENAI_API_KEY?Please set OPENAI_API_KEY in your .env file}
  OPENAI_BASE_URL: ${OPENAI_BASE_URL:-https://api.openai.com/v1}
  GRAPHITI_LOG_LEVEL: ${GRAPHITI_LOG_LEVEL:-info}
  PATH: "/app:/root/.local/bin:${PATH}"

x-graphiti-mcp-base: &graphiti-mcp-base
  build:
    context: .
    dockerfile: Dockerfile
  env_file:
    - path: .env
      required: true
  environment:
    <<: [*mcp-env, *neo4j-connection] # Aliases refer to anchors above
  healthcheck:
    <<: *mcp-healthcheck             # Alias refers to anchor above
  restart: unless-stopped

x-graphiti-mcp-custom-base: &graphiti-mcp-custom-base
  <<: *graphiti-mcp-base # Alias refers to anchor above
  depends_on:
    neo4j:
      condition: service_healthy
    graphiti-mcp-root:
      condition: service_healthy

# --- Services (Static Ones) ---
services:
  # --- Database ---
  neo4j:
    image: neo4j:5.26.0
    container_name: ${NEO4J_CONTAINER_NAME:-graphiti-mcp-neo4j}
    ports:
      - "${NEO4J_HOST_HTTP_PORT:-7474}:${NEO4J_CONTAINER_HTTP_PORT:-7474}"
      - "${NEO4J_HOST_BOLT_PORT:-7687}:${NEO4J_CONTAINER_BOLT_PORT:-7687}"
    environment:
      - NEO4J_AUTH=${NEO4J_USER?Please set NEO4J_USER in your .env file}/${NEO4J_PASSWORD?Please set NEO4J_PASSWORD in your .env file}
      - NEO4J_server_memory_heap_initial__size=${NEO4J_HEAP_INITIAL:-512m}
      - NEO4J_server_memory_heap_max__size=${NEO4J_HEAP_MAX:-1G}
      - NEO4J_server_memory_pagecache_size=${NEO4J_PAGECACHE:-512m}
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    healthcheck:
      test:
        [
          "CMD",
          "wget",
          "-O",
          "/dev/null",
          "http://localhost:${NEO4J_CONTAINER_HTTP_PORT:-7474}",
        ]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  # --- Root MCP Server (Required) ---
  graphiti-mcp-root:
    <<: *graphiti-mcp-base # Alias refers to anchor above
    container_name: ${MCP_ROOT_CONTAINER_NAME:-graphiti-mcp-root}
    depends_on:
      neo4j:
        condition: service_healthy
    ports:
      - "${MCP_ROOT_HOST_PORT:-8000}:${MCP_ROOT_CONTAINER_PORT:-8000}"
    environment:
      # Specific env vars merged with base env vars via the alias above
      MCP_GROUP_ID: "root"
      MCP_USE_CUSTOM_ENTITIES: "true"
      MCP_ENTITY_TYPE_DIR: "entity_types/base"

# --- Volumes ---
volumes:
  neo4j_data: # Persists Neo4j graph data
  neo4j_logs: # Persists Neo4j logs
````

## File: custom_servers.yaml
````yaml
# custom_servers.yaml
# Configuration for custom Graphiti MCP services.
# Defaults:
# - container variable: <ID>_CONTAINER_NAME (e.g., CIV7_CONTAINER_NAME)
# - port variable: <ID>_PORT (e.g., CIV7_PORT)
# - port default value: 8001, 8002, ... based on order in this list
# - dir: entity_types/<id> (e.g., entity_types/civ7)
# - group_id: <id> (e.g., civ7)

custom_mcp_servers:
  - id: civ7 # Uses default container var (CIV7_CONTAINER_NAME), port var (CIV7_PORT:-8001), dir (entity_types/civ7), group_id (civ7)

  - id: magic-api
  
  - id: filesystem
    # Overriding default dir and setting types
    # Uses default container var (FILESYSTEM_CONTAINER_NAME), port var (FILESYSTEM_PORT:-8002), group_id (filesystem)
    dir: "entity_types/specific_fs" # Override default dir
    types: "Requirement Preference"

  - id: candidates
    # Overriding default group_id and dir explicitly
    # Uses default container var (CANDIDATES_CONTAINER_NAME), port var (CANDIDATES_PORT:-8003)
    group_id: "graphiti-candidates" # Override default group_id
    dir: "entity_types/candidates"  # Explicitly set dir (same as default here, just showing override)
````

## File: docker-compose.yml
````yaml
# Generated by graphiti CLI
# Do not edit this file directly. Modify base-compose.yaml or project-specific mcp-config.yaml files instead.

# --- Custom MCP Services Info ---
# Default Ports: Assigned sequentially starting from 8001
#              Can be overridden by specifying 'port_default' in project's mcp-config.yaml.

# base-compose.yaml
# Base structure for the Docker Compose configuration, including static services and anchors.

version: "3.8"

# --- Base Definitions (Anchors) ---
# Anchors are defined here and will be loaded by the Python script.

x-mcp-healthcheck: &mcp-healthcheck
  test: ["CMD-SHELL", "curl -s -I --max-time 1 http://localhost:${MCP_ROOT_CONTAINER_PORT:-8000}/sse
        | grep -q 'text/event-stream' || exit 1"]
  interval: 30s
  timeout: 10s
  retries: 5
  start_period: 5s

x-neo4j-connection: &neo4j-connection
  NEO4J_URI: "bolt://neo4j:${NEO4J_CONTAINER_BOLT_PORT:-7687}"
  NEO4J_USER: "${NEO4J_USER}"
  NEO4J_PASSWORD: "${NEO4J_PASSWORD}"

x-mcp-env: &mcp-env
  MODEL_NAME: "${MODEL_NAME:-gpt-4o}"
  OPENAI_API_KEY: ${OPENAI_API_KEY?Please set OPENAI_API_KEY in your .env file}
  OPENAI_BASE_URL: ${OPENAI_BASE_URL:-https://api.openai.com/v1}
  GRAPHITI_LOG_LEVEL: ${GRAPHITI_LOG_LEVEL:-info}
  PATH: "/app:/root/.local/bin:${PATH}"

x-graphiti-mcp-base: &graphiti-mcp-base
  build:
    context: .
    dockerfile: Dockerfile
  env_file:
    - path: .env
      required: true
  environment:
    <<: [*mcp-env, *neo4j-connection]
  healthcheck:
    <<: *mcp-healthcheck
                                     # Alias refers to anchor above
  restart: unless-stopped

x-graphiti-mcp-custom-base: &graphiti-mcp-custom-base
  <<: *graphiti-mcp-base
                         # Alias refers to anchor above
  depends_on:
    neo4j:
      condition: service_healthy
    graphiti-mcp-root:
      condition: service_healthy

# --- Services (Static Ones) ---
services:
  # --- Database ---
  neo4j:
    image: neo4j:5.26.0
    container_name: ${NEO4J_CONTAINER_NAME:-graphiti-mcp-neo4j}
    ports:
      - "${NEO4J_HOST_HTTP_PORT:-7474}:${NEO4J_CONTAINER_HTTP_PORT:-7474}"
      - "${NEO4J_HOST_BOLT_PORT:-7687}:${NEO4J_CONTAINER_BOLT_PORT:-7687}"
    environment:
      - NEO4J_AUTH=${NEO4J_USER?Please set NEO4J_USER in your .env file}/${NEO4J_PASSWORD?Please
        set NEO4J_PASSWORD in your .env file}
      - NEO4J_server_memory_heap_initial__size=${NEO4J_HEAP_INITIAL:-512m}
      - NEO4J_server_memory_heap_max__size=${NEO4J_HEAP_MAX:-1G}
      - NEO4J_server_memory_pagecache_size=${NEO4J_PAGECACHE:-512m}
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    healthcheck:
      test: ["CMD", "wget", "-O", "/dev/null", "http://localhost:${NEO4J_CONTAINER_HTTP_PORT:-7474}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  # --- Root MCP Server (Required) ---
  graphiti-mcp-root:
    <<: *graphiti-mcp-base
                           # Alias refers to anchor above
    container_name: ${MCP_ROOT_CONTAINER_NAME:-graphiti-mcp-root}
    depends_on:
      neo4j:
        condition: service_healthy
    ports:
      - "${MCP_ROOT_HOST_PORT:-8000}:${MCP_ROOT_CONTAINER_PORT:-8000}"
    environment:
      # Specific env vars merged with base env vars via the alias above
      MCP_GROUP_ID: "root"
      MCP_USE_CUSTOM_ENTITIES: "true"
      MCP_ENTITY_TYPE_DIR: "entity_types/base"

# --- Volumes ---
  mcp-filesystem-main:
    <<: *graphiti-mcp-custom-base
    environment:
      MCP_GROUP_ID: filesystem
      MCP_USE_CUSTOM_ENTITIES: 'true'
      MCP_ENTITY_TYPE_DIR: /app/project_entities
    container_name: mcp-filesystem-main
    ports:
      - 8001:${MCP_PORT}
    volumes:
      - /Users/mateicanavra/Documents/.nosync/DEV/mcp-servers/mcp-filesystem/entities:/app/project_entities:ro
volumes:
  neo4j_data: # Persists Neo4j graph data
  neo4j_logs: # Persists Neo4j logs
````

## File: Dockerfile
````dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv for package management
RUN apt-get update && apt-get install -y curl && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Add uv to PATH
ENV PATH="/root/.local/bin:${PATH}"

# Create dist directory first
RUN mkdir -p /dist/

# Copy the dist directory with our local wheel to container root (if it exists)
COPY dist/* /dist/

# Copy pyproject.toml and install dependencies
COPY pyproject.toml .
RUN uv sync
# RUN chmod +x $(which uv)

# Copy necessary application code and directories into /app/
# The destination must end with '/' when copying directories
COPY graphiti_mcp_server.py ./
COPY entity_types/ ./entity_types/

# --- Add Entrypoint Script ---
# Copy the entrypoint script into the working directory
COPY entrypoint.sh .
# Make it executable
RUN chmod +x ./entrypoint.sh
# ---------------------------

# Set environment variables
ENV PYTHONUNBUFFERED=1

# # Create a non-root user and group
# RUN groupadd --system appuser && useradd --system --gid appuser appuser

# # Change ownership of the app directory to the new user
# # Ensure entrypoint.sh is also owned correctly
# RUN chown -R appuser:appuser /app

# # Switch to the non-root user
# USER appuser

# --- Set Entrypoint ---
# Use the script as the main container command
ENTRYPOINT ["./entrypoint.sh"]

# Original CMD instruction has been replaced by the ENTRYPOINT above
# CMD ["uv", "run", "graphiti_mcp_server.py"]
````

## File: entrypoint.sh
````bash
#!/bin/sh
# docker-entrypoint.sh
# This script constructs and executes the graphiti_mcp_server command
# based on environment variables set in docker-compose.yml.

# Exit immediately if a command exits with a non-zero status.
set -e

# Base command parts
CMD_PREFIX="uv run graphiti_mcp_server.py"
CMD_ARGS="--transport sse" # Common arguments

# Append arguments based on environment variables

# --group-id (Required or has default handling in script?)
if [ -n "$MCP_GROUP_ID" ]; then
  CMD_ARGS="$CMD_ARGS --group-id \"$MCP_GROUP_ID\""
else
  echo "Warning: MCP_GROUP_ID environment variable not set."
  # Decide: exit 1? Or let the python script handle default/error?
fi

# --use-custom-entities (Boolean flag)
# Adjust check if different values like "1", "yes" are used
if [ "$MCP_USE_CUSTOM_ENTITIES" = "true" ]; then
  CMD_ARGS="$CMD_ARGS --use-custom-entities"
fi

# --entity-type-dir (Optional path)
if [ -n "$MCP_ENTITY_TYPE_DIR" ]; then
  CMD_ARGS="$CMD_ARGS --entity-type-dir $MCP_ENTITY_TYPE_DIR"
fi

# --entity-types (Optional space-separated list)
# Assumes the python script handles a space-separated list after the flag.
if [ -n "$MCP_ENTITY_TYPES" ]; then
   CMD_ARGS="$CMD_ARGS --entity-types $MCP_ENTITY_TYPES"
fi

# --log-level (Pass based on ENV var)
# Read the env var set by docker compose (from .env or compose override)
if [ -n "$GRAPHITI_LOG_LEVEL" ]; then
  CMD_ARGS="$CMD_ARGS --log-level $GRAPHITI_LOG_LEVEL"
fi

# --destroy-graph (Boolean flag)
if [ "$NEO4J_DESTROY_ENTIRE_GRAPH" = "true" ]; then
  CMD_ARGS="$CMD_ARGS --destroy-graph"
  echo "!!! DANGER !!! NEO4J_DESTROY_ENTIRE_GRAPH flag is set to 'true'."
  echo "!!! WARNING !!! This will PERMANENTLY DELETE ALL DATA in the Neo4j database, not just data for this group."
  echo "                 Set to 'false' immediately after use to prevent accidental data loss."
fi

# Add logic for any other configurable flags here...

# Combine prefix and arguments
FULL_CMD="$CMD_PREFIX $CMD_ARGS"

echo "--------------------------------------------------"
echo " Running MCP Server with Group ID: ${MCP_GROUP_ID:-<Not Set>}"
echo " Executing command: $FULL_CMD"
echo "--------------------------------------------------"

# Use 'exec' to replace the shell process with the Python process.
# "$@" passes along any arguments that might have been added via
# 'command:' in docker-compose.yml (though we aren't using them here).
exec $FULL_CMD "$@"
````

## File: graphiti_mcp_server.py
````python
#!/usr/bin/env python3
"""
Graphiti MCP Server - Exposes Graphiti functionality through the Model Context Protocol (MCP)
"""

import argparse
import asyncio
import importlib
import importlib.util
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, TypedDict, Union, cast

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from graphiti_core import Graphiti
from graphiti_core.edges import EntityEdge
from graphiti_core.llm_client import LLMClient
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.llm_client.openai_client import OpenAIClient
from graphiti_core.nodes import EpisodeType, EpisodicNode
from graphiti_core.search.search_config_recipes import (
    NODE_HYBRID_SEARCH_NODE_DISTANCE,
    NODE_HYBRID_SEARCH_RRF,
)
from graphiti_core.search.search_filters import SearchFilters
from graphiti_core.utils.maintenance.graph_data_operations import clear_data
from entity_types import get_entity_types, get_entity_type_subset, register_entity_type

load_dotenv()

DEFAULT_LLM_MODEL = 'gpt-4o'
DEFAULT_LOG_LEVEL = logging.INFO

# The ENTITY_TYPES dictionary is managed by the registry in mcp_server.entity_types
# NOTE: This global reference is only used for predefined entity subsets below.
# For the latest entity types, always use get_entity_types() directly.
ENTITY_TYPES = get_entity_types()

# Predefined entity type sets for different use cases
REQUIREMENT_ONLY_ENTITY_TYPES = get_entity_type_subset(['Requirement'])
PREFERENCE_ONLY_ENTITY_TYPES = get_entity_type_subset(['Preference'])
PROCEDURE_ONLY_ENTITY_TYPES = get_entity_type_subset(['Procedure'])


# Type definitions for API responses
class ErrorResponse(TypedDict):
    error: str


class SuccessResponse(TypedDict):
    message: str


class NodeResult(TypedDict):
    uuid: str
    name: str
    summary: str
    labels: list[str]
    group_id: str
    created_at: str
    attributes: dict[str, Any]


class NodeSearchResponse(TypedDict):
    message: str
    nodes: list[NodeResult]


class FactSearchResponse(TypedDict):
    message: str
    facts: list[dict[str, Any]]


class EpisodeSearchResponse(TypedDict):
    message: str
    episodes: list[dict[str, Any]]


class StatusResponse(TypedDict):
    status: str
    message: str


# Server configuration classes
class GraphitiConfig(BaseModel):
    """Configuration for Graphiti client.

    Centralizes all configuration parameters for the Graphiti client,
    including database connection details and LLM settings.
    """

    # neo4j_uri: str = 'bolt://localhost:7687'
    neo4j_uri: str = 'bolt://neo4j:7687'
    neo4j_user: str = 'neo4j'
    neo4j_password: str = 'password'
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    model_name: Optional[str] = None
    group_id: Optional[str] = None
    use_custom_entities: bool = False
    entity_type_subset: Optional[list[str]] = None

    @classmethod
    def from_env(cls) -> 'GraphitiConfig':
        """Create a configuration instance from environment variables."""
        return cls(
            # neo4j_uri=os.environ.get('NEO4J_URI', 'bolt://localhost:7687'),
            neo4j_uri=os.environ.get('NEO4J_URI', 'bolt://neo4j:7687'),
            neo4j_user=os.environ.get('NEO4J_USER', 'neo4j'),
            neo4j_password=os.environ.get('NEO4J_PASSWORD', 'password'),
            openai_api_key=os.environ.get('OPENAI_API_KEY'),
            openai_base_url=os.environ.get('OPENAI_BASE_URL'),
            model_name=os.environ.get('MODEL_NAME'),
        )


class MCPConfig(BaseModel):
    """Configuration for MCP server."""

    transport: str


# Configure logging
log_level_str = os.environ.get('GRAPHITI_LOG_LEVEL', 'info').upper()
log_level = getattr(logging, log_level_str, DEFAULT_LOG_LEVEL)

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)
logger.info(f'Initial logging configured with level: {logging.getLevelName(log_level)}')

# Function to reconfigure logging level based on final decision
def configure_logging(level_name: str):
    """
    Configure or reconfigure the logging level based on a string level name.
    
    Args:
        level_name: A string representation of the logging level ('debug', 'info', etc.)
    """
    global logger, log_level
    level_name_upper = level_name.upper()
    new_level = getattr(logging, level_name_upper, DEFAULT_LOG_LEVEL)
    if new_level != log_level:  # Only reconfigure if level changes
        log_level = new_level
        logging.getLogger().setLevel(log_level)  # Set level on root logger
        # Re-get logger instance for safety
        logger = logging.getLogger(__name__)
        logger.info(f"Logging level reconfigured to: {logging.getLevelName(log_level)}")
    else:
        logger.info(f"Logging level remains at: {logging.getLevelName(log_level)}")

# Create global config instance
config = GraphitiConfig.from_env()

# MCP server instructions
GRAPHITI_MCP_INSTRUCTIONS = """
Welcome to Graphiti MCP - a memory service for AI agents built on a knowledge graph. Graphiti performs well
with dynamic data such as user interactions, changing enterprise data, and external information.

Graphiti transforms information into a richly connected knowledge network, allowing you to 
capture relationships between concepts, entities, and information. The system organizes data as episodes 
(content snippets), nodes (entities), and facts (relationships between entities), creating a dynamic, 
queryable memory store that evolves with new information. Graphiti supports multiple data formats, including 
structured JSON data, enabling seamless integration with existing data pipelines and systems.

Facts contain temporal metadata, allowing you to track the time of creation and whether a fact is invalid 
(superseded by new information).

Key capabilities:
1. Add episodes (text, messages, or JSON) to the knowledge graph with the add_episode tool
2. Search for nodes (entities) in the graph using natural language queries with search_nodes
3. Find relevant facts (relationships between entities) with search_facts
4. Retrieve specific entity edges or episodes by UUID
5. Manage the knowledge graph with tools like delete_episode, delete_entity_edge, and clear_graph

The server connects to a database for persistent storage and uses language models for certain operations. 
Each piece of information is organized by group_id, allowing you to maintain separate knowledge domains.

When adding information, provide descriptive names and detailed content to improve search quality. 
When searching, use specific queries and consider filtering by group_id for more relevant results.

For optimal performance, ensure the database is properly configured and accessible, and valid 
API keys are provided for any language model operations.
"""


# MCP server instance
mcp = FastMCP(
    'graphiti',
    instructions=GRAPHITI_MCP_INSTRUCTIONS,
)


# Initialize Graphiti client
graphiti_client: Optional[Graphiti] = None


async def initialize_graphiti(llm_client: Optional[LLMClient] = None, destroy_graph: bool = False):
    """Initialize the Graphiti client with the provided settings.

    Args:
        llm_client: Optional LLMClient instance to use for LLM operations
        destroy_graph: Optional boolean to destroy all Graphiti graphs
    """
    global graphiti_client

    # If no client is provided, create a default OpenAI client
    if not llm_client:
        if config.openai_api_key:
            llm_config = LLMConfig(api_key=config.openai_api_key)
            if config.openai_base_url:
                llm_config.base_url = config.openai_base_url
            if config.model_name:
                llm_config.model = config.model_name
            llm_client = OpenAIClient(config=llm_config)
        else:
            raise ValueError('OPENAI_API_KEY must be set when not using a custom LLM client')

    if not config.neo4j_uri or not config.neo4j_user or not config.neo4j_password:
        raise ValueError('NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD must be set')

    graphiti_client = Graphiti(
        uri=config.neo4j_uri,
        user=config.neo4j_user,
        password=config.neo4j_password,
        llm_client=llm_client,
    )

    if destroy_graph:
        logger.info('Destroying graph...')
        await clear_data(graphiti_client.driver)

    # Initialize the graph database with Graphiti's indices
    await graphiti_client.build_indices_and_constraints()
    logger.info('Graphiti client initialized successfully')


def format_fact_result(edge: EntityEdge) -> dict[str, Any]:
    """Format an entity edge into a readable result.

    Since EntityEdge is a Pydantic BaseModel, we can use its built-in serialization capabilities.

    Args:
        edge: The EntityEdge to format

    Returns:
        A dictionary representation of the edge with serialized dates and excluded embeddings
    """
    return edge.model_dump(
        mode='json',
        exclude={
            'fact_embedding',
        },
    )


# Dictionary to store queues for each group_id
# Each queue is a list of tasks to be processed sequentially
episode_queues: dict[str, asyncio.Queue] = {}
# Dictionary to track if a worker is running for each group_id
queue_workers: dict[str, bool] = {}


async def process_episode_queue(group_id: str):
    """Process episodes for a specific group_id sequentially.

    This function runs as a long-lived task that processes episodes
    from the queue one at a time.
    """
    global queue_workers

    logger.info(f'Starting episode queue worker for group_id: {group_id}')
    queue_workers[group_id] = True

    try:
        while True:
            # Get the next episode processing function from the queue
            # This will wait if the queue is empty
            process_func = await episode_queues[group_id].get()

            try:
                # Process the episode
                await process_func()
            except Exception as e:
                logger.error(f'Error processing queued episode for group_id {group_id}: {str(e)}')
            finally:
                # Mark the task as done regardless of success/failure
                episode_queues[group_id].task_done()
    except asyncio.CancelledError:
        logger.info(f'Episode queue worker for group_id {group_id} was cancelled')
    except Exception as e:
        logger.error(f'Unexpected error in queue worker for group_id {group_id}: {str(e)}')
    finally:
        queue_workers[group_id] = False
        logger.info(f'Stopped episode queue worker for group_id: {group_id}')


@mcp.tool()
async def add_episode(
    name: str,
    episode_body: str,
    group_id: Optional[str] = None,
    source: str = 'text',
    source_description: str = '',
    uuid: Optional[str] = None,
    entity_type_subset: Optional[list[str]] = None,
) -> Union[SuccessResponse, ErrorResponse]:
    """Add an episode to the Graphiti knowledge graph. This is the primary way to add information to the graph.

    This function returns immediately and processes the episode addition in the background.
    Episodes for the same group_id are processed sequentially to avoid race conditions.

    Args:
        name (str): Name of the episode
        episode_body (str): The content of the episode. When source='json', this must be a properly escaped JSON string,
                           not a raw Python dictionary. The JSON data will be automatically processed
                           to extract entities and relationships.
        group_id (str, optional): A unique ID for this graph. If not provided, uses the default group_id from CLI
                                 or a generated one.
        source (str, optional): Source type, must be one of:
                               - 'text': For plain text content (default)
                               - 'json': For structured data
                               - 'message': For conversation-style content
        source_description (str, optional): Description of the source
        uuid (str, optional): Optional UUID for the episode
        entity_type_subset (list[str], optional): Optional list of entity type names to use for this episode.
                                                If not provided, uses all entity types if enabled.

    Examples:
        # Adding plain text content
        add_episode(
            name="Company News",
            episode_body="Acme Corp announced a new product line today.",
            source="text",
            source_description="news article",
            group_id="some_arbitrary_string"
        )

        # Adding structured JSON data
        # NOTE: episode_body must be a properly escaped JSON string. Note the triple backslashes
        add_episode(
            name="Customer Profile",
            episode_body="{\\\"company\\\": {\\\"name\\\": \\\"Acme Technologies\\\"}, \\\"products\\\": [{\\\"id\\\": \\\"P001\\\", \\\"name\\\": \\\"CloudSync\\\"}, {\\\"id\\\": \\\"P002\\\", \\\"name\\\": \\\"DataMiner\\\"}]}",
            source="json",
            source_description="CRM data"
        )

        # Adding message-style content
        add_episode(
            name="Customer Conversation",
            episode_body="user: What's your return policy?\nassistant: You can return items within 30 days.",
            source="message",
            source_description="chat transcript",
            group_id="some_arbitrary_string"
        )

        # Using a specific subset of entity types
        add_episode(
            name="Project Requirements",
            episode_body="We need to implement user authentication with SSO.",
            entity_type_subset=["Requirement"],
            source="text",
            source_description="meeting notes"
        )

    Notes:
        When using source='json':
        - The JSON must be a properly escaped string, not a raw Python dictionary
        - The JSON will be automatically processed to extract entities and relationships
        - Complex nested structures are supported (arrays, nested objects, mixed data types), but keep nesting to a minimum
        - Entities will be created from appropriate JSON properties
        - Relationships between entities will be established based on the JSON structure
    """
    global graphiti_client, episode_queues, queue_workers

    if graphiti_client is None:
        return {'error': 'Graphiti client not initialized'}

    try:
        # Map string source to EpisodeType enum
        source_type = EpisodeType.text
        if source.lower() == 'message':
            source_type = EpisodeType.message
        elif source.lower() == 'json':
            source_type = EpisodeType.json

        # Use the provided group_id or fall back to the default from config
        effective_group_id = group_id if group_id is not None else config.group_id

        # Cast group_id to str to satisfy type checker
        # The Graphiti client expects a str for group_id, not Optional[str]
        group_id_str = str(effective_group_id) if effective_group_id is not None else ''

        # We've already checked that graphiti_client is not None above
        # This assert statement helps type checkers understand that graphiti_client is defined
        assert graphiti_client is not None, 'graphiti_client should not be None here'

        # Use cast to help the type checker understand that graphiti_client is not None
        client = cast(Graphiti, graphiti_client)

        # Define the episode processing function
        async def process_episode():
            try:
                logger.info(f"Processing queued episode '{name}' for group_id: {group_id_str}")
                
                # Import here to ensure we get the most up-to-date entity registry
                from entity_types import get_entity_types, get_entity_type_subset
                
                # Determine which entity types to use based on configuration and parameters
                logger.info(f"Configuration settings - use_custom_entities: {config.use_custom_entities}, "
                           f"entity_type_subset param: {entity_type_subset}, "
                           f"config.entity_type_subset: {config.entity_type_subset}")
                
                if not config.use_custom_entities:
                    # If custom entities are disabled, use empty dict
                    entity_types_to_use = {}
                    logger.info("Custom entities disabled, using empty entity type dictionary")
                elif entity_type_subset:
                    # If a subset is specified in function call, it takes highest precedence
                    entity_types_to_use = get_entity_type_subset(entity_type_subset)
                    logger.info(f"Using function parameter entity subset: {entity_type_subset}")
                elif config.entity_type_subset:
                    # If subset is specified via command line, use that
                    entity_types_to_use = get_entity_type_subset(config.entity_type_subset)
                    logger.info(f"Using command-line entity subset: {config.entity_type_subset}")
                else:
                    # Otherwise use all registered entity types - get fresh reference here
                    entity_types_to_use = get_entity_types()
                    logger.info(f"Using all registered entity types: {list(entity_types_to_use.keys())}")
                
                logger.info(f"Final entity types being used: {list(entity_types_to_use.keys())}")

                await client.add_episode(
                    name=name,
                    episode_body=episode_body,
                    source=source_type,
                    source_description=source_description,
                    group_id=group_id_str,  # Using the string version of group_id
                    uuid=uuid,
                    reference_time=datetime.now(timezone.utc),
                    entity_types=entity_types_to_use,
                )
                logger.info(f"Episode '{name}' added successfully")

                logger.info(f"Building communities after episode '{name}'")
                await client.build_communities()

                logger.info(f"Episode '{name}' processed successfully")
            except Exception as e:
                error_msg = str(e)
                logger.error(
                    f"Error processing episode '{name}' for group_id {group_id_str}: {error_msg}"
                )

        # Initialize queue for this group_id if it doesn't exist
        if group_id_str not in episode_queues:
            episode_queues[group_id_str] = asyncio.Queue()

        # Add the episode processing function to the queue
        await episode_queues[group_id_str].put(process_episode)

        # Start a worker for this queue if one isn't already running
        if not queue_workers.get(group_id_str, False):
            asyncio.create_task(process_episode_queue(group_id_str))

        # Return immediately with a success message
        return {
            'message': f"Episode '{name}' queued for processing (position: {episode_queues[group_id_str].qsize()})"
        }
    except Exception as e:
        error_msg = str(e)
        logger.error(f'Error queuing episode task: {error_msg}')
        return {'error': f'Error queuing episode task: {error_msg}'}


@mcp.tool()
async def search_nodes(
    query: str,
    group_ids: Optional[list[str]] = None,
    max_nodes: int = 10,
    center_node_uuid: Optional[str] = None,
    entity: str = '',  # cursor seems to break with None
) -> Union[NodeSearchResponse, ErrorResponse]:
    """Search the Graphiti knowledge graph for relevant node summaries.
    These contain a summary of all of a node's relationships with other nodes.

    Note: entity is a single entity type to filter results (permitted: "Preference", "Procedure").

    Args:
        query: The search query
        group_ids: Optional list of group IDs to filter results
        max_nodes: Maximum number of nodes to return (default: 10)
        center_node_uuid: Optional UUID of a node to center the search around
        entity: Optional single entity type to filter results (permitted: "Preference", "Procedure")
    """
    global graphiti_client

    if graphiti_client is None:
        return ErrorResponse(error='Graphiti client not initialized')

    try:
        # Use the provided group_ids or fall back to the default from config if none provided
        effective_group_ids = (
            group_ids if group_ids is not None else [config.group_id] if config.group_id else []
        )

        # Configure the search
        if center_node_uuid is not None:
            search_config = NODE_HYBRID_SEARCH_NODE_DISTANCE.model_copy(deep=True)
        else:
            search_config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
        search_config.limit = max_nodes

        filters = SearchFilters()
        if entity != '':
            filters.node_labels = [entity]

        # We've already checked that graphiti_client is not None above
        assert graphiti_client is not None

        # Use cast to help the type checker understand that graphiti_client is not None
        client = cast(Graphiti, graphiti_client)

        # Perform the search using the _search method
        search_results = await client._search(
            query=query,
            config=search_config,
            group_ids=effective_group_ids,
            center_node_uuid=center_node_uuid,
            search_filter=filters,
        )

        if not search_results.nodes:
            return NodeSearchResponse(message='No relevant nodes found', nodes=[])

        # Format the node results
        formatted_nodes: list[NodeResult] = [
            {
                'uuid': node.uuid,
                'name': node.name,
                'summary': node.summary if hasattr(node, 'summary') else '',
                'labels': node.labels if hasattr(node, 'labels') else [],
                'group_id': node.group_id,
                'created_at': node.created_at.isoformat(),
                'attributes': node.attributes if hasattr(node, 'attributes') else {},
            }
            for node in search_results.nodes
        ]

        return NodeSearchResponse(message='Nodes retrieved successfully', nodes=formatted_nodes)
    except Exception as e:
        error_msg = str(e)
        logger.error(f'Error searching nodes: {error_msg}')
        return ErrorResponse(error=f'Error searching nodes: {error_msg}')


@mcp.tool()
async def search_facts(
    query: str,
    group_ids: Optional[list[str]] = None,
    max_facts: int = 10,
    center_node_uuid: Optional[str] = None,
) -> Union[FactSearchResponse, ErrorResponse]:
    """Search the Graphiti knowledge graph for relevant facts.

    Args:
        query: The search query
        group_ids: Optional list of group IDs to filter results
        max_facts: Maximum number of facts to return (default: 10)
        center_node_uuid: Optional UUID of a node to center the search around
    """
    global graphiti_client

    if graphiti_client is None:
        return {'error': 'Graphiti client not initialized'}

    try:
        # Use the provided group_ids or fall back to the default from config if none provided
        effective_group_ids = (
            group_ids if group_ids is not None else [config.group_id] if config.group_id else []
        )

        # We've already checked that graphiti_client is not None above
        assert graphiti_client is not None

        # Use cast to help the type checker understand that graphiti_client is not None
        client = cast(Graphiti, graphiti_client)

        relevant_edges = await client.search(
            group_ids=effective_group_ids,
            query=query,
            num_results=max_facts,
            center_node_uuid=center_node_uuid,
        )

        if not relevant_edges:
            return {'message': 'No relevant facts found', 'facts': []}

        facts = [format_fact_result(edge) for edge in relevant_edges]
        return {'message': 'Facts retrieved successfully', 'facts': facts}
    except Exception as e:
        error_msg = str(e)
        logger.error(f'Error searching facts: {error_msg}')
        return {'error': f'Error searching facts: {error_msg}'}


@mcp.tool()
async def delete_entity_edge(uuid: str) -> Union[SuccessResponse, ErrorResponse]:
    """Delete an entity edge from the Graphiti knowledge graph.

    Args:
        uuid: UUID of the entity edge to delete
    """
    global graphiti_client

    if graphiti_client is None:
        return {'error': 'Graphiti client not initialized'}

    try:
        # We've already checked that graphiti_client is not None above
        assert graphiti_client is not None

        # Use cast to help the type checker understand that graphiti_client is not None
        client = cast(Graphiti, graphiti_client)

        # Get the entity edge by UUID
        entity_edge = await EntityEdge.get_by_uuid(client.driver, uuid)
        # Delete the edge using its delete method
        await entity_edge.delete(client.driver)
        return {'message': f'Entity edge with UUID {uuid} deleted successfully'}
    except Exception as e:
        error_msg = str(e)
        logger.error(f'Error deleting entity edge: {error_msg}')
        return {'error': f'Error deleting entity edge: {error_msg}'}


@mcp.tool()
async def delete_episode(uuid: str) -> Union[SuccessResponse, ErrorResponse]:
    """Delete an episode from the Graphiti knowledge graph.

    Args:
        uuid: UUID of the episode to delete
    """
    global graphiti_client

    if graphiti_client is None:
        return {'error': 'Graphiti client not initialized'}

    try:
        # We've already checked that graphiti_client is not None above
        assert graphiti_client is not None

        # Use cast to help the type checker understand that graphiti_client is not None
        client = cast(Graphiti, graphiti_client)

        # Get the episodic node by UUID - EpisodicNode is already imported at the top
        episodic_node = await EpisodicNode.get_by_uuid(client.driver, uuid)
        # Delete the node using its delete method
        await episodic_node.delete(client.driver)
        return {'message': f'Episode with UUID {uuid} deleted successfully'}
    except Exception as e:
        error_msg = str(e)
        logger.error(f'Error deleting episode: {error_msg}')
        return {'error': f'Error deleting episode: {error_msg}'}


@mcp.tool()
async def get_entity_edge(uuid: str) -> Union[dict[str, Any], ErrorResponse]:
    """Get an entity edge from the Graphiti knowledge graph by its UUID.

    Args:
        uuid: UUID of the entity edge to retrieve
    """
    global graphiti_client

    if graphiti_client is None:
        return {'error': 'Graphiti client not initialized'}

    try:
        # We've already checked that graphiti_client is not None above
        assert graphiti_client is not None

        # Use cast to help the type checker understand that graphiti_client is not None
        client = cast(Graphiti, graphiti_client)

        # Get the entity edge directly using the EntityEdge class method
        entity_edge = await EntityEdge.get_by_uuid(client.driver, uuid)

        # Use the format_fact_result function to serialize the edge
        # Return the Python dict directly - MCP will handle serialization
        return format_fact_result(entity_edge)
    except Exception as e:
        error_msg = str(e)
        logger.error(f'Error getting entity edge: {error_msg}')
        return {'error': f'Error getting entity edge: {error_msg}'}


@mcp.tool()
async def get_episodes(
    group_id: Optional[str] = None, last_n: int = 10
) -> Union[list[dict[str, Any]], EpisodeSearchResponse, ErrorResponse]:
    """Get the most recent episodes for a specific group.

    Args:
        group_id: ID of the group to retrieve episodes from. If not provided, uses the default group_id.
        last_n: Number of most recent episodes to retrieve (default: 10)
    """
    global graphiti_client

    if graphiti_client is None:
        return {'error': 'Graphiti client not initialized'}

    try:
        # Use the provided group_id or fall back to the default from config
        effective_group_id = group_id if group_id is not None else config.group_id

        if not isinstance(effective_group_id, str):
            return {'error': 'Group ID must be a string'}

        # We've already checked that graphiti_client is not None above
        assert graphiti_client is not None

        # Use cast to help the type checker understand that graphiti_client is not None
        client = cast(Graphiti, graphiti_client)

        episodes = await client.retrieve_episodes(
            group_ids=[effective_group_id], last_n=last_n, reference_time=datetime.now(timezone.utc)
        )

        if not episodes:
            return {'message': f'No episodes found for group {effective_group_id}', 'episodes': []}

        # Use Pydantic's model_dump method for EpisodicNode serialization
        formatted_episodes = [
            # Use mode='json' to handle datetime serialization
            episode.model_dump(mode='json')
            for episode in episodes
        ]

        # Return the Python list directly - MCP will handle serialization
        return formatted_episodes
    except Exception as e:
        error_msg = str(e)
        logger.error(f'Error getting episodes: {error_msg}')
        return {'error': f'Error getting episodes: {error_msg}'}


@mcp.tool()
async def clear_graph() -> Union[SuccessResponse, ErrorResponse]:
    """Clear all data from the Graphiti knowledge graph and rebuild indices."""
    global graphiti_client

    if graphiti_client is None:
        return {'error': 'Graphiti client not initialized'}

    try:
        # We've already checked that graphiti_client is not None above
        assert graphiti_client is not None

        # Use cast to help the type checker understand that graphiti_client is not None
        client = cast(Graphiti, graphiti_client)

        # clear_data is already imported at the top
        await clear_data(client.driver)
        await client.build_indices_and_constraints()
        return {'message': 'Graph cleared successfully and indices rebuilt'}
    except Exception as e:
        error_msg = str(e)
        logger.error(f'Error clearing graph: {error_msg}')
        return {'error': f'Error clearing graph: {error_msg}'}


@mcp.resource('http://graphiti/status')
async def get_status() -> StatusResponse:
    """Get the status of the Graphiti MCP server and Neo4j connection."""
    global graphiti_client

    if graphiti_client is None:
        return {'status': 'error', 'message': 'Graphiti client not initialized'}

    try:
        # We've already checked that graphiti_client is not None above
        assert graphiti_client is not None

        # Use cast to help the type checker understand that graphiti_client is not None
        client = cast(Graphiti, graphiti_client)

        # Test Neo4j connection
        await client.driver.verify_connectivity()
        return {'status': 'ok', 'message': 'Graphiti MCP server is running and connected to Neo4j'}
    except Exception as e:
        error_msg = str(e)
        logger.error(f'Error checking Neo4j connection: {error_msg}')
        return {
            'status': 'error',
            'message': f'Graphiti MCP server is running but Neo4j connection failed: {error_msg}',
        }


def create_llm_client(api_key: Optional[str] = None, model: Optional[str] = None) -> LLMClient:
    """Create an OpenAI LLM client.

    Args:
        api_key: API key for the OpenAI service
        model: Model name to use

    Returns:
        An instance of the OpenAI LLM client
    """
    # Create config with provided API key and model
    llm_config = LLMConfig(api_key=api_key)

    # Set model if provided
    if model:
        llm_config.model = model

    # Create and return the client
    return OpenAIClient(config=llm_config)


async def initialize_server() -> MCPConfig:
    """Initialize the Graphiti server with the specified LLM client."""
    global config

    parser = argparse.ArgumentParser(
        description='Run the Graphiti MCP server with optional LLM client'
    )
    parser.add_argument(
        '--group-id',
        help='Namespace for the graph. This is an arbitrary string used to organize related data. '
        'If not provided, a random UUID will be generated.',
    )
    parser.add_argument(
        '--transport',
        choices=['sse', 'stdio'],
        default='sse',
        help='Transport to use for communication with the client. (default: sse)',
    )
    # OpenAI is the only supported LLM client
    parser.add_argument('--model', help='Model name to use with the LLM client')
    parser.add_argument('--destroy-graph', action='store_true', help='Destroy all Graphiti graphs')
    parser.add_argument(
        '--use-custom-entities',
        action='store_true',
        help='Enable entity extraction using the predefined ENTITY_TYPES',
    )
    # Add argument for specifying entity types
    parser.add_argument(
        '--entity-types',
        nargs='+',
        help='Specify which entity types to use (e.g., --entity-types Requirement Preference). '
        'If not provided but --use-custom-entities is set, all registered entity types will be used.',
    )
    # Add argument for custom entity type directory
    parser.add_argument(
        '--entity-type-dir',
        help='Directory containing custom entity type modules to load'
    )
    # Add argument for log level
    parser.add_argument(
        '--log-level',
        choices=['debug', 'info', 'warn', 'error', 'fatal'],
        default=os.environ.get('GRAPHITI_LOG_LEVEL', 'info').lower(),  # Default to ENV or 'info'
        help='Set the logging level.'
    )

    args = parser.parse_args()

    # Reconfigure logging based on final argument
    configure_logging(args.log_level)
    logger.info(f"Final effective logging level: {logging.getLevelName(log_level)}")

    # Set the group_id from CLI argument or generate a random one
    if args.group_id:
        config.group_id = args.group_id
        logger.info(f'Using provided group_id: {config.group_id}')
    else:
        config.group_id = f'graph_{uuid.uuid4().hex[:8]}'
        logger.info(f'Generated random group_id: {config.group_id}')

    # Define the expected path for base entity types within the container
    container_base_entity_dir = "/app/entity_types/base"
    
    # Always load base entity types first
    if os.path.exists(container_base_entity_dir) and os.path.isdir(container_base_entity_dir):
        logger.info(f'Loading base entity types from: {container_base_entity_dir}')
        load_entity_types_from_directory(container_base_entity_dir)
    else:
        logger.warning(f"Base entity types directory not found at: {container_base_entity_dir}")
    
    # Load project-specific entity types if directory is specified and different from base
    if args.entity_type_dir:
        # Resolve paths to handle potential symlinks or relative paths inside container
        abs_project_dir = os.path.abspath(args.entity_type_dir)
        abs_base_dir = os.path.abspath(container_base_entity_dir)
        
        if abs_project_dir != abs_base_dir:
            if os.path.exists(abs_project_dir) and os.path.isdir(abs_project_dir):
                logger.info(f'Loading project-specific entity types from: {abs_project_dir}')
                load_entity_types_from_directory(abs_project_dir)
            else:
                logger.warning(f"Project entity types directory not found or not a directory: {abs_project_dir}")
        else:
            logger.info(f"Project entity directory '{args.entity_type_dir}' is the same as base, skipping redundant load.")

    # Set use_custom_entities flag if specified
    if args.use_custom_entities:
        config.use_custom_entities = True
        logger.info('Entity extraction enabled using predefined ENTITY_TYPES')
    else:
        logger.info('Entity extraction disabled (no custom entities will be used)')
        
    # Store the entity types to use if specified
    if args.entity_types:
        config.entity_type_subset = args.entity_types
        logger.info(f'Using entity types: {", ".join(args.entity_types)}')
    else:
        config.entity_type_subset = None
        if config.use_custom_entities:
            logger.info('Using all registered entity types')
        
    # Log all registered entity types after initialization
    logger.info(f"All registered entity types after initialization: {len(get_entity_types())}")
    for entity_name in get_entity_types().keys():
        logger.info(f"  - Available entity: {entity_name}")

    llm_client = None

    # Create OpenAI client if model is specified or if OPENAI_API_KEY is available
    if args.model or config.openai_api_key:
        # Override model from command line if specified

        config.model_name = args.model or DEFAULT_LLM_MODEL

        # Create the OpenAI client
        llm_client = create_llm_client(api_key=config.openai_api_key, model=config.model_name)

    # Initialize Graphiti with the specified LLM client
    await initialize_graphiti(llm_client, destroy_graph=args.destroy_graph)

    return MCPConfig(transport=args.transport)


async def run_mcp_server():
    """Run the MCP server in the current event loop."""
    # Initialize the server
    mcp_config = await initialize_server()

    # Run the server with stdio transport for MCP in the same event loop
    logger.info(f'Starting MCP server with transport: {mcp_config.transport}')
    if mcp_config.transport == 'stdio':
        await mcp.run_stdio_async()
    elif mcp_config.transport == 'sse':
        logger.info(
            f'Running MCP server with SSE transport on {mcp.settings.host}:{mcp.settings.port}'
        )
        await mcp.run_sse_async()


def main():
    """Main function to run the Graphiti MCP server."""
    try:
        # Run everything in a single event loop
        asyncio.run(run_mcp_server())
    except Exception as e:
        logger.error(f'Error initializing Graphiti MCP server: {str(e)}')
        raise


def load_entity_types_from_directory(directory_path: str) -> None:
    """Load all Python modules in the specified directory as entity types.
    
    This function dynamically imports all Python files in the specified directory,
    and automatically registers any Pydantic BaseModel classes that have docstrings.
    No explicit imports or registration calls are needed in the entity type files.
    
    Args:
        directory_path: Path to the directory containing entity type modules
    """
    logger.info(f"Attempting to load entities from directory: {directory_path}")
    directory = Path(directory_path)
    if not directory.exists() or not directory.is_dir():
        logger.warning(f"Entity types directory {directory_path} does not exist or is not a directory")
        return
        
    # Find all Python files in the directory
    python_files = list(directory.glob('*.py'))
    logger.info(f"Found {len(python_files)} Python files in {directory_path}")
    
    for file_path in python_files:
        if file_path.name.startswith('__'):
            continue  # Skip __init__.py and similar files
            
        module_name = file_path.stem
        full_module_path = str(file_path.absolute())
        
        try:
            # Dynamically import the module
            spec = importlib.util.spec_from_file_location(module_name, full_module_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Track how many entities were registered from this file
                entities_registered = 0
                
                # Look for BaseModel classes in the module
                for attribute_name in dir(module):
                    attribute = getattr(module, attribute_name)
                    
                    # Check if it's a class and a subclass of BaseModel
                    if (isinstance(attribute, type) and 
                        issubclass(attribute, BaseModel) and 
                        attribute != BaseModel and
                        attribute.__doc__):  # Only consider classes with docstrings
                        
                        # Register the entity type
                        register_entity_type(attribute_name, attribute)
                        entities_registered += 1
                        logger.info(f"Auto-registered entity type: {attribute_name}")
                
                logger.info(f"Successfully loaded entity type module: {module_name} (registered {entities_registered} entities)")
        except Exception as e:
            logger.error(f"Error loading entity type module {module_name}: {str(e)}")
    
    # Log total registered entity types after loading this directory
    logger.info(f"Total registered entity types after loading {directory_path}: {len(get_entity_types())}")
    for entity_name in get_entity_types().keys():
        logger.info(f"  - Registered entity: {entity_name}")


if __name__ == '__main__':
    main()
````

## File: mcp_config_sse_example.json
````json
{
    "mcpServers": {
        "graphiti": {
            "transport": "sse",
            "url": "http://localhost:8000/sse"
        }
    }
}
````

## File: mcp_config_stdio_example.json
````json
{
    "mcpServers": {
        "graphiti": {
            "transport": "stdio",
            "command": "uv",
            "args": [
                "run",
                "/ABSOLUTE/PATH/TO/graphiti_mcp_server.py",
                "--transport",
                "stdio"
            ],
            "env": {
                "NEO4J_URI": "bolt://localhost:7687",
                "NEO4J_USER": "neo4j",
                "NEO4J_PASSWORD": "demodemo",
                "OPENAI_API_KEY": "${OPENAI_API_KEY}",
                "MODEL_NAME": "gpt-4o"
            }
        }
    }
}
````

## File: mcp-projects.yaml
````yaml
# !! WARNING: This file is managed by the 'graphiti init' command. !!
# !! Avoid manual edits unless absolutely necessary.                 !!
#
# Maps project names to their configuration details.
# Paths should be absolute for reliability.
projects:
# Example Entry (will be added by 'graphiti init'):
# alpha:
#   config_file: /abs/path/to/project-alpha/mcp-config.yaml
#   root_dir: /abs/path/to/project-alpha
#   enabled: true 
  filesystem:
    root_dir: /Users/mateicanavra/Documents/.nosync/DEV/mcp-servers/mcp-filesystem
    config_file: 
      /Users/mateicanavra/Documents/.nosync/DEV/mcp-servers/mcp-filesystem/ai/graph/mcp-config.yaml
    enabled: true
````

## File: pyproject.toml
````toml
[project]
name = "mcp-server"
version = "0.1.0"
description = "Graphiti MCP Server"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "mcp>=1.5.0",
    "openai>=1.68.2",
    # For local development with local graphiti-core wheel:
    # "graphiti-core @ file:///dist/graphiti_core-0.8.5-py3-none-any.whl",
    # For production/normal use (uncomment this and comment out the above):
    "graphiti-core>=0.8.5",
    "ruamel.yaml>=0.17.21",
    "typer[all]>=0.9.0",
    "python-dotenv>=1.0.0",
]

[project.scripts]
graphiti = "graphiti_cli.main:app"

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

# Explicitly specify packages to include
[tool.setuptools.packages.find]
include = ["graphiti_cli*"]
exclude = ["entity_types*", "rules*", "llm_cache*"]
````

## File: repomix.config.json
````json
{
  "output": {
    "filePath": "graphiti-mcp-repo.md",
    "style": "markdown",
    "parsableStyle": false,
    "fileSummary": true,
    "directoryStructure": true,
    "removeComments": false,
    "removeEmptyLines": false,
    "compress": false,
    "topFilesLength": 5,
    "showLineNumbers": false,
    "copyToClipboard": false,
    "git": {
      "sortByChanges": true,
      "sortByChangesMaxCommits": 100
    }
  },
  "include": [],
  "ignore": {
    "useGitignore": true,
    "useDefaultPatterns": true,
    "customPatterns": [
      ".venv/**",
      "uv.lock",
      "dist/**",
      ".ai/.archive/**",
      "llm_cache/**",
      "scripts/README.md",
      "README.md",
      "docs/**"
    ]
  },
  "security": {
    "enableSecurityCheck": true
  },
  "tokenCount": {
    "encoding": "o200k_base"
  }
}
````
