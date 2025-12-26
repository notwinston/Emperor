# Emperor AI Assistant - Implementation Roadmap v3

## Hybrid Architecture: CLI Orchestrator + SDK Agents

High-level implementation roadmap for building the Emperor AI Assistant using a **hybrid architecture**:
- **Orchestrator**: Claude Code CLI (max billing, built-in tools, routing)
- **Domain Leads & Workers**: Anthropic SDK (fine-grained control, custom tools)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                       Emperor Backend                            │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │            ORCHESTRATOR (Claude Code CLI)                   │ │
│  │                                                             │ │
│  │  • Receives user messages via WebSocket                     │ │
│  │  • Classifies intent                                        │ │
│  │  • Routes to appropriate Lead                               │ │
│  │  • Synthesizes final response                               │ │
│  │  • Has access to CLI's built-in tools                       │ │
│  └──────────────────────────┬─────────────────────────────────┘ │
│                             │                                    │
│              ┌──────────────┼──────────────┐                    │
│              ▼              ▼              ▼                    │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐         │
│  │  CODE LEAD    │ │ RESEARCH LEAD │ │  TASK LEAD    │         │
│  │ (Anthropic    │ │ (Anthropic    │ │ (Anthropic    │         │
│  │    SDK)       │ │    SDK)       │ │    SDK)       │         │
│  └───────┬───────┘ └───────┬───────┘ └───────┬───────┘         │
│          │                 │                 │                  │
│          ▼                 ▼                 ▼                  │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐         │
│  │   WORKERS     │ │   WORKERS     │ │   WORKERS     │         │
│  │ (Anthropic    │ │ (Anthropic    │ │ (Anthropic    │         │
│  │    SDK)       │ │    SDK)       │ │    SDK)       │         │
│  └───────────────┘ └───────────────┘ └───────────────┘         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Table of Contents

