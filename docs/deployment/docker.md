# Docker Deployment

> **Last Updated**: 2025-12-06

This guide covers deploying DeepBoner using Docker.

## Quick Start

```bash
# Build the image
docker build -t deepboner .

# Run the container
docker run -p 7860:7860 deepboner
```

Open http://localhost:7860

## Dockerfile Overview

The project uses a multi-stage approach:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y git curl

# Install uv package manager
RUN pip install uv==0.5.4

# Copy project files
COPY pyproject.toml uv.lock src/ README.md .

# Install runtime dependencies (no dev tools)
RUN uv sync --frozen --no-dev --extra embeddings --extra magentic

# Create non-root user
RUN useradd --create-home appuser
USER appuser

# Pre-download embedding model
RUN uv run python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Expose port and run
EXPOSE 7860
CMD ["uv", "run", "python", "-m", "src.app"]
```

## Building

### Basic Build

```bash
docker build -t deepboner .
```

### With Build Arguments

```bash
# Custom tag
docker build -t deepboner:v0.1.0 .

# No cache (clean build)
docker build --no-cache -t deepboner .
```

### Multi-Platform Build

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t deepboner .
```

## Running

### Basic Run

```bash
docker run -p 7860:7860 deepboner
```

### With Environment Variables

```bash
docker run -p 7860:7860 \
  -e OPENAI_API_KEY=sk-your-key \
  -e NCBI_API_KEY=your-ncbi-key \
  -e LOG_LEVEL=INFO \
  deepboner
```

### Using .env File

```bash
docker run -p 7860:7860 --env-file .env deepboner
```

### With Persistent Storage

```bash
# Persist ChromaDB data
docker run -p 7860:7860 \
  -v $(pwd)/data/chroma:/app/chroma_db \
  deepboner
```

### Detached Mode

```bash
docker run -d -p 7860:7860 --name deepboner-app deepboner
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key (premium mode) | No |
| `NCBI_API_KEY` | NCBI API key (higher rate limits) | No |
| `HF_TOKEN` | HuggingFace token | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No |
| `MAX_ITERATIONS` | Max search iterations (1-50) | No |

### Ports

| Port | Service |
|------|---------|
| 7860 | Gradio UI + MCP Server |

### Volumes

| Path | Purpose |
|------|---------|
| `/app/chroma_db` | ChromaDB vector store |
| `/app/.cache` | HuggingFace model cache |

## Health Check

The container includes a health check:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1
```

Check health status:

```bash
docker inspect --format='{{.State.Health.Status}}' deepboner-app
```

## Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  deepboner:
    build: .
    ports:
      - "7860:7860"
    environment:
      - LOG_LEVEL=INFO
    env_file:
      - .env
    volumes:
      - chroma_data:/app/chroma_db
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7860/"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  chroma_data:
```

Run with:

```bash
docker-compose up -d
```

## Production Considerations

### Resource Limits

```bash
docker run -p 7860:7860 \
  --memory=4g \
  --cpus=2 \
  deepboner
```

### Logging

```bash
# View logs
docker logs deepboner-app

# Follow logs
docker logs -f deepboner-app

# With timestamps
docker logs -t deepboner-app
```

### Security

The container runs as non-root user (`appuser`):

```dockerfile
RUN useradd --create-home appuser
USER appuser
```

Do not:
- Expose ports beyond 7860
- Mount sensitive host paths
- Run as root in production

### Reverse Proxy

For production, use a reverse proxy (nginx, traefik):

```nginx
server {
    listen 80;
    server_name deepboner.example.com;

    location / {
        proxy_pass http://localhost:7860;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## Troubleshooting

### Container exits immediately

Check logs:
```bash
docker logs deepboner-app
```

Common causes:
- Missing environment variables
- Port conflict
- Insufficient memory

### Slow startup

First run downloads models. Pre-warm the cache:
```bash
# Build includes model download
docker build -t deepboner .
```

### Out of memory

Increase memory limit:
```bash
docker run -p 7860:7860 --memory=8g deepboner
```

### Cannot connect to port

Check if port is in use:
```bash
lsof -i :7860
```

Use a different port:
```bash
docker run -p 8080:7860 deepboner
```

## Related Documentation

- [HuggingFace Spaces Deployment](huggingface-spaces.md)
- [MCP Integration](mcp-integration.md)
- [Configuration Reference](../reference/configuration.md)
