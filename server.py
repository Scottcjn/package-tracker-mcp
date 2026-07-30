# SPDX-License-Identifier: MIT
"""
package-tracker-mcp — an MCP server that identifies a shipping carrier from a
tracking number and returns the carrier's official tracking URL.

Offline and credential-free: it works from the tracking number's format alone.
It does not fetch live delivery status — the returned URL is the authoritative
source for that. Honest by design: it never reports a status it cannot verify.

Run:  python3 server.py        (stdio transport — for an MCP client to launch)
"""

# The high-level server class moved in mcp 2.0: `mcp.server.fastmcp.FastMCP`
# became `mcp.server.mcpserver.MCPServer`, and the old module was removed, not
# aliased. `requirements.txt` asks for `mcp>=1.0`, so a fresh install now
# resolves to 2.x and this import is the very first thing that runs — the
# server never starts. Both classes take the same server name and expose the
# same `.tool()` decorator and `.run()` stdio entry point, so accept either.
try:  # mcp >= 2.0
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server

from carriers import CARRIERS, detect, normalize, tracking_url

mcp = _Server("package-tracker")


@mcp.tool()
def track_package(tracking_number: str) -> dict:
    """Identify the shipping carrier for a tracking number and return its
    official tracking URL.

    Works offline from the number's format — no API key, no carrier account.
    When the format is ambiguous, alternative carrier candidates are included.
    The tracking_url is the authoritative place to see live delivery status.
    """
    tn = normalize(tracking_number)
    candidates = detect(tn)
    if not candidates:
        return {"tracking_number": tn, "detected": False,
                "message": "No known carrier format matched this number."}
    best = candidates[0]
    return {
        "tracking_number": tn,
        "detected": True,
        "carrier": best["name"],
        "confidence": best["confidence"],
        "tracking_url": tracking_url(best["carrier"], tn),
        "alternatives": [
            {"carrier": c["name"], "confidence": c["confidence"],
             "tracking_url": tracking_url(c["carrier"], tn)}
            for c in candidates[1:]
        ],
    }


@mcp.tool()
def list_carriers() -> list:
    """List the shipping carriers this server can recognize."""
    return [{"carrier": key, "name": name} for key, (name, _) in CARRIERS.items()]


if __name__ == "__main__":
    mcp.run()
