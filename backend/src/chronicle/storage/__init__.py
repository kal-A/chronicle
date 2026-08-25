from .agent_run_store import AgentRunStore

__all__ = ["AgentRunStore", "RunStore"]


def __getattr__(name: str):
    """Keep the legacy export lazy so AI storage does not import it eagerly."""

    if name == "RunStore":
        from .run_store import RunStore

        return RunStore
    raise AttributeError(name)
