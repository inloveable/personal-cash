#!/usr/bin/env python3
"""[可选] stdio -> 远程 Streamable HTTP 的 MCP 包装。

仅当你的 MCP 客户端不支持远程 HTTP 时使用。需要 pip install mcp。
环境变量：LEDGER_URL（如 http://host:8000/mcp/）、LEDGER_TOKEN。
"""
import os
import sys


def main() -> None:
    try:
        from mcp.client.streamable_http import streamablehttp_client  # noqa: F401
    except ImportError:
        print("需要 pip install mcp", file=sys.stderr)
        sys.exit(1)

    url = os.environ.get("LEDGER_URL", "http://127.0.0.1:8000/mcp/")
    token = os.environ.get("LEDGER_TOKEN", "dev-token")
    print(f"请直接配置客户端使用 streamable-http: {url} (Bearer {token[:3]}***)", file=sys.stderr)
    print("大多数现代客户端（CodeBuddy/Claude Code/Cursor）已原生支持，无需本代理。", file=sys.stderr)


if __name__ == "__main__":
    main()
