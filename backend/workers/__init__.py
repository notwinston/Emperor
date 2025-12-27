"""Worker Agents for Emperor AI Assistant.

Workers are specialized, focused agents spawned by Leads for subtasks:
- Programmer: Writes and modifies code
- Reviewer: Reviews code for issues
- Documentor: Writes documentation
- Researcher: Gathers information
- Executor: Runs commands and scripts

Workers have:
- Focused system prompts for their specialty
- Limited tool sets (only what they need)
- Read-only memory access (via recall tool)

Usage:
    >>> from workers import Programmer, Reviewer
    >>> programmer = Programmer()
    >>> result = await programmer.run("Implement a login function")
    >>> reviewer = Reviewer()
    >>> result = await reviewer.run("Review the login function")
"""

from .programmer import Programmer
from .reviewer import Reviewer
from .documentor import Documentor
from .researcher import Researcher
from .executor import Executor

# Worker registry for dynamic selection
_worker_registry: dict[str, type] = {
    "programmer": Programmer,
    "reviewer": Reviewer,
    "documentor": Documentor,
    "researcher": Researcher,
    "executor": Executor,
}


def get_worker(worker_type: str):
    """
    Create a new worker instance by type.

    Args:
        worker_type: The worker type name

    Returns:
        A new worker instance

    Raises:
        ValueError: If worker type is not registered
    """
    if worker_type not in _worker_registry:
        raise ValueError(
            f"Unknown worker type: {worker_type}. "
            f"Available: {list(_worker_registry.keys())}"
        )

    return _worker_registry[worker_type]()


def get_available_workers() -> list[str]:
    """
    Get list of available worker types.

    Returns:
        List of worker type names
    """
    return list(_worker_registry.keys())


__all__ = [
    # Workers
    "Programmer",
    "Reviewer",
    "Documentor",
    "Researcher",
    "Executor",
    # Registry
    "get_worker",
    "get_available_workers",
]
