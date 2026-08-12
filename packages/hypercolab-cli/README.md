# Hypercolab CLI

`hypercolab` is both the standalone project-coordination CLI and the local
stdio MCP shim used by the HyperColab plugin for ChatGPT and Codex.

```bash
pipx install .
hypercolab login
hypercolab setup
hypercolab join --goal "Implement project invitations"
hypercolab mcp
```

The CLI detects the current Git root, remote, branch, and worktree. Project
graph and timeline identifiers are resolved by the HyperMemory backend and are
never selected directly by an agent.

The CLI uses the same service methods for direct commands, coding-client hooks,
Git activity capture, and MCP tools. Git events are queued when the API is down.
New claims fail closed while offline; existing cached leases are honored only
until their server-issued expiry. The package configures Codex only.
