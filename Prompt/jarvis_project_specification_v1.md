# Jarvis AI Assistant - Complete Project Specification

## Executive Summary

This document expands on the original project prompt to provide a comprehensive specification for building a **local-first, persistent AI assistant** ("Jarvis") for macOS. The system combines:

- **Tauri** desktop shell with chat + voice UI
- **Claude Agent SDK** for intelligent orchestration
- **Tiered Autonomous Swarm Architecture** for complex task execution
- **Persistent Memory System** (short-term, long-term, semantic RAG)
- **Human-in-the-loop** permission controls
- **Scripted Event Bus** to overcome SDK limitations on nested agent spawning

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [The Subagent Spawning Problem](#the-subagent-spawning-problem)
3. [Proposed Solution: Scripted Orchestration Layer](#proposed-solution-scripted-orchestration-layer)
4. [System Components](#system-components)
5. [Memory Architecture](#memory-architecture)
6. [Orchestrator Design](#orchestrator-design)
7. [Domain Lead Specifications](#domain-lead-specifications)
8. [Event Bus Architecture](#event-bus-architecture)
9. [Technology Stack](#technology-stack)
10. [Implementation Roadmap](#implementation-roadmap)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TAURI FRONTEND                                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │ Chat Panel  │ │ Voice UI    │ │ Task        │ │ Memory Manager          ││
│  │ (Streaming) │ │ (Whisper)   │ │ Timeline    │ │ (View/Edit/Delete)      ││
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └───────────┬─────────────┘│
│         └───────────────┴───────────────┴───────────────────┬───────────────│
│                                                             │               │
│                    WebSocket / SSE Event Stream             │               │
└─────────────────────────────────────────────────────────────┼───────────────┘
                                                              │
┌─────────────────────────────────────────────────────────────▼───────────────┐
│                         ORCHESTRATION LAYER (Python)                         │
│  ┌──────────────────────────────────────────────────────────────────────────┐│
│  │                        JARVIS ORCHESTRATOR                               ││
│  │                   (Persistent Claude Agent Instance)                      ││
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ ││
│  │  │ Routing     │ │ State       │ │ Permission  │ │ Memory Interface    │ ││
│  │  │ Engine      │ │ Machine     │ │ Broker      │ │ (Read/Write)        │ ││
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────────┘ ││
│  └──────────────────────────────────┬───────────────────────────────────────┘│
│                                     │                                        │
│  ┌──────────────────────────────────▼───────────────────────────────────────┐│
│  │                         SCRIPTED EVENT BUS                               ││
│  │         (Manages Agent Lifecycle, Message Routing, Results)              ││
│  └──────────────────────────────────┬───────────────────────────────────────┘│
│                                     │                                        │
│      ┌──────────────────────────────┼──────────────────────────────┐        │
│      │                              │                              │        │
│      ▼                              ▼                              ▼        │
│  ┌────────────┐              ┌────────────┐              ┌────────────┐     │
│  │ CODE LEAD  │              │RESEARCH    │              │ TASK LEAD  │     │
│  │ (Spawned)  │              │LEAD        │              │ (Spawned)  │     │
│  └─────┬──────┘              └─────┬──────┘              └─────┬──────┘     │
│        │                           │                           │            │
│  ┌─────▼──────┐              ┌─────▼──────┐              ┌─────▼──────┐     │
│  │ WORKER     │              │ WORKER     │              │ WORKER     │     │
│  │ POOL       │              │ POOL       │              │ POOL       │     │
│  └────────────┘              └────────────┘              └────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────────┐
│                           LOCAL SERVICES                                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │ Memory DB   │ │ RAG Vector  │ │ Tool        │ │ Audit Log               ││
│  │ (SQLite)    │ │ Store       │ │ Executor    │ │ (Immutable)             ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## The Subagent Spawning Problem

### The Limitation

You correctly identified a critical limitation in the Claude Agent SDK:

> **Agents spawned via the SDK cannot themselves spawn additional subagents using the SDK's `Task` tool or similar mechanisms.**

This is because:

1. **Process Isolation**: Each agent runs in its own context/process
2. **No Recursive SDK Access**: Subagents don't have access to spawn new SDK clients
3. **Context Limitations**: The SDK's `Task` tool creates agents that don't inherit spawning capabilities
4. **Credential Scope**: API keys and MCP servers aren't automatically inherited

### Why This Matters for Jarvis

Your tiered swarm architecture requires:
```
Orchestrator → Domain Lead → Workers
     ↓              ↓           ↓
  Routes       Delegates    Executes
```

Without nested spawning, a Domain Lead (Code Lead, Research Lead, etc.) **cannot** create Worker agents to parallelize work.

---

## Proposed Solution: Scripted Orchestration Layer

### Core Concept: External Process Manager

Instead of relying on agents to spawn agents, we create a **Python-based Orchestration Layer** that:

1. **Receives spawn requests** via a structured protocol
2. **Manages agent lifecycles** externally (not from within agents)
3. **Routes messages** between agents via an event bus
4. **Collects and synthesizes results** back to the requesting agent

### Architecture Pattern: Agent-as-a-Service with Event Bus

```python
"""
The key insight: Agents don't spawn agents.
The ORCHESTRATION LAYER spawns agents based on REQUESTS from agents.
"""

# Agents communicate via structured tool calls:
{
    "type": "spawn_request",
    "requester": "code_lead_001",
    "agent_type": "programmer",
    "task": "Implement authentication module",
    "config": {
        "model": "claude-sonnet-4-5-20250929",
        "tools": ["coding"],
        "mcp_servers": ["linear"]
    },
    "callback_id": "task_auth_001"
}
```

### The Two-Layer Solution

#### Layer 1: Orchestrator Agent (Claude)
- Persistent Claude instance
- Understands user intent
- Makes high-level decisions
- Routes to appropriate Domain Leads
- Does NOT directly spawn—sends spawn requests

#### Layer 2: Process Manager (Python)
- Listens for spawn requests via tool calls
- Actually creates agent processes using `spawn_agents.py`
- Manages agent lifecycle (start, monitor, terminate)
- Routes messages between agents
- Collects results and sends them back

---

## System Components

### 1. Jarvis Orchestrator (The Persistent Brain)

```python
class JarvisOrchestrator:
    """
    The persistent AI that users interact with.
    Acts as the 'face' of Jarvis and the routing intelligence.
    """

    def __init__(self):
        self.memory_interface = MemoryInterface()
        self.event_bus = EventBus()
        self.active_tasks = {}
        self.conversation_context = []

    # Core responsibilities:
    # 1. Understand user intent
    # 2. Retrieve relevant memory/context
    # 3. Decide: handle directly OR delegate to Domain Lead
    # 4. Track task progress
    # 5. Synthesize results for user
    # 6. Update memory based on interactions
```

**System Prompt for Orchestrator:**
```markdown
# YOUR ROLE — JARVIS ORCHESTRATOR

You are the primary AI assistant interface for the user. You are persistent—you
remember past conversations and learn user preferences over time.

## Core Responsibilities

1. **Understand Intent**: Parse user requests to determine what they need
2. **Memory Access**: Query short-term and long-term memory for context
3. **Routing Decision**: Decide if you can handle directly or need to delegate
4. **Task Orchestration**: Dispatch work to appropriate Domain Leads
5. **Result Synthesis**: Combine outputs from multiple agents into coherent responses
6. **Memory Updates**: Store new facts, preferences, and outcomes

## Delegation Protocol

When a task requires specialized work, use the `delegate_task` tool:

```json
{
    "domain": "CODE|RESEARCH|TASK",
    "objective": "What needs to be accomplished",
    "context": "Relevant background from memory",
    "priority": "P0|P1|P2|P3",
    "callback_expected": true
}
```

## You Do NOT:
- Execute code directly (delegate to Code Lead)
- Perform deep research (delegate to Research Lead)
- Bypass permission checks
- Store memory without policy approval
```

### 2. Process Manager (Python Backend)

```python
class ProcessManager:
    """
    External Python process that manages agent lifecycles.
    This is the KEY to enabling hierarchical agent spawning.
    """

    def __init__(self):
        self.active_agents: Dict[str, AgentProcess] = {}
        self.event_bus = EventBus()
        self.spawn_queue = asyncio.Queue()
        self.result_store = {}

    async def handle_spawn_request(self, request: SpawnRequest) -> str:
        """
        Called when ANY agent requests spawning another agent.
        The orchestrator or domain leads don't spawn directly—
        they send spawn requests that THIS manager fulfills.
        """
        agent_id = self.generate_agent_id(request)

        config = AgentSpawner.create_config(
            name=agent_id,
            system_prompt=self.load_prompt(request.agent_type),
            model=request.config.model,
            tools=get_tools(request.config.tools),
            mcp_server_names=request.config.mcp_servers,
        )

        # Spawn in background, results go to event bus
        asyncio.create_task(
            self.run_agent_with_callback(
                config=config,
                query=request.task,
                callback_id=request.callback_id,
                requester=request.requester
            )
        )

        return agent_id

    async def run_agent_with_callback(
        self,
        config: AgentConfig,
        query: str,
        callback_id: str,
        requester: str
    ):
        """Run agent and send results back via event bus."""
        try:
            messages = await AgentSpawner.spawn_agent(config, query)
            result = self.extract_result(messages)

            # Send result back to the requesting agent
            await self.event_bus.publish(
                channel=f"agent.{requester}",
                event=AgentCompletionEvent(
                    callback_id=callback_id,
                    status="success",
                    result=result
                )
            )
        except Exception as e:
            await self.event_bus.publish(
                channel=f"agent.{requester}",
                event=AgentCompletionEvent(
                    callback_id=callback_id,
                    status="error",
                    error=str(e)
                )
            )
```

### 3. Custom Tools for Agents

Agents don't call `AgentSpawner` directly. They use **custom tools** that send messages to the Process Manager:

```python
# Tool definition for agents to request spawning
SPAWN_AGENT_TOOL = {
    "name": "request_agent_spawn",
    "description": """
    Request the Process Manager to spawn a new agent.
    Use this when you need to delegate work to a specialized worker.
    The result will be delivered asynchronously via callback.
    """,
    "parameters": {
        "type": "object",
        "properties": {
            "agent_type": {
                "type": "string",
                "enum": ["programmer", "researcher", "writer", "reviewer"],
                "description": "Type of agent to spawn"
            },
            "task": {
                "type": "string",
                "description": "The task for the agent to perform"
            },
            "priority": {
                "type": "string",
                "enum": ["P0", "P1", "P2", "P3"]
            },
            "await_result": {
                "type": "boolean",
                "description": "Whether to wait for result before continuing"
            }
        },
        "required": ["agent_type", "task"]
    }
}

# Tool definition to check on spawned agents
CHECK_AGENT_RESULT_TOOL = {
    "name": "check_agent_result",
    "description": "Check if a previously spawned agent has completed",
    "parameters": {
        "type": "object",
        "properties": {
            "callback_id": {
                "type": "string",
                "description": "The callback ID from the spawn request"
            }
        },
        "required": ["callback_id"]
    }
}
```

---

## Memory Architecture

### Three-Tier Memory System

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              MEMORY SYSTEM                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                    TIER 1: SHORT-TERM MEMORY                            ││
│  │  ┌────────────────────────────────────────────────────────────────────┐ ││
│  │  │ • Current conversation context (last N turns)                      │ ││
│  │  │ • Active task state (what's being worked on)                       │ ││
│  │  │ • Pending approvals queue                                          │ ││
│  │  │ • Recent tool call results                                         │ ││
│  │  │                                                                    │ ││
│  │  │ Storage: In-memory + Redis (optional)                              │ ││
│  │  │ TTL: Session-scoped or 24 hours                                    │ ││
│  │  └────────────────────────────────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                    TIER 2: LONG-TERM STRUCTURED MEMORY                  ││
│  │  ┌────────────────────────────────────────────────────────────────────┐ ││
│  │  │ • User profile (name, preferences, communication style)           │ ││
│  │  │ • Learned facts ("User prefers TypeScript over JavaScript")       │ ││
│  │  │ • Recurring patterns ("User usually codes in the evening")        │ ││
│  │  │ • Project metadata (repos, file locations, conventions)           │ ││
│  │  │ • Relationship graph (people, tools, topics of interest)          │ ││
│  │  │                                                                    │ ││
│  │  │ Storage: SQLite with structured schema                             │ ││
│  │  │ TTL: Persistent until user deletes                                 │ ││
│  │  └────────────────────────────────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                    TIER 3: SEMANTIC MEMORY (RAG)                        ││
│  │  ┌────────────────────────────────────────────────────────────────────┐ ││
│  │  │ • User documents (notes, papers, code)                             │ ││
│  │  │ • Past conversation summaries                                      │ ││
│  │  │ • Indexed local files (with user permission)                       │ ││
│  │  │ • External knowledge (cached web pages, docs)                      │ ││
│  │  │                                                                    │ ││
│  │  │ Storage: Vector DB (ChromaDB, Qdrant, or LanceDB)                  │ ││
│  │  │ Embedding: Local model (all-MiniLM-L6-v2) or OpenAI                │ ││
│  │  │ TTL: User-controlled per source                                    │ ││
│  │  └────────────────────────────────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Memory Schema (SQLite)

```sql
-- User profile and preferences
CREATE TABLE user_profile (
    id INTEGER PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    source TEXT,  -- 'inferred', 'explicit', 'observed'
    confidence REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Learned facts with provenance
CREATE TABLE facts (
    id INTEGER PRIMARY KEY,
    content TEXT NOT NULL,
    category TEXT,  -- 'preference', 'skill', 'project', 'relationship'
    source_conversation_id TEXT,
    source_timestamp TIMESTAMP,
    confidence REAL DEFAULT 1.0,
    times_reinforced INTEGER DEFAULT 1,
    last_accessed TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversation summaries
CREATE TABLE conversation_summaries (
    id INTEGER PRIMARY KEY,
    conversation_id TEXT UNIQUE NOT NULL,
    summary TEXT NOT NULL,
    key_topics TEXT,  -- JSON array
    action_items TEXT,  -- JSON array
    new_facts_learned TEXT,  -- JSON array of fact IDs
    started_at TIMESTAMP,
    ended_at TIMESTAMP
);

-- Memory access log (for explainability)
CREATE TABLE memory_access_log (
    id INTEGER PRIMARY KEY,
    memory_type TEXT,  -- 'profile', 'fact', 'rag', 'conversation'
    memory_id TEXT,
    access_type TEXT,  -- 'read', 'write', 'delete'
    reason TEXT,
    agent_id TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Memory Interface for Agents

```python
class MemoryInterface:
    """
    Unified interface for all memory operations.
    Enforces access policies and tracks provenance.
    """

    async def remember(
        self,
        content: str,
        category: str,
        source: str = "conversation",
        requires_approval: bool = True
    ) -> MemoryWriteResult:
        """
        Store a new fact in long-term memory.
        High-confidence facts may require user approval.
        """
        if requires_approval:
            approval = await self.permission_broker.request_approval(
                action="memory_write",
                content=content,
                category=category
            )
            if not approval.granted:
                return MemoryWriteResult(stored=False, reason="User denied")

        # Store with provenance
        fact_id = await self.store_fact(content, category, source)
        await self.log_access("fact", fact_id, "write", source)
        return MemoryWriteResult(stored=True, fact_id=fact_id)

    async def recall(
        self,
        query: str,
        memory_types: List[str] = ["facts", "profile", "rag"],
        limit: int = 10
    ) -> RecallResult:
        """
        Retrieve relevant memories for a query.
        Combines structured and semantic search.
        """
        results = []

        if "profile" in memory_types:
            profile_hits = await self.search_profile(query)
            results.extend(profile_hits)

        if "facts" in memory_types:
            fact_hits = await self.search_facts(query, limit)
            results.extend(fact_hits)

        if "rag" in memory_types:
            rag_hits = await self.vector_search(query, limit)
            results.extend(rag_hits)

        # Deduplicate and rank
        ranked = self.rank_and_dedupe(results, query)
        return RecallResult(memories=ranked[:limit])

    async def forget(
        self,
        memory_id: str,
        reason: str
    ) -> bool:
        """
        Delete a memory (user-initiated).
        This is an explicit action, not automatic decay.
        """
        await self.log_access("fact", memory_id, "delete", reason)
        return await self.delete_fact(memory_id)
```

---

## Event Bus Architecture

### Why an Event Bus?

The event bus solves several problems:

1. **Decouples agents** from direct communication
2. **Enables async workflows** (spawn, continue working, receive result later)
3. **Provides observability** (all messages can be logged/displayed)
4. **Allows the UI** to subscribe to events for real-time updates

### Event Bus Implementation

```python
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Any
from datetime import datetime
import asyncio
import json


@dataclass
class Event:
    """Base event structure."""
    event_type: str
    payload: Dict[str, Any]
    source: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class AgentSpawnRequestEvent(Event):
    event_type: str = "agent.spawn.request"


@dataclass
class AgentCompletionEvent(Event):
    event_type: str = "agent.completion"


@dataclass
class ToolExecutionEvent(Event):
    event_type: str = "tool.execution"


@dataclass
class ApprovalRequestEvent(Event):
    event_type: str = "approval.request"


@dataclass
class MemoryUpdateEvent(Event):
    event_type: str = "memory.update"


class EventBus:
    """
    Central event bus for inter-agent communication.
    Supports pub/sub pattern with channel filtering.
    """

    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_log: List[Event] = []
        self.pending_events: Dict[str, asyncio.Queue] = {}

    def subscribe(self, channel: str, callback: Callable):
        """Subscribe to events on a channel."""
        if channel not in self.subscribers:
            self.subscribers[channel] = []
        self.subscribers[channel].append(callback)

    async def publish(self, channel: str, event: Event):
        """Publish an event to a channel."""
        # Log for observability
        self.event_log.append(event)

        # Notify subscribers
        if channel in self.subscribers:
            for callback in self.subscribers[channel]:
                asyncio.create_task(callback(event))

        # Also notify wildcard subscribers
        if "*" in self.subscribers:
            for callback in self.subscribers["*"]:
                asyncio.create_task(callback(event))

        # If there's a pending queue for this channel, add to it
        if channel in self.pending_events:
            await self.pending_events[channel].put(event)

    async def wait_for(
        self,
        channel: str,
        timeout: float = 300.0
    ) -> Event:
        """Wait for next event on a channel (blocking with timeout)."""
        if channel not in self.pending_events:
            self.pending_events[channel] = asyncio.Queue()

        try:
            event = await asyncio.wait_for(
                self.pending_events[channel].get(),
                timeout=timeout
            )
            return event
        except asyncio.TimeoutError:
            raise TimeoutError(f"No event on {channel} within {timeout}s")

    def get_event_log(
        self,
        since: datetime = None,
        event_types: List[str] = None
    ) -> List[Event]:
        """Get event log for debugging/UI."""
        events = self.event_log
        if since:
            events = [e for e in events if e.timestamp >= since]
        if event_types:
            events = [e for e in events if e.event_type in event_types]
        return events
```

### Event Flow Example

```
User: "Help me refactor the authentication module and write tests"

1. [UI → Orchestrator]
   Event: user.message
   Payload: { "text": "Help me refactor..." }

2. [Orchestrator → Event Bus]
   Event: agent.spawn.request
   Payload: {
     "agent_type": "code_lead",
     "task": "Refactor authentication module and write tests",
     "callback_id": "task_001"
   }

3. [Process Manager receives spawn request]
   → Spawns Code Lead agent

4. [Code Lead → Event Bus]
   Event: agent.spawn.request (via tool call)
   Payload: {
     "agent_type": "programmer",
     "task": "Refactor auth module",
     "callback_id": "subtask_001a"
   }

   Event: agent.spawn.request
   Payload: {
     "agent_type": "programmer",
     "task": "Write tests for auth module",
     "callback_id": "subtask_001b"
   }

5. [Process Manager spawns 2 programmers in parallel]

6. [Programmer agents complete]
   Event: agent.completion (×2)
   → Results routed back to Code Lead

7. [Code Lead synthesizes results]
   Event: agent.completion
   → Result routed back to Orchestrator

8. [Orchestrator → UI]
   Event: assistant.message
   Payload: { "text": "I've refactored the auth module..." }
```

---

## Orchestrator Design

### Orchestrator Responsibilities

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           JARVIS ORCHESTRATOR                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  INPUTS                          PROCESSING                    OUTPUTS      │
│  ──────                          ──────────                    ───────      │
│                                                                              │
│  ┌──────────────┐               ┌──────────────┐              ┌───────────┐ │
│  │ User Message │──────────────▶│ Intent       │              │ Response  │ │
│  └──────────────┘               │ Classification│             │ to User   │ │
│                                 └───────┬──────┘              └─────▲─────┘ │
│  ┌──────────────┐                       │                           │       │
│  │ Voice Input  │────────────────────┐  │                           │       │
│  │ (Transcribed)│                    │  │                           │       │
│  └──────────────┘                    │  ▼                           │       │
│                                 ┌────┴─────────┐                    │       │
│  ┌──────────────┐               │ Memory       │                    │       │
│  │ Agent Results│──────────────▶│ Retrieval    │                    │       │
│  │ (Callbacks)  │               │ (Context)    │                    │       │
│  └──────────────┘               └───────┬──────┘                    │       │
│                                         │                           │       │
│                                         ▼                           │       │
│                                 ┌──────────────┐                    │       │
│                                 │ Decision     │                    │       │
│                                 │ Engine       │                    │       │
│                                 └───────┬──────┘                    │       │
│                                         │                           │       │
│                    ┌────────────────────┼────────────────────┐      │       │
│                    │                    │                    │      │       │
│                    ▼                    ▼                    ▼      │       │
│             ┌────────────┐      ┌──────────────┐      ┌──────────┐  │       │
│             │ Handle     │      │ Delegate to  │      │ Request  │  │       │
│             │ Directly   │──────│ Domain Lead  │──────│ Approval │──┘       │
│             │            │      │              │      │ (HITL)   │          │
│             └────────────┘      └──────────────┘      └──────────┘          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Decision Matrix

| User Request Type | Handle Directly? | Delegate To | Requires Approval? |
|-------------------|------------------|-------------|-------------------|
| Casual conversation | ✅ Yes | — | No |
| Simple questions | ✅ Yes | — | No |
| Code implementation | ❌ No | Code Lead | For file writes |
| Research tasks | ❌ No | Research Lead | No |
| File operations (read) | ✅ Yes | — | No |
| File operations (write) | ❌ No | Code Lead | Yes |
| System commands | ❌ No | Task Lead | Yes |
| Memory updates | ✅ Yes | — | Policy-based |
| Schedule/reminders | ✅ Yes | — | No |

### Orchestrator Tools

```python
ORCHESTRATOR_TOOLS = [
    # Memory operations
    {
        "name": "memory_recall",
        "description": "Retrieve relevant memories for context",
        "parameters": {
            "query": "string",
            "memory_types": "array of: profile, facts, rag, conversations",
            "limit": "integer"
        }
    },
    {
        "name": "memory_store",
        "description": "Store a new fact or preference in long-term memory",
        "parameters": {
            "content": "string",
            "category": "preference|fact|project|relationship",
            "confidence": "float 0-1"
        }
    },

    # Delegation
    {
        "name": "delegate_to_lead",
        "description": "Delegate a complex task to a specialized Domain Lead",
        "parameters": {
            "domain": "CODE|RESEARCH|TASK",
            "objective": "string",
            "context": "string",
            "priority": "P0|P1|P2|P3",
            "constraints": "array of strings"
        }
    },

    # Task tracking
    {
        "name": "check_task_status",
        "description": "Check status of a delegated task",
        "parameters": {
            "task_id": "string"
        }
    },
    {
        "name": "list_active_tasks",
        "description": "List all currently running tasks",
        "parameters": {}
    },

    # User interaction
    {
        "name": "request_user_approval",
        "description": "Request explicit user approval for a sensitive action",
        "parameters": {
            "action": "string",
            "risk_level": "low|medium|high",
            "details": "string"
        }
    },

    # File operations (direct, for simple reads)
    {
        "name": "read_file",
        "description": "Read a file from disk",
        "parameters": {
            "path": "string"
        }
    }
]
```

---

## Domain Lead Specifications

### Available Domain Leads

| Lead | Responsibility | Workers Available |
|------|----------------|-------------------|
| **Code Lead** | Software development, architecture, debugging | Programmer, Reviewer, Documentor |
| **Research Lead** | Information gathering, synthesis, reports | Researcher, Writer, Summarizer |
| **Task Lead** | System automation, workflows, integrations | Executor, Scheduler, Monitor |

### Code Lead Integration

The Code Lead from your existing architecture integrates seamlessly:

```python
CODE_LEAD_CONFIG = {
    "agent_type": "code_lead",
    "base_prompt": ".claude/agents/leads/Code_Lead_Architect.md",
    "model": "claude-sonnet-4-5-20250929",  # or opus for complex architecture
    "tools": [
        "request_agent_spawn",      # To spawn programmers
        "check_agent_result",       # To check worker status
        "read_file",
        "write_file",
        "execute_command",
        "linear_tools",             # Project management
    ],
    "mcp_servers": ["linear"],
    "worker_types": ["programmer", "reviewer", "documentor"],
    "max_parallel_workers": 5
}
```

### Modified Delegation Flow

The existing delegation template works, but spawn calls go through the event bus:

```markdown
# Task Delegation (Modified for Event Bus)

When spawning workers, use `request_agent_spawn` tool:

```json
{
    "agent_type": "programmer",
    "task": "Implement the authentication controller",
    "priority": "P1",
    "context": {
        "related_files": ["src/auth/", "src/models/User.ts"],
        "acceptance_criteria": [
            "Implement login/logout endpoints",
            "Add JWT token generation",
            "Include input validation"
        ]
    },
    "await_result": false
}
```

The Process Manager will spawn the agent and deliver results via callback.
```

---

## Technology Stack

### Core Technologies

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Desktop Shell** | Tauri 2.0 | Native performance, Rust security, smaller than Electron |
| **Frontend** | React + TypeScript | Mature ecosystem, strong typing |
| **UI Components** | shadcn/ui + Tailwind | Accessible, customizable, modern |
| **Backend Runtime** | Python 3.11+ | Claude SDK support, rich async ecosystem |
| **Agent Framework** | Claude Agent SDK | Native Claude support, tool calling |
| **Database** | SQLite + SQLCipher | Local-first, encrypted, zero-config |
| **Vector Store** | ChromaDB (local) | Embedded, Python-native, simple API |
| **Embeddings** | all-MiniLM-L6-v2 | Local, fast, good quality |
| **Voice STT** | Whisper (local) | Privacy, accuracy, open source |
| **Voice TTS** | macOS AVSpeechSynthesizer | Native, free, good quality |
| **IPC** | WebSocket + JSON-RPC | Bidirectional, streaming support |
| **Process Management** | asyncio + anyio | Robust async, task groups |

### Dependency Versions

```toml
# pyproject.toml (backend)
[project]
requires-python = ">=3.11"

[project.dependencies]
claude-agent-sdk = ">=0.1.0"
anyio = ">=4.0.0"
chromadb = ">=0.4.0"
sentence-transformers = ">=2.2.0"
openai-whisper = ">=20231117"
sqlalchemy = ">=2.0.0"
pydantic = ">=2.0.0"
fastapi = ">=0.100.0"
websockets = ">=12.0"
python-json-logger = ">=2.0.0"
```

```json
// package.json (frontend)
{
  "dependencies": {
    "@tauri-apps/api": "^2.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@radix-ui/react-*": "latest",
    "tailwindcss": "^3.4.0",
    "zustand": "^4.4.0",
    "react-query": "^5.0.0"
  }
}
```

---

## Implementation Roadmap

### Phase 1: Foundation (Core Infrastructure)

```markdown
## Phase 1 Deliverables

### 1.1 Project Scaffolding
- [ ] Tauri project setup with React frontend
- [ ] Python backend with FastAPI
- [ ] WebSocket communication layer
- [ ] Basic UI shell (menu bar, chat panel)

### 1.2 Agent Infrastructure
- [ ] Process Manager implementation
- [ ] Event Bus with pub/sub
- [ ] Spawn request handling
- [ ] Result callback routing

### 1.3 Orchestrator MVP
- [ ] Basic orchestrator agent setup
- [ ] Intent classification (direct vs delegate)
- [ ] Simple memory interface (in-memory only)
- [ ] Basic tool set (file read, delegate)

### 1.4 Single Domain Lead
- [ ] Code Lead integration
- [ ] Programmer worker spawning
- [ ] End-to-end code task execution
```

### Phase 2: Memory & Persistence

```markdown
## Phase 2 Deliverables

### 2.1 Short-term Memory
- [ ] Conversation context management
- [ ] Active task state tracking
- [ ] Session persistence (Redis optional)

### 2.2 Long-term Memory
- [ ] SQLite schema implementation
- [ ] User profile storage
- [ ] Fact storage with provenance
- [ ] Conversation summarization

### 2.3 Semantic Memory (RAG)
- [ ] ChromaDB integration
- [ ] Local embedding model setup
- [ ] Document indexing pipeline
- [ ] Hybrid search (structured + semantic)

### 2.4 Memory UI
- [ ] Memory manager view
- [ ] Edit/delete capabilities
- [ ] Source provenance display
```

### Phase 3: Voice & Interaction

```markdown
## Phase 3 Deliverables

### 3.1 Speech-to-Text
- [ ] Whisper model integration
- [ ] Push-to-talk UI
- [ ] Streaming transcription
- [ ] Recording indicator

### 3.2 Text-to-Speech
- [ ] macOS native TTS integration
- [ ] Interruptible playback
- [ ] Voice selection settings

### 3.3 Enhanced UI
- [ ] Task timeline view
- [ ] Real-time event streaming
- [ ] Approval modal system
- [ ] Settings panel
```

### Phase 4: Full Swarm

```markdown
## Phase 4 Deliverables

### 4.1 Additional Domain Leads
- [ ] Research Lead implementation
- [ ] Task Lead implementation
- [ ] Lead prompt refinement

### 4.2 Worker Pool Management
- [ ] Parallel worker spawning
- [ ] Worker lifecycle management
- [ ] Result aggregation
- [ ] Error handling & recovery

### 4.3 Cross-Lead Communication
- [ ] Event bus channels per lead
- [ ] Result routing between leads
- [ ] Conflict resolution
```

### Phase 5: Polish & Security

```markdown
## Phase 5 Deliverables

### 5.1 Permission System
- [ ] Tool risk classification
- [ ] Approval workflow refinement
- [ ] Audit log implementation
- [ ] Permission presets (strict/relaxed)

### 5.2 Security Hardening
- [ ] SQLCipher encryption
- [ ] Prompt injection defenses
- [ ] Input sanitization
- [ ] Secure IPC

### 5.3 User Experience
- [ ] Onboarding flow
- [ ] Error recovery UX
- [ ] Performance optimization
- [ ] Keyboard shortcuts
```

---

## Complete Event Bus Protocol

### Message Types

```typescript
// TypeScript definitions for frontend consumption

interface BaseEvent {
  event_id: string;
  event_type: string;
  source: string;
  timestamp: string;
  payload: Record<string, any>;
}

// User → Orchestrator
interface UserMessageEvent extends BaseEvent {
  event_type: "user.message";
  payload: {
    text: string;
    attachments?: Attachment[];
    voice_audio_path?: string;
  };
}

// Orchestrator → UI (streaming response)
interface AssistantMessageEvent extends BaseEvent {
  event_type: "assistant.message";
  payload: {
    text: string;
    is_streaming: boolean;
    is_complete: boolean;
  };
}

// Agent → Process Manager
interface SpawnRequestEvent extends BaseEvent {
  event_type: "agent.spawn.request";
  payload: {
    requester: string;
    agent_type: string;
    task: string;
    config: AgentConfig;
    callback_id: string;
    priority: "P0" | "P1" | "P2" | "P3";
  };
}

// Process Manager → Agent
interface AgentCompletionEvent extends BaseEvent {
  event_type: "agent.completion";
  payload: {
    callback_id: string;
    status: "success" | "error" | "cancelled";
    result?: any;
    error?: string;
    execution_time_ms: number;
  };
}

// Any Agent → UI (for timeline display)
interface ToolExecutionEvent extends BaseEvent {
  event_type: "tool.execution";
  payload: {
    agent_id: string;
    tool_name: string;
    tool_input: Record<string, any>;
    status: "started" | "completed" | "failed";
    result?: any;
  };
}

// Orchestrator → UI
interface ApprovalRequestEvent extends BaseEvent {
  event_type: "approval.request";
  payload: {
    request_id: string;
    action: string;
    risk_level: "low" | "medium" | "high";
    details: string;
    timeout_seconds: number;
  };
}

// UI → Orchestrator
interface ApprovalResponseEvent extends BaseEvent {
  event_type: "approval.response";
  payload: {
    request_id: string;
    granted: boolean;
    modified_action?: string;
  };
}

// Memory system events
interface MemoryUpdateEvent extends BaseEvent {
  event_type: "memory.update";
  payload: {
    operation: "write" | "delete";
    memory_type: "profile" | "fact" | "rag";
    memory_id: string;
    content_preview: string;
  };
}
```

### WebSocket Protocol

```python
# Backend WebSocket handler
from fastapi import WebSocket
import json

class WebSocketManager:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.connections: List[WebSocket] = []

        # Subscribe to all events for UI streaming
        self.event_bus.subscribe("*", self.broadcast_to_ui)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)

    async def broadcast_to_ui(self, event: Event):
        """Send all events to connected UI clients."""
        message = json.dumps({
            "event_id": event.event_id,
            "event_type": event.event_type,
            "source": event.source,
            "timestamp": event.timestamp.isoformat(),
            "payload": event.payload
        })

        for connection in self.connections:
            try:
                await connection.send_text(message)
            except:
                self.connections.remove(connection)

    async def handle_message(self, websocket: WebSocket, message: str):
        """Handle incoming messages from UI."""
        data = json.loads(message)
        event_type = data.get("event_type")

        if event_type == "user.message":
            await self.event_bus.publish(
                channel="orchestrator.input",
                event=UserMessageEvent(
                    source="ui",
                    payload=data["payload"]
                )
            )
        elif event_type == "approval.response":
            await self.event_bus.publish(
                channel="orchestrator.approvals",
                event=ApprovalResponseEvent(
                    source="ui",
                    payload=data["payload"]
                )
            )
```

---

## Key Architectural Decisions

### Decision 1: External Process Manager vs In-Agent Spawning

**Decision**: Use external Process Manager

**Rationale**:
- Claude Agent SDK doesn't support recursive agent spawning
- External process maintains control and observability
- Enables proper resource management and cleanup
- Allows UI to observe all agent activity

### Decision 2: Event Bus vs Direct Calls

**Decision**: All inter-agent communication goes through Event Bus

**Rationale**:
- Decouples agents from each other
- Enables async/parallel workflows
- Provides natural logging/observability point
- UI can subscribe to see all activity
- Enables replay/debugging

### Decision 3: Local-first with Cloud LLM

**Decision**: Local everything except LLM inference

**Rationale**:
- User data never leaves machine
- Memory, tools, and state are fully local
- Only prompts/completions go to Claude API
- Enables offline operation for cached contexts

### Decision 4: SQLite + ChromaDB over Postgres + Pinecone

**Decision**: Embedded databases only

**Rationale**:
- Zero external dependencies
- No server processes to manage
- Portable (single directory)
- Sufficient for single-user workloads
- Can migrate to hosted if needed later

---

## Open Questions & Future Considerations

### Questions to Resolve

1. **Agent Context Size**: How much context can each agent handle before needing to summarize?
2. **Memory Consolidation**: How often should conversation history be summarized into long-term memory?
3. **Worker Pool Limits**: What's the optimal max parallel workers per Domain Lead?
4. **Approval Fatigue**: How to balance security with approval UX?

### Future Enhancements

1. **Multi-user Support**: Separate memory stores per user
2. **Plugin System**: Third-party tool integrations
3. **Wake Word**: "Hey Jarvis" activation
4. **Mobile Companion**: iOS/Android app for remote queries
5. **Learning from Corrections**: Improve based on user feedback

---

## Appendix A: Full Directory Structure

```
jarvis/
├── src-tauri/                      # Tauri Rust backend
│   ├── src/
│   │   └── main.rs
│   ├── Cargo.toml
│   └── tauri.conf.json
│
├── src/                            # React frontend
│   ├── components/
│   │   ├── ChatPanel.tsx
│   │   ├── TaskTimeline.tsx
│   │   ├── MemoryManager.tsx
│   │   ├── ApprovalModal.tsx
│   │   └── VoiceButton.tsx
│   ├── hooks/
│   │   ├── useWebSocket.ts
│   │   └── useEventBus.ts
│   ├── stores/
│   │   ├── conversationStore.ts
│   │   └── memoryStore.ts
│   ├── App.tsx
│   └── main.tsx
│
├── backend/                        # Python backend
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── jarvis.py              # Main orchestrator agent
│   │   ├── prompts.py             # System prompts
│   │   └── tools.py               # Orchestrator tools
│   │
│   ├── process_manager/
│   │   ├── __init__.py
│   │   ├── manager.py             # Agent lifecycle management
│   │   ├── spawner.py             # spawn_agents.py integration
│   │   └── event_bus.py           # Event bus implementation
│   │
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── interface.py           # MemoryInterface class
│   │   ├── short_term.py          # Conversation context
│   │   ├── long_term.py           # SQLite facts/profile
│   │   ├── semantic.py            # ChromaDB RAG
│   │   └── models.py              # SQLAlchemy models
│   │
│   ├── leads/
│   │   ├── __init__.py
│   │   ├── code_lead.py
│   │   ├── research_lead.py
│   │   └── task_lead.py
│   │
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── programmer.py
│   │   ├── researcher.py
│   │   └── writer.py
│   │
│   ├── voice/
│   │   ├── __init__.py
│   │   ├── stt.py                 # Whisper integration
│   │   └── tts.py                 # macOS TTS
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── filesystem.py
│   │   ├── shell.py
│   │   └── web.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── websocket.py           # WebSocket handlers
│   │   └── routes.py              # REST endpoints
│   │
│   ├── config/
│   │   ├── settings.py
│   │   └── prompts/               # Agent prompt templates
│   │       ├── orchestrator.md
│   │       ├── code_lead.md
│   │       └── ...
│   │
│   └── main.py                    # FastAPI app entry
│
├── data/                          # Local data directory
│   ├── memory.db                  # SQLite (encrypted)
│   ├── chroma/                    # Vector store
│   ├── whisper/                   # Whisper models
│   └── logs/                      # Audit logs
│
├── scripts/
│   ├── setup.sh
│   ├── dev.sh
│   └── build.sh
│
├── tests/
│   ├── test_orchestrator.py
│   ├── test_event_bus.py
│   └── test_memory.py
│
├── pyproject.toml
├── package.json
└── README.md
```

---

## Appendix B: Example Conversation Flow

```
USER: "Help me set up a new Node.js project with TypeScript and Express"

JARVIS (Orchestrator):
1. Receives message
2. Classifies intent: CODE task
3. Retrieves memory: "User prefers pnpm over npm" (from past conversations)
4. Delegates to Code Lead

CODE LEAD:
1. Receives task with context
2. Plans subtasks:
   - Create project structure
   - Initialize package.json with pnpm
   - Configure TypeScript
   - Set up Express boilerplate
3. Spawns Programmer worker (via event bus)

PROGRAMMER:
1. Executes file operations
2. Runs pnpm commands
3. Creates files
4. Returns result

CODE LEAD:
1. Receives programmer result
2. Verifies structure
3. Returns success to Orchestrator

JARVIS (Orchestrator):
1. Receives Code Lead result
2. Formats user-friendly response
3. Stores fact: "User has Node project at ~/projects/new-app"
4. Responds to user with summary + next steps

UI:
- Shows streaming response
- Timeline shows: Thinking → Delegated to Code Lead → Programmer working → Files created → Complete
- Memory manager shows new project fact
```

---

*Document Version: 1.0*
*Last Updated: 2025-12-25*
*Author: Claude (Opus 4.5)*
