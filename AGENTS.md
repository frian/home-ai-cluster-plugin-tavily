# Agent Guidelines

Architecture is owned by upstream Home AI Cluster RFC-0078 and RFC-0093.
Agents implement those accepted decisions and do not expand them.

Changes to destination, credentials, request body, timeouts, retries, result
fetching, provider selection, configuration, or network authority require
upstream architecture/RFC work. Preserve local-first, privacy-first,
boring-solutions-first behavior. Do not log sensitive queries, API keys,
Authorization headers, or provider responses.
