# Custom Cognitive Memory System Specification

## For Future Implementation in Emperor AI Assistant

*This document specifies a complete 5-layer cognitive memory system for future implementation when more advanced memory capabilities are needed.*

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Layer Specifications](#layer-specifications)
   - [Layer 1: Working Memory](#layer-1-working-memory)
   - [Layer 2: Episodic Memory](#layer-2-episodic-memory)
   - [Layer 3: Semantic Memory](#layer-3-semantic-memory)
   - [Layer 4: Procedural Memory](#layer-4-procedural-memory)
   - [Layer 5: Meta-Memory](#layer-5-meta-memory)
4. [Consolidation Engine](#consolidation-engine)
5. [Retrieval System](#retrieval-system)
6. [Extraction Pipeline](#extraction-pipeline)
7. [Database Schemas](#database-schemas)
8. [API Interface](#api-interface)
9. [File Structure](#file-structure)
10. [Implementation Guide](#implementation-guide)
11. [Dependencies](#dependencies)
12. [Migration from Letta](#migration-from-letta)

---

## Overview

### Purpose

The Custom Cognitive Memory System provides human-like memory capabilities for Emperor AI:

- **Remember** who the user is and their preferences
- **Recall** relevant past experiences and facts
- **Learn** workflows and behavioral patterns
- **Forget** stale or irrelevant information
- **Consolidate** memories over time (like sleep)

### Design Principles

1. **Local-first**: All data stays on user's machine
2. **Privacy-respecting**: No external API calls for storage
3. **Efficient**: Fast retrieval with hybrid search
4. **Explainable**: Track provenance of all memories
5. **Self-maintaining**: Automatic consolidation and decay

### Memory Types Supported

| Type | Description | Example |
|------|-------------|---------|
| **Semantic** | Facts and knowledge | "User prefers TypeScript" |
| **Episodic** | Events and experiences | "Dec 25: Fixed WebSocket bug" |
| **Procedural** | Skills and workflows | "Deploy: test → build → ship" |
| **Working** | Immediate context | Current conversation |
| **Meta** | Memory about memory | Confidence scores, provenance |

---

## Architecture

### System Diagram

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                      CUSTOM COGNITIVE MEMORY SYSTEM                               │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│                              ┌─────────────────┐                                  │
│                              │   ORCHESTRATOR  │                                  │
│                              │                 │                                  │
│                              │  recall(query)  │                                  │
│                              │  remember(conv) │                                  │
│                              └────────┬────────┘                                  │
│                                       │                                           │
│                                       ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                         COGNITIVE MEMORY INTERFACE                           │ │
│  │                                                                              │ │
│  │   remember_conversation()    recall()    forget()    consolidate()           │ │
│  │                                                                              │ │
│  └──────────────────────────────────┬───────────────────────────────────────────┘ │
│                                     │                                             │
│         ┌───────────────┬───────────┼───────────┬───────────────┐                │
│         ▼               ▼           ▼           ▼               ▼                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │   LAYER 1   │ │   LAYER 2   │ │   LAYER 3   │ │   LAYER 4   │ │   LAYER 5   │ │
│  │   WORKING   │ │  EPISODIC   │ │  SEMANTIC   │ │ PROCEDURAL  │ │    META     │ │
│  │   MEMORY    │ │   MEMORY    │ │   MEMORY    │ │   MEMORY    │ │   MEMORY    │ │
│  │             │ │             │ │             │ │             │ │             │ │
│  │   Redis/    │ │  ChromaDB   │ │  SQLite +   │ │   SQLite    │ │   SQLite    │ │
│  │   Dict      │ │             │ │  ChromaDB + │ │             │ │             │ │
│  │             │ │             │ │  NetworkX   │ │             │ │             │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
│                                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                         BACKGROUND SERVICES                                  │ │
│  │                                                                              │ │
│  │   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │ │
│  │   │  CONSOLIDATION  │  │   EXTRACTION    │  │    PATTERN      │             │ │
│  │   │     ENGINE      │  │    PIPELINE     │  │    DETECTOR     │             │ │
│  │   │                 │  │                 │  │                 │             │ │
│  │   │ • Decay         │  │ • Facts         │  │ • Workflows     │             │ │
│  │   │ • Compress      │  │ • Entities      │  │ • Habits        │             │ │
│  │   │ • Resolve       │  │ • Relations     │  │ • Preferences   │             │ │
│  │   └─────────────────┘  └─────────────────┘  └─────────────────┘             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
USER MESSAGE
     │
     ▼
┌─────────────────┐
│ 1. RETRIEVE     │◄─── Working Memory (current context)
│    CONTEXT      │◄─── Episodic Memory (similar situations)
│                 │◄─── Semantic Memory (relevant facts)
│                 │◄─── Procedural Memory (applicable workflows)
│                 │◄─── Knowledge Graph (related entities)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. AUGMENT      │
│    PROMPT       │───► System prompt + Memory context + User message
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. GENERATE     │
│    RESPONSE     │───► LLM generates response
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. EXTRACT &    │───► Facts extracted
│    STORE        │───► Entities identified
│                 │───► Relationships mapped
│                 │───► Patterns detected
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 5. CONSOLIDATE  │───► Background: decay, compress, resolve
│    (ASYNC)      │
└─────────────────┘
```

---

## Layer Specifications

### Layer 1: Working Memory

**Purpose**: Fast, session-scoped storage for immediate context.

**Storage**: Redis (preferred) or in-memory dictionary (fallback)

**TTL**: Session-scoped or 1 hour

#### Schema

```python
@dataclass
class WorkingMemoryState:
    session_id: str
    conversation_buffer: list[dict[str, str]]  # Last N messages
    active_task: Optional[dict[str, Any]]       # Current goal
    attention_weights: dict[str, float]         # Memory relevance
    scratchpad: dict[str, Any]                  # Temporary reasoning
    pending_tool_calls: list[dict]              # Awaiting results
    created_at: datetime
    updated_at: datetime
```

#### Key Operations

| Operation | Description | Latency Target |
|-----------|-------------|----------------|
| `get_conversation(session_id, n)` | Get last N turns | < 5ms |
| `update_conversation(session_id, messages)` | Update buffer | < 5ms |
| `set_active_task(session_id, task)` | Set current goal | < 5ms |
| `get_attention(session_id)` | Get relevance weights | < 5ms |
| `clear_session(session_id)` | Clear all session data | < 10ms |

#### Implementation Notes

```python
class WorkingMemory:
    """
    Layer 1: Immediate context buffer

    Features:
    - Conversation buffer with configurable size
    - Active task tracking
    - Attention weights for retrieved memories
    - Scratchpad for intermediate reasoning

    Storage:
    - Primary: Redis with TTL
    - Fallback: In-memory dict with manual expiry
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        max_conversation_turns: int = 20,
        default_ttl_seconds: int = 3600,
    ):
        self.max_turns = max_conversation_turns
        self.ttl = default_ttl_seconds
        self._init_storage(redis_url)
```

---

### Layer 2: Episodic Memory

**Purpose**: Store and retrieve autobiographical experiences.

**Storage**: ChromaDB (vector database)

**TTL**: Permanent (compressed after 30 days)

#### Schema

```python
@dataclass
class Episode:
    id: str                              # UUID
    timestamp: datetime                  # When it happened
    session_id: str                      # Which session
    user_id: str                         # Which user

    # Content
    summary: str                         # Brief description
    full_transcript: list[dict]          # Complete conversation

    # Metadata
    topics: list[str]                    # Detected topics
    sentiment: dict[str, str]            # start/end emotional state
    outcome: Optional[str]               # success/failure/abandoned
    duration_minutes: int                # How long

    # Relationships
    linked_facts: list[str]              # Facts learned from this
    linked_procedures: list[str]         # Procedures learned
    related_episodes: list[str]          # Similar past episodes

    # Embeddings
    embedding: list[float]               # Vector representation
```

#### Key Operations

| Operation | Description | Latency Target |
|-----------|-------------|----------------|
| `store_conversation(conv, session_id)` | Store new episode | < 100ms |
| `search(query, limit)` | Semantic search | < 50ms |
| `get_by_timerange(start, end)` | Temporal query | < 100ms |
| `get_similar(episode_id, limit)` | Find similar | < 50ms |
| `compress_old(days)` | Summarize old episodes | Background |

#### Vector Search Configuration

```python
# ChromaDB collection settings
collection_config = {
    "name": "episodic_memories",
    "metadata": {
        "hnsw:space": "cosine",      # Distance metric
        "hnsw:M": 16,                 # Graph connectivity
        "hnsw:ef_construction": 100,  # Index quality
    }
}

# Embedding model
embedding_model = "all-MiniLM-L6-v2"  # 384 dimensions, fast
# Alternative: "all-mpnet-base-v2"    # 768 dimensions, better quality
```

---

### Layer 3: Semantic Memory

**Purpose**: Store facts, knowledge, and entity relationships.

**Storage**: SQLite (facts) + ChromaDB (embeddings) + NetworkX (graph)

**TTL**: Permanent (with confidence decay)

#### Components

##### 3a. Facts Database

```python
@dataclass
class Fact:
    id: str                          # UUID
    content: str                     # The fact itself
    category: str                    # user/project/preference/skill/general

    # Confidence tracking
    confidence: float                # 0.0 to 1.0
    times_reinforced: int            # How often confirmed
    times_contradicted: int          # How often disputed

    # Provenance
    source_type: str                 # explicit/inferred/observed
    source_episode_id: Optional[str] # Where learned
    source_timestamp: datetime       # When learned

    # Access patterns
    times_accessed: int              # Retrieval count
    last_accessed: Optional[datetime]

    # Metadata
    user_id: str
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    # Embedding
    embedding: list[float]
```

##### 3b. Knowledge Graph

```python
@dataclass
class Entity:
    name: str                        # Unique identifier
    type: str                        # person/project/tool/concept/language
    attributes: dict[str, Any]       # Flexible properties
    created_at: datetime
    updated_at: datetime

@dataclass
class Relationship:
    source: str                      # Entity name
    target: str                      # Entity name
    type: str                        # prefers/uses/builds/knows/works_with
    weight: float                    # Strength of relationship
    source_episode_id: Optional[str] # Where learned
    created_at: datetime
```

##### Graph Schema Visualization

```
ENTITY TYPES:
┌─────────────────────────────────────────────────────────────────┐
│  User          Project        Tool           Concept            │
│  • name        • name         • name         • name             │
│  • skill_level • language     • version      • domain           │
│  • preferences • framework    • category     • complexity       │
└─────────────────────────────────────────────────────────────────┘

RELATIONSHIP TYPES:
┌─────────────────────────────────────────────────────────────────┐
│  prefers      uses           builds         knows               │
│  works_with   created        learned        depends_on          │
│  related_to   part_of        instance_of    similar_to          │
└─────────────────────────────────────────────────────────────────┘

EXAMPLE GRAPH:
                    ┌──────────────┐
                    │   Winston    │
                    │   (User)     │
                    └──────┬───────┘
                           │
         ┌─────────────────┼─────────────────┐
         │ prefers         │ builds          │ knows
         ▼                 ▼                 ▼
  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
  │ TypeScript  │   │  Emperor    │   │   Python    │
  │ (Language)  │   │ (Project)   │   │ (Language)  │
  └─────────────┘   └──────┬──────┘   └─────────────┘
                           │
              ┌────────────┼────────────┐
              │ uses       │ uses       │ has_component
              ▼            ▼            ▼
       ┌──────────┐ ┌──────────┐ ┌──────────────┐
       │  Tauri   │ │  React   │ │ Orchestrator │
       │ (Tool)   │ │ (Tool)   │ │ (Concept)    │
       └──────────┘ └──────────┘ └──────────────┘
```

#### Key Operations

| Operation | Description | Latency Target |
|-----------|-------------|----------------|
| `store_fact(content, category)` | Store new fact | < 50ms |
| `search(query, limit)` | Semantic search | < 30ms |
| `get_by_category(category)` | Filter by type | < 20ms |
| `update_confidence(fact_id, delta)` | Adjust confidence | < 10ms |
| `graph.add_entity(entity)` | Add graph node | < 10ms |
| `graph.add_relationship(rel)` | Add graph edge | < 10ms |
| `graph.traverse(entities, depth)` | Graph search | < 50ms |

---

### Layer 4: Procedural Memory

**Purpose**: Store learned workflows, patterns, and behavioral rules.

**Storage**: SQLite

**TTL**: Permanent (with success-rate tracking)

#### Schema

```python
@dataclass
class Procedure:
    id: str                          # UUID

    # Trigger conditions
    trigger: str                     # Natural language trigger
    trigger_patterns: list[str]      # Regex patterns
    conditions: list[str]            # Required context conditions

    # Steps
    steps: list[str]                 # Ordered actions
    step_details: list[dict]         # Detailed step info

    # Learning source
    learned_from: list[str]          # Episode IDs
    first_observed: datetime

    # Usage statistics
    times_used: int
    success_count: int
    failure_count: int
    last_used: Optional[datetime]

    # User control
    user_approved: bool              # Explicitly approved
    user_modified: bool              # User edited the steps

    # Metadata
    user_id: str
    category: str                    # deploy/test/commit/review/etc
    created_at: datetime
    updated_at: datetime

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0
```

#### Example Procedures

```python
# Learned deployment workflow
Procedure(
    id="proc_001",
    trigger="deploy to production",
    trigger_patterns=[
        r"deploy.*prod",
        r"ship.*production",
        r"release.*live",
    ],
    conditions=[
        "project has tests",
        "on main branch",
        "all tests passing",
    ],
    steps=[
        "Run full test suite",
        "Build production bundle",
        "Run security scan",
        "Deploy to staging first",
        "Verify staging",
        "Deploy to production",
        "Verify production",
        "Notify team",
    ],
    times_used=12,
    success_count=11,
    failure_count=1,
    user_approved=True,
)

# Learned code review preference
Procedure(
    id="proc_002",
    trigger="review code",
    trigger_patterns=[
        r"review.*code",
        r"check.*changes",
        r"look at.*pr",
    ],
    conditions=[],
    steps=[
        "Check for TypeScript errors first",
        "Look for security issues",
        "Review logic correctness",
        "Check test coverage",
        "Suggest improvements",
    ],
    times_used=8,
    success_count=8,
    failure_count=0,
    user_approved=False,  # Inferred, not confirmed
)
```

#### Key Operations

| Operation | Description | Latency Target |
|-----------|-------------|----------------|
| `add_or_reinforce(pattern)` | Store/reinforce procedure | < 20ms |
| `match(query, context)` | Find applicable procedures | < 30ms |
| `record_usage(proc_id, success)` | Track outcome | < 10ms |
| `get_by_category(category)` | Filter by type | < 20ms |
| `get_suggestions(context)` | Proactive suggestions | < 50ms |

---

### Layer 5: Meta-Memory

**Purpose**: Track confidence, provenance, and memory health.

**Storage**: SQLite

**TTL**: Permanent

#### Schema

```python
@dataclass
class MemoryProvenance:
    memory_id: str                   # ID of the memory
    memory_type: str                 # fact/episode/procedure

    # Source tracking
    source_type: str                 # explicit/inferred/observed/extracted
    source_id: Optional[str]         # Episode or conversation ID
    source_timestamp: datetime

    # Confidence tracking
    initial_confidence: float
    current_confidence: float
    confidence_history: list[dict]   # [{timestamp, confidence, reason}]

    # Contradiction tracking
    contradictions: list[dict]       # [{timestamp, conflicting_info, resolution}]

    # Access tracking
    access_count: int
    last_accessed: Optional[datetime]
    access_history: list[datetime]   # Last N accesses

    # Lifecycle
    created_at: datetime
    updated_at: datetime
    flagged_for_review: bool
    review_reason: Optional[str]

@dataclass
class MemoryAccessLog:
    id: str
    memory_id: str
    memory_type: str
    access_type: str                 # read/write/delete/decay
    query: Optional[str]             # What triggered access
    agent_id: Optional[str]          # Which agent accessed
    timestamp: datetime
```

#### Confidence Decay Formula

```python
def calculate_confidence_decay(
    initial_confidence: float,
    days_since_reinforcement: int,
    times_reinforced: int,
    times_accessed: int,
) -> float:
    """
    Confidence decays over time but is boosted by reinforcement and access.

    Formula:
    confidence = initial * decay_factor * reinforcement_boost * access_boost

    Where:
    - decay_factor = 0.99 ^ days (slow decay)
    - reinforcement_boost = 1 + (0.1 * times_reinforced)  (max 2.0)
    - access_boost = 1 + (0.05 * times_accessed)  (max 1.5)
    """
    decay_factor = 0.99 ** days_since_reinforcement
    reinforcement_boost = min(2.0, 1 + (0.1 * times_reinforced))
    access_boost = min(1.5, 1 + (0.05 * times_accessed))

    confidence = initial_confidence * decay_factor * reinforcement_boost * access_boost
    return min(1.0, max(0.0, confidence))  # Clamp to [0, 1]
```

#### Key Operations

| Operation | Description | Latency Target |
|-----------|-------------|----------------|
| `track_provenance(memory_id, source)` | Record source | < 10ms |
| `get_confidence(memory_id)` | Get current confidence | < 5ms |
| `reinforce(memory_id)` | Boost confidence | < 10ms |
| `record_contradiction(memory_id, info)` | Log conflict | < 10ms |
| `flag_for_review(memory_id, reason)` | Mark for user review | < 10ms |
| `get_stale_memories(threshold)` | Find low-confidence | < 50ms |
| `decay_all(factor)` | Batch confidence decay | < 500ms |

---

## Consolidation Engine

### Purpose

Background process that maintains memory health, similar to human sleep:
- Extract lasting facts from episodes
- Detect and store procedural patterns
- Decay unreinforced memories
- Resolve contradictions
- Compress old episodes

### Consolidation Jobs

```python
class ConsolidationEngine:
    """
    Background memory maintenance.

    Runs periodically (default: every 24 hours) or on-demand.
    """

    async def run_full_consolidation(self) -> ConsolidationReport:
        """Run all consolidation tasks."""
        report = ConsolidationReport()

        # 1. Episodic → Semantic extraction
        report.facts_extracted = await self._extract_facts_from_episodes()

        # 2. Entity and relationship extraction
        report.entities_added = await self._update_knowledge_graph()

        # 3. Pattern detection → Procedural
        report.procedures_learned = await self._detect_procedures()

        # 4. Confidence decay
        report.memories_decayed = await self._decay_stale_memories()

        # 5. Contradiction resolution
        report.contradictions_resolved = await self._resolve_contradictions()

        # 6. Episode compression
        report.episodes_compressed = await self._compress_old_episodes()

        # 7. Cleanup
        report.memories_deleted = await self._delete_forgotten_memories()

        return report
```

### Job Specifications

#### 1. Fact Extraction

```python
async def _extract_facts_from_episodes(
    self,
    lookback_hours: int = 24,
) -> int:
    """
    Extract lasting facts from recent conversations.

    Uses LLM to identify facts worth remembering.
    """
    # Get recent episodes not yet processed
    episodes = await self.episodic.get_unprocessed(hours=lookback_hours)

    facts_count = 0
    for episode in episodes:
        # LLM extraction prompt
        prompt = f"""
        Extract facts worth remembering from this conversation.

        Conversation:
        {episode.full_transcript}

        Return JSON array of facts:
        [
            {{"content": "fact text", "category": "user|project|preference|skill", "confidence": 0.0-1.0}}
        ]

        Only include facts that would be useful in future conversations.
        """

        facts = await self.llm.extract(prompt)

        for fact in facts:
            await self.semantic.store_fact(
                content=fact["content"],
                category=fact["category"],
                confidence=fact["confidence"],
                source_episode_id=episode.id,
            )
            facts_count += 1

        # Mark episode as processed
        await self.episodic.mark_processed(episode.id)

    return facts_count
```

#### 2. Pattern Detection

```python
async def _detect_procedures(
    self,
    min_occurrences: int = 2,
) -> int:
    """
    Detect repeated workflows across episodes.
    """
    # Get recent episodes
    episodes = await self.episodic.get_recent(days=7)

    # Extract action sequences
    sequences = []
    for episode in episodes:
        actions = await self._extract_actions(episode)
        sequences.append({
            "episode_id": episode.id,
            "actions": actions,
        })

    # Find common patterns
    patterns = self._find_common_subsequences(sequences, min_occurrences)

    procedures_count = 0
    for pattern in patterns:
        await self.procedural.add_or_reinforce({
            "trigger": pattern["trigger"],
            "steps": pattern["steps"],
            "learned_from": pattern["episode_ids"],
        })
        procedures_count += 1

    return procedures_count
```

#### 3. Confidence Decay

```python
async def _decay_stale_memories(
    self,
    decay_factor: float = 0.95,
    min_confidence: float = 0.1,
) -> int:
    """
    Reduce confidence of unreinforced memories.
    """
    # Get all memories not accessed recently
    stale_memories = await self.meta.get_unreinforced(days=7)

    decayed_count = 0
    for memory in stale_memories:
        new_confidence = memory.confidence * decay_factor

        if new_confidence < min_confidence:
            # Flag for potential deletion
            await self.meta.flag_for_review(
                memory.id,
                reason="confidence_below_threshold"
            )
        else:
            await self.meta.update_confidence(memory.id, new_confidence)

        decayed_count += 1

    return decayed_count
```

#### 4. Episode Compression

```python
async def _compress_old_episodes(
    self,
    age_days: int = 30,
) -> int:
    """
    Summarize old episodes, archive full transcripts.
    """
    old_episodes = await self.episodic.get_older_than(days=age_days)

    compressed_count = 0
    for episode in old_episodes:
        if episode.is_compressed:
            continue

        # Generate detailed summary
        summary = await self.llm.summarize(
            episode.full_transcript,
            include_key_decisions=True,
            include_outcomes=True,
        )

        # Archive full transcript
        await self.archive.store(
            episode_id=episode.id,
            transcript=episode.full_transcript,
        )

        # Update episode with summary only
        await self.episodic.compress(
            episode_id=episode.id,
            summary=summary,
        )

        compressed_count += 1

    return compressed_count
```

### Scheduling

```python
# Consolidation schedule
CONSOLIDATION_CONFIG = {
    "full_consolidation": {
        "interval": "24h",
        "preferred_time": "03:00",  # Run at 3 AM
    },
    "quick_decay": {
        "interval": "6h",
    },
    "pattern_detection": {
        "interval": "12h",
    },
}
```

---

## Retrieval System

### Hybrid Retrieval Pipeline

```python
class HybridRetriever:
    """
    Multi-source, multi-method retrieval.
    """

    async def retrieve(
        self,
        query: str,
        user_id: str,
        context: Optional[dict] = None,
        config: Optional[RetrievalConfig] = None,
    ) -> MemoryBundle:
        """
        Retrieve relevant memories from all layers.
        """
        config = config or RetrievalConfig()

        # Parallel retrieval from all sources
        results = await asyncio.gather(
            self._retrieve_semantic(query, user_id, config),
            self._retrieve_episodic(query, user_id, config),
            self._retrieve_graph(query, config),
            self._retrieve_procedural(query, context, config),
            self._get_user_profile(user_id),
        )

        semantic_facts, episodes, graph_context, procedures, profile = results

        # Filter by confidence
        semantic_facts = await self._filter_by_confidence(
            semantic_facts,
            threshold=config.confidence_threshold,
        )

        # Re-rank results
        ranked_facts = await self._rerank(
            query,
            semantic_facts,
            method=config.rerank_method,
        )

        # Build memory bundle
        bundle = MemoryBundle(
            user_profile=profile,
            semantic_facts=ranked_facts[:config.max_facts],
            episodic_memories=episodes[:config.max_episodes],
            graph_context=graph_context,
            procedural_matches=procedures[:config.max_procedures],
        )

        # Record access for meta-memory
        await self._record_access(query, bundle)

        return bundle
```

### Retrieval Methods

```python
@dataclass
class RetrievalConfig:
    # Limits
    max_facts: int = 10
    max_episodes: int = 5
    max_procedures: int = 3

    # Filtering
    confidence_threshold: float = 0.3
    recency_weight: float = 0.2

    # Re-ranking
    rerank_method: str = "rrf"  # "rrf", "cross_encoder", "none"

    # Sources to include
    include_semantic: bool = True
    include_episodic: bool = True
    include_graph: bool = True
    include_procedural: bool = True
```

### Reciprocal Rank Fusion (RRF)

```python
def reciprocal_rank_fusion(
    ranked_lists: list[list[dict]],
    k: int = 60,
) -> list[dict]:
    """
    Combine multiple ranked lists using RRF.

    RRF score = sum(1 / (k + rank_i)) for each list
    """
    scores = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list):
            item_id = item["id"]
            if item_id not in scores:
                scores[item_id] = {"item": item, "score": 0}
            scores[item_id]["score"] += 1 / (k + rank + 1)

    # Sort by combined score
    combined = sorted(
        scores.values(),
        key=lambda x: x["score"],
        reverse=True,
    )

    return [x["item"] for x in combined]
```

---

## Extraction Pipeline

### Fact Extraction

```python
class FactExtractor:
    """
    Extract facts from conversations using LLM.
    """

    EXTRACTION_PROMPT = """
    Analyze this conversation and extract facts worth remembering.

    Focus on:
    - User preferences and opinions
    - Project details and decisions
    - Technical choices and rationale
    - Personal information shared
    - Learned skills or knowledge

    Conversation:
    {conversation}

    Return JSON:
    {{
        "facts": [
            {{
                "content": "The fact in clear language",
                "category": "user|project|preference|skill|general",
                "confidence": 0.0-1.0,
                "reasoning": "Why this is worth remembering"
            }}
        ]
    }}

    Only extract facts that would be useful in future conversations.
    Skip trivial or obvious information.
    """

    async def extract(
        self,
        conversation: list[dict[str, str]],
    ) -> list[dict]:
        """Extract facts from a conversation."""
        conv_text = self._format_conversation(conversation)

        response = await self.llm.generate(
            self.EXTRACTION_PROMPT.format(conversation=conv_text),
            response_format="json",
        )

        return response.get("facts", [])
```

### Entity Extraction

```python
class EntityExtractor:
    """
    Extract entities and relationships for knowledge graph.
    """

    ENTITY_PROMPT = """
    Extract entities and their relationships from this conversation.

    Entity types: person, project, tool, language, concept, organization

    Relationship types: prefers, uses, builds, knows, works_with, depends_on

    Conversation:
    {conversation}

    Return JSON:
    {{
        "entities": [
            {{"name": "Entity name", "type": "entity_type", "attributes": {{}}}}
        ],
        "relationships": [
            {{"source": "entity1", "target": "entity2", "type": "relationship_type"}}
        ]
    }}
    """

    async def extract(
        self,
        conversation: list[dict[str, str]],
    ) -> tuple[list[dict], list[dict]]:
        """Extract entities and relationships."""
        conv_text = self._format_conversation(conversation)

        response = await self.llm.generate(
            self.ENTITY_PROMPT.format(conversation=conv_text),
            response_format="json",
        )

        return response.get("entities", []), response.get("relationships", [])
```

### Pattern Detection

```python
class PatternDetector:
    """
    Detect procedural patterns from conversation history.
    """

    async def detect(
        self,
        episodes: list[Episode],
        min_occurrences: int = 2,
    ) -> list[dict]:
        """
        Find repeated action patterns across episodes.
        """
        # Extract action sequences from each episode
        action_sequences = []
        for episode in episodes:
            actions = await self._extract_actions(episode)
            action_sequences.append({
                "episode_id": episode.id,
                "actions": actions,
            })

        # Find common subsequences
        patterns = self._find_common_patterns(
            action_sequences,
            min_occurrences,
        )

        # Convert to procedure format
        procedures = []
        for pattern in patterns:
            procedures.append({
                "trigger": pattern["trigger_phrase"],
                "steps": pattern["action_sequence"],
                "learned_from": pattern["episode_ids"],
                "occurrences": pattern["count"],
            })

        return procedures
```

---

## Database Schemas

### SQLite Schema

```sql
-- ============================================
-- SEMANTIC MEMORY TABLES
-- ============================================

CREATE TABLE facts (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    confidence REAL DEFAULT 0.7,

    -- Provenance
    source_type TEXT DEFAULT 'inferred',
    source_episode_id TEXT,

    -- Usage tracking
    times_reinforced INTEGER DEFAULT 0,
    times_accessed INTEGER DEFAULT 0,
    last_accessed TEXT,

    -- Ownership
    user_id TEXT DEFAULT 'default',

    -- Timestamps
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    FOREIGN KEY (source_episode_id) REFERENCES episodes(id)
);

CREATE INDEX idx_facts_category ON facts(category);
CREATE INDEX idx_facts_user ON facts(user_id);
CREATE INDEX idx_facts_confidence ON facts(confidence);

CREATE TABLE user_profiles (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    skill_level TEXT,
    preferences TEXT,  -- JSON
    timezone TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- ============================================
-- PROCEDURAL MEMORY TABLES
-- ============================================

CREATE TABLE procedures (
    id TEXT PRIMARY KEY,

    -- Trigger
    trigger TEXT NOT NULL,
    trigger_patterns TEXT,  -- JSON array of regex
    conditions TEXT,        -- JSON array

    -- Steps
    steps TEXT NOT NULL,    -- JSON array

    -- Learning
    learned_from TEXT,      -- JSON array of episode IDs

    -- Statistics
    times_used INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    last_used TEXT,

    -- User control
    user_approved INTEGER DEFAULT 0,
    user_modified INTEGER DEFAULT 0,

    -- Ownership
    user_id TEXT DEFAULT 'default',
    category TEXT,

    -- Timestamps
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_procedures_user ON procedures(user_id);
CREATE INDEX idx_procedures_category ON procedures(category);

-- ============================================
-- META-MEMORY TABLES
-- ============================================

CREATE TABLE memory_provenance (
    memory_id TEXT PRIMARY KEY,
    memory_type TEXT NOT NULL,  -- fact/episode/procedure

    -- Source
    source_type TEXT NOT NULL,
    source_id TEXT,
    source_timestamp TEXT,

    -- Confidence history
    initial_confidence REAL,
    current_confidence REAL,
    confidence_history TEXT,  -- JSON array

    -- Contradictions
    contradictions TEXT,  -- JSON array

    -- Flags
    flagged_for_review INTEGER DEFAULT 0,
    review_reason TEXT,

    -- Timestamps
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE memory_access_log (
    id TEXT PRIMARY KEY,
    memory_id TEXT NOT NULL,
    memory_type TEXT NOT NULL,
    access_type TEXT NOT NULL,  -- read/write/delete/decay
    query TEXT,
    agent_id TEXT,
    timestamp TEXT NOT NULL
);

CREATE INDEX idx_access_log_memory ON memory_access_log(memory_id);
CREATE INDEX idx_access_log_timestamp ON memory_access_log(timestamp);

-- ============================================
-- CONSOLIDATION TABLES
-- ============================================

CREATE TABLE consolidation_runs (
    id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT DEFAULT 'running',  -- running/completed/failed

    -- Results
    facts_extracted INTEGER DEFAULT 0,
    entities_added INTEGER DEFAULT 0,
    procedures_learned INTEGER DEFAULT 0,
    memories_decayed INTEGER DEFAULT 0,
    contradictions_resolved INTEGER DEFAULT 0,
    episodes_compressed INTEGER DEFAULT 0,
    memories_deleted INTEGER DEFAULT 0,

    -- Error info
    error_message TEXT
);
```

---

## API Interface

### Main Interface

```python
class CognitiveMemorySystem:
    """
    Main interface for the cognitive memory system.
    """

    # =========== REMEMBER ===========

    async def remember_conversation(
        self,
        conversation: list[dict[str, str]],
        session_id: str,
        user_id: str,
        auto_extract: bool = True,
    ) -> RememberResult:
        """Process and store a conversation."""
        pass

    async def remember_fact(
        self,
        content: str,
        category: str = "general",
        confidence: float = 0.8,
        user_id: str = "default",
    ) -> str:
        """Explicitly store a fact."""
        pass

    async def remember_procedure(
        self,
        trigger: str,
        steps: list[str],
        user_id: str = "default",
    ) -> str:
        """Explicitly store a procedure."""
        pass

    # =========== RECALL ===========

    async def recall(
        self,
        query: str,
        user_id: str,
        context: Optional[dict] = None,
        config: Optional[RetrievalConfig] = None,
    ) -> MemoryBundle:
        """Retrieve relevant memories."""
        pass

    async def recall_user_profile(
        self,
        user_id: str,
    ) -> dict[str, Any]:
        """Get user profile."""
        pass

    async def recall_similar_episodes(
        self,
        query: str,
        user_id: str,
        limit: int = 5,
    ) -> list[Episode]:
        """Find similar past conversations."""
        pass

    async def recall_procedures_for(
        self,
        query: str,
        context: dict,
        user_id: str,
    ) -> list[Procedure]:
        """Find applicable workflows."""
        pass

    # =========== UPDATE ===========

    async def update_user_profile(
        self,
        user_id: str,
        updates: dict[str, Any],
    ) -> None:
        """Update user profile."""
        pass

    async def reinforce_fact(
        self,
        fact_id: str,
    ) -> None:
        """Confirm a fact is still true."""
        pass

    async def contradict_fact(
        self,
        fact_id: str,
        new_info: str,
        resolution: str = "flag",
    ) -> None:
        """Handle fact contradiction."""
        pass

    async def approve_procedure(
        self,
        procedure_id: str,
    ) -> None:
        """User approves a learned procedure."""
        pass

    # =========== FORGET ===========

    async def forget_fact(
        self,
        fact_id: str,
    ) -> None:
        """Delete a fact."""
        pass

    async def forget_procedure(
        self,
        procedure_id: str,
    ) -> None:
        """Delete a procedure."""
        pass

    # =========== MAINTENANCE ===========

    async def consolidate(
        self,
    ) -> ConsolidationReport:
        """Run memory consolidation."""
        pass

    async def get_memory_stats(
        self,
    ) -> MemoryStats:
        """Get system statistics."""
        pass

    async def get_stale_memories(
        self,
        confidence_threshold: float = 0.3,
    ) -> list[dict]:
        """Get memories needing review."""
        pass
```

### Integration with Orchestrator

```python
# In orchestrator/orchestrator.py

class Orchestrator:
    def __init__(self):
        # ... existing init ...
        self._memory = get_cognitive_memory()

    async def process(self, message: str, ...) -> OrchestratorResult:
        # 1. Retrieve memory context
        memory_bundle = await self._memory.recall(
            query=message,
            user_id=self._user_id,
            context={"session_id": self._session_id},
        )

        # 2. Build prompt with memory
        prompt = self._build_prompt(
            message=message,
            memory=memory_bundle,
        )

        # 3. Get response
        response = await self._get_response(prompt)

        # 4. Store conversation
        await self._memory.remember_conversation(
            conversation=[
                {"role": "user", "content": message},
                {"role": "assistant", "content": response},
            ],
            session_id=self._session_id,
            user_id=self._user_id,
        )

        return OrchestratorResult(content=response, ...)
```

---

## File Structure

```
backend/memory/
├── __init__.py                    # Public exports
├── cognitive_memory.py            # Main interface (CognitiveMemorySystem)
│
├── layers/
│   ├── __init__.py
│   ├── working_memory.py          # Layer 1: Session state
│   ├── episodic_memory.py         # Layer 2: Experiences
│   ├── semantic_memory.py         # Layer 3: Facts + embeddings
│   ├── knowledge_graph.py         # Layer 3b: Graph storage
│   ├── procedural_memory.py       # Layer 4: Workflows
│   └── meta_memory.py             # Layer 5: Provenance + confidence
│
├── retrieval/
│   ├── __init__.py
│   ├── hybrid_retriever.py        # Multi-source retrieval
│   ├── reranker.py                # Result re-ranking (RRF, cross-encoder)
│   └── config.py                  # Retrieval configuration
│
├── extraction/
│   ├── __init__.py
│   ├── fact_extractor.py          # LLM-based fact extraction
│   ├── entity_extractor.py        # Entity + relationship extraction
│   └── pattern_detector.py        # Procedural pattern detection
│
├── consolidation/
│   ├── __init__.py
│   ├── engine.py                  # Consolidation engine
│   ├── jobs.py                    # Individual consolidation jobs
│   └── scheduler.py               # Background scheduler
│
├── models/
│   ├── __init__.py
│   ├── episode.py                 # Episode dataclass
│   ├── fact.py                    # Fact dataclass
│   ├── procedure.py               # Procedure dataclass
│   ├── entity.py                  # Entity + Relationship dataclasses
│   └── bundle.py                  # MemoryBundle dataclass
│
├── storage/
│   ├── __init__.py
│   ├── sqlite_store.py            # SQLite operations
│   ├── vector_store.py            # ChromaDB operations
│   └── graph_store.py             # NetworkX operations
│
└── utils/
    ├── __init__.py
    ├── embeddings.py              # Embedding generation
    └── prompts.py                 # LLM prompts for extraction
```

---

## Implementation Guide

### Phase 1: Core Infrastructure (Week 1)

1. **Set up storage layers**
   - SQLite database with schema
   - ChromaDB collection
   - NetworkX graph

2. **Implement basic models**
   - Episode, Fact, Procedure dataclasses
   - MemoryBundle

3. **Build working memory**
   - In-memory dict (Redis optional)
   - Conversation buffer

### Phase 2: Memory Layers (Week 1-2)

4. **Implement episodic memory**
   - Store conversations
   - Semantic search

5. **Implement semantic memory**
   - Fact storage with embeddings
   - Knowledge graph CRUD

6. **Implement procedural memory**
   - Pattern storage
   - Matching logic

7. **Implement meta-memory**
   - Provenance tracking
   - Confidence management

### Phase 3: Retrieval & Extraction (Week 2)

8. **Build hybrid retriever**
   - Multi-source retrieval
   - RRF ranking

9. **Implement extractors**
   - Fact extraction (LLM)
   - Entity extraction (LLM)
   - Pattern detection

### Phase 4: Consolidation & Integration (Week 2-3)

10. **Build consolidation engine**
    - Background jobs
    - Scheduler

11. **Integrate with orchestrator**
    - Memory retrieval in process()
    - Conversation storage

12. **Testing & refinement**
    - Unit tests
    - Integration tests
    - Performance tuning

---

## Dependencies

### Required

```
# requirements.txt additions for cognitive memory

# Vector database
chromadb>=0.4.0

# Embeddings
sentence-transformers>=2.2.0

# Graph
networkx>=3.0

# Background tasks (optional, for consolidation scheduler)
apscheduler>=3.10.0
```

### Optional

```
# Redis for working memory
redis>=4.5.0

# Better graph database (if NetworkX isn't enough)
neo4j>=5.0.0

# Cross-encoder re-ranking
transformers>=4.30.0
```

### Installation

```bash
pip install chromadb sentence-transformers networkx apscheduler
```

---

## Migration from Letta

When ready to migrate from Letta to custom:

### Step 1: Export Letta Memories

```python
# Export core memory blocks
core_memory = letta_agent.get_core_memory()
user_block = core_memory.get_block("human")
persona_block = core_memory.get_block("persona")

# Export archival memory
archival = letta_agent.get_archival_memory(limit=1000)
```

### Step 2: Import to Custom System

```python
# Import user profile
await cognitive_memory.update_user_profile(
    user_id="default",
    updates=parse_user_block(user_block),
)

# Import archival as facts
for memory in archival:
    await cognitive_memory.remember_fact(
        content=memory["content"],
        category="imported",
        confidence=0.8,
    )
```

### Step 3: Update Orchestrator

```python
# Change import
# from letta import Letta
from memory import get_cognitive_memory

# Update init
# self._letta = Letta()
self._memory = get_cognitive_memory()

# Update recall
# results = self._letta.search(query)
bundle = await self._memory.recall(query, user_id)
```

---

## Notes

### When to Build This

- When Letta's paradigm doesn't fit Emperor's architecture
- When you need knowledge graph relationships
- When you need procedural pattern learning
- When you want full control over memory behavior
- When you understand exactly what memory features you need

### When to Stick with Letta

- Memory isn't your core differentiator
- You want to ship faster
- Letta's features are sufficient
- You prefer battle-tested solutions

---

*Document Version: 1.0*
*Created: 2024-12-26*
*Status: Specification for future implementation*
*Current Implementation: Letta*
