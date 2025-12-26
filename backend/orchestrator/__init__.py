"""Orchestrator module for Emperor AI Assistant.

The Orchestrator is the main entry point for user interactions.
It uses the Claude Code CLI to:
- Understand user intent
- Handle simple queries directly
- Delegate complex tasks to Domain Leads (SDK agents)
- Synthesize final responses
"""

from .orchestrator import Orchestrator, OrchestratorResult, get_orchestrator
from .intent_classifier import (
    IntentType,
    IntentResult,
    DelegationTarget,
    IntentClassifier,
    get_classifier,
)
from .delegation import (
    DelegationType,
    DelegationStatus,
    Priority,
    DelegationContext,
    DelegationRequest,
    DelegationResult,
    DelegationManager,
    get_delegation_manager,
)
from .memory_integration import (
    UserProfile,
    MemoryItem,
    SessionSummary,
    MemoryContext,
    MemoryRetriever,
    get_memory_retriever,
)

__all__ = [
    # Orchestrator
    "Orchestrator",
    "OrchestratorResult",
    "get_orchestrator",
    # Intent Classifier
    "IntentType",
    "IntentResult",
    "DelegationTarget",
    "IntentClassifier",
    "get_classifier",
    # Delegation Protocol
    "DelegationType",
    "DelegationStatus",
    "Priority",
    "DelegationContext",
    "DelegationRequest",
    "DelegationResult",
    "DelegationManager",
    "get_delegation_manager",
    # Memory Integration
    "UserProfile",
    "MemoryItem",
    "SessionSummary",
    "MemoryContext",
    "MemoryRetriever",
    "get_memory_retriever",
]
