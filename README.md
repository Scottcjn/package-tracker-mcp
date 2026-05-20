# package-tracker-mcp

A tiny [MCP](https://modelcontextprotocol.io) server that identifies a shipping
carrier from a tracking number and hands back the carrier's **official tracking
URL** — so an AI agent given a bare tracking number can act on it.

It works **offline, with no API keys**. A tracking number encodes its carrier in
its format (UPS starts `1Z`, Amazon Logistics starts `TBA`, FedEx Express is a
bare 12 digits, USPS international uses the S10 letter format, …). This server
reads that format and builds the authoritative tracking link.

## Honest scope

This server **detects the carrier and links to it.** It does **not** fetch live
delivery status — that needs per-carrier API credentials, and a tool that
fabricates a status it cannot verify is worse than no tool. The returned
`tracking_url` is the authoritative source for live status. (Live-status
integration behind an optional carrier/aggregator API key is a clean v2.)

## Tools

| Tool | Purpose |
|---|---|
| `track_package(tracking_number)` | Detect carrier, return official tracking URL + any ambiguous alternatives |
| `list_carriers()` | List the carriers this server recognizes |

## Recognized carriers

UPS, FedEx, USPS, DHL, Amazon Logistics, OnTrac.

## Install

```bash
pip install -r requirements.txt
```

## Use with Claude Code

```bash
claude mcp add package-tracker -- python3 /path/to/package-tracker-mcp/server.py
```

Or add to an MCP client config:

```json
{
  "mcpServers": {
    "package-tracker": {
      "command": "python3",
      "args": ["/path/to/package-tracker-mcp/server.py"]
    }
  }
}
```

## Example

```
track_package("123456789012")
-> { "carrier": "FedEx", "confidence": "high",
     "tracking_url": "https://www.fedex.com/fedextrack/?trknbr=123456789012" }
```

## Test

```bash
python3 test_carriers.py
```

## License

MIT
