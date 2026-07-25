"""
scaffold_mcp.py

Run this from INSIDE the `continuum/` directory:

    cd continuum
    python scaffold_mcp.py

What it does:
  - Creates mcp/ (mcp/__init__.py, mcp/server.py, mcp/tools.py) as skeleton files
  - Creates mcp_manifest.json at the project root (skeleton)
  - Appends the MCP SDK to requirements.txt if not already present
  - Deletes the cli/ folder (superseded by mcp/ as the interface layer)

It does NOT touch any existing file under agents/, database/, models/,
services/, utils/, main.py, or any of the docs/tests already present.
Safe to re-run: it skips creating anything that already exists, and
only deletes cli/ if that folder is still there.
"""

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent

MCP_INIT_CONTENT = '''"""MCP server package for Continuum.

Exposes Continuum's capabilities (init, interview, extract, validate,
explain, codify, mentor, demo) as MCP tools, callable by any MCP client.
"""
'''

MCP_SERVER_CONTENT = '''"""
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
'''

MCP_TOOLS_CONTENT = '''"""
mcp/tools.py

MCP tool handlers for Continuum.

Each handler here is a thin wrapper: parse/validate input, call the
appropriate function in services/, and return a structured result.
No business logic should live in this file.

Tools to implement (Phase 2+):
  - continuum_init
  - continuum_interview
  - continuum_extract
  - continuum_validate
  - continuum_explain
  - continuum_codify
  - continuum_mentor
  - continuum_demo
"""


def continuum_init() -> None:
    """Initialize the system: create the SQLite DB and load synthetic data."""
    raise NotImplementedError


def continuum_interview() -> None:
    """Run a grounded interview with a technician about an incident."""
    raise NotImplementedError


def continuum_extract() -> None:
    """Extract a structured heuristic from an interview transcript."""
    raise NotImplementedError


def continuum_validate() -> None:
    """Statistically validate a heuristic against historical data."""
    raise NotImplementedError


def continuum_explain() -> None:
    """Generate an explanation and supporting evidence for a validation result."""
    raise NotImplementedError


def continuum_codify() -> None:
    """Convert an accepted heuristic into a stored operational rule."""
    raise NotImplementedError


def continuum_mentor() -> None:
    """Return a recommendation for a given set of live sensor readings."""
    raise NotImplementedError


def continuum_demo() -> None:
    """Run the full pipeline end-to-end and return a structured summary."""
    raise NotImplementedError
'''

MCP_MANIFEST_CONTENT = '''{
  "name": "continuum",
  "description": "Tacit Knowledge Capture & Transfer Network - MCP server",
  "version": "0.1.0",
  "tools": [
    "continuum_init",
    "continuum_interview",
    "continuum_extract",
    "continuum_validate",
    "continuum_explain",
    "continuum_codify",
    "continuum_mentor",
    "continuum_demo"
  ]
}
'''

REQUIREMENTS_MCP_LINE = "mcp"


def create_if_missing(path: Path, content: str) -> None:
    if path.exists():
        print(f"skip  (already exists): {path.relative_to(ROOT)}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"create: {path.relative_to(ROOT)}")


def update_requirements() -> None:
    req_path = ROOT / "requirements.txt"
    if not req_path.exists():
        print("skip  (requirements.txt not found, leaving untouched)")
        return

    existing = req_path.read_text(encoding="utf-8")
    lines = [line.strip() for line in existing.splitlines()]

    already_present = any(
        line == REQUIREMENTS_MCP_LINE or line.startswith(REQUIREMENTS_MCP_LINE + "==")
        or line.startswith(REQUIREMENTS_MCP_LINE + ">=")
        for line in lines
    )
    if already_present:
        print("skip  (requirements.txt already lists mcp)")
        return

    with req_path.open("a", encoding="utf-8") as f:
        if existing and not existing.endswith("\\n"):
            f.write("\\n")
        f.write(REQUIREMENTS_MCP_LINE + "\\n")
    print("update: requirements.txt (added 'mcp')")


def delete_cli_folder() -> None:
    cli_path = ROOT / "cli"
    if not cli_path.exists():
        print("skip  (cli/ already removed)")
        return
    shutil.rmtree(cli_path)
    print("delete: cli/")


def main() -> None:
    print(f"Scaffolding MCP structure in: {ROOT}\\n")

    create_if_missing(ROOT / "mcp" / "__init__.py", MCP_INIT_CONTENT)
    create_if_missing(ROOT / "mcp" / "server.py", MCP_SERVER_CONTENT)
    create_if_missing(ROOT / "mcp" / "tools.py", MCP_TOOLS_CONTENT)
    create_if_missing(ROOT / "mcp_manifest.json", MCP_MANIFEST_CONTENT)

    update_requirements()
    delete_cli_folder()

    print("\\nDone. Existing files under agents/, database/, models/, "
          "services/, utils/, main.py, and docs were not modified.")


if __name__ == "__main__":
    main()