"""
mcp_tool_server.py
=================
A minimal MCP (Model Context Protocol) server that exposes TOOLS and a RESOURCE to any
MCP-compatible host (Claude Desktop, IDEs, custom agents).

WHY MCP:
    Before MCP, every agent<->tool integration was bespoke (N agents x M tools = N*M glue).
    MCP standardizes the interface: expose a capability ONCE as an MCP server and any MCP
    host can use it. It's the "USB-C for AI tools." Adopted across Anthropic/OpenAI/Google/
    Microsoft and donated to the Linux Foundation's Agentic AI foundation (late 2025).

MCP capability types shown here:
    - Tools     : model-invoked ACTIONS (side effects / computation).
    - Resources : app-exposed CONTEXT DATA (read-only, addressed by URI).
    (Others in the spec: Prompts, Sampling, Roots, Elicitation.)

SECURITY NOTE (straight from the mindset in the MCP docs, rephrased):
    MCP enables real data access and code-execution paths. A host must gate tool calls
    behind user consent, validate inputs, and scope what a server can touch. Treat every
    argument as untrusted — which is why we validate before doing anything.

Requires: `pip install mcp`. Uses the FastMCP helper from the official Python SDK.
Run (stdio transport, the local default):  python mcp_tool_server.py
Then register it in an MCP host's config to actually call the tools.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

# The server object. The name is what hosts display in their tool list.
mcp = FastMCP("demo-tools")


# ---------------------------------------------------------------------------
# TOOLS
# The docstring + type hints become the schema the model reads. WHY: descriptions ARE
# prompts — the model chooses tools from them, so state clearly what each does and when.
# ---------------------------------------------------------------------------
@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers and return the sum. Use for basic arithmetic requests."""
    return a + b


@mcp.tool()
def word_count(text: str) -> int:
    """Return the number of words in the given text."""
    # Validation guardrail: reject oversized input so a huge payload can't be forced
    # through and bloat the model's context on the way back.
    if len(text) > 10_000:
        raise ValueError("text too long (max 10k chars)")
    return len(text.split())


@mcp.tool()
def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert a temperature from Celsius to Fahrenheit."""
    return round(celsius * 9 / 5 + 32, 2)


# ---------------------------------------------------------------------------
# RESOURCE
# A resource is read-only CONTEXT the host can pull in, addressed by a URI. WHY separate
# from tools: resources are app-controlled data (no side effects), tools are model-invoked
# actions. Keeping them distinct is core to MCP's security model.
# ---------------------------------------------------------------------------
@mcp.resource("config://units")
def units_info() -> str:
    """Expose reference info about supported unit conversions as context."""
    return (
        "Supported conversions:\n"
        "- celsius_to_fahrenheit: C -> F (F = C * 9/5 + 32)\n"
        "Numbers use dot decimal notation."
    )


if __name__ == "__main__":
    # stdio is the standard LOCAL transport (host launches the server as a subprocess and
    # talks JSON-RPC over stdin/stdout). For REMOTE servers, prefer Streamable HTTP, which
    # replaced SSE as the recommended remote transport in the 2025-03-26 spec.
    mcp.run(transport="stdio")
