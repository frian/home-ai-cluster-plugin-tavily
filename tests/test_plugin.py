"""Focused RFC-0093 contract tests using only in-process HTTPX transports."""

import asyncio
import gzip
import importlib.metadata
import json
import subprocess
import sys
from collections.abc import Callable

import httpx
import pytest

from home_ai_cluster_plugin_tavily import plugin


def run(coroutine: object) -> object:
    return asyncio.run(coroutine)  # type: ignore[arg-type]


def install_transport(
    monkeypatch: pytest.MonkeyPatch,
    handler: Callable[[httpx.Request], httpx.Response],
) -> list[dict[str, object]]:
    observations: list[dict[str, object]] = []
    original_client = httpx.AsyncClient

    def client_factory(*args: object, **kwargs: object) -> httpx.AsyncClient:
        observations.append(dict(kwargs))
        return original_client(*args, transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(plugin.httpx, "AsyncClient", client_factory)
    return observations


def usable_result(index: int = 1, **extra: object) -> dict[str, object]:
    return {
        "title": f"title-{index}",
        "url": f"https://example.invalid/{index}",
        "content": f"content-{index}",
        **extra,
    }


def test_entry_point_metadata_exposes_exact_async_callable() -> None:
    entries = importlib.metadata.entry_points().select(
        group="home_ai_cluster.external_information_acquisition.v1", name="tavily"
    )
    assert len(entries) == 1
    entry = next(iter(entries))
    assert entry.value == "home_ai_cluster_plugin_tavily.plugin:acquire"
    assert asyncio.iscoroutinefunction(entry.load())


def test_package_import_has_no_network_side_effect() -> None:
    code = """
import socket
socket.socket.connect = lambda *args: (_ for _ in ()).throw(AssertionError())
import home_ai_cluster_plugin_tavily
"""
    completed = subprocess.run([sys.executable, "-c", code], check=False)
    assert completed.returncode == 0


def test_missing_or_blank_key_fails_before_any_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    observations = install_transport(
        monkeypatch,
        lambda request: pytest.fail("the provider must not be called"),
    )
    with pytest.raises(plugin.AcquisitionFailure):
        run(plugin.acquire("query"))
    monkeypatch.setenv("TAVILY_API_KEY", " \t ")
    with pytest.raises(plugin.AcquisitionFailure):
        run(plugin.acquire("query"))
    assert observations == []


def test_key_is_read_at_invocation_time_and_used_exactly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    keys: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        keys.append(request.headers["Authorization"])
        return httpx.Response(200, json={"results": [usable_result()]})

    install_transport(monkeypatch, handler)
    monkeypatch.setenv("TAVILY_API_KEY", "first fake key")
    run(plugin.acquire("first"))
    monkeypatch.setenv("TAVILY_API_KEY", " second fake key ")
    run(plugin.acquire("second"))
    assert keys == ["Bearer first fake key", "Bearer  second fake key "]


def test_exact_single_json_post_preserves_query_and_client_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "fake-key")
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"results": [usable_result()]})

    observations = install_transport(monkeypatch, handler)
    query = "  !images exact +syntax  "
    assert run(plugin.acquire(query)) == [usable_result()]
    assert len(requests) == 1
    request = requests[0]
    assert request.method == "POST"
    assert str(request.url) == "https://api.tavily.com/search"
    assert request.headers["authorization"] == "Bearer fake-key"
    assert request.headers["content-type"] == "application/json"
    assert json.loads(request.content) == {
        "query": query,
        "search_depth": "basic",
        "max_results": 5,
        "chunks_per_source": 1,
        "include_answer": False,
        "include_raw_content": False,
        "include_images": False,
        "include_image_descriptions": False,
        "auto_parameters": False,
    }
    assert observations == [
        {
            "timeout": plugin._TIMEOUT,
            "limits": plugin._LIMITS,
            "follow_redirects": False,
            "trust_env": False,
            "verify": True,
        }
    ]
    assert plugin._TIMEOUT.connect == 5.0
    assert plugin._TIMEOUT.read == 20.0
    assert plugin._TIMEOUT.write == 5.0
    assert plugin._TIMEOUT.pool == 2.0
    assert plugin._LIMITS.max_connections == 1
    assert plugin._LIMITS.max_keepalive_connections == 0


def test_each_operation_creates_a_fresh_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "fake-key")
    observations = install_transport(
        monkeypatch,
        lambda request: httpx.Response(200, json={"results": [usable_result()]}),
    )
    run(plugin.acquire("first"))
    run(plugin.acquire("second"))
    assert len(observations) == 2


def test_redirect_is_not_followed_or_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "fake-key")
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(302, headers={"location": "https://example.invalid/"})

    install_transport(monkeypatch, handler)
    with pytest.raises(plugin.AcquisitionFailure):
        run(plugin.acquire("query"))
    assert len(requests) == 1


