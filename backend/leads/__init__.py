"""Domain Lead Agents for Emperor AI Assistant.

Domain Leads are specialized agents that handle specific domains:
- Code Lead: All code-related tasks (architecture, reviews, programming)
- Research Lead: Research, analysis, and information gathering
- Task Lead: Automation, workflows, and system operations

Each Lead:
- Receives tasks from the Orchestrator
- Has domain-specific tools and expertise
- Can spawn Worker agents for subtasks
- Has full access to the memory system
- Returns aggregated results to Orchestrator

Usage:
    >>> from leads import get_code_lead, get_research_lead, get_task_lead
    >>> code_lead = get_code_lead()
    >>> result = await code_lead.run("Refactor the auth module")
    >>> research_lead = get_research_lead()
    >>> result = await research_lead.run("What are best practices for OAuth2?")
    >>> task_lead = get_task_lead()
    >>> result = await task_lead.run("Run the test suite")
"""

from .code_lead import (
    CodeLead,
    get_code_lead,
    reset_code_lead,
)

from .research_lead import (
    ResearchLead,
    get_research_lead,
    reset_research_lead,
)

from .task_lead import (
    TaskLead,
    get_task_lead,
    reset_task_lead,
)

# Domain registry for dynamic Lead selection
_lead_registry: dict[str, type] = {
    "code": CodeLead,
    "research": ResearchLead,
    "task": TaskLead,
}


def get_lead(domain: str):
    """
    Get a Lead instance for a domain.

    Args:
        domain: The domain name ("code", "research", "task")

    Returns:
        The Lead instance for that domain

    Raises:
        ValueError: If domain is not registered
    """
    if domain == "code":
        return get_code_lead()
    elif domain == "research":
        return get_research_lead()
    elif domain == "task":
        return get_task_lead()

    raise ValueError(f"Unknown domain: {domain}. Available: {list(_lead_registry.keys())}")


def get_available_domains() -> list[str]:
    """
    Get list of available domain names.

    Returns:
        List of domain names that have Lead implementations
    """
    return list(_lead_registry.keys())


__all__ = [
    # Code Lead
    "CodeLead",
    "get_code_lead",
    "reset_code_lead",
    # Research Lead
    "ResearchLead",
    "get_research_lead",
    "reset_research_lead",
    # Task Lead
    "TaskLead",
    "get_task_lead",
    "reset_task_lead",
    # Registry
    "get_lead",
    "get_available_domains",
]
