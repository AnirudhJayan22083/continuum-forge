"""
mcp/server.py

MCP server entrypoint for Continuum.

Responsible for:
  - Instantiating the MCP server via the official MCP Python SDK
  - Registering all tool handlers defined in mcp/tools.py
  - Starting the server on the appropriate transport (stdio or HTTP/SSE)

Business logic must NOT live here — this module only wires the server
up and delegates to services/ via the handlers in tools.py.
"""


def run_server() -> None:
    """Start the Continuum MCP server.

    To be implemented in Phase 2+: instantiate the MCP server object,
    register tools from mcp/tools.py, and run it on the configured
    transport.
    """
    raise NotImplementedError("MCP server startup not yet implemented.")


if __name__ == "__main__":
    run_server()
