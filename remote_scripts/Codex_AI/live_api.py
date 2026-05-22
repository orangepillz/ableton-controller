"""Live API import boundary for modules that need Ableton-specific classes."""

try:
    import Live
except Exception:
    Live = None
