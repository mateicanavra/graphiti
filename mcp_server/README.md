# Graphiti MCP Server Orchestrator

This repository contains the central orchestrator for deploying and managing the Graphiti Model Context Protocol (MCP) ecosystem. Its primary role is to manage the deployment of:

1.  A shared **Neo4j** database instance.
2.  A **root Graphiti MCP server** (`graphiti-mcp-root`) providing base functionality.
3.  Multiple **project-specific Graphiti MCP server instances** defined in external project directories.

It uses a configuration-driven approach (`mcp-projects.yaml`) and helper scripts (`./scripts/graphiti`) to generate a unified `docker-compose.yml` file for all services.

## Architecture Overview

*   **`mcp-projects.yaml`**: A central registry mapping project names to their configurations, including paths to their specific entity definitions and root directories. **Requires manual editing after cloning.**
*   **`base-compose.yaml`**: A Docker Compose template defining base service configurations (like Neo4j settings, common MCP server environment variables) using YAML anchors.
*   **`scripts/graphiti`**: A bash script that reads `mcp-projects.yaml` and `base-compose.yaml` to generate the final `docker-compose.yml` and provides commands (`compose`, `up`, `down`, `logs`, `ps`) to manage the entire stack of services.
*   **`Dockerfile` / `graphiti_mcp_server.py`**: Defines the container image and runs the code for the *root* MCP server instance (`graphiti-mcp-root`) and serves as the base for project-specific instances unless they override.
*   **`graphiti_cli/`**: Contains a Python-based CLI (`graphiti`) installable via `uv pip install .`. This offers some utility commands but is **not** the primary tool for managing the Docker services orchestrated by this repository (use `./scripts/graphiti` for that).

## Prerequisites

Ensure you have the following installed:

1.  **Python**: Version 3.11 or higher (for running scripts).
2.  **uv**: The Python package installer/resolver (`curl -LsSf https://astral.sh/uv/install.sh | sh`).
3.  **Docker**: The containerization platform.
4.  **Docker Compose**: The tool for defining and running multi-container Docker applications (usually included with Docker Desktop).
5.  **Git**: For cloning the repository.