1. [Part 1: Project Scaffolding](#part-1-project-scaffolding)
2. [Part 2: Frontend Customization](#part-2-frontend-customization)
3. [Part 3: Python Backend Foundation](#part-3-python-backend-foundation)
4. [Part 4: WebSocket Communication](#part-4-websocket-communication)
5. [Part 5: Claude Code Bridge (Orchestrator)](#part-5-claude-code-bridge-orchestrator)
6. [Part 6: Anthropic SDK Setup (Agents)](#part-6-anthropic-sdk-setup-agents)
7. [Part 7: Event Bus Implementation](#part-7-event-bus-implementation)
8. [Part 8: Orchestrator Agent](#part-8-orchestrator-agent)
9. [Part 9: Memory System](#part-9-memory-system)
10. [Part 10: Domain Leads (SDK)](#part-10-domain-leads-sdk)
11. [Part 11: Tool System](#part-11-tool-system)
12. [Part 12: Voice Integration](#part-12-voice-integration)
13. [Part 13: Advanced UI Components](#part-13-advanced-ui-components)
14. [Part 14: Security & Permissions](#part-14-security--permissions)
15. [Part 15: Testing & Deployment](#part-15-testing--deployment)

---

# Part 1: Project Scaffolding

## Prerequisites

Ensure the following are installed:
- **Node.js 18+** — JavaScript runtime
- **Rust** — Required for Tauri backend
- **pnpm** — Package manager (faster than npm)
- **Python 3.11+** — For backend
- **Claude Code CLI** — `npm install -g @anthropic-ai/claude-code`

---

## Step 1.1: Create Project with Tauri

Run the Tauri create script and select the following options when prompted:

| Prompt | Selection |
|--------|-----------|
| Project name | Your choice (e.g., `emperor`) |
| Identifier | `com.yourname.assistant` |
| Package manager | `pnpm` |
| UI template | `React` |
| UI flavor | `TypeScript` |

---

## Step 1.2: Verify Scaffolding

Enter the project directory, install dependencies, and run a test build.

**Expected result:** A native window opens with the default Tauri + React template.

---

## Step 1.3: Create Backend Directory Structure

```
backend/
├── api/              # FastAPI routes and WebSocket handlers
├── config/           # Settings and logging configuration
├── sdk/              # Anthropic SDK client and base agent
│   ├── client.py     # SDK client wrapper
│   ├── base_agent.py # Base class for SDK agents
│   └── tools/        # Tool definitions for SDK agents
├── orchestrator/     # Main orchestrator (uses CLI bridge)
├── leads/            # Domain lead agents (use SDK)
├── workers/          # Worker agents (use SDK)
├── memory/           # Short-term, long-term, and RAG memory
├── tools/            # Tool registry and executors
├── process_manager/  # Agent lifecycle and event bus
└── voice/            # Speech-to-text and text-to-speech
```

Also create data directories:

```
data/
├── chroma/           # Vector database storage
├── logs/             # Application logs
└── whisper/          # Voice model cache
```

---

## Step 1.4: Create Frontend Directory Structure

```
src/
├── components/
│   └── ui/           # Base UI components (Button, Input, etc.)
├── hooks/            # Custom React hooks (useWebSocket, etc.)
├── stores/           # Zustand state stores
├── lib/              # Utility functions
├── types/            # TypeScript type definitions
└── assets/           # Static assets (icons, images)
```

---

## Step 1.5: Install Frontend Dependencies

**UI Framework:**
- Tailwind CSS with PostCSS and Autoprefixer
- Class variance authority for component variants
- Tailwind merge for class combining
- Lucide React for icons

**Radix UI Primitives:**
- Dialog, Dropdown Menu, Scroll Area
- Separator, Slot, Toast, Tooltip
- Avatar, Switch, Tabs

**State & Data:**
- Zustand for state management
- TanStack React Query for data fetching

**Utilities:**
- date-fns for date formatting
- uuid for ID generation
- react-markdown with remark-gfm for rendering
- tailwindcss-animate for animations

---

## Step 1.6-1.7: Initialize Tailwind & Checkpoint

Initialize Tailwind and verify the app runs with styles applied.

---

# Part 2: Frontend Customization

## Steps 2.1-2.15: Frontend Setup

(Same as original - configure Tailwind, create base CSS, update HTML template, configure TypeScript/Vite/Tauri, create utility functions, type definitions, base UI components, state store, WebSocket hook, chat components, main app)

See original roadmap for detailed steps.

---

# Part 3: Python Backend Foundation

## Step 3.1: Initialize Python Environment

In the `backend/` directory:
- Create Python virtual environment (venv)
- Create `requirements.txt` with core dependencies:

```
# Core API Framework
fastapi
uvicorn[standard]
websockets
pydantic
pydantic-settings
python-dotenv
python-json-logger
anyio

# Anthropic SDK (for Domain Leads & Workers)
anthropic>=0.40.0

# Memory System (mem0)
mem0ai>=0.1.0
```

---

## Steps 3.2-3.8: Backend Setup

(Same as original - create configuration module, API types, WebSocket manager, main application, environment file, development script, checkpoint)

See original roadmap for detailed steps.

---

# Part 4: WebSocket Communication

## Steps 4.1-4.4: WebSocket Enhancements

(Same as original - streaming responses, message queue, heartbeat, error recovery)

See original roadmap for detailed steps.

---

# Part 5: Claude Code Bridge (Orchestrator)

The orchestrator uses Claude Code CLI for max billing and built-in tools.

## Step 5.1: CLI Verification

Create `backend/claude_code_bridge.py`:
- Check Claude Code CLI is installed (`claude --version`)
- Verify authentication (`claude auth status`)
- Test connection with simple query
- Raise clear errors if not configured

---

## Step 5.2: Query Execution

Implement CLI query methods:
- `query(prompt)` — Basic prompt to response
- `stream_query(prompt)` — Streaming response chunks
- `query_with_retry(prompt)` — Auto-retry on transient failures
- `query_with_context(prompt, system, history)` — With context

CLI flags used:
- `--print` — Non-interactive output
- `--output-format` — text, json, or stream-json
- `--max-turns` — Limit conversation turns
- `--allowedTools` — Control tool access
- `-p` — The prompt

---

## Step 5.3: Orchestrator Integration

Update message handler to use CLI bridge:
- Route user messages through `bridge.query()`
- Use orchestrator system prompt for intent classification
- Determine if task needs delegation to SDK agents
- Return direct responses for simple queries

---

# Part 6: Anthropic SDK Setup (Agents)

Domain Leads and Workers use the Anthropic SDK for fine-grained control.

## Step 6.1: SDK Client Wrapper

Create `backend/sdk/client.py`:
- Initialize Anthropic client (uses same auth as CLI for max billing)
- Configure default model and settings
- Provide sync and async interfaces
- Handle rate limiting and retries

---

## Step 6.2: Base Agent Class

Create `backend/sdk/base_agent.py`:
- Abstract base class for all SDK agents
- Agent loop implementation (prompt → response → tool → repeat)
- Tool execution handling
- Conversation state management
- Streaming support

**BaseAgent interface:**
- `run(task, context)` — Execute task and return result
- `stream_run(task, context)` — Stream execution results
- `get_tools()` — Return available tools
- `get_system_prompt()` — Return agent's system prompt

---

## Step 6.3: Tool Definition Format

Create `backend/sdk/tools/base.py`:
- Tool definition schema matching Anthropic API format
- Base class for tool implementations
- Input validation with Pydantic
- Result formatting

**Tool interface:**
- `name` — Tool identifier
- `description` — What the tool does
- `input_schema` — JSON schema for parameters
- `execute(input)` — Run the tool

---

## Step 6.4: Common Tools

Create `backend/sdk/tools/`:
- `file_tools.py` — read_file, write_file, list_directory
- `search_tools.py` — grep, glob, web_search
- `shell_tools.py` — execute_command (with approval)
- `memory_tools.py` — remember, recall, forget

---

# Part 7: Event Bus Implementation

## Steps 7.1-7.4: Event Bus

(Same as original - event definitions, pub/sub implementation, UI event streaming, cross-agent communication)

Key events:
- `orchestrator.delegate` — Orchestrator delegates to Lead
- `lead.assign` — Lead assigns to Worker
- `worker.complete` — Worker returns result
- `tool.execute` — Tool execution request/result
- `approval.request` — High-risk action needs approval

---

# Part 8: Orchestrator Agent

The orchestrator uses CLI and decides when to delegate to SDK agents.

## Step 8.1: System Prompt Design

Create `backend/config/prompts/orchestrator.md`:
- Role: Primary AI interface
- Responsibilities: Intent understanding, routing, synthesis
- Delegation rules: When to handle vs delegate
- Available leads: Code, Research, Task
- Response format guidelines

---

## Step 8.2: Intent Classification

Categories:
- `casual_chat` — Handle directly (CLI)
- `question` — Handle directly or delegate to Research
- `code_task` — Delegate to Code Lead
- `research_task` — Delegate to Research Lead
- `automation_task` — Delegate to Task Lead

---

## Step 8.3: Delegation Protocol

When orchestrator delegates:
1. Classify intent using CLI
2. Select appropriate Lead (SDK agent)
3. Format context and task description
4. Call Lead's `run()` method
5. Receive result and synthesize response
6. Return to user via WebSocket

---

## Step 8.4: Memory Integration

Before responding, orchestrator:
- Retrieves user profile from mem0
- Gets relevant conversation history via semantic search
- Fetches applicable facts from knowledge graph
- Passes memory context to delegates

Create `backend/orchestrator/memory_integration.py`:
- `MemoryRetriever` class wrapping mem0 client
- `get_context_for_user(user_id, query)` — Retrieves relevant memories
- `get_user_profile(user_id)` — Returns user preferences
- Context formatting for inclusion in prompts

---

# Part 9: Memory System (mem0)

The memory system uses **mem0** for intelligent, auto-managed memory with knowledge graph support.

## Step 9.1: mem0 Configuration

Create `backend/memory/config.py`:

```python
from mem0 import Memory

# mem0 Configuration
MEM0_CONFIG = {
    "version": "v1.1",  # Enables knowledge graph
    "embedder": {
        "provider": "openai",  # or "huggingface" for local
        "config": {
            "model": "text-embedding-3-small"
        }
    },
    "vector_store": {
        "provider": "chroma",  # Local vector DB
        "config": {
            "collection_name": "emperor_memories",
            "path": "./data/chroma"
        }
    },
    "graph_store": {
        "provider": "neo4j",  # Optional: for knowledge graph
        "config": {
            "url": "bolt://localhost:7687",
            "username": "neo4j",
            "password": "password"
        }
    },
    "llm": {
        "provider": "anthropic",
        "config": {
            "model": "claude-sonnet-4-20250514",
            "api_key": "${ANTHROPIC_API_KEY}"
        }
    }
}

# Alternative: Simple local config (no Neo4j)
MEM0_LOCAL_CONFIG = {
    "version": "v1.1",
    "embedder": {
        "provider": "huggingface",
        "config": {
            "model": "sentence-transformers/all-MiniLM-L6-v2"
        }
    },
    "vector_store": {
        "provider": "chroma",
        "config": {
            "collection_name": "emperor_memories",
            "path": "./data/chroma"
        }
    }
}
```

---

## Step 9.2: Memory Service

Create `backend/memory/memory_service.py`:

```python
from mem0 import Memory
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class MemoryResult:
    """Structured memory retrieval result."""
    id: str
    content: str
    metadata: Dict[str, Any]
    relevance_score: float
    created_at: datetime

class MemoryService:
    """Central memory service using mem0."""

    def __init__(self, config: Dict[str, Any]):
        self.memory = Memory.from_config(config)
        self._user_id = "default"

    def set_user(self, user_id: str):
        """Set the current user context."""
        self._user_id = user_id

    def add(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a memory. mem0 automatically:
        - Extracts facts and entities
        - Builds knowledge graph relationships
        - Handles deduplication
        - Updates existing memories
        """
        uid = user_id or self._user_id
        return self.memory.add(
            content,
            user_id=uid,
            metadata=metadata or {}
        )

    def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 10
    ) -> List[MemoryResult]:
        """
        Search memories with semantic similarity.
        Returns ranked results with relevance scores.
        """
        uid = user_id or self._user_id
        results = self.memory.search(
            query,
            user_id=uid,
            limit=limit
        )
        return [
            MemoryResult(
                id=r["id"],
                content=r["memory"],
                metadata=r.get("metadata", {}),
                relevance_score=r.get("score", 0.0),
                created_at=datetime.fromisoformat(
                    r.get("created_at", datetime.now().isoformat())
                )
            )
            for r in results
        ]

    def get_all(self, user_id: Optional[str] = None) -> List[Dict]:
        """Get all memories for a user."""
        uid = user_id or self._user_id
        return self.memory.get_all(user_id=uid)

    def update(self, memory_id: str, content: str) -> Dict[str, Any]:
        """Update an existing memory."""
        return self.memory.update(memory_id, content)

    def delete(self, memory_id: str) -> bool:
        """Delete a specific memory."""
        self.memory.delete(memory_id)
        return True

    def delete_all(self, user_id: Optional[str] = None) -> bool:
        """Delete all memories for a user."""
        uid = user_id or self._user_id
        self.memory.delete_all(user_id=uid)
        return True

    def get_history(self, memory_id: str) -> List[Dict]:
        """Get version history of a memory."""
        return self.memory.history(memory_id)
```

---

## Step 9.3: Conversation Memory Handler

Create `backend/memory/conversation_handler.py`:

```python
from typing import List, Dict, Optional
from .memory_service import MemoryService

class ConversationMemoryHandler:
    """Handles automatic memory extraction from conversations."""

    def __init__(self, memory_service: MemoryService):
        self.memory = memory_service

    def process_conversation(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a conversation and extract memories.
        mem0 automatically identifies:
        - User preferences ("I prefer dark mode")
        - Facts ("My project uses Python 3.11")
        - Relationships ("My team lead is Sarah")
        - Instructions ("Always format code with black")
        """
        # Format conversation for mem0
        formatted = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in messages
        ])

        # Add to memory with session context
        result = self.memory.add(
            formatted,
            user_id=user_id,
            metadata={
                "type": "conversation",
                "session_id": session_id,
                "message_count": len(messages)
            }
        )

        return result

    def get_relevant_context(
        self,
        query: str,
        user_id: str,
        limit: int = 5
    ) -> str:
        """
        Get relevant memories formatted as context.
        Used by orchestrator before processing queries.
        """
        memories = self.memory.search(query, user_id=user_id, limit=limit)

        if not memories:
            return ""

        context_parts = ["Relevant memories:"]
        for mem in memories:
            context_parts.append(f"- {mem.content}")

        return "\n".join(context_parts)
```

---

## Step 9.4: User Profile Manager

Create `backend/memory/user_profile.py`:

```python
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from .memory_service import MemoryService

@dataclass
class UserProfile:
    """User profile extracted from memories."""
    user_id: str
    preferences: Dict[str, Any] = field(default_factory=dict)
    facts: List[str] = field(default_factory=list)
    work_context: Dict[str, Any] = field(default_factory=dict)

class UserProfileManager:
    """Manages user profiles derived from memories."""

    PROFILE_QUERIES = [
        "user preferences and settings",
        "user's work and projects",
        "user's coding style and tools",
        "user's personal information"
    ]

    def __init__(self, memory_service: MemoryService):
        self.memory = memory_service

    def build_profile(self, user_id: str) -> UserProfile:
        """
        Build a user profile from stored memories.
        Aggregates information from multiple memory searches.
        """
        profile = UserProfile(user_id=user_id)

        for query in self.PROFILE_QUERIES:
            memories = self.memory.search(query, user_id=user_id, limit=3)
            for mem in memories:
                self._categorize_memory(mem.content, profile)

        return profile

    def _categorize_memory(self, content: str, profile: UserProfile):
        """Categorize memory content into profile sections."""
        content_lower = content.lower()

        # Detect preferences
        if any(kw in content_lower for kw in ["prefer", "like", "want", "always"]):
            profile.preferences[content[:50]] = content

        # Detect work context
        if any(kw in content_lower for kw in ["project", "work", "team", "company"]):
            profile.work_context[content[:50]] = content

        # Add as general fact
        profile.facts.append(content)

    def get_profile_context(self, user_id: str) -> str:
        """Get formatted profile for prompt context."""
        profile = self.build_profile(user_id)

        parts = [f"User Profile for {user_id}:"]

        if profile.preferences:
            parts.append("\nPreferences:")
            for pref in list(profile.preferences.values())[:5]:
                parts.append(f"  - {pref}")

        if profile.work_context:
            parts.append("\nWork Context:")
            for ctx in list(profile.work_context.values())[:5]:
                parts.append(f"  - {ctx}")

        return "\n".join(parts)
```

---

## Step 9.5: Memory Module Interface

Create `backend/memory/__init__.py`:

```python
"""Memory module using mem0 for intelligent memory management."""

from .config import MEM0_CONFIG, MEM0_LOCAL_CONFIG
from .memory_service import MemoryService, MemoryResult
from .conversation_handler import ConversationMemoryHandler
from .user_profile import UserProfile, UserProfileManager

# Singleton instances
_memory_service: Optional[MemoryService] = None
_conversation_handler: Optional[ConversationMemoryHandler] = None
_profile_manager: Optional[UserProfileManager] = None

def get_memory_service(use_local: bool = True) -> MemoryService:
    """Get the memory service singleton."""
    global _memory_service
    if _memory_service is None:
        config = MEM0_LOCAL_CONFIG if use_local else MEM0_CONFIG
        _memory_service = MemoryService(config)
    return _memory_service

def get_conversation_handler() -> ConversationMemoryHandler:
    """Get the conversation handler singleton."""
    global _conversation_handler
    if _conversation_handler is None:
        _conversation_handler = ConversationMemoryHandler(get_memory_service())
    return _conversation_handler

def get_profile_manager() -> UserProfileManager:
    """Get the profile manager singleton."""
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = UserProfileManager(get_memory_service())
    return _profile_manager

__all__ = [
    "MEM0_CONFIG",
    "MEM0_LOCAL_CONFIG",
    "MemoryService",
    "MemoryResult",
    "ConversationMemoryHandler",
    "UserProfile",
    "UserProfileManager",
    "get_memory_service",
    "get_conversation_handler",
    "get_profile_manager",
]
```

---

## Step 9.6: Integration with Orchestrator

Update `backend/orchestrator/orchestrator.py` to use mem0:

```python
from memory import get_memory_service, get_conversation_handler, get_profile_manager

class Orchestrator:
    def __init__(self):
        # ... existing init ...
        self.memory = get_memory_service()
        self.conversation_handler = get_conversation_handler()
        self.profile_manager = get_profile_manager()

    async def process(self, message: str, user_id: str) -> str:
        # Get memory context
        memory_context = self.conversation_handler.get_relevant_context(
            query=message,
            user_id=user_id,
            limit=5
        )

        # Get user profile
        profile_context = self.profile_manager.get_profile_context(user_id)

        # Build enhanced prompt
        enhanced_prompt = self._build_prompt_with_memory(
            message=message,
            memory_context=memory_context,
            profile_context=profile_context
        )

        # Process with CLI
        response = await self.bridge.query(enhanced_prompt)

        # Store conversation in memory
        self.conversation_handler.process_conversation(
            messages=[
                {"role": "user", "content": message},
                {"role": "assistant", "content": response}
            ],
            user_id=user_id
        )

        return response
```

---

## mem0 Key Features Used

| Feature | Purpose |
|---------|---------|
| Auto-extraction | Automatically identifies facts, preferences, entities |
| Knowledge Graph | Builds relationships between entities (v1.1) |
| Semantic Search | Retrieves relevant memories by meaning |
| Memory Updates | Intelligently updates existing memories |
| History Tracking | Maintains version history of memories |
| Metadata Support | Attach custom data to memories |

---

# Part 10: Domain Leads (SDK)

Each Lead is an SDK-based agent with specialized tools.

## Step 10.1: Code Lead

Create `backend/leads/code_lead.py`:
- Extends BaseAgent
- System prompt for code architecture decisions
- Tools: file operations, AST parsing, refactoring, **memory tools**
- Spawns workers: Programmer, Reviewer, Documentor
- Aggregates worker results
- **Memory access**: Can store/recall code patterns and project context

---

## Step 10.2: Research Lead

Create `backend/leads/research_lead.py`:
- Extends BaseAgent
- System prompt for research and analysis
- Tools: web search, document analysis, citation, **memory tools**
- Spawns workers: Researcher, Analyst, Writer
- Maintains source tracking
- **Memory access**: Stores research findings for future reference

---

## Step 10.3: Task Lead

Create `backend/leads/task_lead.py`:
- Extends BaseAgent
- System prompt for automation and workflows
- Tools: shell execution, scheduling, monitoring, **memory tools**
- Spawns workers: Executor, Monitor
- Permission enforcement for system operations
- **Memory access**: Remembers workflow patterns and user automation preferences

---

## Step 10.4: Worker Agents

Create `backend/workers/`:
- `programmer.py` — Writes code
- `reviewer.py` — Reviews code for issues
- `documentor.py` — Writes documentation
- `researcher.py` — Gathers information
- `executor.py` — Runs automated tasks

Each worker:
- Extends BaseAgent
- Has focused system prompt
- Limited tool set for their specialty
- Returns structured results
- **Read-only memory access** via memory tools

---

## Step 10.5: Lead-Worker Communication

Leads spawn and manage workers:
- Create worker instance with context
- Call `worker.run(subtask)`
- Collect results
- Handle failures gracefully
- Aggregate into Lead's response

---

## Step 10.6: Memory Tools for Agents

Create `backend/sdk/tools/memory_tools.py`:

```python
from typing import Dict, Any, Optional, List
from ..tools.base import BaseTool
from memory import get_memory_service

class RememberTool(BaseTool):
    """Store information in memory."""

    name = "remember"
    description = "Store important information for future reference"
    input_schema = {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "The information to remember"
            },
            "category": {
                "type": "string",
                "enum": ["preference", "fact", "workflow", "code_pattern"],
                "description": "Category of memory"
            }
        },
        "required": ["content"]
    }

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        memory = get_memory_service()
        result = memory.add(
            content=input["content"],
            metadata={"category": input.get("category", "general")}
        )
        return {"status": "stored", "id": result.get("id")}


class RecallTool(BaseTool):
    """Retrieve relevant memories."""

    name = "recall"
    description = "Search and retrieve relevant memories"
    input_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "What to search for in memory"
            },
            "limit": {
                "type": "integer",
                "description": "Max results to return",
                "default": 5
            }
        },
        "required": ["query"]
    }

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        memory = get_memory_service()
        results = memory.search(
            query=input["query"],
            limit=input.get("limit", 5)
        )
        return {
            "memories": [
                {"content": r.content, "score": r.relevance_score}
                for r in results
            ]
        }


class ForgetTool(BaseTool):
    """Remove a specific memory."""

    name = "forget"
    description = "Delete a specific memory by ID"
    input_schema = {
        "type": "object",
        "properties": {
            "memory_id": {
                "type": "string",
                "description": "ID of the memory to delete"
            }
        },
        "required": ["memory_id"]
    }

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        memory = get_memory_service()
        success = memory.delete(input["memory_id"])
        return {"status": "deleted" if success else "failed"}
```

---

# Part 11: Tool System

## Step 11.1: Tool Registry

Create `backend/tools/registry.py`:
- Central registry for all available tools
- Tool lookup by name
- Permission checking per tool
- Category organization (file, shell, memory, search)

---

## Step 11.2: Permission Checking

Create `backend/tools/permissions.py`:
- Permission levels: read, write, execute, memory
- User-based permission grants
- Approval flow for dangerous operations
- Audit logging for tool usage

---

## Step 11.3: File System Tools

Create `backend/tools/file_tools.py`:
- `read_file` — Read file contents
- `write_file` — Write/create files
- `list_directory` — List directory contents
- `search_files` — Glob pattern search

---

## Step 11.4: Shell Tools

Create `backend/tools/shell_tools.py`:
- `execute_command` — Run shell commands
- Requires explicit user approval for dangerous commands
- Sandboxed execution environment
- Output capture and streaming

---

## Step 11.5: Memory Tools (mem0)

Create `backend/tools/memory_tools.py`:

```python
"""Memory tools using mem0 for agent use."""

from typing import Dict, Any, List
from memory import get_memory_service, get_conversation_handler

class MemoryTools:
    """Memory tool implementations for both CLI and SDK agents."""

    @staticmethod
    def remember(
        content: str,
        user_id: str,
        category: str = "general",
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Store information in memory.
        mem0 automatically extracts facts and builds relationships.
        """
        memory = get_memory_service()
        result = memory.add(
            content=content,
            user_id=user_id,
            metadata={
                "category": category,
                **(metadata or {})
            }
        )
        return {
            "status": "stored",
            "extracted": result.get("extracted_memories", [])
        }

    @staticmethod
    def recall(
        query: str,
        user_id: str,
        limit: int = 5,
        category: str = None
    ) -> List[Dict[str, Any]]:
        """
        Search and retrieve relevant memories.
        Uses semantic search with optional category filter.
        """
        memory = get_memory_service()
        results = memory.search(
            query=query,
            user_id=user_id,
            limit=limit
        )

        # Filter by category if specified
        if category:
            results = [
                r for r in results
                if r.metadata.get("category") == category
            ]

        return [
            {
                "id": r.id,
                "content": r.content,
                "score": r.relevance_score,
                "category": r.metadata.get("category", "general")
            }
            for r in results
        ]

    @staticmethod
    def forget(memory_id: str) -> Dict[str, str]:
        """Delete a specific memory by ID."""
        memory = get_memory_service()
        success = memory.delete(memory_id)
        return {"status": "deleted" if success else "failed"}

    @staticmethod
    def get_context(
        query: str,
        user_id: str,
        limit: int = 5
    ) -> str:
        """
        Get formatted memory context for prompts.
        Used by orchestrator for context injection.
        """
        handler = get_conversation_handler()
        return handler.get_relevant_context(
            query=query,
            user_id=user_id,
            limit=limit
        )

    @staticmethod
    def list_memories(
        user_id: str,
        category: str = None
    ) -> List[Dict[str, Any]]:
        """List all memories for a user."""
        memory = get_memory_service()
        all_memories = memory.get_all(user_id=user_id)

        if category:
            all_memories = [
                m for m in all_memories
                if m.get("metadata", {}).get("category") == category
            ]

        return all_memories

    @staticmethod
    def get_memory_history(memory_id: str) -> List[Dict[str, Any]]:
        """Get version history for a memory."""
        memory = get_memory_service()
        return memory.get_history(memory_id)
```

---

## Step 11.6: Tool Execution

Create `backend/tools/executor.py`:
- Unified tool execution interface
- Input validation with JSON schema
- Error handling and reporting
- Result formatting

Tools are used by both:
- CLI orchestrator (via CLI's built-in tools + custom memory tools)
- SDK agents (via custom tool implementations)

---

# Part 12: Voice Integration

## Steps 12.1-12.5: Voice Features

(Same as original - Whisper setup, recording handler, frontend voice UI, text-to-speech, voice command handling)

---

# Part 13: Advanced UI Components

## Step 13.1: Task Timeline

Create `src/components/TaskTimeline.tsx`:
- Visual timeline of agent activities
- Real-time updates via WebSocket
- Expandable task details
- Status indicators (pending, running, completed, failed)

---

## Step 13.2: Memory Manager (mem0)

Create `src/components/MemoryManager.tsx`:

```tsx
import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ScrollArea } from '@radix-ui/react-scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@radix-ui/react-tabs';
import { Trash2, Search, Clock, Brain } from 'lucide-react';

interface Memory {
  id: string;
  content: string;
  category: string;
  score?: number;
  created_at: string;
  metadata: Record<string, any>;
}

interface MemoryManagerProps {
  userId: string;
}

export function MemoryManager({ userId }: MemoryManagerProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // Fetch all memories
  const { data: memories, isLoading } = useQuery({
    queryKey: ['memories', userId, selectedCategory],
    queryFn: async () => {
      const params = new URLSearchParams({ user_id: userId });
      if (selectedCategory) params.append('category', selectedCategory);
      const res = await fetch(`/api/memory/list?${params}`);
      return res.json();
    }
  });

  // Search memories
  const { data: searchResults, refetch: doSearch } = useQuery({
    queryKey: ['memory-search', userId, searchQuery],
    queryFn: async () => {
      if (!searchQuery) return null;
      const res = await fetch('/api/memory/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery, user_id: userId, limit: 10 })
      });
      return res.json();
    },
    enabled: false
  });

  // Delete memory mutation
  const deleteMutation = useMutation({
    mutationFn: async (memoryId: string) => {
      await fetch(`/api/memory/${memoryId}`, { method: 'DELETE' });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memories'] });
    }
  });

  const categories = ['preference', 'fact', 'workflow', 'code_pattern', 'general'];

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Search Bar */}
      <div className="p-4 border-b">
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Search memories..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 px-3 py-2 border rounded-lg"
          />
          <button
            onClick={() => doSearch()}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg"
          >
            <Search className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Category Tabs */}
      <Tabs defaultValue="all" className="flex-1">
        <TabsList className="px-4 border-b">
          <TabsTrigger value="all" onClick={() => setSelectedCategory(null)}>
            All
          </TabsTrigger>
          {categories.map((cat) => (
            <TabsTrigger
              key={cat}
              value={cat}
              onClick={() => setSelectedCategory(cat)}
            >
              {cat}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="all" className="flex-1">
          <ScrollArea className="h-full">
            {/* Search Results */}
            {searchResults && (
              <div className="p-4 bg-muted/50">
                <h3 className="text-sm font-medium mb-2">Search Results</h3>
                {searchResults.map((memory: Memory) => (
                  <MemoryCard
                    key={memory.id}
                    memory={memory}
                    onDelete={() => deleteMutation.mutate(memory.id)}
                    showScore
                  />
                ))}
              </div>
            )}

            {/* All Memories */}
            <div className="p-4 space-y-2">
              {isLoading ? (
                <div className="text-center py-8 text-muted-foreground">
                  Loading memories...
                </div>
              ) : memories?.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Brain className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>No memories stored yet</p>
                </div>
              ) : (
                memories?.map((memory: Memory) => (
                  <MemoryCard
                    key={memory.id}
                    memory={memory}
                    onDelete={() => deleteMutation.mutate(memory.id)}
                  />
                ))
              )}
            </div>
          </ScrollArea>
        </TabsContent>
      </Tabs>
    </div>
  );
}

interface MemoryCardProps {
  memory: Memory;
  onDelete: () => void;
  showScore?: boolean;
}

function MemoryCard({ memory, onDelete, showScore }: MemoryCardProps) {
  return (
    <div className="p-3 bg-card rounded-lg border group">
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <p className="text-sm">{memory.content}</p>
          <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
            <span className="px-2 py-0.5 bg-muted rounded">
              {memory.category}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {new Date(memory.created_at).toLocaleDateString()}
            </span>
            {showScore && memory.score && (
              <span className="text-primary">
                {(memory.score * 100).toFixed(0)}% match
              </span>
            )}
          </div>
        </div>
        <button
          onClick={onDelete}
          className="opacity-0 group-hover:opacity-100 p-1 text-destructive hover:bg-destructive/10 rounded"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
```

---

## Step 13.3: Memory API Routes

Create `backend/api/memory_routes.py`:

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from memory import get_memory_service

router = APIRouter(prefix="/api/memory", tags=["memory"])

class SearchRequest(BaseModel):
    query: str
    user_id: str
    limit: int = 10

class AddMemoryRequest(BaseModel):
    content: str
    user_id: str
    category: str = "general"

@router.get("/list")
async def list_memories(user_id: str, category: Optional[str] = None):
    """List all memories for a user."""
    memory = get_memory_service()
    results = memory.get_all(user_id=user_id)
    if category:
        results = [r for r in results if r.get("metadata", {}).get("category") == category]
    return results

@router.post("/search")
async def search_memories(request: SearchRequest):
    """Search memories with semantic similarity."""
    memory = get_memory_service()
    results = memory.search(
        query=request.query,
        user_id=request.user_id,
        limit=request.limit
    )
    return [
        {
            "id": r.id,
            "content": r.content,
            "category": r.metadata.get("category", "general"),
            "score": r.relevance_score,
            "created_at": r.created_at.isoformat()
        }
        for r in results
    ]

@router.post("/add")
async def add_memory(request: AddMemoryRequest):
    """Add a new memory."""
    memory = get_memory_service()
    result = memory.add(
        content=request.content,
        user_id=request.user_id,
        metadata={"category": request.category}
    )
    return {"status": "stored", "id": result.get("id")}

@router.delete("/{memory_id}")
async def delete_memory(memory_id: str):
    """Delete a memory by ID."""
    memory = get_memory_service()
    success = memory.delete(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"status": "deleted"}

@router.get("/{memory_id}/history")
async def get_memory_history(memory_id: str):
    """Get version history for a memory."""
    memory = get_memory_service()
    return memory.get_history(memory_id)
```

---

## Step 13.4: Approval Modal

Create `src/components/ApprovalModal.tsx`:
- Modal for dangerous operation approval
- Shows command/action details
- Approve/Deny buttons
- Timeout handling

---

## Step 13.5: Settings Panel

Create `src/components/SettingsPanel.tsx`:
- User preferences management
- Memory configuration (enable/disable auto-extraction)
- API key management
- Theme settings

---

# Part 14: Security & Permissions

## Steps 14.1-14.4: Security Implementation

(Same as original - permission system, audit logging, input sanitization, data encryption)

---

# Part 15: Testing & Deployment

## Steps 15.1-15.5: Testing & Release

(Same as original - unit tests, integration tests, E2E tests, macOS distribution, release process)

---

# Quick Reference

## Development Commands

| Command | Description |
|---------|-------------|
| `./scripts/dev.sh` | Start full stack (backend + frontend) |
| `pnpm tauri dev` | Frontend only |
| `python -m api.main` | Backend only (from backend/) |
| `pnpm tauri build` | Production build |

## Key Configuration Files

| File | Purpose |
|------|---------|
| `backend/.env` | Backend environment variables |
| `src-tauri/tauri.conf.json` | Tauri window and build settings |
| `tailwind.config.js` | UI theme configuration |
| `vite.config.ts` | Frontend build configuration |

## Hybrid Architecture Summary

| Component | Technology | Purpose |
|-----------|------------|---------|
| Orchestrator | Claude Code CLI | Routing, built-in tools, max billing |
| Code Lead | Anthropic SDK | Code architecture, worker management |
| Research Lead | Anthropic SDK | Research, analysis, citations |
| Task Lead | Anthropic SDK | Automation, shell execution |
| Workers | Anthropic SDK | Specialized subtasks |

## Project Structure

```
project/
├── src/                    # React frontend
│   ├── components/ui/      # Base UI components
│   ├── components/         # Feature components
│   ├── hooks/              # Custom hooks
│   ├── stores/             # State management
│   ├── lib/                # Utilities
│   └── types/              # TypeScript types
├── src-tauri/              # Tauri Rust backend
├── backend/                # Python backend
│   ├── api/                # FastAPI application
│   ├── config/             # Settings and logging
│   ├── sdk/                # Anthropic SDK wrapper
│   │   ├── client.py       # SDK client
│   │   ├── base_agent.py   # Base agent class
│   │   └── tools/          # SDK tool definitions
│   ├── orchestrator/       # CLI-based orchestrator
│   ├── leads/              # SDK-based domain leads
│   ├── workers/            # SDK-based workers
│   ├── memory/             # Memory system
│   ├── tools/              # Tool registry
│   ├── process_manager/    # Event bus
│   └── voice/              # Voice features
├── data/                   # Local data storage
└── scripts/                # Development scripts
```

---

*Document Version: 3.0*
*Architecture: Hybrid (CLI Orchestrator + SDK Agents)*
*Created: 2025-12-25*
*Type: High-level implementation guide*
