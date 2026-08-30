# home-ai-cluster-plugin-tavily

Bounded Tavily external-information acquisition plugin for Home AI Cluster.

This separately installed plugin implements accepted [Home AI Cluster
RFC-0093](https://github.com/frian/home-ai-cluster/blob/main/RFC/RFC-0093-bounded-tavily-acquisition-plugin.md).

An operator must explicitly select it with `hac external-information --plugin
tavily ...`. The explicit query is disclosed to the public Tavily service. Set
`TAVILY_API_KEY` in the environment of that `hac external-information` caller;
installation alone performs no Tavily request.

The HTTPS endpoint and request shape are fixed. Each selected operation makes
at most one request, with no retries, automatic fallback, URL fetching,
provider-generated answer, crawl/research behavior, or ordinary Chat
acquisition. Returned URLs are provenance strings only.

## Installation

Install this separately packaged plugin into the same environment that runs
`hac`.

### HAC repository checkout

For a published package:

```sh
uv pip install \
  --python ./home-ai-cluster/.venv/bin/python \
  home-ai-cluster-plugin-tavily
```

For development from a sibling workspace, install the local checkout instead:

```sh
uv pip install \
  --python ./home-ai-cluster/.venv/bin/python \
  ./home-ai-cluster-plugin-tavily
```

### HAC as an isolated uv tool

For a published package:

```sh
uv tool install \
  --with home-ai-cluster-plugin-tavily \
  home-ai-cluster
```

For development from sibling local checkouts:

```sh
uv tool install \
  --with ./home-ai-cluster-plugin-tavily \
  ./home-ai-cluster
```
