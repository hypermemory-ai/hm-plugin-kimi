# Security policy

## Reporting a vulnerability

Do not open a public issue for a vulnerability, credential exposure, or tenant
isolation concern. Email `info@hypermemory.io` with a concise description,
affected component, reproduction steps, and impact. Do not include live access
tokens or personal data.

## Security boundaries

- HyperMemory MCP authentication uses OAuth. The plugin contains no API key or
  bearer token.
- HyperColab credentials are stored by the local CLI, outside the repository
  and plugin package.
- Non-managed plugin hooks require explicit trust in Codex.
- HyperMemory token telemetry parses counters only and must not upload chat or
  source content.
- HyperColab timeline events contain structured summaries and repository paths,
  not raw code, diffs, transcripts, or hidden reasoning.
- Path claims are coordination controls, not a substitute for operating-system
  access control or code review.

## Supported versions

Security fixes target the latest version of each plugin on the default branch.
