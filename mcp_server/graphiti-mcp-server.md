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
    refactor-architecture-plan.md
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
rules/
  examples/
    graphiti-example-schema.md
  templates/
    project_schema_template.md
  graphiti-knowledge-graph-maintenance.md
  graphiti-mcp-core-rules.md
scripts/
  _yaml_helper.py
  graphiti
.env.example
.python-version
.repomixignore
base-compose.yaml
custom_servers.yaml
docker-compose.template.yml
docker-compose.yml
Dockerfile
entrypoint.sh
generate_compose.py
graphiti_mcp_server.py
mcp_config_sse_example.json
mcp_config_stdio_example.json
mcp-projects.yaml
pyproject.toml
repomix.config.json
```

# Files

## File: .ai/plans/refactor-architecture-plan.md
````markdown
Okay, here is the detailed, step-by-step implementation plan based on the "Central Generation with Project YAML Config (No Project `.env`)" architecture. This plan is designed for an expert implementation agent.

**Overall Goal:** Refactor the system to allow project repositories to define their custom MCP servers via a local YAML file, managed and run centrally from the `mcp-server` repository, ensuring only one `neo4j` and `graphiti-mcp-root` instance.

**Target Architecture Summary:** Central `mcp-server` repo runs `docker compose` using a generated `docker-compose.yml`. The generator reads a central `mcp-projects.yaml` registry (auto-managed by `graphiti init`) to find project-specific `mcp-config.yaml` files. These project configs define custom services, non-secret settings, and relative entity paths. The generator creates the final compose file, injecting project environment settings and volume mounts for project entities. `graphiti_mcp_server.py` loads both base and project-specific entities.

---

**Phase 1: Foundational Changes (Central Repo: `mcp-server`)**

**Step 1.1: Create Project Registry File** [COMPLETED]

*   **Objective:** Establish the central registry file.
*   **File:** `mcp-server/mcp-projects.yaml`
*   **Action:** Create this new file with the following initial content:
    ```yaml
    # !! WARNING: This file is managed by the 'graphiti init' command. !!
    # !! Avoid manual edits unless absolutely necessary.                 !!
    #
    # Maps project names to their configuration details.
    # Paths should be absolute for reliability.
    projects: {}
    # Example Entry (will be added by 'graphiti init'):
    # alpha:
    #   config_file: /abs/path/to/project-alpha/mcp-config.yaml
    #   root_dir: /abs/path/to/project-alpha
    #   enabled: true
    ```
*   **Acceptance Criteria:** The file `mcp-server/mcp-projects.yaml` exists with the specified structure and comments.

**Step 1.2: Enhance Generator (`generate_compose.py`) - Load Registry & Modify Loop** [COMPLETED]

*   **Objective:** Update the generator to read the new registry instead of `custom_servers.yaml`.
*   **File:** `mcp-server/generate_compose.py`
*   **Actions:**
    1.  Import `os` at the top.
    2.  Define `MCP_PROJECTS_FILE = 'mcp-projects.yaml'` near other constants (@LINE:13).
    3.  Remove the constant `CUSTOM_SERVERS_CONFIG_FILE = 'custom_servers.yaml'` (@LINE:12).
    4.  **Replace** the "Load Custom Server Configurations" block (approx. @LINE:42-@LINE:64):
        *   Load `MCP_PROJECTS_FILE` using `yaml.load()` (consider `YAML(typ='safe')` for this registry file).
        *   Handle `FileNotFoundError` (log warning, set `projects_registry = {'projects': {}}`).
        *   Handle parsing errors (log warning/error, exit or proceed cautiously).
    5.  **Replace** the outer loop structure in "Generate and Add Custom Service Definitions" (approx. @LINE:81):
        *   Remove the old loop `for n, server_conf in enumerate(custom_mcp_servers):`.
        *   Initialize an overall service index `overall_service_index = 0`.
        *   Start a new loop: `for project_name, project_data in projects_registry.get('projects', {}).items():`.
        *   Inside this loop, check `if not project_data.get('enabled', False): continue`.
        *   Load the project's config file: `project_config_path = project_data.get('config_file')`. Add error handling (file not found, parse error - log warning and skip project). Use `yaml.load()` (safe load).
        *   Start an inner loop: `for server_conf in project_config.get('services', []):`.
        *   Inside the inner loop, retrieve `server_id = server_conf.get('id')`. Add validation (skip service if no id).
        *   Increment `overall_service_index` at the end of the inner loop.
*   **Acceptance Criteria:**
    *   `generate_compose.py` attempts to load `mcp-projects.yaml`.
    *   The script iterates through enabled projects found in the registry.
    *   For each enabled project, it attempts to load the specified project configuration file.
    *   It then iterates through the `services` defined within that project configuration.
    *   The old `custom_servers.yaml` logic is removed.

**Step 1.3: Enhance Generator (`generate_compose.py`) - Resolve Paths & Add Volumes** [COMPLETED]

*   **Objective:** Calculate absolute entity paths and add volume mounts to service definitions.
*   **File:** `mcp-server/generate_compose.py`
*   **Actions:**
    1.  Define `CONTAINER_ENTITY_PATH = "/app/project_entities"` near constants (@LINE:13).
    2.  Inside the *inner* service loop (after getting `server_conf`):
        *   Get `relative_entity_dir = server_conf.get('entity_dir')`. Add validation (log warning/skip service if missing).
        *   Get `project_root_dir = project_data.get('root_dir')`. Add validation (log warning/skip project if missing).
        *   Calculate `abs_host_entity_path = os.path.abspath(os.path.join(project_root_dir, relative_entity_dir))`.
        *   Ensure the `new_service` map (created via `CommentedMap()`) has a `volumes` key initialized as an empty list if it doesn't exist.
        *   Append the volume string: `new_service.setdefault('volumes', []).append(f"{abs_host_entity_path}:{CONTAINER_ENTITY_PATH}:ro")`. (Using `:ro` for read-only mount is safer).
*   **Acceptance Criteria:**
    *   The generator calculates the absolute path on the host for the project's entity directory.
    *   A `volumes` section is added/appended to each generated custom service definition, mapping the host path to `/app/project_entities` (read-only).

**Step 1.4: Enhance Generator (`generate_compose.py`) - Update Environment Variables** [COMPLETED]

*   **Objective:** Set `MCP_ENTITY_TYPE_DIR` correctly and merge project-specific environment variables.
*   **File:** `mcp-server/generate_compose.py`
*   **Actions:**
    1.  Inside the inner service loop, locate the `env_vars = CommentedMap()` creation (@LINE:110).
    2.  Modify the setting of `MCP_ENTITY_TYPE_DIR` (@LINE:115): Set it directly to the container path: `env_vars['MCP_ENTITY_TYPE_DIR'] = CONTAINER_ENTITY_PATH`.
    3.  Remove the `if entity_types is not None:` block (@LINE:117-@LINE:121) if the `types` key in project config is no longer supported (confirm this - current `custom_servers.yaml` uses it @LINE:17). *If `types` is still needed*, ensure `MCP_ENTITY_TYPES` is added correctly to `env_vars`. **Plan Decision:** Let's assume `types` is deprecated for V1 simplicity; remove the block.
    4.  Get the project environment dictionary: `project_environment = server_conf.get('environment', {})`.
    5.  Merge `project_environment` into `env_vars`: `env_vars.update(project_environment)`. This ensures project-specific vars are added. *Note: `ruamel.yaml`'s `CommentedMap` update preserves order and comments if possible.*
*   **Acceptance Criteria:**
    *   The `MCP_ENTITY_TYPE_DIR` environment variable in generated services is set to `/app/project_entities`.
    *   Any key-value pairs defined under the `environment:` key in the project's `mcp-config.yaml` are added to the service's environment definition.
    *   The logic for the `types` key (and `MCP_ENTITY_TYPES` env var) is removed (or confirmed working if kept).

**Step 1.5: Enhance Generator (`generate_compose.py`) - Update Port/Container Name Logic** [COMPLETED]

*   **Objective:** Source ports and container names directly from project config or generator defaults.
*   **File:** `mcp-server/generate_compose.py`
*   **Actions:**
    1.  Inside the inner service loop, **remove** the lines defining `container_name_var` (@LINE:95) and `port_var` (@LINE:96).
    2.  **Replace** the `port_mapping` definition (@LINE:101):
        *   Get `port_default = server_conf.get('port_default')`.
        *   If `port_default is None`: `port_default = DEFAULT_PORT_START + overall_service_index + 1` (Use the index tracking overall services across all projects).
        *   Define `port_mapping = f"{port_default}:${{{DEFAULT_MCP_CONTAINER_PORT_VAR}}}"`.
        *   Ensure `new_service['ports'] = [port_mapping]` (@LINE:109) uses this new `port_mapping`.
    3.  **Replace** the `container_name` definition (@LINE:108):
        *   Get `container_name = server_conf.get('container_name')`.
        *   If `container_name is None`: `container_name = f"mcp-{server_id}"`.
        *   Set `new_service['container_name'] = container_name`.
*   **Acceptance Criteria:**
    *   The generator no longer looks for `*_PORT` or `*_CONTAINER_NAME` environment variables for custom services.
    *   Ports are assigned based on `port_default` in project config, or sequentially otherwise.
    *   Container names are assigned based on `container_name` in project config, or derived from the service `id` otherwise.

**Step 1.6: Enhance Generator (`generate_compose.py`) - Ensure Base Merge** [COMPLETED]

*   **Objective:** Verify that shared configurations are still inherited correctly.
*   **File:** `mcp-server/generate_compose.py`
*   **Actions:**
    1.  Confirm the line `new_service.add_yaml_merge([(0, custom_base_anchor_obj)])` (@LINE:126) is still present within the inner service loop and functions as expected.
*   **Acceptance Criteria:** Generated custom services in `docker-compose.yml` contain `<<: *graphiti-mcp-custom-base`.

**Step 1.7: Adapt Server Script (`graphiti_mcp_server.py`) - Entity Loading** [COMPLETED]

*   **Objective:** Enable loading of both base and project-specific entity types.
*   **File:** `mcp-server/graphiti_mcp_server.py`
*   **Actions:**
    1.  Inside the `initialize_server` function (after `args = parser.parse_args()` approx. @LINE:761):
    2.  Define the expected path for base types within the container: `container_base_entity_dir = "/app/entity_types/base"` (Ensure this matches Dockerfile copy destination).
    3.  Add logic to *always* load base types first:
        ```python
        if os.path.exists(container_base_entity_dir) and os.path.isdir(container_base_entity_dir):
            logger.info(f'Loading base entity types from: {container_base_entity_dir}')
            load_entity_types_from_directory(container_base_entity_dir)
        else:
            logger.warning(f"Base entity types directory not found at: {container_base_entity_dir}")
        ```
    4.  Add logic to load project-specific types if the directory is provided and different:
        ```python
        project_entity_dir = args.entity_type_dir # From --entity-type-dir arg
        if project_entity_dir:
             # Resolve paths to handle potential symlinks or relative paths inside container if needed
             abs_project_dir = os.path.abspath(project_entity_dir)
             abs_base_dir = os.path.abspath(container_base_entity_dir)
             if abs_project_dir != abs_base_dir:
                  if os.path.exists(abs_project_dir) and os.path.isdir(abs_project_dir):
                      logger.info(f'Loading project-specific entity types from: {abs_project_dir}')
                      load_entity_types_from_directory(abs_project_dir)
                  else:
                      logger.warning(f"Project entity types directory not found or not a directory: {abs_project_dir}")
             else:
                  logger.info(f"Project entity directory '{project_entity_dir}' is the same as base, skipping redundant load.")
        ```
    5.  Ensure `load_entity_types_from_directory` (@LINE:811) handles being called multiple times correctly (the current implementation using a global registry `@LINE:28` should be fine).
*   **Acceptance Criteria:**
    *   The server logs attempts to load base entities.
    *   If a custom service container has a volume mounted at `/app/project_entities` and `MCP_ENTITY_TYPE_DIR` set to that path, the server logs attempts to load entities from that directory as well.
    *   The final list of registered entities includes both base and project-specific types.

**Step 1.8: Verify Dockerfile** [COMPLETED]

*   **Objective:** Confirm base entities are copied into the image.
*   **File:** `Dockerfile` (provided in clipboard)
*   **Actions:**
    1.  Verify the line `COPY entity_types/ ./entity_types/` (@LINE:21) is present and correctly copies `mcp-server/entity_types/base` into `/app/entity_types/base` within the image.
*   **Acceptance Criteria:** The Docker build process includes the base entity type definitions.

---

**Phase 2: CLI and Project Workflow**

**Step 2.1: Create YAML Helper Script (Optional but Recommended)** [COMPLETED]

*   **Objective:** Provide a robust way for the bash `graphiti` script to modify `mcp-projects.yaml`.
*   **File:** `mcp-server/scripts/_yaml_helper.py` (New File)
*   **Actions:**
    1.  Create the Python script.
    2.  Use `argparse` to handle command-line arguments (e.g., `update-registry`, `--registry-file`, `--project-name`, `--root-dir`, `--config-file`).
    3.  Use `ruamel.yaml` (specifically `YAML()` for round-trip loading/dumping) to:
        *   Load the specified registry file.
        *   Navigate to `data['projects']`.
        *   Add or update the entry for the given project name with the provided absolute paths (`root_dir`, `config_file`) and set `enabled: true`.
        *   Write the modified data back to the registry file, preserving comments and formatting.
    4.  Include error handling (file not found, parsing errors, key errors).
*   **Acceptance Criteria:** A Python script exists that can reliably add/update project entries in `mcp-projects.yaml` via command-line arguments.

**Step 2.2: Enhance CLI (`scripts/graphiti`) - `init` Command** [COMPLETED]

*   **Objective:** Automate project setup and registration in `mcp-projects.yaml`.
*   **File:** `mcp-server/scripts/graphiti`
*   **Actions:**
    1.  Locate the `init` command block (@LINE:377).
    2.  **Remove** the call to `_link_dev_files "$TARGET_DIR"` (@LINE:387).
    3.  Add commands to create a template `mcp-config.yaml` in `$TARGET_DIR`. Example content:
        ```bash
        cat > "$TARGET_DIR/mcp-config.yaml" << EOF
        # Configuration for project: $PROJECT_NAME
        services:
          - id: ${PROJECT_NAME}-main # Service ID (used for default naming)
            # container_name: "custom-name" # Optional: Specify custom container name
            # port_default: 8001           # Optional: Specify custom host port
            group_id: "$PROJECT_NAME"     # Graph group ID
            entity_dir: "entities"       # Relative path to entity definitions within project
            # environment:                 # Optional: Add non-secret env vars here
            #   MY_FLAG: "true"
        EOF
        echo -e "Created template ${CYAN}$TARGET_DIR/mcp-config.yaml${NC}"
        ```
    4.  Add command to create the entity directory: `mkdir -p "$TARGET_DIR/entities"` and add a placeholder `.gitkeep` or example file.
    5.  Implement the registry update:
        *   Get absolute path of target dir: `ABS_TARGET_DIR=$(cd "$TARGET_DIR" && pwd)`
        *   Define absolute config path: `ABS_CONFIG_PATH="$ABS_TARGET_DIR/mcp-config.yaml"`
        *   Define central registry path: `CENTRAL_REGISTRY_PATH="$SOURCE_SERVER_DIR/mcp-projects.yaml"`
        *   Call the helper script (assuming Option A from thought process):
            ```bash
            echo -e "Updating central project registry: ${CYAN}$CENTRAL_REGISTRY_PATH${NC}"
            python "$SOURCE_SERVER_DIR/scripts/_yaml_helper.py" update-registry \
              --registry-file "$CENTRAL_REGISTRY_PATH" \
              --project-name "$PROJECT_NAME" \
              --root-dir "$ABS_TARGET_DIR" \
              --config-file "$ABS_CONFIG_PATH"
            # Add error checking based on python script exit code
            if [ $? -ne 0 ]; then
              echo -e "${RED}Error: Failed to update project registry.${NC}"
              # Decide whether to exit or just warn
              exit 1
            fi
            ```
*   **Acceptance Criteria:**
    *   `graphiti init <name> <dir>` creates `mcp-config.yaml` and `entities/` dir in `<dir>`.
    *   It correctly calls the YAML helper script (or other method) to add/update the project entry in `mcp-projects.yaml` with absolute paths.
    *   The obsolete linking step is removed.

**Step 2.3: Enhance CLI (`scripts/graphiti`) - Update Compose/Run Commands** [COMPLETED]

*   **Objective:** Ensure Docker Compose commands use the centrally generated file correctly.
*   **File:** `mcp-server/scripts/graphiti`
*   **Actions:**
    1.  Verify the `compose` command (@LINE:590) simply runs `python generate_compose.py` within the `$MCP_SERVER_DIR` context.
    2.  Verify the `up`, `down`, `restart` commands (@LINE:400, @LINE:471, @LINE:536) correctly `cd` to `$MCP_SERVER_DIR`, call `_ensure_docker_compose_file` (which runs the generator), and then execute `docker compose ...`.
*   **Acceptance Criteria:** The `compose`, `up`, `down`, `restart` commands function correctly with the new generator logic, operating within the central `mcp-server` directory.

**Step 2.4: Enhance CLI (`scripts/graphiti`) - Remove `link` Command** [COMPLETED]

*   **Objective:** Remove the obsolete symlinking functionality.
*   **File:** `mcp-server/scripts/graphiti`
*   **Actions:**
    1.  Delete the `_link_dev_files` function (approx. @LINE:58-@LINE:74).
    2.  Delete the `elif [[ "$COMMAND" == "link" ]];` block (approx. @LINE:579-@LINE:584).
    3.  Remove `"link"` from the command list in the `usage` function (@LINE:13).
    4.  Remove the "Arguments for link" section from the `usage` function (@LINE:25-@LINE:27).
    5.  Update the default command logic (@LINE:371): Change `COMMAND="${1:-link}"` to something sensible, perhaps default to showing usage or remove the default entirely: `COMMAND="${1}"`. If removing the default, add a check: `if [ -z "$COMMAND" ]; then usage; fi`. Let's choose to default to usage if no command is given.
        *   Change `@LINE:371` to `COMMAND="${1}"`.
        *   Add after `@LINE:372`:
            ```bash
            if [ -z "$COMMAND" ]; then
              echo -e "${YELLOW}No command specified.${NC}"
              usage
            fi
            ```
*   **Acceptance Criteria:**
    *   The `_link_dev_files` function is removed.
    *   The `link` command logic block is removed.
    *   The `usage` function no longer mentions the `link` command.
    *   Running `graphiti` with no command now shows the usage help text.

---

**Phase 3: Testing and Documentation**

**Step 3.1: Create Sample Projects** [COMPLETED]

*   **Objective:** Set up test projects to validate the new workflow.
*   **Actions:**
    1.  Create two new directories outside `mcp-server`, e.g., `/workspace/test-project-1` and `/workspace/test-project-2`.
    2.  In `test-project-1`:
        *   Create a basic `entities/` directory with a simple Pydantic model `TestEntity1.py`.
        *   Prepare a basic `mcp-config.yaml`:
            ```yaml
            # /workspace/test-project-1/mcp-config.yaml
            services:
              - id: test1-main
                port_default: 8051 # Assign a unique, available port
                container_name: "mcp-test1-service"
                group_id: "test-project-1"
                entity_dir: "entities"
                environment:
                  TEST_PROJECT_FLAG: "Project1"
            ```
    3.  In `test-project-2`:
        *   Create `entities/` with `TestEntity2.py`.
        *   Prepare `mcp-config.yaml`:
            ```yaml
            # /workspace/test-project-2/mcp-config.yaml
            services:
              - id: test2-aux
                # Rely on generator defaults for port/name
                group_id: "test-project-2"
                entity_dir: "entities"
                environment:
                  TEST_PROJECT_FLAG: "Project2"
                  ANOTHER_FLAG: "enabled"
            ```
*   **Acceptance Criteria:** Two distinct project directories exist, each containing a basic entity definition and an `mcp-config.yaml` file defining at least one service.

**Step 3.2: Test `graphiti init`** [COMPLETED]

*   **Objective:** Verify project initialization and registry update.
*   **Actions:**
    1.  Navigate to `/workspace/test-project-1`.
    2.  Run `../mcp-server/scripts/graphiti init test-project-1 .` (adjust path to `graphiti` as needed).
    3.  Verify console output indicates success and registry update.
    4.  Inspect `/workspace/mcp-server/mcp-projects.yaml`. Check if an entry for `test-project-1` exists with correct absolute paths and `enabled: true`.
    5.  Verify `.cursor/rules/graphiti` structure is created in `test-project-1`.
    6.  Repeat steps 1-5 for `test-project-2`.
*   **Acceptance Criteria:** Both test projects are successfully registered in `mcp-projects.yaml` with correct absolute paths. Rules directories are created.

**Step 3.3: Test `graphiti compose`** [COMPLETED]

*   **Objective:** Verify correct generation of the combined `docker-compose.yml`.
*   **Actions:**
    1.  Navigate to `/workspace/mcp-server`.
    2.  Run `scripts/graphiti compose`.
    3.  Verify console output indicates success.
    4.  Inspect the generated `docker-compose.yml`:
        *   Check for services `neo4j`, `graphiti-mcp-root`, `mcp-test1-main`, `mcp-test2-aux`.
        *   Verify `mcp-test1-main`:
            *   Has `container_name: "mcp-test1-service"`.
            *   Has `ports: ["8051:8000"]` (or correct mapping based on `MCP_ROOT_CONTAINER_PORT`).
            *   Has correct `volumes` mount for `/workspace/test-project-1/entities` to `/app/project_entities`.
            *   Has `environment` including `MCP_GROUP_ID: "test-project-1"`, `MCP_ENTITY_TYPE_DIR: "/app/project_entities"`, `TEST_PROJECT_FLAG: "Project1"`, and inherited base env vars.
        *   Verify `mcp-test2-aux`:
            *   Has default container name (e.g., `mcp-test2-aux`).
            *   Has default sequential port (e.g., `8002:8000`).
            *   Has correct `volumes` mount for `/workspace/test-project-2/entities`.
            *   Has `environment` including `MCP_GROUP_ID: "test-project-2"`, `MCP_ENTITY_TYPE_DIR: "/app/project_entities"`, `TEST_PROJECT_FLAG: "Project2"`, `ANOTHER_FLAG: "enabled"`, and inherited base env vars.
*   **Acceptance Criteria:** The generated `docker-compose.yml` accurately reflects the combination of `base-compose.yaml` and the configurations from both registered test projects.

**Step 3.4: Test `graphiti up`/`down`/`restart`** [COMPLETED]

*   **Objective:** Verify the full stack runs correctly.
*   **Actions:**
    1.  Navigate to `/workspace/mcp-server`.
    2.  Run `scripts/graphiti up -d` (detached mode for easier testing).
    3.  Check container status (`docker ps`). Verify all four containers (`neo4j`, `graphiti-mcp-root`, `mcp-test1-service`, `mcp-test2-aux`) are running.
    4.  Check logs (`docker logs mcp-test1-service`, `docker logs mcp-test2-aux`). Verify:
        *   Logs indicate loading of base entities.
        *   Logs indicate loading of project-specific entities (`TestEntity1`, `TestEntity2`).
        *   Correct `MCP_GROUP_ID` and other environment variables are logged/used.
    5.  (Optional) Test basic functionality via `curl` or MCP client if available.
    6.  Run `scripts/graphiti down`. Verify all containers are stopped and removed.
    7.  Run `scripts/graphiti restart -d`. Verify containers stop and restart successfully.
*   **Acceptance Criteria:** All defined services start correctly, load appropriate entities, use correct configurations, and can be managed via the `graphiti` CLI commands.

**Step 3.5: Update Documentation**

*   **Objective:** Reflect the new architecture and workflow in documentation.
*   **Files:** `README.md`, potentially other `.md` files. Remove/Update `docker-compose.template.yml`.
*   **Actions:**
    1.  Update `README.md`:
        *   Describe the new architecture (central control, project configs, registry).
        *   Explain the updated `graphiti init` workflow for setting up a project.
        *   Explain the structure and purpose of `mcp-config.yaml`.
        *   Explain the purpose of `mcp-projects.yaml` (and warn against manual editing).
        *   Document the `graphiti compose`, `up`, `down`, `restart` commands, emphasizing they run from the central repo.
        *   Remove references to the old `custom_servers.yaml` and symlinking (`link` command).
    2.  Decide fate of `docker-compose.template.yml`: Either remove it entirely or update it drastically to only show the *base* services and explain that custom services are added via the generation process. Removing might be cleaner.
    3.  Review rule files (`graphiti-mcp-core-rules.md`, etc.) for any outdated references to configuration or workflow.
*   **Acceptance Criteria:** Documentation accurately reflects the V1 architecture and usage. Obsolete documentation is removed or updated.
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

## File: scripts/_yaml_helper.py
````python
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
````

## File: scripts/graphiti
````
#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

# Define color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Function to display usage information
usage() {
  echo -e "${BOLD}Usage:${NC} graphiti [-h|--help] [COMMAND] [ARGS...]"
  echo
  echo -e "${BOLD}Commands:${NC}"
  echo -e "  ${CYAN}init${NC} PROJECT_NAME [DIR]        Initialize a project: create config and entities directory, and set up rules."
  echo -e "  ${CYAN}entity${NC} SET_NAME                Create a new entity type set with an example entity in the mcp-graphiti repo."
  echo -e "  ${CYAN}rules${NC} PROJECT_NAME [DIR]       Setup Cursor rules (.mdc files) for Graphiti in a target project directory."
  echo -e "  ${CYAN}up${NC} [-d] [--log-level LEVEL]    Start all containers using docker compose. Use -d for detached mode."
  echo -e "  ${CYAN}down${NC} [--log-level LEVEL]       Stop and remove all containers using docker compose."
  echo -e "  ${CYAN}restart${NC} [--log-level LEVEL]    Restart all containers: runs 'down' followed by 'up'."
  echo -e "  ${CYAN}compose${NC}                        Generate docker-compose.yml file from base-compose.yaml and mcp-projects.yaml."
  echo
  echo -e "${BOLD}Arguments for init & rules:${NC}"
  echo -e "  ${BOLD}PROJECT_NAME${NC}  Name of the target project (used for schema filename)."
  echo -e "  ${BOLD}DIR${NC}           Optional. Target project root directory. Defaults to current directory (.)."
  echo
  echo -e "${BOLD}Options:${NC}"
  echo -e "  ${BOLD}-h, --help${NC}                Show this help message and exit."
  echo -e "  ${BOLD}-d${NC}                        Run containers in detached mode (background) with 'up' command."
  echo -e "  ${BOLD}--log-level LEVEL${NC}         Set logging level (with up/down/restart). Valid values: debug, info, warn, error, fatal."
  echo -e "                                  Default: info"
  echo
  echo -e "${BOLD}Prerequisites:${NC}"
  echo -e "  The ${CYAN}MCP_GRAPHITI_REPO_PATH${NC} environment variable must be set to the"
  echo -e "  absolute path of your local mcp-graphiti repository."
  echo -e "  Example: ${YELLOW}export MCP_GRAPHITI_REPO_PATH=/path/to/mcp-graphiti${NC}"
  exit 0
}

# Function to convert set name to a class name (e.g., my-cool-set to MyCoolSetEntity)
set_name_to_class_name() {
  local set_name="$1"
  local class_name=""
  
  # Split by hyphens and underscores, capitalize each part, and join
  IFS='-_' read -ra PARTS <<< "$set_name"
  for part in "${PARTS[@]}"; do
    # Capitalize first letter of each part
    class_name+="$(tr '[:lower:]' '[:upper:]' <<< "${part:0:1}")${part:1}"
  done
  
  # Add "Entity" suffix
  echo "${class_name}Entity"
}

# --- Helper Function for Setting Up Rules ---
_setup_rules() {
  local PROJECT_NAME="$1"
  local TARGET_DIR="${2:-.}" # Default target directory to current if not provided

  # Validate PROJECT_NAME format (optional, but good practice)
  if ! [[ "$PROJECT_NAME" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    echo -e "${RED}Error: Invalid PROJECT_NAME. Use only letters, numbers, underscores, and hyphens.${NC}"
    exit 1
  fi

  # Define paths
  local CURSOR_RULES_DIR="$TARGET_DIR/.cursor/rules/graphiti"
  local SOURCE_CORE_RULE="$SOURCE_SERVER_DIR/rules/graphiti-mcp-core-rules.md"
  local SOURCE_MAINT_RULE="$SOURCE_SERVER_DIR/rules/graphiti-knowledge-graph-maintenance.md"
  local TARGET_CORE_RULE_LINK="$CURSOR_RULES_DIR/graphiti-mcp-core-rules.mdc"
  local TARGET_MAINT_RULE_LINK="$CURSOR_RULES_DIR/graphiti-knowledge-graph-maintenance.mdc"
  local TARGET_SCHEMA_FILE="$CURSOR_RULES_DIR/graphiti-$PROJECT_NAME-schema.mdc"
  local SCHEMA_TEMPLATE_FILE="$SOURCE_SERVER_DIR/rules/templates/project_schema_template.md"

  echo -e "Setting up Graphiti Cursor rules for project '${CYAN}$PROJECT_NAME${NC}' in ${CYAN}$TARGET_DIR${NC}"

  # Create target directory
  mkdir -p "$CURSOR_RULES_DIR"
  echo -e "Created rules directory: ${CYAN}$CURSOR_RULES_DIR${NC}"

  # Check source files exist before linking/generating
  if [ ! -f "$SOURCE_CORE_RULE" ]; then
    echo -e "${RED}Error: Source rule file not found: $SOURCE_CORE_RULE${NC}"
    exit 1
  fi
  if [ ! -f "$SOURCE_MAINT_RULE" ]; then
    echo -e "${RED}Error: Source rule file not found: $SOURCE_MAINT_RULE${NC}"
    exit 1
  fi
  if [ ! -f "$SCHEMA_TEMPLATE_FILE" ]; then
    echo -e "${RED}Error: Schema template file not found: $SCHEMA_TEMPLATE_FILE${NC}"
    exit 1
  fi

  # Create symlinks
  echo -e "Linking core rule: ${CYAN}$TARGET_CORE_RULE_LINK${NC} -> ${CYAN}$SOURCE_CORE_RULE${NC}"
  ln -sf "$SOURCE_CORE_RULE" "$TARGET_CORE_RULE_LINK"

  echo -e "Linking maintenance rule: ${CYAN}$TARGET_MAINT_RULE_LINK${NC} -> ${CYAN}$SOURCE_MAINT_RULE${NC}"
  ln -sf "$SOURCE_MAINT_RULE" "$TARGET_MAINT_RULE_LINK"

  # Generate template project schema file from template (.md -> .mdc)
  if [ -e "$TARGET_SCHEMA_FILE" ]; then
    echo -e "${YELLOW}Warning: Project schema file already exists, skipping template generation: $TARGET_SCHEMA_FILE${NC}"
  else
    echo -e "Generating template project schema file: ${CYAN}$TARGET_SCHEMA_FILE${NC}"
    sed "s/__PROJECT_NAME__/$PROJECT_NAME/g" "$SCHEMA_TEMPLATE_FILE" > "$TARGET_SCHEMA_FILE"
  fi

  echo -e "${GREEN}Graphiti Cursor rules setup complete for project '$PROJECT_NAME'.${NC}"
}

# --- Helper Function for Ensuring docker-compose.yml is Generated ---
_ensure_docker_compose_file() {
  local MCP_SERVER_DIR="$MCP_GRAPHITI_REPO_PATH/mcp_server"
  local DOCKER_COMPOSE_FILE="$MCP_SERVER_DIR/docker-compose.yml"
  
  echo -e "${BOLD}Ensuring docker-compose.yml is up-to-date...${NC}"
  
  # Check if we need to regenerate the file
  # Always regenerate for safety, but could add timestamp checks later if needed
  local CURRENT_DIR=$(pwd)
  
  # Change to mcp_server directory
  cd "$MCP_SERVER_DIR"
  
  # Run the generation script
  echo -e "Generating docker-compose.yml from templates..."
  "./generate_compose.py" > /dev/null 2>&1
  local RESULT=$?
  
  if [ $RESULT -ne 0 ]; then
    echo -e "${RED}Warning: Failed to generate docker-compose.yml file.${NC}"
    echo -e "${YELLOW}Continuing with existing file if it exists.${NC}"
  fi
  
  # Return to the original directory
  cd "$CURRENT_DIR"
  
  # Check if the file exists now
  if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    echo -e "${RED}Error: docker-compose.yml file does not exist and could not be generated.${NC}"
    return 1
  fi
  
  return 0
}

# Function to find the repository path based on script location
detect_repo_path() {
  # Get the real path of the script (resolving any symlinks)
  local SCRIPT_PATH=""
  
  # First attempt - use readlink if available
  if command -v readlink >/dev/null 2>&1; then
    # Check if readlink -f is supported (Linux/BSD)
    if readlink -f / >/dev/null 2>&1; then
      SCRIPT_PATH=$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || readlink -f "$0" 2>/dev/null)
    else
      # For macOS, which doesn't support readlink -f
      SCRIPT_PATH=$(perl -MCwd -e 'print Cwd::abs_path shift' "${BASH_SOURCE[0]}" 2>/dev/null || perl -MCwd -e 'print Cwd::abs_path shift' "$0" 2>/dev/null)
    fi
  fi
  
  # Fallback if readlink or perl failed
  if [ -z "$SCRIPT_PATH" ]; then
    SCRIPT_PATH="${BASH_SOURCE[0]:-$0}"
  fi
  
  echo "Debug: Script path resolved to: $SCRIPT_PATH" >&2
  
  # Get the script directory
  local SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
  echo "Debug: Script directory: $SCRIPT_DIR" >&2
  
  # Check if we're in the expected directory structure
  # We know the script should be in mcp_server/scripts/
  # First possibility: script is executed from its original location
  if [[ "$SCRIPT_DIR" == */mcp_server/scripts ]]; then
    # Go up two levels to get the repo root
    local REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
    echo "Debug: Detected repo root (direct): $REPO_ROOT" >&2
    
    if [ -d "$REPO_ROOT/mcp_server" ] && [ -d "$REPO_ROOT/mcp_server/entity_types" ]; then
      echo "$REPO_ROOT"
      return 0
    fi
  fi
  
  # Second possibility: we need to search for the repo structure
  # Try the current directory first
  local CURRENT_DIR="$(pwd)"
  echo "Debug: Checking current directory: $CURRENT_DIR" >&2
  
  if [ -d "$CURRENT_DIR/mcp_server" ] && [ -d "$CURRENT_DIR/mcp_server/entity_types" ]; then
    echo "Debug: Found repo structure in current directory" >&2
    echo "$CURRENT_DIR"
    return 0
  fi
  
  # Try one level up (in case we're in a subdirectory of the repo)
  local PARENT_DIR="$(cd .. && pwd)"
  echo "Debug: Checking parent directory: $PARENT_DIR" >&2
  
  if [ -d "$PARENT_DIR/mcp_server" ] && [ -d "$PARENT_DIR/mcp_server/entity_types" ]; then
    echo "Debug: Found repo structure in parent directory" >&2
    echo "$PARENT_DIR"
    return 0
  fi
  
  # If we got here, we couldn't find the repo root
  echo "Debug: Could not find repository structure" >&2
  return 1
}

# Function to offer saving the path to shell config
save_path_to_shell_config() {
  local PATH_TO_SAVE="$1"
  local CONFIG_FILE=""
  
  # Detect which shell config file to use
  if [ -n "$BASH_VERSION" ]; then
    CONFIG_FILE="$HOME/.bashrc"
  elif [ -n "$ZSH_VERSION" ]; then
    CONFIG_FILE="$HOME/.zshrc"
  else
    # Try to detect shell from process
    local SHELL_NAME="$(basename "$SHELL")"
    case "$SHELL_NAME" in
      bash) CONFIG_FILE="$HOME/.bashrc" ;;
      zsh) CONFIG_FILE="$HOME/.zshrc" ;;
      *) 
        echo "Could not determine your shell configuration file."
        echo "Please manually add the following line to your shell configuration:"
        echo "export MCP_GRAPHITI_REPO_PATH=\"$PATH_TO_SAVE\""
        return 1
        ;;
    esac
  fi
  
  # Ask user for confirmation before modifying their shell config
  echo -n "Would you like to permanently save MCP_GRAPHITI_REPO_PATH=\"$PATH_TO_SAVE\" to $CONFIG_FILE? (y/n): "
  read -r CONFIRM
  
  if [[ "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "" >> "$CONFIG_FILE"
    echo "# Added by graphiti script" >> "$CONFIG_FILE"
    echo "export MCP_GRAPHITI_REPO_PATH=\"$PATH_TO_SAVE\"" >> "$CONFIG_FILE"
    echo "Path saved to $CONFIG_FILE. Please restart your terminal or run 'source $CONFIG_FILE' to apply."
    return 0
  else
    echo "Path not saved. You'll need to set MCP_GRAPHITI_REPO_PATH manually each time."
    echo "You can do this by running: export MCP_GRAPHITI_REPO_PATH=\"$PATH_TO_SAVE\""
    return 1
  fi
}

# Function to validate and set the log level
validate_log_level() {
  local log_level=$1
  
  # Convert to lowercase for case-insensitive comparison
  log_level=$(echo "$log_level" | tr '[:upper:]' '[:lower:]')
  
  # Validate against allowed values
  case "$log_level" in
    debug|info|warn|error|fatal)
      echo "$log_level"
      return 0
      ;;
    *)
      echo -e "${RED}Error: Invalid log level '$log_level'. Valid values are: debug, info, warn, error, fatal.${NC}" >&2
      echo -e "Using default log level: info" >&2
      echo "info"
      return 1
      ;;
  esac
}

# Function to ensure dist directory is available for Docker build
#
# This function checks if the graphiti-core package is configured to use a local wheel
# If so, it ensures the dist directory exists and copies the wheel files to the mcp_server/dist directory
# This is used to ensure the graphiti-core package is built and available for use in the Docker containers
#
# If the graphiti-core package is configured to use the published package, this function will return 0 and no action will be taken
ensure_dist_for_build() {
  echo -e "${BOLD}Checking build configuration...${NC}"
  
  # Check if we're using local wheel in pyproject.toml
  if ! grep -q "graphiti-core @ file:///dist/" "$MCP_GRAPHITI_REPO_PATH/mcp_server/pyproject.toml" || \
     grep -q "^[^#]*graphiti-core>=" "$MCP_GRAPHITI_REPO_PATH/mcp_server/pyproject.toml"; then
    echo -e "${CYAN}Using published graphiti-core package. Skipping local wheel setup.${NC}"
    return 0
  fi
  
  echo -e "${CYAN}Local graphiti-core wheel configuration detected.${NC}"
  
  # Source and target paths
  local REPO_DIST="$MCP_GRAPHITI_REPO_PATH/dist"
  local SERVER_DIST="$MCP_GRAPHITI_REPO_PATH/mcp_server/dist"
  
  # Check if source dist exists
  if [ ! -d "$REPO_DIST" ]; then
    echo -e "${RED}Error: dist directory not found at $REPO_DIST${NC}"
    echo -e "Please build the graphiti-core wheel first."
    return 1
  fi
  
  # Create target directory if needed
  mkdir -p "$SERVER_DIST"
  
  # Copy wheel files
  echo -e "Copying wheel files from ${CYAN}$REPO_DIST${NC} to ${CYAN}$SERVER_DIST${NC}"
  cp -f "$REPO_DIST"/*.whl "$SERVER_DIST/"
  
  echo -e "${GREEN}Dist directory prepared for Docker build.${NC}"
  return 0
}

# Check for help flag
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
  usage
fi

# 1. Check and Determine Source Path
if [ -z "$MCP_GRAPHITI_REPO_PATH" ]; then
  echo -e "${YELLOW}MCP_GRAPHITI_REPO_PATH is not set. Attempting to auto-detect...${NC}"
  
  # Try to auto-detect the repository path based on script location
  AUTO_DETECTED_PATH=$(detect_repo_path)
  
  if [ -n "$AUTO_DETECTED_PATH" ]; then
    echo -e "Detected repository path: ${CYAN}$AUTO_DETECTED_PATH${NC}"
    export MCP_GRAPHITI_REPO_PATH="$AUTO_DETECTED_PATH"
    
    # Offer to save it permanently
    save_path_to_shell_config "$AUTO_DETECTED_PATH"
  else
    echo -e "${RED}Error: Could not auto-detect the repository path.${NC}"
    echo -e "Please set the ${CYAN}MCP_GRAPHITI_REPO_PATH${NC} environment variable manually."
    echo -e "Example: ${YELLOW}export MCP_GRAPHITI_REPO_PATH=/path/to/mcp-graphiti${NC}"
    exit 1
  fi
fi

SOURCE_SERVER_DIR="$MCP_GRAPHITI_REPO_PATH/mcp_server"
if [ ! -d "$SOURCE_SERVER_DIR" ]; then
  echo -e "${RED}Error: Source directory not found: $SOURCE_SERVER_DIR${NC}"
  echo -e "Please ensure ${CYAN}MCP_GRAPHITI_REPO_PATH${NC} is set correctly."
  exit 1
fi

# 2. Parse command and arguments
COMMAND="${1}" # No default command
shift || true # Shift arguments even if $1 was empty (no command given). Use || true to prevent exit on error if no args.

# If no command is provided, show usage
if [ -z "$COMMAND" ]; then
  echo -e "${YELLOW}No command specified.${NC}"
  usage
fi

# Handle commands using if/elif/else structure
if [[ "$COMMAND" == "init" ]]; then
  PROJECT_NAME="$1"
  TARGET_DIR="${2:-.}" # Default target directory to current if not provided

  if [ -z "$PROJECT_NAME" ]; then
    echo -e "${RED}Error: Missing PROJECT_NAME argument for init command.${NC}"
    echo -e "Usage: ${CYAN}graphiti init PROJECT_NAME [TARGET_DIRECTORY]${NC}"
    exit 1
  fi

  echo -e "Initializing Graphiti project '${CYAN}$PROJECT_NAME${NC}' in '${CYAN}$TARGET_DIR${NC}'..."

  # Create template mcp-config.yaml in the target directory
  cat > "$TARGET_DIR/mcp-config.yaml" << EOF
# Configuration for project: $PROJECT_NAME
services:
  - id: ${PROJECT_NAME}-main # Service ID (used for default naming)
    # container_name: "custom-name" # Optional: Specify custom container name
    # port_default: 8001           # Optional: Specify custom host port
    group_id: "$PROJECT_NAME"     # Graph group ID
    entity_dir: "entities"       # Relative path to entity definitions within project
    # environment:                 # Optional: Add non-secret env vars here
    #   MY_FLAG: "true"
EOF
  echo -e "Created template ${CYAN}$TARGET_DIR/mcp-config.yaml${NC}"

  # Create entities directory
  mkdir -p "$TARGET_DIR/entities"
  touch "$TARGET_DIR/entities/.gitkeep"
  echo -e "Created entities directory: ${CYAN}$TARGET_DIR/entities${NC}"

  # Set up rules
  _setup_rules "$PROJECT_NAME" "$TARGET_DIR"

  # Update central registry
  # Get absolute paths
  ABS_TARGET_DIR=$(cd "$TARGET_DIR" && pwd)
  ABS_CONFIG_PATH="$ABS_TARGET_DIR/mcp-config.yaml"
  CENTRAL_REGISTRY_PATH="$SOURCE_SERVER_DIR/mcp-projects.yaml"
  
  echo -e "Updating central project registry: ${CYAN}$CENTRAL_REGISTRY_PATH${NC}"
  "$SOURCE_SERVER_DIR/scripts/_yaml_helper.py" update-registry \
    --registry-file "$CENTRAL_REGISTRY_PATH" \
    --project-name "$PROJECT_NAME" \
    --root-dir "$ABS_TARGET_DIR" \
    --config-file "$ABS_CONFIG_PATH"
  
  # Check exit code from the Python script
  if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to update project registry.${NC}"
    exit 1
  fi

  echo -e "${GREEN}Graphiti project '$PROJECT_NAME' initialization complete.${NC}"
  exit 0

elif [[ "$COMMAND" == "up" ]]; then
  # Parse flags
  DETACHED=""
  LOG_LEVEL_OVERRIDE=""
  
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -d)
        DETACHED="-d"
        shift
        ;;
      --log-level)
        if [[ -z "$2" || "$2" == -* ]]; then
          echo -e "${RED}Error: --log-level requires a value${NC}"
          exit 1
        fi
        LOG_LEVEL_OVERRIDE=$(validate_log_level "$2")
        shift 2
        ;;
      *)
        echo -e "${RED}Error: Unknown option: $1${NC}"
        usage
        ;;
    esac
  done

  # We need to run docker-compose from the mcp_server directory
  MCP_SERVER_DIR="$MCP_GRAPHITI_REPO_PATH/mcp_server"
  
  if [ ! -d "$MCP_SERVER_DIR" ]; then
    echo -e "${RED}Error: mcp_server directory not found at $MCP_SERVER_DIR${NC}"
    exit 1
  fi

  # Save current directory to return to it afterwards
  CURRENT_DIR=$(pwd)
  
  echo -e "${BOLD}Starting Graphiti containers with docker compose...${NC}"
  echo -e "This will rebuild containers to incorporate any changes."
  echo -e "Running Docker Compose from: ${CYAN}$MCP_SERVER_DIR${NC}"
  
  # Change to mcp_server directory where docker-compose.yml is located
  cd "$MCP_SERVER_DIR"
  
  # Create environment variable exports for Docker Compose
  if [ -n "$LOG_LEVEL_OVERRIDE" ]; then
    echo -e "Setting log level to: ${CYAN}$LOG_LEVEL_OVERRIDE${NC}"
    export GRAPHITI_LOG_LEVEL="$LOG_LEVEL_OVERRIDE"
  fi
  
  # Ensure docker-compose.yml is generated before continuing
  _ensure_docker_compose_file || exit 1
  
  # Ensure dist directory is ready for build
  ensure_dist_for_build || exit 1
  
  # Run docker compose up with build and force-recreate flags
  if [ -n "$DETACHED" ]; then
    echo -e "${YELLOW}Running in detached mode.${NC}"
    docker compose up --build --force-recreate -d
  else
    docker compose up --build --force-recreate
  fi
  
  # Return to original directory
  cd "$CURRENT_DIR"
  
  echo -e "${GREEN}Docker compose up completed.${NC}"
  exit 0

elif [[ "$COMMAND" == "down" ]]; then
  # Parse flags
  LOG_LEVEL_OVERRIDE=""
  
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --log-level)
        if [[ -z "$2" || "$2" == -* ]]; then
          echo -e "${RED}Error: --log-level requires a value${NC}"
          exit 1
        fi
        LOG_LEVEL_OVERRIDE=$(validate_log_level "$2")
        shift 2
        ;;
      *)
        echo -e "${RED}Error: Unknown option: $1${NC}"
        usage
        ;;
    esac
  done
  
  # We need to run docker-compose from the mcp_server directory
  MCP_SERVER_DIR="$MCP_GRAPHITI_REPO_PATH/mcp_server"
  
  if [ ! -d "$MCP_SERVER_DIR" ]; then
    echo -e "${RED}Error: mcp_server directory not found at $MCP_SERVER_DIR${NC}"
    exit 1
  fi

  # Save current directory to return to it afterwards
  CURRENT_DIR=$(pwd)
  
  echo -e "${BOLD}Stopping and removing Graphiti containers...${NC}"
  echo -e "Running Docker Compose from: ${CYAN}$MCP_SERVER_DIR${NC}"
  
  # Change to mcp_server directory where docker-compose.yml is located
  cd "$MCP_SERVER_DIR"
  
  # Set environment variables for Docker Compose
  if [ -n "$LOG_LEVEL_OVERRIDE" ]; then
    echo -e "Setting log level to: ${CYAN}$LOG_LEVEL_OVERRIDE${NC}"
    export GRAPHITI_LOG_LEVEL="$LOG_LEVEL_OVERRIDE"
  fi
  
  # Run docker compose down to stop and remove containers
  docker compose down
  
  # Return to original directory
  cd "$CURRENT_DIR"
  
  echo -e "${GREEN}Docker compose down completed.${NC}"
  exit 0

elif [[ "$COMMAND" == "restart" ]]; then
  # Parse flags
  DETACHED=""
  LOG_LEVEL_OVERRIDE=""
  
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -d)
        DETACHED="-d"
        shift
        ;;
      --log-level)
        if [[ -z "$2" || "$2" == -* ]]; then
          echo -e "${RED}Error: --log-level requires a value${NC}"
          exit 1
        fi
        LOG_LEVEL_OVERRIDE=$(validate_log_level "$2")
        shift 2
        ;;
      *)
        echo -e "${RED}Error: Unknown option: $1${NC}"
        usage
        ;;
    esac
  done
  
  # We need to run docker-compose from the mcp_server directory
  MCP_SERVER_DIR="$MCP_GRAPHITI_REPO_PATH/mcp_server"
  
  if [ ! -d "$MCP_SERVER_DIR" ]; then
    echo -e "${RED}Error: mcp_server directory not found at $MCP_SERVER_DIR${NC}"
    exit 1
  fi

  # Save current directory to return to it afterwards
  CURRENT_DIR=$(pwd)
  
  echo -e "${BOLD}Restarting Graphiti containers: first down, then up...${NC}"
  echo -e "Running Docker Compose from: ${CYAN}$MCP_SERVER_DIR${NC}"
  
  # Set environment variables for Docker Compose
  if [ -n "$LOG_LEVEL_OVERRIDE" ]; then
    echo -e "Setting log level to: ${CYAN}$LOG_LEVEL_OVERRIDE${NC}"
    export GRAPHITI_LOG_LEVEL="$LOG_LEVEL_OVERRIDE"
  fi
  
  # Change to mcp_server directory where docker-compose.yml is located
  cd "$MCP_SERVER_DIR"
  
  # First run docker compose down
  echo -e "${CYAN}Stopping containers...${NC}"
  docker compose down
  
  # Ensure docker-compose.yml is generated before continuing
  _ensure_docker_compose_file || exit 1
  
  # Ensure dist directory is ready for build
  ensure_dist_for_build || exit 1
  
  # Then run docker compose up
  echo -e "${CYAN}Starting containers...${NC}"
  if [ -n "$DETACHED" ]; then
    echo -e "${YELLOW}Running in detached mode.${NC}"
    docker compose up --build --force-recreate -d
  else
    docker compose up --build --force-recreate
  fi
  
  # Return to original directory
  cd "$CURRENT_DIR"
  
  echo -e "${GREEN}Restart sequence completed.${NC}"
  exit 0

elif [[ "$COMMAND" == "entity" ]]; then
  # Get SET_NAME from first remaining argument
  SET_NAME="$1"
  
  # Input validation
  if [ -z "$SET_NAME" ]; then
    echo -e "${RED}Error: Missing SET_NAME argument.${NC}"
    echo -e "Usage: ${CYAN}graphiti entity SET_NAME${NC}"
    exit 1
  fi
  
  # Validate SET_NAME format (only allow letters, numbers, underscores, hyphens)
  if ! [[ "$SET_NAME" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    echo -e "${RED}Error: Invalid SET_NAME. Use only letters, numbers, underscores, and hyphens.${NC}"
    exit 1
  fi
  
  # Path construction
  ENTITY_TYPES_DIR="$SOURCE_SERVER_DIR/entity_types"
  NEW_SET_DIR="$ENTITY_TYPES_DIR/$SET_NAME"
  
  # Check if directory already exists
  if [ -d "$NEW_SET_DIR" ]; then
    echo "Error: Entity type set '$SET_NAME' already exists at: $NEW_SET_DIR"
    exit 1
  fi
  
  # Create the new directory
  mkdir -p "$NEW_SET_DIR"
  echo "Created entity type set directory: $NEW_SET_DIR"
  
  # Generate class name from SET_NAME
  CLASS_NAME=$(set_name_to_class_name "$SET_NAME")
  
  # Create entity file using the custom_entity_example.py as a template
  ENTITY_FILE="$NEW_SET_DIR/entity.py"
  TEMPLATE_FILE="$SOURCE_SERVER_DIR/entity_types/example/custom_entity_example.py"
  
  # Check if template file exists
  if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "Warning: Template file not found: $TEMPLATE_FILE"
    echo "Creating a minimal entity file instead."
    
    # Create a minimal entity file
    cat > "$ENTITY_FILE" << EOF
from pydantic import BaseModel, Field


class $CLASS_NAME(BaseModel):
    """Example entity for the '$SET_NAME' set."""
    
    example_field: str = Field(
        ...,
        description='An example field.',
    )
EOF
  else
    # Read the template and replace the class name
    sed -e "s/class Product/class $CLASS_NAME/" \
        -e "s/A Product/$CLASS_NAME/" \
        -e "s/products/${SET_NAME}s/" \
        -e "s/the product/the ${SET_NAME}/" \
        "$TEMPLATE_FILE" > "$ENTITY_FILE"
    
    echo "Created entity file using template: $ENTITY_FILE"
  fi
  
  echo "Entity set '$SET_NAME' successfully created."
  exit 0

elif [[ "$COMMAND" == "rules" ]]; then
  PROJECT_NAME="$1"
  TARGET_DIR="${2:-.}" # Default target directory to current if not provided

  if [ -z "$PROJECT_NAME" ]; then
    echo "Error: Missing PROJECT_NAME argument for rules command."
    echo "Usage: graphiti rules PROJECT_NAME [TARGET_DIRECTORY]"
    exit 1
  fi

  # Call the helper function (validation is inside the helper)
  _setup_rules "$PROJECT_NAME" "$TARGET_DIR"
  exit 0

elif [[ "$COMMAND" == "compose" ]]; then
  # We need to run generate_compose.py from the mcp_server directory
  MCP_SERVER_DIR="$MCP_GRAPHITI_REPO_PATH/mcp_server"
  
  if [ ! -d "$MCP_SERVER_DIR" ]; then
    echo -e "${RED}Error: mcp_server directory not found at $MCP_SERVER_DIR${NC}"
    exit 1
  fi

  # Save current directory to return to it afterwards
  CURRENT_DIR=$(pwd)
  
  echo -e "${BOLD}Generating docker-compose.yml from templates...${NC}"
  echo -e "Running from: ${CYAN}$MCP_SERVER_DIR${NC}"
  
  # Change to mcp_server directory where the script is located
  cd "$MCP_SERVER_DIR"
  
  # Run the generation script
  "./generate_compose.py"
  RESULT=$?
  
  # Check the result and provide appropriate feedback
  if [ $RESULT -eq 0 ]; then
    echo -e "${GREEN}Successfully generated docker-compose.yml file.${NC}"
  else
    echo -e "${RED}Error: Failed to generate docker-compose.yml file.${NC}"
  fi
  
  # Return to original directory
  cd "$CURRENT_DIR"
  
  exit $RESULT

else
  echo -e "${RED}Error: Unknown command '$COMMAND'${NC}"
  usage
fi
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

## File: docker-compose.template.yml
````yaml
# docker-compose.template.yml
# This is a template file for setting up Graphiti MCP servers with Docker Compose.
# Copy this file to docker-compose.yml and customize as needed for your environment.
version: "3.8"

# --- Base Definitions ---
# These YAML anchors provide reusable configuration blocks

x-mcp-healthcheck:
    &mcp-healthcheck # Healthcheck for all MCP servers
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
    # Neo4j connection details shared by all MCP servers
    NEO4J_URI: "bolt://neo4j:${NEO4J_CONTAINER_BOLT_PORT:-7687}"
    NEO4J_USER: "${NEO4J_USER}" # Required by neo4j service
    NEO4J_PASSWORD: "${NEO4J_PASSWORD}" # Required by neo4j service 

x-mcp-env: &mcp-env 
    # Common environment variables for all MCP servers
    MODEL_NAME: "${MODEL_NAME:-gpt-4o}"
    OPENAI_API_KEY: ${OPENAI_API_KEY?Please set OPENAI_API_KEY in your .env file}
    OPENAI_BASE_URL: ${OPENAI_BASE_URL:-https://api.openai.com/v1}
    GRAPHITI_LOG_LEVEL: ${GRAPHITI_LOG_LEVEL:-info}
    PATH: "/app:/root/.local/bin:${PATH}"

# Base definition for ALL graphiti MCP services
x-graphiti-mcp-base: &graphiti-mcp-base
    build:
        context: .
        dockerfile: Dockerfile # Dockerfile must include the entrypoint.sh script
    env_file:
        - path: .env
          required: true # Required by default (can be set to false if you want to provide all env vars directly)
    environment:
        <<: [*mcp-env, *neo4j-connection] # Merge environment variable blocks
    healthcheck:
        <<: *mcp-healthcheck
    restart: unless-stopped
    # Command execution is handled by entrypoint.sh using environment variables

# Base for custom MCP services that depend on the root service
x-graphiti-mcp-custom-base: &graphiti-mcp-custom-base
    <<: *graphiti-mcp-base # Inherit base configuration
    depends_on:
        neo4j:
            condition: service_healthy
        graphiti-mcp-root: # All custom services depend on the root service
            condition: service_healthy

# --- Services ---
services:
    # --- Database Service ---
    neo4j:
        image: neo4j:5.26.0
        container_name: ${NEO4J_CONTAINER_NAME:-graphiti-mcp-neo4j}
        ports:
            - "${NEO4J_HOST_HTTP_PORT:-7474}:${NEO4J_CONTAINER_HTTP_PORT:-7474}" # HTTP interface
            - "${NEO4J_HOST_BOLT_PORT:-7687}:${NEO4J_CONTAINER_BOLT_PORT:-7687}" # Bolt protocol
        environment:
            - NEO4J_AUTH=${NEO4J_USER?Please set NEO4J_USER in your .env file}/${NEO4J_PASSWORD?Please set NEO4J_PASSWORD in your .env file}
            - NEO4J_server_memory_heap_initial__size=${NEO4J_HEAP_INITIAL:-512m}
            - NEO4J_server_memory_heap_max__size=${NEO4J_HEAP_MAX:-1G}
            - NEO4J_server_memory_pagecache_size=${NEO4J_PAGECACHE:-512m}
        volumes:
            - neo4j_data:/data # Persists graph data
            - neo4j_logs:/logs # Stores Neo4j logs
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
    # This is the primary MCP server instance required for all setups
    graphiti-mcp-root:
        <<: *graphiti-mcp-base
        container_name: ${MCP_ROOT_CONTAINER_NAME:-graphiti-mcp-root}
        depends_on:
            neo4j:
                condition: service_healthy
        ports:
            - "${MCP_ROOT_HOST_PORT:-8000}:${MCP_ROOT_CONTAINER_PORT:-8000}"
        environment:
            # Configuration for entrypoint.sh
            MCP_GROUP_ID: "root" # Unique group ID for this MCP instance
            MCP_USE_CUSTOM_ENTITIES: "true"
            MCP_ENTITY_TYPE_DIR: "entity_types/base"
            # MCP_ENTITY_TYPES: "" # Use this to specify specific entity types
            # NEO4J_DESTROY_ENTIRE_GRAPH can be set to "true" to clear ALL Neo4j data (DANGER!)
            # Not recommended to define here - use .env temporarily if needed

    # --- Custom MCP Server Examples ---
    # NAMING CONVENTION:
    # - Service name: mcp-[project-name] (e.g., mcp-myproject)
    # - Container name: MCP_[PROJECT]_CONTAINER_NAME in .env (e.g., MCP_MYPROJECT_CONTAINER_NAME=mcp-myproject)
    # - Port: MCP_HOST_PORT_[PROJECT] in .env, incrementing from 8001 (e.g., MCP_HOST_PORT_MYPROJECT=8001)
    # - Group ID: A unique identifier for your project's knowledge graph (e.g., "myproject")

    # --- Custom MCP Server Example 1 (Optional) ---
    # Uncomment this section to add a custom MCP server instance
    # mcp-custom-1:
    #     <<: *graphiti-mcp-custom-base
    #     container_name: ${MCP_CUSTOM_1_CONTAINER_NAME}
    #     ports:
    #         - "${MCP_CUSTOM_HOST_PORT_1}:${MCP_ROOT_CONTAINER_PORT:-8000}"
    #     environment:
    #         MCP_GROUP_ID: "custom-group-1" # Unique ID for this knowledge graph
    #         MCP_USE_CUSTOM_ENTITIES: "true"
    #         MCP_ENTITY_TYPE_DIR: "entity_types/custom_1"
    #         # MCP_ENTITY_TYPES: "" # Use this to specify specific entity types
    #         # NEO4J_DESTROY_ENTIRE_GRAPH can be set to "true" to clear ALL Neo4j data
    #         # Not recommended to define here - use .env temporarily if needed

    # --- Custom MCP Server Example 2 (Optional) ---
    # This example shows using specific entity types instead of a directory
    # mcp-custom-2:
    #     <<: *graphiti-mcp-custom-base
    #     container_name: ${MCP_CUSTOM_2_CONTAINER_NAME}
    #     ports:
    #         - "${MCP_CUSTOM_HOST_PORT_2}:${MCP_ROOT_CONTAINER_PORT:-8000}"
    #     environment:
    #         MCP_GROUP_ID: "another-custom-group"
    #         MCP_USE_CUSTOM_ENTITIES: "true"
    #         # MCP_ENTITY_TYPE_DIR: ""
    #         MCP_ENTITY_TYPES: "SpecificTypeA SpecificTypeB"
    #         # NEO4J_DESTROY_ENTIRE_GRAPH can be set to "true" to clear ALL Neo4j data
    #         # Not recommended to define here - use .env temporarily if needed

    # --- Add your custom MCP server definitions below ---
    # Copy one of the examples above and modify as needed
    # Each service must have a unique:
    # - container_name
    # - port mapping
    # - MCP_GROUP_ID

# --- Persistent Storage ---
volumes:
    neo4j_data: # Persists Neo4j graph data between container restarts
    neo4j_logs: # Persists Neo4j logs between container restarts
````

## File: docker-compose.yml
````yaml
# Generated by generate_compose.py
# Do not edit this file directly. Modify base-compose.yaml or project-specific mcp-config.yaml files instead.

# --- Custom MCP Services Info ---
# Default Ports: Assigned sequentially starting from 8001 (8000 + index + 1)
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
  mcp-test-project-1-main:
    <<: *graphiti-mcp-custom-base
    container_name: mcp-test-project-1-main
    ports:
      - 8001:${MCP_ROOT_CONTAINER_PORT:-8000}
    volumes:
      - /Users/mateicanavra/Documents/.nosync/DEV/mcp-servers/test-project-1/entities:/app/project_entities:ro
    environment:
      MCP_GROUP_ID: test-project-1
      MCP_USE_CUSTOM_ENTITIES: 'true'
      MCP_ENTITY_TYPE_DIR: /app/project_entities
  mcp-test-project-2-main:
    <<: *graphiti-mcp-custom-base
    container_name: mcp-test-project-2-main
    ports:
      - 8002:${MCP_ROOT_CONTAINER_PORT:-8000}
    volumes:
      - /Users/mateicanavra/Documents/.nosync/DEV/mcp-servers/test-project-2/entities:/app/project_entities:ro
    environment:
      MCP_GROUP_ID: test-project-2
      MCP_USE_CUSTOM_ENTITIES: 'true'
      MCP_ENTITY_TYPE_DIR: /app/project_entities
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
  CMD_ARGS="$CMD_ARGS --entity-type-dir \"$MCP_ENTITY_TYPE_DIR\""
fi

# --entity-types (Optional space-separated list)
# Assumes the python script handles a space-separated list after the flag.
if [ -n "$MCP_ENTITY_TYPES" ]; then
   CMD_ARGS="$CMD_ARGS --entity-types $MCP_ENTITY_TYPES"
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

## File: generate_compose.py
````python
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
# Path inside container where project entities will be mounted
CONTAINER_ENTITY_PATH = "/app/project_entities"

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
log_level = getattr(logging, log_level_str, logging.INFO)

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)
logger.info(f'Logging configured with level: {logging.getLevelName(log_level)}')

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

    args = parser.parse_args()

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
  test:
    root_dir: 
      /Users/mateicanavra/Documents/.nosync/DEV/mcp-servers/mcp-graphiti/mcp_server/test
    config_file: 
      /Users/mateicanavra/Documents/.nosync/DEV/mcp-servers/mcp-graphiti/mcp_server/test/mcp-config.yaml
    enabled: true
# Example Entry (will be added by 'graphiti init'):
# alpha:
#   config_file: /abs/path/to/project-alpha/mcp-config.yaml
#   root_dir: /abs/path/to/project-alpha
#   enabled: true 
  test-project-1:
    root_dir: /Users/mateicanavra/Documents/.nosync/DEV/mcp-servers/test-project-1
    config_file: 
      /Users/mateicanavra/Documents/.nosync/DEV/mcp-servers/test-project-1/mcp-config.yaml
    enabled: true
  test-project-2:
    root_dir: /Users/mateicanavra/Documents/.nosync/DEV/mcp-servers/test-project-2
    config_file: 
      /Users/mateicanavra/Documents/.nosync/DEV/mcp-servers/test-project-2/mcp-config.yaml
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
]
````

## File: repomix.config.json
````json
{
  "output": {
    "filePath": "graphiti-mcp-server.md",
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
