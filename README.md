# home-ai-cluster-plugin-tavily

Bounded Tavily external-information acquisition plugin for Home AI Cluster.

This separately installed plugin implements accepted [Home AI Cluster
RFC-0093](https://github.com/frian/home-ai-cluster/blob/main/RFC/RFC-0093-bounded-tavily-acquisition-plugin.md).

An operator selects it only through accepted HAC External Information flows,
either explicitly or through the retained `tavily` plugin choice. The
acquisition query is disclosed to the public Tavily service. The plugin reads
`TAVILY_API_KEY` only from the environment of the process that invokes it;
installation alone and ordinary HAC startup perform no Tavily request.

The HTTPS endpoint and request shape are fixed. Each selected operation makes
at most one request, with no retries, automatic fallback, URL fetching,
provider-generated answer, crawl/research behavior, or ordinary Chat
acquisition. Returned URLs are provenance strings only.

## Installation

Install this separately packaged plugin into the same environment that runs
`hac`.

### HAC repository checkout

For the published package, use this complete path from an existing Home AI
Cluster checkout:

```sh
cd /path/to/home-ai-cluster
uv sync --locked
uv pip install \
  --python .venv/bin/python \
  home-ai-cluster-plugin-tavily
export TAVILY_API_KEY="<YOUR_TAVILY_API_KEY>"
uv run hac config external-information --plugin tavily
uv run hac config show
uv run hac local
```

`TAVILY_API_KEY` remains operator/plugin-owned environment state: HAC does not
read, retain, manage, or store it. Keep the `hac local` terminal open.

To make one explicit CLI External Information request, open a second terminal,
enter the same checkout, and export the key there too. That command invokes the
plugin in its own caller process, so an export in the terminal running
`hac local` does not apply to it:

```sh
cd /path/to/home-ai-cluster
export TAVILY_API_KEY="<YOUR_TAVILY_API_KEY>"
uv run hac external-information \
  --query "Python 3.14 release notes free threading" \
  --question "What changed for free-threaded Python in 3.14?"
```

This example uses the retained `tavily` selection. Add `--plugin tavily` to
explicitly select it for one request instead.

The native loopback browser's External Information flow runs the plugin in the
already-running `hac local` process. Start that process with
`TAVILY_API_KEY` exported; exporting the key later in another terminal does
not update its environment. If necessary, set the key and restart `hac local`.

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
