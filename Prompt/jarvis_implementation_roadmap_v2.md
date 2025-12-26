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
- Retrieves user profile from memory
- Gets relevant conversation history
- Fetches applicable facts
- Includes RAG results if relevant
- Passes context to delegates

---

# Part 9: Memory System

## Steps 9.1-9.5: Memory Implementation

(Same as original - database schema, short-term memory, long-term memory, semantic memory/RAG, memory interface)

Memory is accessible to both CLI orchestrator and SDK agents via tools.

---

# Part 10: Domain Leads (SDK)

Each Lead is an SDK-based agent with specialized tools.

## Step 10.1: Code Lead

Create `backend/leads/code_lead.py`:
- Extends BaseAgent
- System prompt for code architecture decisions
- Tools: file operations, AST parsing, refactoring
- Spawns workers: Programmer, Reviewer, Documentor
- Aggregates worker results

---

## Step 10.2: Research Lead

Create `backend/leads/research_lead.py`:
- Extends BaseAgent
- System prompt for research and analysis
- Tools: web search, document analysis, citation
- Spawns workers: Researcher, Analyst, Writer
- Maintains source tracking

---

## Step 10.3: Task Lead

Create `backend/leads/task_lead.py`:
- Extends BaseAgent
- System prompt for automation and workflows
- Tools: shell execution, scheduling, monitoring
- Spawns workers: Executor, Monitor
- Permission enforcement for system operations

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

---

## Step 10.5: Lead-Worker Communication

Leads spawn and manage workers:
- Create worker instance with context
- Call `worker.run(subtask)`
- Collect results
- Handle failures gracefully
- Aggregate into Lead's response

---

# Part 11: Tool System

## Steps 11.1-11.5: Tool Implementation

(Same as original - tool registry, permission checking, file system tools, shell tools, tool execution)

Tools are used by both:
- CLI orchestrator (via CLI's built-in tools)
- SDK agents (via custom tool implementations)

---

# Part 12: Voice Integration

## Steps 12.1-12.5: Voice Features

(Same as original - Whisper setup, recording handler, frontend voice UI, text-to-speech, voice command handling)

---

# Part 13: Advanced UI Components

## Steps 13.1-13.5: UI Components

(Same as original - task timeline, memory manager, approval modal, settings panel, history view)

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
