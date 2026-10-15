import asyncio
import json
import os
import sys
from datetime import timedelta
from pathlib import Path

from fastapi.testclient import TestClient
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.memory import create_connected_server_and_client_session

from bilingual_glossary.cli import main
from bilingual_glossary.mcp_server import create_server
from bilingual_glossary.web.app import create_app

ROOT = Path(__file__).resolve().parents[1]


def test_cli_all_commands(glossary, tmp_path, capsys):
    def run(*args):
        code = main(["--data-dir", str(glossary.directory), *args, "--json"])
        return code, json.loads(capsys.readouterr().out)

    for args in [
        ("--version",),
        ("list", "--domain", "it"),
        ("show", "water-treatment-01"),
        ("search", "fst"),
        ("backup",),
        ("prompt", "--text", str(ROOT / "examples/clean.md")),
    ]:
        code, result = run(*args)
        assert code == 0 and result["ok"]
    assert run("check", str(ROOT / "examples/review.md"))[0] == 1
    assert run("check", str(ROOT / "examples/clean.md"))[0] == 0
    path = tmp_path / "export.json"
    assert run("export", "--out", str(path))[0] == 0
    assert run("import", str(path))[1]["data"]["skipped"] == 90
    record = {"zh": "示例", "en": "example", "status": "draft"}
    code, result = run("add", "--record", json.dumps(record))
    assert code == 0
    identifier = result["data"]["id"]
    assert run("update", identifier, "--record", '{"status":"approved"}')[0] == 0
    assert run("delete", identifier)[0] == 2
    assert run("delete", identifier, "--yes")[0] == 0
    assert run("show", "missing")[0] == 3
    assert run("unknown")[0] == 2
    assert run("add", "--record", "bad-json")[0] == 1
    bad = tmp_path / "bad.tbx"
    bad.write_text("<bad")
    assert run("import", str(bad))[0] == 1
    fix = tmp_path / "fix.md"
    fix.write_text("inverse osmosis")
    assert run("check", str(fix), "--fix")[1]["data"]["written"] is False
    assert run("fix", str(fix), "--write")[1]["data"]["written"] is True
    assert fix.read_text() == "reverse osmosis"


def test_web_search_edit_import_and_guards(glossary):
    with TestClient(create_app(glossary), base_url="http://127.0.0.1") as client:
        assert "Bilingual Glossary" in client.get("/").text
        assert client.get("/static/app.js").status_code == 200
        assert len(client.get("/api/domains").json()["data"]) == 3
        result = client.get("/api/terms?query=fst").json()["data"][0]
        assert result["en"] == "reverse osmosis"
        identifier = result["id"]
        response = client.patch(
            "/api/terms/" + identifier,
            json={
                "changes": {"notes": "Browser review"},
                "expected_updated_at": result["updated_at"],
            },
        )
        assert response.json()["data"]["notes"] == "Browser review"
        assert (
            client.patch(
                "/api/terms/" + identifier,
                json={"changes": {"notes": "Stale"}, "expected_updated_at": result["updated_at"]},
            ).status_code
            == 400
        )
        assert client.post("/api/terms", json={"zh": "样例", "en": "sample"}).status_code == 200
        assert (
            client.post(
                "/api/terms",
                json={"zh": "样例2", "en": "sample 2"},
                headers={"Origin": "https://example.invalid"},
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/api/import",
                json={"format": "json", "text": json.dumps([{"zh": "例词", "en": "example word"}])},
            ).json()["data"]["inserted"]
            == 1
        )
        assert (
            client.post(
                "/api/import",
                json={
                    "format": "tbx",
                    "text": '<!DOCTYPE tbx [<!ENTITY x SYSTEM "file:///etc/passwd">]><tbx>&x;</tbx>',
                },
            ).status_code
            == 400
        )
        assert "terms" in client.get("/api/export?format=json").json()
        assert client.get("/api/terms", headers={"Host": "evil.invalid"}).status_code == 400


def payload(result):
    return json.loads(result.content[0].text)


def test_all_mcp_tools(glossary):
    async def scenario():
        server = create_server(glossary)
        async with create_connected_server_and_client_session(server._mcp_server) as client:
            tools = await client.list_tools()
            assert len(tools.tools) == 4
            assert (
                payload(await client.call_tool("lookup_term", {"query": "fst"}))["data"][0]["en"]
                == "reverse osmosis"
            )
            assert (
                len(
                    payload(await client.call_tool("check_text", {"text": "inverse osmosis"}))[
                        "data"
                    ]
                )
                == 1
            )
            assert (
                payload(await client.call_tool("check_pair", {"source": "反渗透", "target": "RO"}))[
                    "data"
                ]
                == []
            )
            assert (
                len(
                    payload(await client.call_tool("glossary_for_text", {"text": "反渗透"}))[
                        "data"
                    ]["terms"]
                )
                == 1
            )
            assert not payload(await client.call_tool("lookup_term", {"query": ""}))["ok"]

    asyncio.run(scenario())


def test_real_stdio(glossary):
    async def scenario():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "bilingual_glossary.cli", "--data-dir", str(glossary.directory), "mcp"],
            env=dict(os.environ),
        )
        async with (
            stdio_client(params) as (read, write),
            ClientSession(read, write, read_timeout_seconds=timedelta(seconds=15)) as client,
        ):
            assert (await client.initialize()).serverInfo.name == "Bilingual Glossary"
            assert (
                payload(await client.call_tool("lookup_term", {"query": "RO"}))["data"][0]["en"]
                == "reverse osmosis"
            )

    asyncio.run(scenario())
