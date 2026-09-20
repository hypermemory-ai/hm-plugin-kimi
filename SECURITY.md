# Security policy

## Reporting a vulnerability

Do not open a public issue for a vulnerability, credential exposure, or tenant
isolation concern. Email `info@hypermemory.io` with a concise description,
affected component, reproduction steps, and impact. Do not include live access
tokens or personal data.

## Security boundaries

- HyperMemory MCP authentication uses OAuth. The plugin contains no API key or
  bearer token.
- Plugin hooks run only while the plugin is enabled and fire on their matching
  Kimi Code lifecycle events; all local hook failures fail open.
- HyperMemory token telemetry is self-estimated and must never label invented
  counts, costs, or usage as exact.
- Memory writes contain durable decisions, preferences, and canonical facts —
  never credentials, hidden reasoning, raw transcripts, or large code bodies.

## Supported versions

Security fixes target the latest version of each plugin on the default branch.
