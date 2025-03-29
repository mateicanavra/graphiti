# Graphiti Symlinking Script

This script facilitates the reuse of entity type definitions and Docker Compose configuration from the mcp-graphiti repository in other projects.

## Installation

1.  **Set Environment Variable:** Set the `MCP_GRAPHITI_REPO_PATH` environment variable to the absolute path of your `mcp-graphiti` repository. This tells the script where to find the source files.

    ```bash
    export MCP_GRAPHITI_REPO_PATH="/path/to/your/mcp-graphiti"
    ```

    *Note:* You might want to add this line to your shell configuration file (e.g., `~/.zshrc` or `~/.bashrc`) so it's set automatically in new terminal sessions.

2.  **Make Globally Executable (Recommended):** To run the `graphiti` command from anywhere, create a symbolic link in a directory that is part of your system's `PATH`. The standard location `/usr/local/bin` is recommended.

    Navigate to the root directory of the `mcp-graphiti` repository in your terminal and run:

    ```bash
    sudo ln -sf "$(pwd)/mcp_server/scripts/graphiti" /usr/local/bin/graphiti
    ```

    This command requires administrator privileges (`sudo`). It creates a symlink named `graphiti` in `/usr/local/bin` that points to the actual script.

    *Verification:* You can verify the link by running `which graphiti`. It should output `/usr/local/bin/graphiti`.

3.  **Ensure Executable Permissions:** The script needs execute permissions. This was likely set during creation, but you can ensure it with:

    ```bash
    chmod +x mcp_server/scripts/graphiti
    ```

## Usage

Once installed and configured, you can use the `graphiti` command.

### Basic Usage

Run the command in the directory where you want to create the symlinks:

```bash
graphiti
```

This will create `entity_types` and `docker-compose.yml` symlinks in the current directory (`.`).

### Specify Target Directory

To create the symlinks in a specific directory, provide the path as an argument:

```bash
graphiti /path/to/your/other/project
```

### What It Does

The script creates two symbolic links in the target directory:

1.  `entity_types` -> Points to `$MCP_GRAPHITI_REPO_PATH/mcp_server/entity_types`
2.  `docker-compose.yml` -> Points to `$MCP_GRAPHITI_REPO_PATH/mcp_server/docker-compose.yml`

This allows you to easily reuse the shared entity type definitions and Docker Compose setup from the `mcp-graphiti` repository across different projects.

### Error Handling

*   The script will exit with an error if the `MCP_GRAPHITI_REPO_PATH` environment variable is not set.
*   It will also exit if the source directory (`$MCP_GRAPHITI_REPO_PATH/mcp_server`) does not exist. 