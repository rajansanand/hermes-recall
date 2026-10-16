"""Official Python MCP SDK stdio adapter for fixed-profile memory tools."""

import json

from .retry import safe_error
from .standalone import call_tool, open_runtime
from .tools import schemas


def create_server(runtime):
    """Bind the four fixed-scope tools to an official SDK server instance."""
    import anyio
    from mcp.server import Server
    from mcp.types import CallToolResult, ListToolsResult, TextContent, Tool

    async def list_tools(ctx, params):
        """Advertise only the shared explicit-memory schemas."""
        return ListToolsResult(
            tools=[
                Tool(
                    name=item["name"],
                    description=item["description"],
                    input_schema=item["parameters"],
                )
                for item in schemas()
            ]
        )

    async def invoke(ctx, params):
        """Validate and dispatch without echoing sensitive invalid arguments."""
        try:
            result = await anyio.to_thread.run_sync(
                lambda: call_tool(runtime, params.name, params.arguments)
            )
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False))],
                is_error=False,
            )
        except Exception as exc:
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps({"error": safe_error(exc)}))],
                is_error=True,
            )

    return Server("hermes-recall", on_list_tools=list_tools, on_call_tool=invoke)


def serve(home):
    """Hold the shared writer lease throughout one local stdio server session."""
    import anyio
    from mcp.server.stdio import stdio_server

    with open_runtime(home) as runtime:
        server = create_server(runtime)

        async def run():
            """Run the SDK protocol loop until the local stdio session ends."""
            async with stdio_server() as (read, write):
                await server.run(read, write, server.create_initialization_options())

        anyio.run(run)
