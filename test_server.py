# SPDX-License-Identifier: MIT
"""Tests for the MCP entry point — the server must start on both mcp generations.

mcp 2.0 removed `mcp.server.fastmcp` and renamed the high-level class to
`mcp.server.mcpserver.MCPServer`. `requirements.txt` asks for `mcp>=1.0`, so a
fresh install resolves to 2.x and importing `server` is the first thing that
fails — the whole server, both tools included.

These tests stand in a fake `mcp` package for each generation, so they run
offline with neither version installed. Run: python3 test_server.py
"""

import importlib
import sys
import types

MODULES = ("mcp", "mcp.server", "mcp.server.fastmcp", "mcp.server.mcpserver")


class _FakeServer:
    """Enough of FastMCP/MCPServer for `server` to build: name, .tool(), .run()."""

    def __init__(self, name):
        self.name = name
        self.tools = {}

    def tool(self, *args, **kwargs):
        def register(fn):
            self.tools[fn.__name__] = fn
            return fn
        return register

    def run(self, *args, **kwargs):
        raise AssertionError("run() must not be called at import time")


def _install_fake_mcp(generation):
    """Put a fake `mcp` in sys.modules exposing only `generation`'s class."""
    for name in MODULES + ("server",):
        sys.modules.pop(name, None)
    pkg = types.ModuleType("mcp")
    pkg.__path__ = []
    server_pkg = types.ModuleType("mcp.server")
    server_pkg.__path__ = []
    pkg.server = server_pkg
    sys.modules["mcp"] = pkg
    sys.modules["mcp.server"] = server_pkg
    if generation == "1.x":
        mod = types.ModuleType("mcp.server.fastmcp")
        mod.FastMCP = _FakeServer
        server_pkg.fastmcp = mod
        sys.modules["mcp.server.fastmcp"] = mod
    else:
        mod = types.ModuleType("mcp.server.mcpserver")
        mod.MCPServer = _FakeServer
        server_pkg.mcpserver = mod
        sys.modules["mcp.server.mcpserver"] = mod


def _import_server(generation):
    _install_fake_mcp(generation)
    try:
        return importlib.import_module("server")
    finally:
        for name in MODULES + ("server",):
            sys.modules.pop(name, None)


def test_starts_on_mcp_1x():
    mod = _import_server("1.x")
    assert set(mod.mcp.tools) == {"track_package", "list_carriers"}


def test_starts_on_mcp_2x():
    # Regression: mcp 2.0 dropped mcp.server.fastmcp, so this import used to
    # raise ModuleNotFoundError and no tool was ever registered.
    mod = _import_server("2.x")
    assert set(mod.mcp.tools) == {"track_package", "list_carriers"}


def test_track_package_same_answer_on_both():
    answers = [_import_server(g).mcp.tools["track_package"]("1Z999AA10123456784")
               for g in ("1.x", "2.x")]
    assert answers[0] == answers[1]
    assert answers[0]["carrier"] == "UPS" and answers[0]["detected"] is True


def test_list_carriers_lists_every_carrier():
    mod = _import_server("2.x")
    keys = {c["carrier"] for c in mod.mcp.tools["list_carriers"]()}
    assert keys == set(mod.CARRIERS)


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in tests:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
            passed += 1
        except Exception as exc:            # an ImportError here is the bug itself
            print(f"  FAIL  {fn.__name__}: {type(exc).__name__}: {exc}")
    print(f"\n{passed}/{len(tests)} passed")
    sys.exit(0 if passed == len(tests) else 1)
