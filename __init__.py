"""Directory-provider entry point; package providers use hermes_recall directly."""


def register(ctx):
    """Register the directory-installed provider through Hermes's discoverable entry point."""
    if __package__:
        from .hermes_recall import create_provider
    else:
        from hermes_recall import create_provider
    # Directory discovery checks this registration call without importing code.
    ctx.register_memory_provider(create_provider(ctx))
