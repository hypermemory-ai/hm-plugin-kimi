# HyperMemory write protocol

- Recall before writing. Update an existing node instead of creating a duplicate.
- Use canonical node types: `user`, `person`, `organization`, `component`,
  `event`, `decision`, `concept`, `artifact`, `project`, `technology`,
  `preference`, `fact`, or `skill`.
- Shape keys as `{type}_{name}`. Use `user_profile` for the primary user.
- Never store passwords, API keys, OAuth tokens, credentials, or large code blobs.
- Give each stored node a specific relationship that explains why it connects
  to a project, component, person, organization, or decision.
- Use `hm_ingest` only for dense multi-entity text. Immediately call
  `hm_list_orphans`; connect useful orphans with `hm_add_relationships` and
  delete unenriched noise with `hm_forget`.
- Use `hm_find_related` for traversal and `hm_get_nodes` to hydrate exact keys.
- Use `hm_upload_file` only when the user explicitly asks to store a file.
