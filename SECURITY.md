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
- Plugin hooks run only while the plugin is enabled and fire on their matching
  Kimi Code lifecycle events; all local hook failures fail open.
- HyperMemory token telemetry is self-estimated and must never label invented
  counts, costs, or usage as exact.
- HyperColab timeline events contain structured summaries and repository paths,
  not raw code, diffs, transcripts, or hidden reasoning.
- Path claims are coordination controls, not a substitute for operating-system
  access control or code review.

## Supported versions

Security fixes target the latest version of each plugin on the default branch.
