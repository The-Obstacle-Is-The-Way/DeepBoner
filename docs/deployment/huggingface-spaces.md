# HuggingFace Spaces Deployment

> **Last Updated**: 2025-12-06

This guide covers deploying DeepBoner to HuggingFace Spaces.

## Overview

DeepBoner is deployed to HuggingFace Spaces at:
https://huggingface.co/spaces/MCP-1st-Birthday/DeepBoner

The Space runs the Gradio UI with MCP server support.

## Space Configuration

The Space is configured via the README.md frontmatter:

```yaml
---
title: DeepBoner
emoji: 🍆
colorFrom: pink
colorTo: purple
sdk: gradio
sdk_version: "6.0.1"
python_version: "3.11"
app_file: src/app.py
pinned: true
license: apache-2.0
short_description: "Deep Research Agent for the Strongest Boners"
tags:
  - mcp-hackathon
  - agents
  - sexual-health
  - pydantic-ai
  - pubmed
---
```

## Deployment Methods

### Method 1: Git Push (Recommended)

```bash
# Add HuggingFace remote
git remote add hf https://huggingface.co/spaces/MCP-1st-Birthday/DeepBoner

# Push to HuggingFace
git push hf main
```

### Method 2: HuggingFace Hub

Use the HuggingFace web interface to sync with GitHub.

## Secrets Configuration

Configure secrets in Space Settings → Variables and secrets:

| Secret | Purpose | Required |
|--------|---------|----------|
| `HF_TOKEN` | HuggingFace API token | Yes |
| `NCBI_API_KEY` | Higher PubMed rate limits | No |
| `OPENAI_API_KEY` | Premium mode (if offered) | No |

### Setting Secrets

1. Go to Space Settings
2. Click "Variables and secrets"
3. Add each secret:
   - Name: `HF_TOKEN`
   - Value: `hf_...` (your token)
   - Click "Add"

**Important:** Use Secrets (not Variables) for API keys - secrets are hidden.

## Build Process

When you push to HuggingFace:

1. Space detects changes
2. Builds from Dockerfile (if present) or requirements.txt
3. Installs dependencies
4. Starts the application

Build logs are visible in the Logs tab.

## Collaboration Workflow

### Branch Strategy

```
GitHub (source of truth)
├── main          - Production, synced to HF
└── dev           - Development integration

HuggingFace
├── main          - Production (from GitHub)
└── yourname-dev  - Personal dev branches
```

### Guidelines

- **DO NOT** push directly to `main` on HuggingFace
- Use personal dev branches: `yourname-dev`
- GitHub is the source of truth for code review
- Sync production from GitHub only

### Personal Development

```bash
# Create your dev branch on HuggingFace
git checkout -b myname-dev
git push hf myname-dev

# Test on your branch
# Space will build from your branch if you switch to it
```

## Environment Differences

### Local vs Spaces

| Aspect | Local | HuggingFace Spaces |
|--------|-------|-------------------|
| API Keys | `.env` file | Secrets |
| Storage | Persistent | Ephemeral |
| Port | 7860 | Assigned |
| Memory | Unlimited | Limited (based on tier) |

### Handling Ephemeral Storage

ChromaDB data is not persisted on Space restart. For production use cases requiring persistence:

1. Use external database
2. Accept regeneration on restart
3. Consider paid Spaces with persistent storage

## Hardware Tiers

HuggingFace Spaces offers different hardware:

| Tier | CPU | RAM | GPU | Cost |
|------|-----|-----|-----|------|
| Free | 2 | 16GB | None | Free |
| CPU Basic | 2 | 16GB | None | $0.03/hr |
| CPU Upgrade | 8 | 32GB | None | $0.07/hr |
| T4 Small | 4 | 15GB | T4 | $0.60/hr |

DeepBoner runs on Free tier but benefits from CPU Upgrade for:
- Faster embedding generation
- More concurrent users

## Monitoring

### Logs

View logs in the Logs tab:
- Build logs (during deployment)
- Application logs (runtime)

### Health

Check Space status:
- Green: Running
- Yellow: Building
- Red: Error

## Troubleshooting

### Build fails

1. Check Build Logs tab
2. Common issues:
   - Invalid requirements.txt
   - Missing files
   - Syntax errors in config

### App crashes on start

1. Check Application Logs
2. Common issues:
   - Missing secrets
   - Import errors
   - Memory limits

### Slow performance

1. Check if on Free tier
2. Consider CPU Upgrade
3. Optimize model loading

### Space sleeping

Free Spaces sleep after inactivity:
- Wake time: 30-60 seconds
- Consider "pinned" for popular Spaces

## Git Hooks

To prevent accidental pushes to protected branches:

```bash
# .git/hooks/pre-push
#!/bin/bash
protected_branches=("main" "dev")
current_branch=$(git rev-parse --abbrev-ref HEAD)
remote="$1"

if [[ "$remote" == "hf" || "$remote" == "huggingface" ]]; then
  for branch in "${protected_branches[@]}"; do
    if [[ "$current_branch" == "$branch" ]]; then
      echo "Direct push to $branch on HuggingFace is not allowed."
      exit 1
    fi
  done
fi
```

## Related Documentation

- [Docker Deployment](docker.md)
- [MCP Integration](mcp-integration.md)
- [Configuration Reference](../reference/configuration.md)
