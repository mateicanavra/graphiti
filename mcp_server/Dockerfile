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
