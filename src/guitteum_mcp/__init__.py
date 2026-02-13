"""귀띔 MCP 서버 - 대통령 연설문 수집용"""

__version__ = "0.1.0"


def main():
    from guitteum_mcp.server import mcp

    mcp.run()