## Setup & Configuration

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url> # Replace with the actual URL
    cd graphiti-mcp-orchestrator # Or the name you cloned it as
    ```

2.  **Create & Activate Virtual Environment:**
    This is needed for the Python scripts used by the orchestrator.
    ```bash
    uv venv
    source .venv/bin/activate # (Adjust for your OS/shell if needed)
    ```

3.  **Install Dependencies:**
    Installs dependencies required by the orchestration scripts and the underlying server code.
    ```bash
    uv sync
    ```

4.  **Configure Environment Secrets (`.env`):**
    Copy the example file and add your secrets.
    ```bash
    cp .env.example .env
    ```
    Edit `.env` and provide:
    *   `OPENAI_API_KEY`: Your OpenAI API key (required for LLM features).
    *   `MODEL_NAME`: e.g., `gpt-4o` (required).
    *   `NEO4J_USER` / `NEO4J_PASSWORD`: Credentials for the Neo4j database (defaults match the included Neo4j service).
    *   Optionally adjust other variables like `NEO4J_HOST_HTTP_PORT`, `NEO4J_HOST_BOLT_PORT`, `MCP_ROOT_HOST_PORT` if defaults conflict.

5.  **Configure Project Registry (`mcp-projects.yaml`) - CRITICAL STEP:**
    This file tells the orchestrator where to find the configuration and entity definitions for each project-specific MCP server you want to run.

    **You MUST edit `mcp-projects.yaml` after cloning.**

    *   Open `mcp-projects.yaml`.
    *   For each project listed under the `projects:` key:
        *   Verify the `enabled: true` status for projects you want to run.
        *   **Crucially, update the `config_file` and `root_dir` paths to be correct, absolute paths on the machine where you will run the `./scripts/graphiti` commands.** These paths are used to mount project-specific files (like entity definitions) into their respective Docker containers.
    *   Example project entry:
        ```yaml
        projects:
          mcp-filesystem:
            config_file: /ABSOLUTE/PATH/TO/mcp-filesystem/mcp-config.yaml # EDIT THIS PATH
            root_dir: /ABSOLUTE/PATH/TO/mcp-filesystem # EDIT THIS PATH
            enabled: true
        ```
    *   **Failure to set correct absolute paths here is the most common reason for errors.**

## Core Orchestration Workflow (`./scripts/graphiti`)

The primary way to manage the services defined by this orchestrator is via the `scripts/graphiti` bash script. Ensure your virtual environment is active (`source .venv/bin/activate`).

1.  **Generate Docker Compose File:**
    Reads `mcp-projects.yaml` and `base-compose.yaml` to create/update `docker-compose.yml`.
    ```bash
    ./scripts/graphiti compose
    ```
    *You should run this command whenever you add/remove projects or change configurations in `mcp-projects.yaml` or `base-compose.yaml`.*

2.  **Start All Services:**
    Starts Neo4j, `graphiti-mcp-root`, and all enabled project-specific MCP servers defined in the generated `docker-compose.yml`.
    ```bash
    # Start in detached mode (background)
    ./scripts/graphiti up -d

    # Start in foreground (to see logs directly)
    # ./scripts/graphiti up
    ```
    The first time you run `up`, it might also build the Docker image if needed.

3.  **Check Service Status:**
    ```bash
    ./scripts/graphiti ps
    ```

4.  **View Logs:**
    ```bash
    # View logs for a specific service (e.g., the root server)
    ./scripts/graphiti logs graphiti-mcp-root

    # View logs for Neo4j
    # ./scripts/graphiti logs neo4j

    # View logs for a project-specific server (use the container name from `ps` or compose file)
    # ./scripts/graphiti logs mcp-filesystem-main

    # Follow logs in real-time
    # ./scripts/graphiti logs -f <service_name>
    ```

5.  **Stop All Services:**
    Stops and removes the containers.
    ```bash
    ./scripts/graphiti down
    ```
    *   Add the `-v` flag (`./scripts/graphiti down -v`) to also remove the named volumes (like Neo4j data).

## Managing Projects

*   **To Add a New Project:** Add its definition (including correct absolute paths) to `mcp-projects.yaml`, set `enabled: true`, then run `./scripts/graphiti compose` and `./scripts/graphiti up -d`.
*   **To Disable a Project:** Set `enabled: false` in `mcp-projects.yaml`, run `./scripts/graphiti compose` and `./scripts/graphiti up -d`. The compose tool should handle stopping/removing the disabled service.
*   **To Remove a Project:** Delete its entry from `mcp-projects.yaml`, run `./scripts/graphiti compose` and `./scripts/graphiti up -d`.

## Python CLI (`graphiti` via `pip install .`)

This repository also contains a Python CLI tool in `graphiti_cli/`. You can install it into your virtual environment:

```bash
source .venv/bin/activate
uv pip install .
```

Now you can run the `graphiti` command:

```bash
graphiti --help
# Potentially useful commands like `graphiti init` might be intended for use
# *within external project directories* to set up their structure.
# Refer to the CLI's help output or source code (`graphiti_cli/main.py`) for details.
```

**Important:** This Python `graphiti` CLI is generally **NOT** used for managing the Docker services within *this* orchestrator repository. Use the `./scripts/graphiti` bash script for generating the compose file and managing the service lifecycle (`up`, `down`, `logs`, etc.).

## Connecting MCP Clients

Clients connect to individual MCP server instances, each running on a specific port.

*   **Root Server:** The `graphiti-mcp-root` service typically runs on the host port specified by `MCP_ROOT_HOST_PORT` in your `.env` file (default: 8000).
*   **Project Servers:** Project-specific servers are assigned ports sequentially, starting from 8001 by default (see comments in `docker-compose.yml` after generation). You can find the exact host port mapping by running `./scripts/graphiti ps` or inspecting the generated `docker-compose.yml`.

**Example SSE Configuration (for Root Server):**
```json
{
  "mcpServers": {
    "graphiti-root": {
      "transport": "sse",
      "url": "http://localhost:8000/sse" // Use port from MCP_ROOT_HOST_PORT
    }
  }
}
```

**Example SSE Configuration (for a Project Server, e.g., on host port 8001):**
```json
{
  "mcpServers": {
    "graphiti-filesystem": {
      "transport": "sse",
      "url": "http://localhost:8001/sse" // Use assigned project port
    }
  }
}
```

(Stdio configurations are less common for multi-service Docker setups but could be adapted if needed, pointing the command to execute *inside* the specific container).

## Available MCP Tools (Root Server)

The `graphiti-mcp-root` server instance exposes base Graphiti MCP tools:

-   `add_episode`, `search_nodes`, `search_facts`, `delete_entity_edge`, `delete_episode`, `get_entity_edge`, `get_episodes`, `clear_graph`, `get_status`.

Project-specific servers may expose additional or specialized tools based on their configuration.

## License

Refer to the main Graphiti project repository for license details.
