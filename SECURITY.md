# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in DeepBoner, please report it responsibly.

### How to Report

1. **DO NOT** open a public GitHub issue for security vulnerabilities
2. Email security concerns to the repository maintainers via GitHub's private vulnerability reporting
3. Or use GitHub's Security Advisory feature: **Security** tab > **Report a vulnerability**

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 7 days
- **Fix timeline**: Depends on severity
  - Critical: Within 48 hours
  - High: Within 7 days
  - Medium: Within 30 days
  - Low: Next release cycle

## Security Measures

### API Key Handling

- API keys are loaded from environment variables only
- Keys are never logged or exposed in error messages
- `.env` files are gitignored
- No hardcoded credentials in source code

### Dependency Security

- Regular dependency audits via `pip-audit`
- Security scanning with `bandit` in CI
- Pinned dependencies for reproducibility
- Known CVE fixes:
  - `mcp>=1.23.0` - Fixes GHSA-9h52-p55h-vw2f
  - `langgraph-checkpoint-sqlite>=3.0.0` - Fixes GHSA-wwqv-p2pp-99h5
  - `urllib3>=2.6.0` - Fixes GHSA-gm62-xv2j-4w53 and GHSA-2xpw-w6gg-jr37

### External API Security

- HTTPS enforced for all external API calls
- Rate limiting prevents abuse
- No sensitive data sent to external services (only search queries)

### Input Validation

- Pydantic models for strict input validation
- Query sanitization before external API calls
- Length limits on user inputs

## Security Best Practices for Users

### API Keys

1. Never commit `.env` files
2. Use environment variables in production
3. Rotate keys periodically
4. Use minimal permissions (read-only where possible)

### Deployment

1. Use the provided Docker image for consistency
2. Keep dependencies updated
3. Monitor for security advisories
4. Use HTTPS in production

### HuggingFace Spaces

1. Use Secrets (not public variables) for API keys
2. The HF_TOKEN is used server-side only
3. Users don't need their own tokens

## Known Security Considerations

### Third-Party APIs

DeepBoner queries external biomedical databases:
- PubMed (NCBI)
- ClinicalTrials.gov
- Europe PMC
- OpenAlex

These are trusted public APIs, but:
- Query content is visible to these services
- Rate limits apply
- Availability depends on upstream services

### LLM Providers

- OpenAI and HuggingFace process your queries
- Review their privacy policies if handling sensitive research
- Consider on-premise alternatives for sensitive use cases

### Local Data

- ChromaDB stores embeddings locally
- Default path: `./chroma_db/`
- Contains processed search results (not raw user data)
- Secure or delete when decommissioning

## Security Updates

Security updates will be released as patch versions (e.g., 0.1.1) and announced via:
- GitHub Security Advisories
- Release notes

---

*"Security is rock solid. We take evidence-based security very seriously."* 🔐
