# home-ai-cluster-plugin-tavily

Bounded Tavily external-information acquisition plugin for Home AI Cluster.

This separately installed plugin implements accepted [Home AI Cluster
RFC-0093](https://github.com/frian/home-ai-cluster/blob/main/RFC/RFC-0093-bounded-tavily-acquisition-plugin.md).
It is development software and has not been released.

An operator must explicitly select it with `hac external-information --plugin
tavily ...`. The explicit query is disclosed to the public Tavily service. Set
`TAVILY_API_KEY` in the environment of that `hac external-information` caller;
installation alone performs no Tavily request.

The HTTPS endpoint and request shape are fixed. Each selected operation makes
at most one request, with no retries, automatic fallback, URL fetching,
provider-generated answer, crawl/research behavior, or ordinary Chat
acquisition. Returned URLs are provenance strings only.
