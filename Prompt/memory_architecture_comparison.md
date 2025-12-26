# Memory Architecture Comparison for Emperor AI

A comprehensive analysis of memory layer implementations for AI assistants, with emphasis on advanced cognitive architectures.

---

## Table of Contents

1. [Memory Types Overview](#memory-types-overview)
2. [Implementation Options Comparison](#implementation-options-comparison)
3. [Letta (MemGPT) Deep Dive](#letta-memgpt-deep-dive)
4. [Custom Cognitive Architecture Deep Dive](#custom-cognitive-architecture-deep-dive)
5. [Recommendation for Emperor](#recommendation-for-emperor)

---

## Memory Types Overview

### The Three Core Memory Types

| Type | Human Analogy | What It Stores | Example |
|------|---------------|----------------|---------|
| **Semantic** | "Facts I know" | Context-free knowledge | "Winston prefers TypeScript" |
| **Episodic** | "Things that happened" | Time-stamped experiences | "On Dec 25, we fixed the WebSocket bug" |
| **Procedural** | "How to do things" | Skills and workflows | "When user says 'deploy', run tests first" |

### Memory Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MEMORY HIERARCHY                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  WORKING MEMORY (Immediate)                                                  │
│  ├── Current conversation context                                            │
│  ├── Active goals and tasks                                                  │
│  └── Attention focus                                                         │
│       │                                                                      │
│       ▼                                                                      │
│  SHORT-TERM MEMORY (Session)                                                 │
│  ├── Recent conversation history                                             │
│  ├── Temporary task state                                                    │
│  └── Session-specific context                                                │
│       │                                                                      │
│       ▼                                                                      │
│  LONG-TERM MEMORY (Persistent)                                               │
│  ├── Semantic: Facts, knowledge, user profile                                │
│  ├── Episodic: Past conversations, events                                    │
│  └── Procedural: Learned workflows, patterns                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Options Comparison

### Feature Matrix

| Feature | JSON Files | SQLite | SQLite + Chroma | mem0 | Zep | LangChain | Letta | Custom Cognitive |
|---------|------------|--------|-----------------|------|-----|-----------|-------|------------------|
| **Semantic Memory** | ⚠️ Basic | ✅ FTS5 | ✅ Full | ✅ Full | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| **Episodic Memory** | ⚠️ Manual | ⚠️ Manual | ⚠️ Manual | ✅ Auto | ✅ Auto | ⚠️ Basic | ✅ Full | ✅ Full |
| **Procedural Memory** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ Partial | ✅ Full |
| **Knowledge Graph** | ❌ | ❌ | ❌ | ✅ v1.1 | ❌ | ❌ | ❌ | ✅ Full |
| **Vector Search** | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Auto Fact Extraction** | ❌ | ❌ | ❌ | ✅ LLM | ✅ LLM | ❌ | ✅ Agent | ✅ LLM |
| **Self-Editing Memory** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ Core | ✅ Optional |
| **Memory Consolidation** | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ | ✅ |
| **Temporal Awareness** | ❌ | ⚠️ Manual | ⚠️ Manual | ✅ | ✅ | ⚠️ Basic | ✅ | ✅ |
| **Confidence Scores** | ❌ | ⚠️ Manual | ⚠️ Manual | ✅ | ✅ | ❌ | ✅ | ✅ |
| **Contradiction Detection** | ❌ | ❌ | ❌ | ⚠️ Basic | ⚠️ Basic | ❌ | ✅ | ✅ |
| **Multi-User Support** | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

### Implementation Comparison

| Aspect | JSON | SQLite | SQLite+Chroma | mem0 | Zep | LangChain | Letta | Custom |
|--------|------|--------|---------------|------|-----|-----------|-------|--------|
| **Setup Time** | Done | 3 hrs | 1-2 days | 2-4 hrs | 3 hrs | 4-6 hrs | 1 day | 2-3 weeks |
| **Lines of Code** | ~200 | ~500 | ~1500 | ~100 | ~150 | ~300 | ~200 | 3000+ |
| **Dependencies** | 0 | 0 | 3 | 1 | 1 | 10+ | 1 | 5-8 |
| **LLM Calls Required** | No | No | No | Yes | Yes | Optional | Yes | Yes |
| **Runs Locally** | ✅ | ✅ | ✅ | ✅ | ⚠️ Cloud option | ✅ | ✅ | ✅ |
| **Maintenance Effort** | Low | Low | Medium | Low | Low | Medium | Medium | High |
| **Customization** | Full | Full | Full | Medium | Low | Medium | Medium | Full |

### Power vs Complexity Chart

```
CAPABILITY POWER
     │
 10  │                                                    ┌──────────────┐
     │                                                    │   CUSTOM     │
  9  │                                           ┌───────┐│  COGNITIVE   │
     │                                           │ LETTA ││              │
  8  │                                           │       │└──────────────┘
     │                                  ┌───────┐│       │
  7  │                                  │  ZEP  ││       │
     │                         ┌───────┐│       │└───────┘
  6  │                         │ MEM0  ││       │
     │                         │+Graph │└───────┘
  5  │                ┌───────┐│       │
     │                │SQLite+││       │
  4  │                │Chroma │└───────┘
     │       ┌───────┐│       │
  3  │       │SQLite │└───────┘
     │       │  +FTS │
  2  │┌─────┐│       │
     ││JSON │└───────┘
  1  │└─────┘
     │
  0  └────────────────────────────────────────────────────────────────────
           Low                    COMPLEXITY                          High
```

---

## Letta (MemGPT) Deep Dive

### Overview

Letta (formerly MemGPT) is a framework that gives AI agents **self-managing memory**. Instead of you deciding what to remember, the agent itself decides what's worth storing, updating, or forgetting.

Based on the research paper: *"MemGPT: Towards LLMs as Operating Systems"*

### Core Concept: Memory as an Operating System

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LETTA MEMORY ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                        CORE MEMORY                                       ││
│  │                   (Always in Context Window)                             ││
│  │  ┌─────────────────────────────────────────────────────────────────────┐││
│  │  │ PERSONA BLOCK                    │ HUMAN BLOCK                      │││
│  │  │ "I am Emperor, an AI assistant   │ "User: Winston                   │││
│  │  │  that helps with coding..."      │  Skill: Senior Developer         │││
│  │  │                                  │  Preferences: TypeScript,        │││
│  │  │ [Agent can edit this]            │  concise responses"              │││
│  │  │                                  │  [Agent can edit this]           │││
│  │  └─────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                     │                                        │
│                                     ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                      ARCHIVAL MEMORY                                     ││
│  │                  (Searchable Long-term Storage)                          ││
│  │                                                                          ││
│  │  • Unlimited size (vector database)                                      ││
│  │  • Agent searches when needed                                            ││
│  │  • Agent decides what to archive                                         ││
│  │  • Persists across sessions                                              ││
│  │                                                                          ││
│  │  Examples:                                                               ││
│  │  - "Dec 25: Fixed WebSocket connection issue with Winston"               ││
│  │  - "Emperor project uses Tauri + React + Python backend"                 ││
│  │  - "User prefers exploring options before implementing"                  ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                     │                                        │
│                                     ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                      RECALL MEMORY                                       ││
│  │                  (Conversation History Search)                           ││
│  │                                                                          ││
│  │  • Past conversation chunks                                              ││
│  │  • Searchable by content                                                 ││
│  │  • Auto-paginated (agent requests more if needed)                        ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Memory Tools (Agent-Controlled)

The key innovation: the agent has **tools to manage its own memory**:

```python
# Tools available to the Letta agent
MEMORY_TOOLS = [
    {
        "name": "core_memory_append",
        "description": "Append content to a core memory block (always visible)",
        "parameters": {
            "label": "Which block: 'persona' or 'human'",
            "content": "Text to append"
        }
    },
    {
        "name": "core_memory_replace",
        "description": "Replace content in a core memory block",
        "parameters": {
            "label": "Which block to modify",
            "old_content": "Text to find",
            "new_content": "Text to replace with"
        }
    },
    {
        "name": "archival_memory_insert",
        "description": "Save information to long-term archival storage",
        "parameters": {
            "content": "Information to archive"
        }
    },
    {
        "name": "archival_memory_search",
        "description": "Search archival memory for relevant information",
        "parameters": {
            "query": "Search query",
            "page": "Page number for pagination"
        }
    },
    {
        "name": "conversation_search",
        "description": "Search past conversation history",
        "parameters": {
            "query": "Search query",
            "page": "Page number"
        }
    }
]
```

### Implementation Example

```python
from letta import Letta, LLMConfig, EmbeddingConfig

# Initialize Letta client
client = Letta()

# Create an agent with self-managing memory
agent = client.create_agent(
    name="emperor",

    # LLM configuration
    llm_config=LLMConfig(
        model="claude-sonnet-4-20250514",
        model_endpoint_type="anthropic",
    ),

    # Embedding model for memory search
    embedding_config=EmbeddingConfig(
        embedding_model="text-embedding-3-small",
        embedding_endpoint_type="openai",
    ),

    # Initial core memory blocks
    memory_blocks=[
        {
            "label": "persona",
            "value": """I am Emperor, a powerful AI assistant.
I help users with software development, research, and automation.
I have a sophisticated memory system that I actively manage.
I remember important details about users and our conversations."""
        },
        {
            "label": "human",
            "value": """User information will be stored here as I learn about them.
Currently empty - I will fill this in as we interact."""
        },
        {
            "label": "project",
            "value": """Current project context will be stored here."""
        }
    ],

    # System prompt
    system="""You are Emperor, an AI assistant with persistent memory.
You have tools to manage your own memory:
- Use core_memory_append/replace for important, frequently-needed info
- Use archival_memory_insert for detailed information you might need later
- Use archival_memory_search to recall past information

Be proactive about remembering important details about the user.""",

    # Include memory management tools
    include_base_tools=True,
)

# Send a message - agent will automatically manage memory
response = client.send_message(
    agent_id=agent.id,
    message="Hi! I'm Winston, I'm a senior developer working on a project called Emperor. I prefer TypeScript but I'm using Python for the backend."
)

# The agent might internally do:
# 1. core_memory_replace(label="human", old_content="Currently empty...",
#                        new_content="Name: Winston\nRole: Senior Developer\nPreferences: TypeScript\nCurrent Project: Emperor")
# 2. archival_memory_insert(content="User Winston is building Emperor project with Python backend despite preferring TypeScript")
```

### How Letta Handles Long Conversations

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LETTA CONTEXT MANAGEMENT                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  CONTEXT WINDOW (Limited Size)                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────────────────┐ ││
│  │ │ SYSTEM      │ │ CORE        │ │ RECENT CONVERSATION                 │ ││
│  │ │ PROMPT      │ │ MEMORY      │ │ (Last N messages)                   │ ││
│  │ │             │ │             │ │                                     │ ││
│  │ │ ~500 tokens │ │ ~1000 tokens│ │ ~2000 tokens                        │ ││
│  │ └─────────────┘ └─────────────┘ └─────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  When context fills up:                                                      │
│  1. Agent summarizes old messages                                            │
│  2. Summary goes to archival memory                                          │
│  3. Old messages are evicted                                                 │
│  4. Agent can search archival to recall                                      │
│                                                                              │
│  ARCHIVAL MEMORY (Unlimited)                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ [Conversation summary: Dec 25 - Fixed WebSocket issues...]              ││
│  │ [Conversation summary: Dec 26 - Discussed memory architectures...]      ││
│  │ [Fact: User prefers TypeScript over JavaScript]                         ││
│  │ [Fact: Emperor uses hybrid CLI + SDK architecture]                      ││
│  │ [Fact: ...]                                                             ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Letta Pros and Cons

**Pros:**
- Agent decides what's important (more intelligent memory)
- Handles unlimited context through pagination
- Research-backed architecture
- Self-healing (agent can fix its own memory mistakes)
- Good abstraction for complex memory needs

**Cons:**
- More LLM calls (agent thinks about memory)
- Less predictable (you don't control what's remembered)
- Can conflict with external orchestration (Emperor's orchestrator)
- Newer framework, less battle-tested
- Memory operations add latency

---

## Custom Cognitive Architecture Deep Dive

### Overview

A custom cognitive memory system gives you **maximum control and capability** by implementing all memory types with sophisticated retrieval, consolidation, and meta-cognition.

### Full Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                      CUSTOM COGNITIVE MEMORY SYSTEM                               │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                         LAYER 1: WORKING MEMORY                              │ │
│  │                         (Redis / In-Memory)                                  │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐│ │
│  │  │ • Current conversation buffer (last N turns)                            ││ │
│  │  │ • Active task state and goals                                           ││ │
│  │  │ • Attention weights for retrieved memories                              ││ │
│  │  │ • Reasoning scratchpad                                                  ││ │
│  │  │ • Pending tool calls and results                                        ││ │
│  │  │                                                                         ││ │
│  │  │ TTL: Session-scoped | Access: Immediate | Size: ~10KB                   ││ │
│  │  └─────────────────────────────────────────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                        │                                          │
│                                        ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                         LAYER 2: EPISODIC MEMORY                             │ │
│  │                         (Vector DB: Qdrant/Chroma)                           │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐│ │
│  │  │ Schema:                                                                 ││ │
│  │  │ {                                                                       ││ │
│  │  │   "episode_id": "uuid",                                                 ││ │
│  │  │   "timestamp": "2024-12-26T15:30:00Z",                                  ││ │
│  │  │   "conversation_id": "session_123",                                     ││ │
│  │  │   "summary": "Discussed memory architecture options...",                ││ │
│  │  │   "full_transcript": [...],                                             ││ │
│  │  │   "participants": ["user", "emperor"],                                  ││ │
│  │  │   "topics": ["memory", "letta", "cognitive"],                           ││ │
│  │  │   "sentiment": {"start": "curious", "end": "satisfied"},                ││ │
│  │  │   "outcome": "decision_made",                                           ││ │
│  │  │   "embedding": [0.123, -0.456, ...],                                    ││ │
│  │  │   "linked_facts": ["fact_001", "fact_002"],                             ││ │
│  │  │   "linked_procedures": ["proc_001"]                                     ││ │
│  │  │ }                                                                       ││ │
│  │  │                                                                         ││ │
│  │  │ Capabilities:                                                           ││ │
│  │  │ • Semantic search: "conversations about memory"                         ││ │
│  │  │ • Temporal queries: "what did we discuss yesterday"                     ││ │
│  │  │ • Sentiment filtering: "times user was frustrated"                      ││ │
│  │  │ • Causal chains: "what led to this decision"                            ││ │
│  │  │                                                                         ││ │
│  │  │ TTL: Consolidates after 30 days | Access: ~50ms | Size: Unlimited       ││ │
│  │  └─────────────────────────────────────────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                        │                                          │
│                                        ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                         LAYER 3: SEMANTIC MEMORY                             │ │
│  │                         (SQLite + Vector DB + Graph DB)                      │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐│ │
│  │  │                                                                         ││ │
│  │  │  FACTS DATABASE (SQLite)                                                ││ │
│  │  │  ┌─────────────────────────────────────────────────────────────────────┐││ │
│  │  │  │ id │ content                          │ category │ confidence │ ... │││ │
│  │  │  │ 1  │ "User's name is Winston"         │ user     │ 0.99       │     │││ │
│  │  │  │ 2  │ "User prefers TypeScript"        │ pref     │ 0.85       │     │││ │
│  │  │  │ 3  │ "Emperor uses Tauri + React"     │ project  │ 0.95       │     │││ │
│  │  │  └─────────────────────────────────────────────────────────────────────┘││ │
│  │  │                                                                         ││ │
│  │  │  KNOWLEDGE GRAPH (Neo4j/NetworkX)                                       ││ │
│  │  │  ┌─────────────────────────────────────────────────────────────────────┐││ │
│  │  │  │                                                                     │││ │
│  │  │  │     ┌─────────┐    prefers     ┌────────────┐                       │││ │
│  │  │  │     │ Winston │───────────────▶│ TypeScript │                       │││ │
│  │  │  │     └────┬────┘                └────────────┘                       │││ │
│  │  │  │          │                                                          │││ │
│  │  │  │          │ builds                                                   │││ │
│  │  │  │          ▼                                                          │││ │
│  │  │  │     ┌─────────┐    uses        ┌────────────┐                       │││ │
│  │  │  │     │ Emperor │───────────────▶│   Tauri    │                       │││ │
│  │  │  │     └────┬────┘                └────────────┘                       │││ │
│  │  │  │          │                                                          │││ │
│  │  │  │          │ has_component                                            │││ │
│  │  │  │          ▼                                                          │││ │
│  │  │  │     ┌───────────┐  implements  ┌────────────┐                       │││ │
│  │  │  │     │Orchestrator│────────────▶│Claude Code │                       │││ │
│  │  │  │     └───────────┘              └────────────┘                       │││ │
│  │  │  │                                                                     │││ │
│  │  │  └─────────────────────────────────────────────────────────────────────┘││ │
│  │  │                                                                         ││ │
│  │  │  VECTOR INDEX (Embeddings for semantic search)                          ││ │
│  │  │                                                                         ││ │
│  │  │ TTL: Persistent | Access: ~20ms | Size: ~100MB                          ││ │
│  │  └─────────────────────────────────────────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                        │                                          │
│                                        ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                         LAYER 4: PROCEDURAL MEMORY                           │ │
│  │                         (SQLite + Pattern Engine)                            │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐│ │
│  │  │ Schema:                                                                 ││ │
│  │  │ {                                                                       ││ │
│  │  │   "procedure_id": "proc_001",                                           ││ │
│  │  │   "trigger": "user requests deployment",                                ││ │
│  │  │   "conditions": ["project has tests", "on main branch"],                ││ │
│  │  │   "steps": [                                                            ││ │
│  │  │     "1. Run test suite",                                                ││ │
│  │  │     "2. Check for linting errors",                                      ││ │
│  │  │     "3. Build production bundle",                                       ││ │
│  │  │     "4. Deploy to specified environment"                                ││ │
│  │  │   ],                                                                    ││ │
│  │  │   "learned_from": ["episode_045", "episode_067"],                       ││ │
│  │  │   "times_used": 5,                                                      ││ │
│  │  │   "success_rate": 0.8,                                                  ││ │
│  │  │   "last_used": "2024-12-25",                                            ││ │
│  │  │   "user_approved": true                                                 ││ │
│  │  │ }                                                                       ││ │
│  │  │                                                                         ││ │
│  │  │ Capabilities:                                                           ││ │
│  │  │ • Pattern matching: detect when procedure applies                       ││ │
│  │  │ • Reinforcement: strengthen successful procedures                       ││ │
│  │  │ • Adaptation: modify based on feedback                                  ││ │
│  │  │ • Suggestion: proactively offer known workflows                         ││ │
│  │  │                                                                         ││ │
│  │  │ TTL: Persistent | Access: ~10ms | Size: ~10MB                           ││ │
│  │  └─────────────────────────────────────────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                        │                                          │
│                                        ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                         LAYER 5: META-MEMORY                                 │ │
│  │                         (Memory about Memory)                                │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐│ │
│  │  │ Capabilities:                                                           ││ │
│  │  │                                                                         ││ │
│  │  │ • Confidence Tracking                                                   ││ │
│  │  │   - How sure am I about this fact?                                      ││ │
│  │  │   - Has it been contradicted?                                           ││ │
│  │  │   - When was it last confirmed?                                         ││ │
│  │  │                                                                         ││ │
│  │  │ • Provenance Tracking                                                   ││ │
│  │  │   - Where did I learn this?                                             ││ │
│  │  │   - From which conversation?                                            ││ │
│  │  │   - Was it explicit or inferred?                                        ││ │
│  │  │                                                                         ││ │
│  │  │ • Uncertainty Handling                                                  ││ │
│  │  │   - Should I ask to confirm?                                            ││ │
│  │  │   - Is this memory stale?                                               ││ │
│  │  │   - Are there contradictions?                                           ││ │
│  │  │                                                                         ││ │
│  │  │ • Access Patterns                                                       ││ │
│  │  │   - Which memories are frequently accessed?                             ││ │
│  │  │   - Which are never used?                                               ││ │
│  │  │   - Optimize retrieval based on patterns                                ││ │
│  │  │                                                                         ││ │
│  │  └─────────────────────────────────────────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                      CONSOLIDATION ENGINE                                    │ │
│  │                      (Background Processing)                                 │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐│ │
│  │  │ Runs periodically (like human sleep):                                   ││ │
│  │  │                                                                         ││ │
│  │  │ 1. EPISODIC → SEMANTIC EXTRACTION                                       ││ │
│  │  │    • Extract lasting facts from recent conversations                    ││ │
│  │  │    • Update knowledge graph with new entities/relationships             ││ │
│  │  │                                                                         ││ │
│  │  │ 2. PATTERN DETECTION → PROCEDURAL                                       ││ │
│  │  │    • Identify repeated workflows                                        ││ │
│  │  │    • Create/reinforce procedural memories                               ││ │
│  │  │                                                                         ││ │
│  │  │ 3. MEMORY DECAY                                                         ││ │
│  │  │    • Reduce confidence of unreinforced memories                         ││ │
│  │  │    • Archive or delete stale information                                ││ │
│  │  │                                                                         ││ │
│  │  │ 4. CONTRADICTION RESOLUTION                                             ││ │
│  │  │    • Detect conflicting facts                                           ││ │
│  │  │    • Resolve or flag for user confirmation                              ││ │
│  │  │                                                                         ││ │
│  │  │ 5. EPISODIC COMPRESSION                                                 ││ │
│  │  │    • Summarize old conversations                                        ││ │
│  │  │    • Keep summaries, archive full transcripts                           ││ │
│  │  │                                                                         ││ │
│  │  └─────────────────────────────────────────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### Complete Implementation

#### Directory Structure

```
backend/memory/
├── __init__.py
├── cognitive_memory.py      # Main interface
├── working_memory.py        # Layer 1: Session state
├── episodic_memory.py       # Layer 2: Events/experiences
├── semantic_memory.py       # Layer 3: Facts + Knowledge graph
├── procedural_memory.py     # Layer 4: Workflows/skills
├── meta_memory.py           # Layer 5: Memory about memory
├── consolidation.py         # Background processing
├── retrieval.py             # Multi-layer retrieval
├── extraction.py            # Fact/entity extraction
└── models/
    ├── __init__.py
    ├── episode.py
    ├── fact.py
    ├── procedure.py
    └── entity.py
```

#### Core Implementation

```python
# backend/memory/cognitive_memory.py
"""
Complete Cognitive Memory System for Emperor AI
5-Layer architecture with consolidation and meta-cognition
"""

from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime, timezone
import asyncio

from .working_memory import WorkingMemory
from .episodic_memory import EpisodicMemory
from .semantic_memory import SemanticMemory
from .procedural_memory import ProceduralMemory
from .meta_memory import MetaMemory
from .consolidation import ConsolidationEngine
from .retrieval import HybridRetriever
from .extraction import FactExtractor, EntityExtractor, PatternDetector


@dataclass
class MemoryBundle:
    """Complete memory context for a request."""

    # Core user info (always included)
    user_profile: dict[str, Any] = field(default_factory=dict)

    # Retrieved memories by type
    semantic_facts: list[dict] = field(default_factory=list)
    episodic_memories: list[dict] = field(default_factory=list)
    procedural_matches: list[dict] = field(default_factory=list)
    graph_context: dict[str, Any] = field(default_factory=dict)

    # Meta information
    confidence_scores: dict[str, float] = field(default_factory=dict)
    retrieval_metadata: dict[str, Any] = field(default_factory=dict)

    def to_prompt_context(self) -> str:
        """Format for inclusion in LLM prompt."""
        sections = []

        if self.user_profile:
            profile_str = "\n".join(f"  - {k}: {v}" for k, v in self.user_profile.items())
            sections.append(f"**User Profile:**\n{profile_str}")

        if self.semantic_facts:
            facts_str = "\n".join(f"  - {f['content']}" for f in self.semantic_facts[:10])
            sections.append(f"**Relevant Facts:**\n{facts_str}")

        if self.episodic_memories:
            episodes_str = "\n".join(
                f"  - [{e['timestamp'][:10]}] {e['summary']}"
                for e in self.episodic_memories[:5]
            )
            sections.append(f"**Past Context:**\n{episodes_str}")

        if self.procedural_matches:
            procs_str = "\n".join(
                f"  - {p['trigger']}: {', '.join(p['steps'][:3])}..."
                for p in self.procedural_matches[:3]
            )
            sections.append(f"**Known Workflows:**\n{procs_str}")

        if self.graph_context:
            entities = self.graph_context.get("entities", [])
            relations = self.graph_context.get("relations", [])
            if entities or relations:
                graph_str = f"  Entities: {', '.join(entities[:5])}"
                if relations:
                    graph_str += f"\n  Relations: {', '.join(str(r) for r in relations[:5])}"
                sections.append(f"**Related Concepts:**\n{graph_str}")

        return "\n\n".join(sections) if sections else ""


class CognitiveMemorySystem:
    """
    5-Layer Cognitive Memory Architecture

    Provides human-like memory capabilities:
    - Working memory for immediate context
    - Episodic memory for experiences
    - Semantic memory for facts and knowledge
    - Procedural memory for skills and workflows
    - Meta-memory for self-awareness about memory
    """

    def __init__(self, config: dict[str, Any]):
        """
        Initialize the cognitive memory system.

        Args:
            config: Configuration dict with storage paths and settings
        """
        self.config = config

        # Initialize memory layers
        self.working = WorkingMemory(
            redis_url=config.get("redis_url"),
            fallback_to_dict=True,
        )

        self.episodic = EpisodicMemory(
            vector_store_path=config.get("vector_store_path", "data/chroma"),
            collection_name="episodic",
        )

        self.semantic = SemanticMemory(
            db_path=config.get("db_path", "data/memory.db"),
            vector_store_path=config.get("vector_store_path", "data/chroma"),
            graph_path=config.get("graph_path", "data/knowledge_graph.json"),
        )

        self.procedural = ProceduralMemory(
            db_path=config.get("db_path", "data/memory.db"),
        )

        self.meta = MetaMemory(
            db_path=config.get("db_path", "data/memory.db"),
        )

        # Initialize processing components
        self.retriever = HybridRetriever(
            episodic=self.episodic,
            semantic=self.semantic,
            procedural=self.procedural,
            meta=self.meta,
        )

        self.fact_extractor = FactExtractor(
            llm_model=config.get("extraction_model", "claude-3-haiku-20240307"),
        )

        self.entity_extractor = EntityExtractor()

        self.pattern_detector = PatternDetector()

        self.consolidation = ConsolidationEngine(
            episodic=self.episodic,
            semantic=self.semantic,
            procedural=self.procedural,
            meta=self.meta,
            fact_extractor=self.fact_extractor,
            pattern_detector=self.pattern_detector,
        )

    # =========================================================================
    # REMEMBER: Store new information
    # =========================================================================

    async def remember_conversation(
        self,
        conversation: list[dict[str, str]],
        session_id: str,
        user_id: str,
        auto_extract: bool = True,
    ) -> dict[str, Any]:
        """
        Process and store a conversation across all memory layers.

        Args:
            conversation: List of {"role": str, "content": str} messages
            session_id: Current session ID
            user_id: User identifier
            auto_extract: Whether to auto-extract facts/entities

        Returns:
            Dict with storage results
        """
        results = {
            "episode_id": None,
            "facts_extracted": [],
            "entities_found": [],
            "procedures_detected": [],
        }

        # 1. Update working memory
        await self.working.update_conversation(session_id, conversation)

        # 2. Store as episodic memory
        episode = await self.episodic.store_conversation(
            conversation=conversation,
            session_id=session_id,
            user_id=user_id,
        )
        results["episode_id"] = episode.id

        # 3. Extract and store semantic information
        if auto_extract:
            # Extract facts
            facts = await self.fact_extractor.extract(conversation)
            for fact in facts:
                fact_id = await self.semantic.store_fact(
                    content=fact["content"],
                    category=fact.get("category", "general"),
                    confidence=fact.get("confidence", 0.7),
                    source_episode=episode.id,
                )
                results["facts_extracted"].append(fact_id)

                # Track provenance in meta-memory
                await self.meta.track_provenance(
                    memory_id=fact_id,
                    memory_type="fact",
                    source_type="extraction",
                    source_id=episode.id,
                )

            # Extract entities and update knowledge graph
            entities = await self.entity_extractor.extract(conversation)
            for entity in entities:
                await self.semantic.graph.add_or_update_entity(entity)
                results["entities_found"].append(entity["name"])

            # Extract relationships
            relationships = await self.entity_extractor.extract_relationships(
                conversation, entities
            )
            for rel in relationships:
                await self.semantic.graph.add_relationship(rel)

        # 4. Detect procedural patterns
        patterns = await self.pattern_detector.detect(conversation)
        for pattern in patterns:
            proc_id = await self.procedural.add_or_reinforce(pattern)
            if proc_id:
                results["procedures_detected"].append(proc_id)

        return results

    async def remember_fact(
        self,
        content: str,
        category: str = "general",
        confidence: float = 0.8,
        source: str = "explicit",
        user_id: str = "default",
    ) -> str:
        """
        Explicitly store a fact in semantic memory.

        Args:
            content: The fact to store
            category: Category (user, project, preference, etc.)
            confidence: How confident (0-1)
            source: Where it came from
            user_id: User identifier

        Returns:
            Fact ID
        """
        fact_id = await self.semantic.store_fact(
            content=content,
            category=category,
            confidence=confidence,
            user_id=user_id,
        )

        await self.meta.track_provenance(
            memory_id=fact_id,
            memory_type="fact",
            source_type=source,
            source_id=None,
        )

        return fact_id

    # =========================================================================
    # RECALL: Retrieve relevant information
    # =========================================================================

    async def recall(
        self,
        query: str,
        user_id: str,
        context: Optional[dict] = None,
        max_facts: int = 10,
        max_episodes: int = 5,
        max_procedures: int = 3,
        confidence_threshold: float = 0.3,
    ) -> MemoryBundle:
        """
        Retrieve relevant memories across all layers.

        Args:
            query: Search query
            user_id: User identifier
            context: Optional additional context
            max_facts: Max semantic facts to return
            max_episodes: Max episodic memories to return
            max_procedures: Max procedures to return
            confidence_threshold: Min confidence score

        Returns:
            MemoryBundle with all relevant memories
        """
        bundle = MemoryBundle()

        # 1. Always get user profile
        bundle.user_profile = await self.semantic.get_user_profile(user_id)

        # 2. Semantic search for facts
        facts = await self.semantic.search(
            query=query,
            user_id=user_id,
            limit=max_facts,
        )

        # Filter by confidence
        bundle.semantic_facts = [
            f for f in facts
            if await self.meta.get_confidence(f["id"]) >= confidence_threshold
        ]

        # 3. Episodic search for similar situations
        episodes = await self.episodic.search(
            query=query,
            user_id=user_id,
            limit=max_episodes,
        )
        bundle.episodic_memories = episodes

        # 4. Graph traversal for related concepts
        entities = self.entity_extractor.extract_from_text(query)
        if entities:
            bundle.graph_context = await self.semantic.graph.traverse(
                entities=entities,
                depth=2,
                relationship_types=["prefers", "uses", "builds", "knows"],
            )

        # 5. Procedural matching
        procedures = await self.procedural.match(
            query=query,
            context=context or {},
        )
        bundle.procedural_matches = procedures[:max_procedures]

        # 6. Add confidence scores
        for fact in bundle.semantic_facts:
            bundle.confidence_scores[fact["id"]] = await self.meta.get_confidence(fact["id"])

        # 7. Record access patterns
        await self.meta.record_access(
            query=query,
            retrieved_ids=[f["id"] for f in bundle.semantic_facts],
        )

        return bundle

    async def recall_user_profile(self, user_id: str) -> dict[str, Any]:
        """Get complete user profile."""
        return await self.semantic.get_user_profile(user_id)

    async def recall_recent_context(
        self,
        session_id: str,
        n_turns: int = 10
    ) -> list[dict]:
        """Get recent conversation context from working memory."""
        return await self.working.get_recent(session_id, n_turns)

    # =========================================================================
    # UPDATE: Modify existing memories
    # =========================================================================

    async def update_user_profile(
        self,
        user_id: str,
        updates: dict[str, Any],
    ) -> None:
        """Update user profile information."""
        await self.semantic.update_user_profile(user_id, updates)

    async def reinforce_fact(self, fact_id: str) -> None:
        """Increase confidence in a fact (it was used/confirmed)."""
        await self.meta.reinforce(fact_id)

    async def contradict_fact(
        self,
        fact_id: str,
        new_info: str,
        resolution: str = "flag",  # "flag", "replace", "keep"
    ) -> None:
        """Handle contradiction of an existing fact."""
        await self.meta.record_contradiction(fact_id, new_info)

        if resolution == "replace":
            await self.semantic.update_fact(fact_id, new_info)
        elif resolution == "flag":
            await self.meta.flag_for_review(fact_id, new_info)

    # =========================================================================
    # FORGET: Remove or decay memories
    # =========================================================================

    async def forget_fact(self, fact_id: str) -> None:
        """Explicitly remove a fact."""
        await self.semantic.delete_fact(fact_id)
        await self.meta.remove_tracking(fact_id)

    async def decay_stale_memories(
        self,
        decay_factor: float = 0.95,
        min_confidence: float = 0.1,
    ) -> int:
        """Reduce confidence of unreinforced memories."""
        return await self.meta.decay_all(decay_factor, min_confidence)

    # =========================================================================
    # CONSOLIDATION: Background memory processing
    # =========================================================================

    async def consolidate(self) -> dict[str, Any]:
        """
        Run memory consolidation (call periodically).

        Like human sleep - processes and organizes memories.
        """
        return await self.consolidation.run()

    def start_consolidation_scheduler(
        self,
        interval_hours: int = 24,
    ) -> None:
        """Start background consolidation scheduler."""
        self.consolidation.start_scheduler(interval_hours)

    # =========================================================================
    # INTROSPECTION: Memory system status
    # =========================================================================

    async def get_memory_stats(self) -> dict[str, Any]:
        """Get statistics about the memory system."""
        return {
            "episodic_count": await self.episodic.count(),
            "fact_count": await self.semantic.count_facts(),
            "entity_count": await self.semantic.graph.count_entities(),
            "relationship_count": await self.semantic.graph.count_relationships(),
            "procedure_count": await self.procedural.count(),
            "avg_confidence": await self.meta.average_confidence(),
            "stale_memories": await self.meta.count_stale(),
            "contradictions": await self.meta.count_contradictions(),
        }

    async def explain_memory(self, memory_id: str) -> dict[str, Any]:
        """Get full provenance and history of a memory."""
        return await self.meta.get_full_history(memory_id)


# Singleton instance
_cognitive_memory: Optional[CognitiveMemorySystem] = None


def get_cognitive_memory(config: Optional[dict] = None) -> CognitiveMemorySystem:
    """Get the singleton cognitive memory instance."""
    global _cognitive_memory
    if _cognitive_memory is None:
        _cognitive_memory = CognitiveMemorySystem(config or {})
    return _cognitive_memory
```

#### Working Memory Implementation

```python
# backend/memory/working_memory.py
"""Layer 1: Working Memory - Immediate session context"""

from typing import Any, Optional
from datetime import datetime, timezone
import json

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class WorkingMemory:
    """
    Fast, session-scoped memory for immediate context.
    Uses Redis if available, falls back to in-memory dict.
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        fallback_to_dict: bool = True,
        default_ttl: int = 3600,  # 1 hour
    ):
        self.default_ttl = default_ttl
        self._local_store: dict[str, Any] = {}
        self._redis: Optional[redis.Redis] = None

        if redis_url and REDIS_AVAILABLE:
            try:
                self._redis = redis.from_url(redis_url)
            except Exception as e:
                if not fallback_to_dict:
                    raise
                print(f"Redis unavailable, using local dict: {e}")

    def _key(self, session_id: str, suffix: str) -> str:
        return f"emperor:working:{session_id}:{suffix}"

    async def update_conversation(
        self,
        session_id: str,
        messages: list[dict[str, str]],
        max_messages: int = 20,
    ) -> None:
        """Update conversation buffer for a session."""
        key = self._key(session_id, "conversation")

        # Keep only recent messages
        recent = messages[-max_messages:]

        if self._redis:
            await self._redis.setex(
                key,
                self.default_ttl,
                json.dumps(recent),
            )
        else:
            self._local_store[key] = {
                "data": recent,
                "expires": datetime.now(timezone.utc).timestamp() + self.default_ttl,
            }

    async def get_recent(
        self,
        session_id: str,
        n_turns: int = 10,
    ) -> list[dict[str, str]]:
        """Get recent conversation turns."""
        key = self._key(session_id, "conversation")

        if self._redis:
            data = await self._redis.get(key)
            if data:
                messages = json.loads(data)
                return messages[-n_turns * 2:]  # n_turns = user+assistant pairs
        else:
            entry = self._local_store.get(key)
            if entry and entry["expires"] > datetime.now(timezone.utc).timestamp():
                return entry["data"][-n_turns * 2:]

        return []

    async def set_active_task(
        self,
        session_id: str,
        task: dict[str, Any],
    ) -> None:
        """Set the current active task."""
        key = self._key(session_id, "active_task")

        if self._redis:
            await self._redis.setex(key, self.default_ttl, json.dumps(task))
        else:
            self._local_store[key] = {
                "data": task,
                "expires": datetime.now(timezone.utc).timestamp() + self.default_ttl,
            }

    async def get_active_task(self, session_id: str) -> Optional[dict[str, Any]]:
        """Get the current active task."""
        key = self._key(session_id, "active_task")

        if self._redis:
            data = await self._redis.get(key)
            return json.loads(data) if data else None
        else:
            entry = self._local_store.get(key)
            if entry and entry["expires"] > datetime.now(timezone.utc).timestamp():
                return entry["data"]

        return None

    async def set_attention(
        self,
        session_id: str,
        attention_weights: dict[str, float],
    ) -> None:
        """Set attention weights for retrieved memories."""
        key = self._key(session_id, "attention")

        if self._redis:
            await self._redis.setex(key, self.default_ttl, json.dumps(attention_weights))
        else:
            self._local_store[key] = {
                "data": attention_weights,
                "expires": datetime.now(timezone.utc).timestamp() + self.default_ttl,
            }

    async def clear_session(self, session_id: str) -> None:
        """Clear all working memory for a session."""
        patterns = ["conversation", "active_task", "attention", "scratchpad"]

        for suffix in patterns:
            key = self._key(session_id, suffix)
            if self._redis:
                await self._redis.delete(key)
            else:
                self._local_store.pop(key, None)
```

#### Episodic Memory Implementation

```python
# backend/memory/episodic_memory.py
"""Layer 2: Episodic Memory - Time-stamped experiences"""

from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime, timezone
import uuid
import json

import chromadb
from sentence_transformers import SentenceTransformer


@dataclass
class Episode:
    """A single episodic memory."""
    id: str
    timestamp: str
    session_id: str
    user_id: str
    summary: str
    full_transcript: list[dict[str, str]]
    topics: list[str] = field(default_factory=list)
    sentiment: dict[str, str] = field(default_factory=dict)
    outcome: Optional[str] = None
    linked_facts: list[str] = field(default_factory=list)


class EpisodicMemory:
    """
    Stores and retrieves autobiographical experiences.
    Uses vector similarity for "remember when..." queries.
    """

    def __init__(
        self,
        vector_store_path: str,
        collection_name: str = "episodic",
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        self.client = chromadb.PersistentClient(path=vector_store_path)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self.embedder = SentenceTransformer(embedding_model)

    async def store_conversation(
        self,
        conversation: list[dict[str, str]],
        session_id: str,
        user_id: str,
        summary: Optional[str] = None,
        topics: Optional[list[str]] = None,
    ) -> Episode:
        """Store a conversation as an episodic memory."""
        episode_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        # Generate summary if not provided
        if not summary:
            summary = self._generate_summary(conversation)

        # Extract topics if not provided
        if not topics:
            topics = self._extract_topics(conversation)

        # Create episode
        episode = Episode(
            id=episode_id,
            timestamp=timestamp,
            session_id=session_id,
            user_id=user_id,
            summary=summary,
            full_transcript=conversation,
            topics=topics,
        )

        # Generate embedding from summary
        embedding = self.embedder.encode(summary).tolist()

        # Store in vector DB
        self.collection.add(
            ids=[episode_id],
            embeddings=[embedding],
            documents=[summary],
            metadatas=[{
                "timestamp": timestamp,
                "session_id": session_id,
                "user_id": user_id,
                "topics": json.dumps(topics),
                "transcript": json.dumps(conversation),
            }],
        )

        return episode

    async def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Search for similar episodic memories."""
        query_embedding = self.embedder.encode(query).tolist()

        where_filter = {"user_id": user_id} if user_id else None

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        episodes = []
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i]
            episodes.append({
                "id": results["ids"][0][i],
                "summary": doc,
                "timestamp": meta["timestamp"],
                "session_id": meta["session_id"],
                "topics": json.loads(meta.get("topics", "[]")),
                "similarity": 1 - results["distances"][0][i],
            })

        return episodes

    async def get_by_timerange(
        self,
        start: datetime,
        end: datetime,
        user_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Get episodes within a time range."""
        # ChromaDB doesn't support range queries well, so we get all and filter
        # For production, consider using a proper time-series index

        results = self.collection.get(
            where={"user_id": user_id} if user_id else None,
            include=["documents", "metadatas"],
        )

        episodes = []
        for i, doc in enumerate(results["documents"]):
            meta = results["metadatas"][i]
            timestamp = datetime.fromisoformat(meta["timestamp"].replace("Z", "+00:00"))

            if start <= timestamp <= end:
                episodes.append({
                    "id": results["ids"][i],
                    "summary": doc,
                    "timestamp": meta["timestamp"],
                    "topics": json.loads(meta.get("topics", "[]")),
                })

        return sorted(episodes, key=lambda x: x["timestamp"], reverse=True)

    def _generate_summary(self, conversation: list[dict[str, str]]) -> str:
        """Generate a simple summary of the conversation."""
        # Simple implementation - could use LLM for better summaries
        user_messages = [m["content"] for m in conversation if m["role"] == "user"]
        if user_messages:
            return f"Conversation about: {user_messages[0][:200]}"
        return "Empty conversation"

    def _extract_topics(self, conversation: list[dict[str, str]]) -> list[str]:
        """Extract topics from conversation."""
        # Simple keyword extraction - could use NLP for better results
        text = " ".join(m["content"] for m in conversation)

        # Common topic keywords (expand as needed)
        topic_keywords = [
            "memory", "code", "debug", "error", "feature", "test",
            "deploy", "database", "api", "frontend", "backend",
        ]

        found_topics = [t for t in topic_keywords if t.lower() in text.lower()]
        return found_topics[:5]

    async def count(self) -> int:
        """Count total episodes."""
        return self.collection.count()
```

#### Semantic Memory with Knowledge Graph

```python
# backend/memory/semantic_memory.py
"""Layer 3: Semantic Memory - Facts and Knowledge Graph"""

from typing import Any, Optional
from datetime import datetime, timezone
import sqlite3
import json
import uuid

import chromadb
from sentence_transformers import SentenceTransformer
import networkx as nx


class KnowledgeGraph:
    """Graph-based knowledge representation."""

    def __init__(self, graph_path: str):
        self.graph_path = graph_path
        self.graph = nx.DiGraph()
        self._load()

    def _load(self):
        """Load graph from file."""
        try:
            with open(self.graph_path, "r") as f:
                data = json.load(f)
                self.graph = nx.node_link_graph(data)
        except FileNotFoundError:
            self.graph = nx.DiGraph()

    def _save(self):
        """Save graph to file."""
        data = nx.node_link_data(self.graph)
        with open(self.graph_path, "w") as f:
            json.dump(data, f)

    async def add_or_update_entity(self, entity: dict[str, Any]) -> None:
        """Add or update an entity node."""
        name = entity["name"]
        entity_type = entity.get("type", "unknown")
        attributes = entity.get("attributes", {})

        self.graph.add_node(
            name,
            type=entity_type,
            **attributes,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        self._save()

    async def add_relationship(self, relationship: dict[str, Any]) -> None:
        """Add a relationship between entities."""
        source = relationship["source"]
        target = relationship["target"]
        relation_type = relationship["type"]

        # Ensure nodes exist
        if source not in self.graph:
            self.graph.add_node(source)
        if target not in self.graph:
            self.graph.add_node(target)

        self.graph.add_edge(
            source,
            target,
            type=relation_type,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._save()

    async def traverse(
        self,
        entities: list[str],
        depth: int = 2,
        relationship_types: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Traverse graph from given entities."""
        found_entities = set()
        found_relations = []

        for entity in entities:
            if entity not in self.graph:
                continue

            # BFS traversal
            visited = {entity}
            queue = [(entity, 0)]

            while queue:
                current, current_depth = queue.pop(0)

                if current_depth >= depth:
                    continue

                found_entities.add(current)

                # Get neighbors
                for neighbor in self.graph.neighbors(current):
                    edge_data = self.graph.edges[current, neighbor]
                    edge_type = edge_data.get("type", "related")

                    if relationship_types and edge_type not in relationship_types:
                        continue

                    found_relations.append({
                        "source": current,
                        "target": neighbor,
                        "type": edge_type,
                    })

                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, current_depth + 1))

        return {
            "entities": list(found_entities),
            "relations": found_relations,
        }

    async def count_entities(self) -> int:
        return self.graph.number_of_nodes()

    async def count_relationships(self) -> int:
        return self.graph.number_of_edges()


class SemanticMemory:
    """
    Stores facts with confidence scores and a knowledge graph.
    Supports both structured queries and semantic search.
    """

    def __init__(
        self,
        db_path: str,
        vector_store_path: str,
        graph_path: str,
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

        self.vector_client = chromadb.PersistentClient(path=vector_store_path)
        self.facts_collection = self.vector_client.get_or_create_collection(
            name="semantic_facts",
            metadata={"hnsw:space": "cosine"},
        )

        self.embedder = SentenceTransformer(embedding_model)
        self.graph = KnowledgeGraph(graph_path)

    def _init_schema(self):
        """Initialize database schema."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS facts (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                confidence REAL DEFAULT 0.7,
                user_id TEXT DEFAULT 'default',
                source_episode TEXT,
                times_reinforced INTEGER DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                skill_level TEXT,
                preferences TEXT,  -- JSON
                created_at TEXT,
                updated_at TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_facts_category ON facts(category);
            CREATE INDEX IF NOT EXISTS idx_facts_user ON facts(user_id);
        """)
        self.conn.commit()

    async def store_fact(
        self,
        content: str,
        category: str = "general",
        confidence: float = 0.7,
        user_id: str = "default",
        source_episode: Optional[str] = None,
    ) -> str:
        """Store a new fact."""
        fact_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        # Store in SQLite
        self.conn.execute(
            """INSERT INTO facts
               (id, content, category, confidence, user_id, source_episode, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (fact_id, content, category, confidence, user_id, source_episode, now, now),
        )
        self.conn.commit()

        # Store embedding in vector DB
        embedding = self.embedder.encode(content).tolist()
        self.facts_collection.add(
            ids=[fact_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[{
                "category": category,
                "confidence": confidence,
                "user_id": user_id,
            }],
        )

        return fact_id

    async def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Semantic search for facts."""
        query_embedding = self.embedder.encode(query).tolist()

        where_filter = {}
        if user_id:
            where_filter["user_id"] = user_id
        if category:
            where_filter["category"] = category

        results = self.facts_collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where_filter if where_filter else None,
            include=["documents", "metadatas", "distances"],
        )

        facts = []
        for i, doc in enumerate(results["documents"][0]):
            facts.append({
                "id": results["ids"][0][i],
                "content": doc,
                "category": results["metadatas"][0][i].get("category"),
                "confidence": results["metadatas"][0][i].get("confidence"),
                "similarity": 1 - results["distances"][0][i],
            })

        return facts

    async def get_user_profile(self, user_id: str) -> dict[str, Any]:
        """Get user profile."""
        cursor = self.conn.execute(
            "SELECT * FROM user_profiles WHERE user_id = ?",
            (user_id,),
        )
        row = cursor.fetchone()

        if row:
            return {
                "user_id": row[0],
                "name": row[1],
                "skill_level": row[2],
                "preferences": json.loads(row[3]) if row[3] else {},
            }

        return {"user_id": user_id}

    async def update_user_profile(
        self,
        user_id: str,
        updates: dict[str, Any],
    ) -> None:
        """Update user profile."""
        now = datetime.now(timezone.utc).isoformat()

        # Check if profile exists
        cursor = self.conn.execute(
            "SELECT user_id FROM user_profiles WHERE user_id = ?",
            (user_id,),
        )

        if cursor.fetchone():
            # Update existing
            set_clauses = []
            values = []
            for key, value in updates.items():
                if key in ["name", "skill_level"]:
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
                elif key == "preferences":
                    set_clauses.append("preferences = ?")
                    values.append(json.dumps(value))

            set_clauses.append("updated_at = ?")
            values.append(now)
            values.append(user_id)

            self.conn.execute(
                f"UPDATE user_profiles SET {', '.join(set_clauses)} WHERE user_id = ?",
                values,
            )
        else:
            # Insert new
            self.conn.execute(
                """INSERT INTO user_profiles
                   (user_id, name, skill_level, preferences, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    user_id,
                    updates.get("name"),
                    updates.get("skill_level"),
                    json.dumps(updates.get("preferences", {})),
                    now,
                    now,
                ),
            )

        self.conn.commit()

    async def count_facts(self) -> int:
        """Count total facts."""
        cursor = self.conn.execute("SELECT COUNT(*) FROM facts")
        return cursor.fetchone()[0]
```

#### Procedural Memory Implementation

```python
# backend/memory/procedural_memory.py
"""Layer 4: Procedural Memory - Skills and Workflows"""

from typing import Any, Optional
from datetime import datetime, timezone
import sqlite3
import json
import uuid


class ProceduralMemory:
    """
    Stores learned workflows and behavioral patterns.
    Enables the AI to learn "how the user does things."
    """

    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self):
        """Initialize database schema."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS procedures (
                id TEXT PRIMARY KEY,
                trigger TEXT NOT NULL,
                conditions TEXT,  -- JSON array
                steps TEXT NOT NULL,  -- JSON array
                learned_from TEXT,  -- JSON array of episode IDs
                times_used INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                last_used TEXT,
                user_approved INTEGER DEFAULT 0,
                user_id TEXT DEFAULT 'default',
                created_at TEXT,
                updated_at TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_procedures_user ON procedures(user_id);
        """)
        self.conn.commit()

    async def add_or_reinforce(
        self,
        pattern: dict[str, Any],
        user_id: str = "default",
    ) -> Optional[str]:
        """Add a new procedure or reinforce existing one."""
        trigger = pattern.get("trigger", "")
        steps = pattern.get("steps", [])

        if not trigger or not steps:
            return None

        # Check if similar procedure exists
        cursor = self.conn.execute(
            "SELECT id, times_used FROM procedures WHERE trigger = ? AND user_id = ?",
            (trigger, user_id),
        )
        existing = cursor.fetchone()

        now = datetime.now(timezone.utc).isoformat()

        if existing:
            # Reinforce existing
            self.conn.execute(
                """UPDATE procedures
                   SET times_used = times_used + 1, updated_at = ?
                   WHERE id = ?""",
                (now, existing[0]),
            )
            self.conn.commit()
            return existing[0]
        else:
            # Create new
            proc_id = str(uuid.uuid4())
            self.conn.execute(
                """INSERT INTO procedures
                   (id, trigger, conditions, steps, learned_from, user_id, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    proc_id,
                    trigger,
                    json.dumps(pattern.get("conditions", [])),
                    json.dumps(steps),
                    json.dumps(pattern.get("learned_from", [])),
                    user_id,
                    now,
                    now,
                ),
            )
            self.conn.commit()
            return proc_id

    async def match(
        self,
        query: str,
        context: dict[str, Any],
        user_id: str = "default",
    ) -> list[dict[str, Any]]:
        """Find procedures that match the current query/context."""
        cursor = self.conn.execute(
            """SELECT id, trigger, conditions, steps, times_used, success_count
               FROM procedures
               WHERE user_id = ? AND times_used > 0
               ORDER BY times_used DESC, success_count DESC""",
            (user_id,),
        )

        matches = []
        query_lower = query.lower()

        for row in cursor.fetchall():
            proc_id, trigger, conditions_json, steps_json, times_used, success_count = row

            # Simple trigger matching (could be more sophisticated)
            if trigger.lower() in query_lower or query_lower in trigger.lower():
                success_rate = success_count / times_used if times_used > 0 else 0

                matches.append({
                    "id": proc_id,
                    "trigger": trigger,
                    "conditions": json.loads(conditions_json),
                    "steps": json.loads(steps_json),
                    "times_used": times_used,
                    "success_rate": success_rate,
                })

        return matches

    async def record_usage(
        self,
        proc_id: str,
        success: bool,
    ) -> None:
        """Record that a procedure was used."""
        now = datetime.now(timezone.utc).isoformat()

        self.conn.execute(
            """UPDATE procedures
               SET times_used = times_used + 1,
                   success_count = success_count + ?,
                   last_used = ?,
                   updated_at = ?
               WHERE id = ?""",
            (1 if success else 0, now, now, proc_id),
        )
        self.conn.commit()

    async def count(self) -> int:
        """Count total procedures."""
        cursor = self.conn.execute("SELECT COUNT(*) FROM procedures")
        return cursor.fetchone()[0]
```

### Custom Cognitive System Pros and Cons

**Pros:**
- Maximum control over every aspect
- All memory types (semantic, episodic, procedural)
- Knowledge graph for relationships
- Meta-memory for self-awareness
- Consolidation for memory maintenance
- Can optimize for your specific use case
- No external dependencies for core logic

**Cons:**
- Significant implementation effort (2-3 weeks)
- More code to maintain
- Need to handle edge cases yourself
- Requires more testing
- Higher initial complexity

---

## Recommendation for Emperor

### Decision Matrix

| Your Priority | Best Choice | Why |
|--------------|-------------|-----|
| Ship fast | mem0 | 2-4 hours setup, good features |
| Maximum intelligence | Letta | Self-managing, research-backed |
| Full control + power | Custom Cognitive | All features, your way |
| Balance | mem0 + Graph | Good features, moderate effort |

### Suggested Path for Emperor

**Phase 1 (Now):** Implement mem0 with graph support
- Get memory working quickly
- Move on to Parts 10-15
- Learn what you actually need

**Phase 2 (Later):** Evaluate if you need more
- If mem0 limits you → migrate to Custom Cognitive
- If satisfied → keep mem0

**Phase 3 (Future):** Consider Letta for self-managing agents
- When Domain Leads are mature
- If you want agents to manage their own memory

---

## Appendix: Dependencies

### mem0
```
pip install mem0ai chromadb
```

### Letta
```
pip install letta
```

### Custom Cognitive
```
pip install chromadb sentence-transformers networkx
# Optional: redis, neo4j
```

---

*Document Version: 1.0*
*Created: 2024-12-26*
*Author: Emperor AI Assistant*
