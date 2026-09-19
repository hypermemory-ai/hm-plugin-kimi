HyperMemory is enabled in this environment.

- Follow the HyperMemory skill's turn classification: recall relevant context
  before substantive work; skip recall only for narrowly classified lightweight
  social prompts such as a bare greeting or thanks.
- Keep every durable graph write, timeline entry, and token report off the main
  agent. Before each final response, dispatch exactly one fresh fire-and-forget
  memory-writer sub-agent and never wait for, poll, or message it.
- Keep ordinary memory operations silent. Mention HyperMemory only when the
  user asks about it or a requested memory action cannot be completed.
