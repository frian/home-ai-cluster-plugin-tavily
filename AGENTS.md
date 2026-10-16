# Agent Guidelines

Architecture is owned by upstream Home AI Cluster RFC-0078 and RFC-0093.
Agents implement those accepted decisions and do not expand them.

Changes to destination, credentials, request body, timeouts, retries, result
fetching, provider selection, configuration, or network authority require
upstream architecture/RFC work. Preserve local-first, privacy-first,
boring-solutions-first behavior. Do not log sensitive queries, API keys,
Authorization headers, or provider responses.

## Shared project coordination

The canonical coordination repository is `frian/home-ai-cluster-project`.
For substantial non-BLIND work, consult its current `PROJECT-STATUS.md` when
accessible, identify the relevant workstream, and verify Git references before
acting. Coordination records are not architectural authority and do not
supersede accepted RFCs or this repository's instructions.

After a significant milestone (for example, a Draft PR, merge, accepted RFC,
release, verified blocker, or completed review), briefly propose an update to
the operator when it would change a workstream or merit a durable log entry.
Do not propose updates for trivial intermediate steps. Do not write to the
coordination repository without explicit operator authorization.

If authorized, follow the coordination repository's current `README.md`:
refresh the remote files, preserve concurrent changes, update status only when
needed, and record meaningful milestones. Routine updates may be committed
directly to its `main`; convention changes require a dedicated branch and
Draft PR. Do not modify any other repository without explicit authorization.