@pytest.mark.parametrize("status", [199, 201, 403, 500])
def test_only_http_200_is_accepted(
    monkeypatch: pytest.MonkeyPatch, status: int
) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "fake-key")
    install_transport(monkeypatch, lambda request: httpx.Response(status))
    with pytest.raises(plugin.AcquisitionFailure):
        run(plugin.acquire("query"))


def test_total_deadline_is_independent_and_test_controllable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "fake-key")

    async def slow_handler(request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(0.02)
        return httpx.Response(200, json={"results": [usable_result()]})

    original_client = httpx.AsyncClient
    monkeypatch.setattr(plugin, "_TOTAL_OPERATION_DEADLINE_SECONDS", 0.001)
    monkeypatch.setattr(
        plugin.httpx,
        "AsyncClient",
        lambda *args, **kwargs: original_client(
            *args, transport=httpx.MockTransport(slow_handler), **kwargs
        ),
    )
    with pytest.raises(plugin.AcquisitionFailure):
        run(plugin.acquire("query"))


class ChunkedStream(httpx.AsyncByteStream):
    def __init__(self, chunks: list[bytes]) -> None:
        self.chunks = chunks

    async def __aiter__(self):  # type: ignore[override]
        for chunk in self.chunks:
            yield chunk

    async def aclose(self) -> None:
        pass


def test_incremental_decoded_size_limit_precedes_json_parsing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "fake-key")

    def parsing_must_not_run(_: object) -> object:
        raise AssertionError("JSON parsing must not run for an oversized response")

    monkeypatch.setattr(plugin.json, "loads", parsing_must_not_run)
    install_transport(
        monkeypatch,
        lambda request: httpx.Response(
            200,
            stream=ChunkedStream([b"{", b"x" * plugin._MAX_DECODED_RESPONSE_BYTES]),
        ),
    )
    with pytest.raises(plugin.AcquisitionFailure):
        run(plugin.acquire("query"))


def test_compressed_response_limit_uses_decoded_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "fake-key")
    decoded = b"{" + (b"x" * plugin._MAX_DECODED_RESPONSE_BYTES)
    compressed = gzip.compress(decoded)
    assert len(compressed) < plugin._MAX_DECODED_RESPONSE_BYTES
    install_transport(
        monkeypatch,
        lambda request: httpx.Response(
            200, headers={"content-encoding": "gzip"}, content=compressed
        ),
    )
    with pytest.raises(plugin.AcquisitionFailure):
        run(plugin.acquire("query"))


@pytest.mark.parametrize(
    "body",
    [b"not json", json.dumps([usable_result()]).encode(), b"{}", b'{"results": {}}'],
)
def test_invalid_json_or_structure_fails(
    monkeypatch: pytest.MonkeyPatch, body: bytes
) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "fake-key")
    install_transport(monkeypatch, lambda request: httpx.Response(200, content=body))
    with pytest.raises(plugin.AcquisitionFailure):
        run(plugin.acquire("query"))


def test_normalisation_skips_malformed_preserves_values_and_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "fake-key")
    preserved = {
        "title": " title ",
        "url": " https://example.invalid/a ",
        "content": " body ",
    }
    payload = {
        "results": [
            None,
            {"title": "", "url": "url", "content": "content"},
            {"title": "title", "url": 1, "content": "content"},
            preserved,
            usable_result(2, score=100, raw_content="ignored"),
            usable_result(2),
        ],
        "answer": "ignored",
    }
    install_transport(monkeypatch, lambda request: httpx.Response(200, json=payload))
    assert run(plugin.acquire("query")) == [
        preserved,
        usable_result(2),
        usable_result(2),
    ]


def test_stops_after_five_and_preserves_duplicates_and_large_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "fake-key")
    large = usable_result(1, content="x" * 100_000)
    results = [large, usable_result(2), usable_result(2)] + [
        usable_result(index) for index in range(3, 7)
    ]
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"results": results})

    install_transport(monkeypatch, handler)
    assert run(plugin.acquire("query")) == results[:5]
    assert len(requests) == 1


def test_safe_failure_hides_all_sensitive_details_and_unexpected_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    key = "fake-api-key-secret"
    query = "private query"
    body = "private provider body"
    monkeypatch.setenv("TAVILY_API_KEY", key)
    install_transport(monkeypatch, lambda request: httpx.Response(418, content=body))
    with pytest.raises(plugin.AcquisitionFailure) as failure:
        run(plugin.acquire(query))
    message = str(failure.value)
    for value in (key, query, body, "418", "api.tavily.com"):
        assert value not in message

    monkeypatch.setattr(plugin.httpx, "AsyncClient", lambda **kwargs: 1 / 0)
    with pytest.raises(plugin.AcquisitionFailure) as unexpected:
        run(plugin.acquire(query))
    assert str(unexpected.value) == "external information acquisition failed"
