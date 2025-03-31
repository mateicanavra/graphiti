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

### Docker Deployment

The Graphiti MCP server can be deployed using Docker. The Dockerfile uses `uv` for package management, ensuring consistent dependency installation.

#### Environment Configuration

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

#### Neo4j Configuration

The Docker Compose setup includes a Neo4j container with the following default configuration:

- Username: `neo4j`
- Password: `demodemo`
- URI: `bolt://neo4j:7687` (from within the Docker network)
- Memory settings optimized for development use

#### Running with Docker Compose

Start the services using Docker Compose:

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

# Graphiti MCP Docker Compose Configuration

This directory contains a dynamic Docker Compose configuration system for Graphiti MCP servers. The system separates static configuration from dynamic server definitions, making it easier to maintain and extend.

## Configuration Files

- **base-compose.yaml**: Contains the static parts of the Docker Compose configuration, including:
  - Anchors and aliases for common configurations
  - Neo4j database service
  - Root MCP server service
  - Volume definitions

- **custom_servers.yaml**: Defines additional MCP servers in a simplified format with sensible defaults:
  ```yaml
  custom_mcp_servers:
    - id: server-id                    # Required: Used for service name (mcp-<id>)
      container: CONTAINER_VAR_NAME    # Optional: Defaults to <ID>_CONTAINER_NAME
      port: PORT_VAR_NAME              # Optional: Defaults to <ID>_PORT
      dir: "entity_types/path"         # Optional: Defaults to entity_types/<id>
      types: "Type1 Type2"             # Optional: Space-separated entity types
      group_id: "custom-group-id"      # Optional: Defaults to <id>
  ```

- **generate_compose.py**: Python script that combines `base-compose.yaml` and `custom_servers.yaml` to generate the final `docker-compose.yml` file.

## Default Values System

The configuration system uses sensible defaults to minimize repetitive configuration:

1. **Container Names**: By default, uses environment variables named `<ID>_CONTAINER_NAME` (e.g., `CIV7_CONTAINER_NAME`)

2. **Ports**: 
   - By default, uses environment variables named `<ID>_PORT` (e.g., `CIV7_PORT`)
   - Default port values are assigned sequentially starting at 8001 (8001, 8002, etc.)
   - Port values in the Docker Compose file use the format `${<ID>_PORT:-<default>}` to use the default if the environment variable is not set

3. **Entity Type Directories**: By default, uses `entity_types/<id>` (e.g., `entity_types/civ7`)

4. **Group IDs**: By default, uses the server `id` as the group ID

## Usage

1. Configure your MCP servers in `custom_servers.yaml` using the simplified format with defaults
2. Run the generation script:
   ```
   python3 generate_compose.py
   ```
3. The script will generate a `docker-compose.yml` file that can be used with Docker Compose:
   ```
   docker-compose up -d
   ```

## Adding a New MCP Server

To add a new MCP server with minimal configuration:

1. Add the server definition to `custom_servers.yaml`:
   ```yaml
   custom_mcp_servers:
     # ... existing servers ...
     - id: new-server  # That's it! All other values will use defaults
   ```

2. Optionally, add environment variables to your `.env` file to override default settings:
   ```
   NEW_SERVER_CONTAINER_NAME=graphiti-mcp-new-server
   NEW_SERVER_PORT=8099  # Override the default port
   ```

3. Run the generation script and restart your Docker Compose services:
   ```
   python3 generate_compose.py
   docker-compose up -d
   ```

## Overriding Defaults

If you need to override defaults for a specific service:

```yaml
- id: reporting
  # Override default variable names
  container: REPORTING_SVC_CONTAINER  # Use REPORTING_SVC_CONTAINER instead of REPORTING_CONTAINER_NAME
  port: REPORTING_SVC_PORT            # Use REPORTING_SVC_PORT instead of REPORTING_PORT
  
  # Override default values
  dir: "entity_types/custom_path"     # Use custom_path instead of reporting
  group_id: "reports-group"           # Use reports-group instead of reporting
  types: "Report Metric Dashboard"    # Specify entity types
```

## Customizing the Base Configuration

If you need to modify the base configuration (Neo4j settings, root MCP server, etc.), edit `base-compose.yaml` directly. The changes will be incorporated the next time you run the generation script.

## Notes

- The script requires PyYAML to be installed (`pip install pyyaml`)
- All services inherit common configuration from the anchors defined in `base-compose.yaml`
- Custom MCP servers depend on both Neo4j and the root MCP server
