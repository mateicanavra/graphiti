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

**Phase 5: Cleanup**

9.  **Remove Old Scripts:**
    *   Action: Delete the following files:
        *   `mcp_server/scripts/graphiti` (The original Bash script)
        *   `mcp_server/scripts/_yaml_helper.py`
        *   `mcp_server/generate_compose.py`
    *   Files Involved: `mcp_server/scripts/graphiti`, `mcp_server/scripts/_yaml_helper.py`, `mcp_server/generate_compose.py`
    *   Acceptance: The specified files no longer exist in the repository.

**Phase 6: Verification and Testing**

10. **Functional Testing:**
    *   Action: Execute the *new* Python `graphiti` command for each subcommand and option combination previously supported by the Bash script. Verify the outputs and side effects.
        *   `graphiti init test-py-proj ./temp_test_py_proj` -> Check created files/dirs (ai/graph/mcp-config.yaml, ai/graph/entities/), registry update.
        *   `graphiti entity my-new-set ./temp_test_py_proj` -> Check created directory/file in `temp_test_py_proj/ai/graph/entities/my-new-set/`.
        *   `graphiti rules test-py-proj ./temp_test_py_proj` -> Check symlinks and schema file in `.cursor/`.
        *   `graphiti compose` -> Check `docker-compose.yml` generation.
        *   `graphiti up`
        *   `graphiti up --log-level debug` -> Check container logs for DEBUG level.
        *   `graphiti down`
        *   `graphiti restart`
        *   `graphiti reload <service_name>` (Use a valid service name from generated compose file).
    *   Files Involved: All CLI files, `mcp-projects.yaml`, `docker-compose.yml`, Docker environment, test project directories.
    *   Acceptance Criteria:
        *   Each command executes without Python errors.
        *   The command output (messages, warnings, errors) is informative and matches the intent of the original script.
        *   File system operations (creating projects, entities, rules) produce the correct files and structures.
        *   The init command creates the ai/graph directory structure with mcp-config.yaml and entities directory inside it.
        *   The entity command creates entities within the project's ai/graph/entities/ directory.
        *   Docker commands (`up`, `down`, `restart`, `reload`) successfully interact with Docker Compose and produce the expected container states.
        *   The `--log-level` option correctly sets the `GRAPHITI_LOG_LEVEL` environment variable for Docker Compose commands, overriding `.env` settings, and resulting logs reflect the chosen level.
        *   The generated `docker-compose.yml` is identical to the one generated by the old script (or functionally equivalent).
        *   The `mcp-projects.yaml` file is updated correctly by `init` with the path to ai/graph/mcp-config.yaml.

This plan provides a structured approach to perform the migration, breaking it down into manageable phases and steps with clear acceptance criteria.

**Progress Update (April 2025):**
- Completed all of Phase 1: Setup and Project Structure ✅
  - Created proper package structure in `mcp_server/graphiti_cli/` with necessary files
  - Updated `pyproject.toml` with required dependencies and configurations
  - Successfully installed the package in development mode using `pip install -e .`

- Completed Phase 2: Implement Core and YAML Utilities ✅
  - Completed Step 5: Implemented core utilities in `core.py` ✅
    - Added ANSI color constants, `LogLevel` enum, path finding functions
    - Implemented robust subprocess execution with `run_command()`
    - Added Docker Compose helpers and build utilities
  - Completed Step 6: Implemented YAML utilities in `yaml_utils.py` ✅
    - Added YAML file handling with `load_yaml_file()` and `write_yaml_file()`
    - Implemented `update_registry_logic()` from _yaml_helper.py
    - Implemented `generate_compose_logic()` from generate_compose.py
    - Added proper error handling and input validation

- Completed Phase 3: Implement Command Logic ✅
  - Completed Step 7: Implemented command functions in `commands.py` ✅
    - Implemented Docker commands: docker_up, docker_down, docker_restart, docker_reload, docker_compose_generate
    - Implemented project management commands: init_project, setup_rules, create_entity_set
    - Added robust error handling, input validation, and colorful console output
    - Ensured proper integration with core.py and yaml_utils.py utilities

- Completed Phase 4: Define CLI Interface ✅
  - Completed Step 8: Implemented Typer CLI interface in `main.py` ✅
    - Created Typer app with command definitions for all functions
    - Added proper argument and option handling with validation
    - Implemented callback for repository root verification
    - Added help text and documentation for all commands
  
- Phase 6: Verification and Testing 🔄 CURRENT PHASE
  - Successfully tested project management commands:
    - `init` command: ✅ Confirmed it creates the ai/graph directory structure with mcp-config.yaml and entities directory
    - `entity` command: ✅ Verified it correctly creates entity sets within the project's ai/graph/entities directory
    - `rules` command: ✅ Verified it correctly creates/updates Cursor rules symlinks and schema template
    - `compose` command: ✅ Verified docker-compose.yml generation with proper content and error handling
  - Successfully tested Docker environment commands:
    - `down` command: ✅ Verified it properly stops and removes all containers
    - `up` command: ✅ Tested with default settings, detached mode (-d), and custom log levels
  - Next commands to test:
    - Remaining Docker commands: `restart`, `reload`
  - Test environment:
    - Using dedicated test directory at `~/Desktop/graphiti_cli_test/temp_cli_test_proj`
    - Running via module execution: `python -m mcp_server.graphiti_cli.main [command]`
  - Environment configuration:
    - Added missing `MCP_PORT=8000` to `.env` file to ensure proper container port mapping

**Next Steps:**
1. Test remaining Docker environment management commands (`restart`, `reload`)
2. Verify error handling and validation with edge cases
3. Proceed to Phase 5 (Cleanup) after completing all tests

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