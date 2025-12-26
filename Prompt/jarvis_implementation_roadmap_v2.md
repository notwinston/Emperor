# Jarvis AI Assistant - Implementation Roadmap v2

## Complete Feature-by-Feature Development Guide

High-level implementation roadmap for building the Jarvis AI Assistant. Uses the Tauri create script for scaffolding.

---

## Table of Contents

1. [Part 1: Project Scaffolding](#part-1-project-scaffolding)
2. [Part 2: Frontend Customization](#part-2-frontend-customization)
3. [Part 3: Python Backend Foundation](#part-3-python-backend-foundation)
4. [Part 4: WebSocket Communication](#part-4-websocket-communication)
5. [Part 5: Claude Code Bridge (Max Billing)](#part-5-claude-code-bridge-max-billing)
6. [Part 6: Event Bus Implementation](#part-6-event-bus-implementation)
7. [Part 7: Orchestrator Agent](#part-7-orchestrator-agent)
8. [Part 8: Memory System](#part-8-memory-system)
9. [Part 9: Domain Leads Integration](#part-9-domain-leads-integration)
10. [Part 10: Tool System](#part-10-tool-system)
11. [Part 11: Voice Integration](#part-11-voice-integration)
12. [Part 12: Advanced UI Components](#part-12-advanced-ui-components)
13. [Part 13: Security & Permissions](#part-13-security--permissions)
14. [Part 14: Testing & Deployment](#part-14-testing--deployment)

---

# Part 1: Project Scaffolding

## Prerequisites

Ensure the following are installed:
- **Node.js 18+** — JavaScript runtime
- **Rust** — Required for Tauri backend
- **pnpm** — Package manager (faster than npm)

---

## Step 1.1: Create Project with Tauri

Run the Tauri create script and select the following options when prompted:

| Prompt | Selection |
|--------|-----------|
| Project name | Your choice (e.g., `jarvis` or `emperor`) |
| Identifier | `com.yourname.assistant` |
| Package manager | `pnpm` |
| UI template | `React` |
| UI flavor | `TypeScript` |

This scaffolds a complete Tauri + React + TypeScript project with all config files pre-generated.

---

## Step 1.2: Verify Scaffolding

Enter the project directory, install dependencies, and run a test build to ensure everything works before customizing.

**Expected result:** A native window opens with the default Tauri + React template.

---

## Step 1.3: Create Backend Directory Structure

Create the following folder structure for the Python backend:

```
backend/
├── api/              # FastAPI routes and WebSocket handlers
├── config/           # Settings and logging configuration
├── orchestrator/     # Main Jarvis orchestrator agent
├── process_manager/  # Agent lifecycle and spawning
├── memory/           # Short-term, long-term, and RAG memory
├── leads/            # Domain lead agents (Code, Research, Task)
├── workers/          # Worker agents (Programmer, Researcher, etc.)
├── tools/            # Tool definitions and executors
└── voice/            # Speech-to-text and text-to-speech
```

Also create data directories:

```
data/
├── chroma/           # Vector database storage
├── logs/             # Application logs
└── whisper/          # Voice model cache
```

And a scripts directory for development scripts.

---

## Step 1.4: Create Frontend Directory Structure

Extend the scaffolded `src/` folder with:

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

Install the following categories of packages:

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

## Step 1.6: Initialize Tailwind CSS

Run the Tailwind init command to generate `tailwind.config.js` and `postcss.config.js`.

---

## Step 1.7: Checkpoint

Test that the app runs with:
- Tailwind styles applied
- Dark mode enabled
- All dependencies installed without errors

---

# Part 2: Frontend Customization

## Step 2.1: Configure Tailwind

Update `tailwind.config.js` with:
- Dark mode set to class-based
- Content paths for all TSX files
- Extended color palette using CSS variables for theming
- Custom colors: background, foreground, primary, secondary, muted, accent, destructive, border, input, ring
- Custom border radius values
- Animation keyframes for subtle pulse effect
- Tailwind animate plugin

---

## Step 2.2: Create Base CSS

Replace the default CSS with:
- Tailwind directives (@tailwind base, components, utilities)
- CSS variables for light and dark themes
- Base layer styles for border colors and body
- Custom scrollbar styling for dark mode
- Full-height layout for Tauri window
- Drag region classes for window titlebar
- User selection prevention (except inputs)

---

## Step 2.3: Update HTML Template

Modify `index.html` to:
- Set `class="dark"` on html element for dark mode
- Update title to "Jarvis AI Assistant"
- Update favicon reference

---

## Step 2.4: Configure TypeScript

Update `tsconfig.json` to add:
- Base URL set to project root
- Path alias: `@/*` maps to `./src/*`
- This enables imports like `import { Button } from "@/components/ui/button"`

---

## Step 2.5: Configure Vite

Update `vite.config.ts` to:
- Add path alias resolution matching TypeScript config
- Set server port (e.g., 1420 for Tauri)
- Configure build targets for Tauri platforms
- Set environment variable prefixes

---

## Step 2.6: Configure Tauri

Update `src-tauri/tauri.conf.json` with:
- Product name and identifier
- Window dimensions (width: 440, height: 720)
- Minimum window size (380x500)
- Window starts hidden (shows after setup)
- Dev server URL matching Vite port
- Bundle settings for all platforms

---

## Step 2.7: Create Utility Functions

Create `src/lib/utils.ts` with:
- `cn()` — Combines clsx and tailwind-merge for conditional classes
- `formatTime()` — Formats Date to HH:MM string
- `generateId()` — Wrapper for crypto.randomUUID()

---

## Step 2.8: Create Type Definitions

Create `src/types/index.ts` defining:

**Message interface:**
- id, role (user/assistant/system), content, timestamp
- Optional metadata (toolCalls, tokens, model, isStreaming)

**ToolCall interface:**
- id, name, input, output, status

**Conversation interface:**
- id, title, createdAt, updatedAt, messageCount

**WSEvent interface:**
- event_id, event_type, source, timestamp, payload

**ConnectionStatus type:**
- "connecting" | "connected" | "disconnected" | "error"

---

## Step 2.9: Create Base UI Components

Create shadcn-style components in `src/components/ui/`:

**Button component:**
- Variants: default, destructive, outline, secondary, ghost, link
- Sizes: default, sm, lg, icon
- Supports asChild prop for composition

**Input component:**
- Styled text input with focus ring
- Supports all native input props

**ScrollArea component:**
- Wraps Radix ScrollArea primitive
- Custom styled scrollbar
- Supports vertical and horizontal orientations

---

## Step 2.10: Create State Store

Create `src/stores/conversationStore.ts` using Zustand:

**State:**
- status: ConnectionStatus
- messages: Message[]
- isTyping: boolean
- conversations: Conversation[]
- currentConversationId: string | null

**Actions:**
- setStatus(status)
- addMessage(message)
- updateMessage(id, content)
- setTyping(isTyping)
- clearMessages()
- setCurrentConversation(id)
- createConversation()

---

## Step 2.11: Create WebSocket Hook

Create `src/hooks/useWebSocket.ts`:

**Configuration:**
- WebSocket URL: ws://localhost:8765/ws
- Reconnect delay: 3 seconds
- Max reconnect attempts: 5

**Features:**
- Auto-connect on mount
- Auto-reconnect on disconnect with exponential backoff
- Message parsing and routing by event_type
- Handles: assistant.message, assistant.typing, error, heartbeat

**Returns:**
- connect() — Manual connect function
- disconnect() — Manual disconnect function
- sendMessage(text) — Send user message

---

## Step 2.12: Create Chat Components

**ChatMessage component (`src/components/ChatMessage.tsx`):**
- Displays single message with avatar
- User messages: right-aligned, primary color
- Assistant messages: left-aligned, secondary color, markdown rendered
- Shows timestamp below content
- Memoized for performance

**ChatPanel component (`src/components/ChatPanel.tsx`):**
- ScrollArea containing message list
- Welcome message when empty
- Typing indicator when assistant is responding
- Input form with mic button, text input, send button
- Auto-scrolls to bottom on new messages
- Auto-focuses input on mount
- Disables input when disconnected

**Sidebar component (`src/components/Sidebar.tsx`):**
- Collapsible (default collapsed)
- Header with app name and toggle button
- New Chat button
- Navigation items: Chat, History, Memory, Settings
- Icons from Lucide React

**StatusBar component (`src/components/StatusBar.tsx`):**
- Displays connection status with colored indicator
- Green: connected, Yellow: connecting, Gray: disconnected, Red: error
- Draggable region for window movement

---

## Step 2.13: Create Main App

Update `src/App.tsx`:
- Wrap with QueryClientProvider
- Layout: Sidebar + Main area
- Main area: StatusBar + ChatPanel
- Full height flex layout

Update `src/main.tsx`:
- Import global CSS
- Render App in StrictMode

---

## Step 2.14: Update Rust Main

Update `src-tauri/src/main.rs`:
- Remove default greet command (or keep for testing)
- Setup hook to show window after initialization
- Basic plugin initialization

---

## Step 2.15: Frontend Checkpoint

Run the app and verify:
- Dark themed window opens
- Sidebar toggles collapse/expand
- Status bar shows "Connecting..." (yellow)
- Chat area shows welcome message
- Input field present (disabled until connected)

---

# Part 3: Python Backend Foundation

## Step 3.1: Initialize Python Environment

In the `backend/` directory:
- Create Python virtual environment (venv)
- Create `requirements.txt` with core dependencies:
  - fastapi, uvicorn[standard], websockets
  - pydantic, pydantic-settings, python-dotenv
  - python-json-logger, anyio

---

## Step 3.2: Create Configuration Module

**`backend/config/__init__.py`:**
- Export settings and logger

**`backend/config/settings.py`:**
- Pydantic Settings class loading from .env
- Fields: app_name, debug, log_level, project_root, data_dir, host, port
- Optional: claude_code_oauth_token
- Auto-creates data directories on init

**`backend/config/logging.py`:**
- Setup function returning configured logger
- Console handler with timestamp format
- Log level from settings

---

## Step 3.3: Create API Types

**`backend/api/types.py`:**
- EventType enum: USER_MESSAGE, ASSISTANT_MESSAGE, ASSISTANT_TYPING, ERROR, HEARTBEAT
- BaseEvent Pydantic model with: event_id (auto UUID), event_type, source, timestamp, payload

---

## Step 3.4: Create WebSocket Manager

**`backend/api/websocket.py`:**
- ConnectionManager class
- Methods: connect(ws), disconnect(ws), send(ws, event), broadcast(event)
- Tracks active connections list
- Logs connection/disconnection counts

---

## Step 3.5: Create Main Application

**`backend/api/main.py`:**
- FastAPI app with lifespan handler
- CORS middleware allowing all origins (dev mode)
- Health check endpoint at `/health`
- WebSocket endpoint at `/ws`
- Message handler routing by event_type
- Sends typing indicator then response
- Placeholder echo response (Claude Code Bridge integration later)

---

## Step 3.6: Create Environment File

**`backend/.env`:**
- DEBUG=true
- LOG_LEVEL=DEBUG
- HOST=127.0.0.1
- PORT=8765
- CLAUDE_CODE_OAUTH_TOKEN=(your token)

---

## Step 3.7: Create Development Script

**`scripts/dev.sh`:**
- Starts Python backend with uvicorn (reload enabled)
- Starts Tauri frontend
- Cleanup on exit (kills backend process)

---

## Step 3.8: Backend Checkpoint

Test full stack:
- Start backend: `python -m api.main` from backend/
- Start frontend: `pnpm tauri dev` from project root
- Verify: Status shows green "Jarvis Online"
- Verify: Messages echo back from backend

---

# Part 4: WebSocket Communication

## Step 4.1: Streaming Response Support

Enhance WebSocket handler to:
- Support chunked/streaming responses
- Send partial messages with `is_streaming: true`
- Include `message_id` for updating existing messages
- Send final chunk with `is_complete: true`

---

## Step 4.2: Message Queue

Implement message queuing:
- Queue messages if processing is ongoing
- Process queue in order
- Prevent race conditions with async locks

---

## Step 4.3: Heartbeat Mechanism

Add bidirectional heartbeat:
- Server sends heartbeat every 30 seconds
- Client responds to keep connection alive
- Detect stale connections and clean up

---

## Step 4.4: Error Recovery

Implement robust error handling:
- Catch and log exceptions in message handlers
- Send error events to client
- Don't crash on malformed messages
- Graceful degradation

---

# Part 5: Claude Code Bridge (Max Billing)

## Step 5.1: OAuth Token Verification

Create `backend/claude_code_bridge.py`:
- Load CLAUDE_CODE_OAUTH_TOKEN from environment
- Verify token is set on initialization
- Verify Claude Code CLI is installed
- Test authentication with simple query

---

## Step 5.2: Query Execution

Implement async query method:
- Build command array with flags: --print, --output-format, --allowedTools, -p
- Spawn subprocess with token in environment
- Capture stdout/stderr
- Parse response (text or JSON)
- Handle timeouts
- Return structured response object

---

## Step 5.3: Agent Spawning

Implement agent spawn method:
- Create meta-prompt instructing Claude Code to use Task tool
- Specify agent type (general-purpose, Explore, Plan, etc.)
- Pass system prompt and task description
- Wait for completion
- Return agent's output

---

## Step 5.4: Parallel Agent Spawning

Implement parallel spawn method:
- Accept list of (task, agent_type) tuples
- Create meta-prompt for multiple Task tool calls
- Instruct Claude Code to spawn all agents in single message
- Collect and return combined results

---

## Step 5.5: Integration with Backend

Update `backend/api/main.py`:
- Import ClaudeCodeBridge
- Initialize bridge on startup
- Route user messages through bridge instead of echo
- Handle bridge errors gracefully
- Add retry logic for rate limits

---

# Part 6: Event Bus Implementation

## Step 6.1: Event Definitions

Create `backend/process_manager/events.py`:
- Define event dataclasses for all event types
- Base Event class with: event_id, event_type, source, timestamp, payload
- Specialized events: SpawnRequest, AgentCompletion, ToolExecution, ApprovalRequest

---

## Step 6.2: Pub/Sub Implementation

Create `backend/process_manager/event_bus.py`:
- EventBus class with channels
- subscribe(channel, callback) — Register handler
- publish(channel, event) — Send to subscribers
- wait_for(channel, timeout) — Blocking wait for event
- Wildcard channel "*" for all events
- Event logging for debugging

---

## Step 6.3: UI Event Streaming

Connect event bus to WebSocket:
- Subscribe to all events
- Forward relevant events to connected clients
- Filter events by relevance (don't send internal events)
- Format events for frontend consumption

---

## Step 6.4: Cross-Agent Communication

Enable agent-to-agent messaging:
- Agents publish to event bus via tool calls
- Process manager routes messages
- Results delivered via callbacks
- Support async and sync patterns

---

# Part 7: Orchestrator Agent

## Step 7.1: System Prompt Design

Create `backend/config/prompts/orchestrator.md`:
- Role definition: Primary AI interface, persistent across sessions
- Core responsibilities: intent understanding, memory access, routing, synthesis
- Delegation protocol: when to handle directly vs delegate
- Tool descriptions for memory and delegation
- Constraints: no direct code execution, no bypassing permissions

---

## Step 7.2: Intent Classification

Implement intent classifier:
- Categories: casual_chat, question, code_task, research_task, file_operation, system_command
- Use Claude to classify ambiguous intents
- Route to appropriate handler based on classification

---

## Step 7.3: Memory Integration

Connect orchestrator to memory system:
- Retrieve relevant context before responding
- Include user profile and preferences
- Include recent conversation history
- Include relevant facts from long-term memory
- Include RAG results if applicable

---

## Step 7.4: Delegation Logic

Implement delegation to domain leads:
- Determine if task requires specialized agent
- Select appropriate lead (Code, Research, Task)
- Format delegation request with context
- Track delegated task status
- Synthesize results when complete

---

## Step 7.5: Response Synthesis

Implement response generation:
- Combine orchestrator reasoning with delegate results
- Format for user consumption
- Include relevant metadata (tools used, time taken)
- Update memory with new information

---

# Part 8: Memory System

## Step 8.1: Database Schema

Create SQLite schema in `backend/memory/schema.sql`:
- **user_profile** table: key-value preferences with source and confidence
- **facts** table: learned facts with category, source, confidence, timestamps
- **conversation_summaries** table: conversation metadata and summaries
- **memory_access_log** table: audit trail for all memory operations

---

## Step 8.2: Short-Term Memory

Create `backend/memory/short_term.py`:
- In-memory storage for current session
- Conversation context (last N messages)
- Active task state
- Pending approvals queue
- Methods: add_message, get_context, clear_session

---

## Step 8.3: Long-Term Memory

Create `backend/memory/long_term.py`:
- SQLAlchemy models matching schema
- CRUD operations for profile and facts
- Search by category, keyword, recency
- Confidence scoring and reinforcement
- Provenance tracking

---

## Step 8.4: Semantic Memory (RAG)

Create `backend/memory/semantic.py`:
- ChromaDB client initialization
- Embedding model setup (sentence-transformers)
- Document indexing with metadata
- Similarity search with filters
- Hybrid search combining structured and semantic

---

## Step 8.5: Memory Interface

Create `backend/memory/interface.py`:
- Unified MemoryInterface class
- remember(content, category, source) — Store new information
- recall(query, memory_types, limit) — Retrieve relevant memories
- forget(memory_id, reason) — Delete memory
- Policy enforcement for writes
- Access logging for all operations

---

# Part 9: Domain Leads Integration

## Step 9.1: Code Lead Setup

Create `backend/leads/code_lead.py`:
- Load prompt from existing `.claude/agents/leads/Code_Lead_Architect.md`
- Configure tools: request_agent_spawn, file operations, Linear integration
- Implement task reception and worker delegation
- Result aggregation and synthesis

---

## Step 9.2: Research Lead Setup

Create `backend/leads/research_lead.py`:
- Load prompt from `.claude/agents/leads/Research_Lead.md`
- Configure tools: web search, document analysis, source management
- Implement research task decomposition
- Citation tracking and synthesis

---

## Step 9.3: Task Lead Setup

Create `backend/leads/task_lead.py`:
- System prompt for automation and workflow tasks
- Configure tools: shell execution, scheduling, monitoring
- Permission enforcement for system operations
- Result reporting

---

## Step 9.4: Worker Spawning

Implement worker management:
- Worker types: Programmer, Researcher, Writer, Reviewer, Documentor
- Spawn via Claude Code Bridge using Task tool
- Pass appropriate prompts and tools
- Collect results via event bus

---

## Step 9.5: Result Aggregation

Implement result handling:
- Receive worker completions via callbacks
- Aggregate multiple worker outputs
- Handle partial failures gracefully
- Report synthesized results to orchestrator

---

# Part 10: Tool System

## Step 10.1: Tool Registry

Create `backend/tools/registry.py`:
- Tool definition schema: name, description, parameters, risk_level
- Register built-in tools
- Support custom tool registration
- Tool discovery for agents

---

## Step 10.2: Permission Checking

Create `backend/tools/permissions.py`:
- Risk levels: low, medium, high
- Permission rules by tool and risk
- User approval workflow for high-risk
- Audit logging of all executions

---

## Step 10.3: File System Tools

Create `backend/tools/filesystem.py`:
- read_file: Read file contents with path validation
- write_file: Write with backup and approval
- list_directory: Directory listing with filters
- Sandboxing to allowed directories

---

## Step 10.4: Shell Tools

Create `backend/tools/shell.py`:
- execute_command: Run shell commands
- Timeout enforcement
- Output capture and streaming
- Command allowlist/blocklist
- Always requires approval

---

## Step 10.5: Tool Execution

Create `backend/tools/executor.py`:
- Execute tool by name with parameters
- Pre-execution permission check
- Execution with timeout
- Result formatting
- Post-execution logging

---

# Part 11: Voice Integration

## Step 11.1: Whisper Setup

Create `backend/voice/stt.py`:
- Load Whisper model (base or small for speed)
- Model caching in data/whisper/
- Transcription function accepting audio bytes
- Language detection (optional)

---

## Step 11.2: Recording Handler

Implement audio recording flow:
- Receive audio chunks from frontend
- Buffer until recording complete
- Process with Whisper
- Return transcription
- Stream partial results if possible

---

## Step 11.3: Frontend Voice UI

Update `src/components/ChatPanel.tsx`:
- Push-to-talk button with states: idle, recording, processing
- Visual feedback during recording (pulsing indicator)
- Display partial transcription
- Send final transcription as message

---

## Step 11.4: Text-to-Speech

Create `backend/voice/tts.py`:
- macOS: Use NSSpeechSynthesizer via subprocess
- Generate speech audio from text
- Support voice selection
- Return audio data or play directly

---

## Step 11.5: Voice Command Handling

Implement voice-specific features:
- Wake word detection (optional, future)
- Barge-in support (interrupt TTS)
- Voice activity detection
- Noise handling

---

# Part 12: Advanced UI Components

## Step 12.1: Task Timeline

Create `src/components/TaskTimeline.tsx`:
- Vertical timeline showing agent activity
- Events: thinking, tool_call, tool_result, delegation, completion
- Expandable event details
- Real-time updates via WebSocket
- Visual distinction by event type

---

## Step 12.2: Memory Manager

Create `src/components/MemoryManager.tsx`:
- Tabbed view: Profile, Facts, Documents
- List memories with search and filter
- View memory details with provenance
- Edit and delete capabilities
- Add new memories manually

---

## Step 12.3: Approval Modal

Create `src/components/ApprovalModal.tsx`:
- Dialog showing pending approval request
- Action description and risk level
- Details of what will happen
- Allow/Deny/Edit buttons
- Timeout countdown
- Queue multiple approvals

---

## Step 12.4: Settings Panel

Create `src/components/SettingsPanel.tsx`:
- Model selection (Sonnet/Opus)
- Voice settings (enable/disable, voice selection)
- Permission defaults (strict/relaxed)
- Memory management (clear, export)
- Connection settings
- Theme toggle (if supporting light mode)

---

## Step 12.5: History View

Create `src/components/HistoryView.tsx`:
- List past conversations with titles and dates
- Search conversations
- Click to load conversation
- Delete conversations
- Export conversation

---

# Part 13: Security & Permissions

## Step 13.1: Permission System

Implement granular permissions:
- Tool-level permissions (per tool risk assessment)
- Category permissions (file, shell, network)
- Per-session vs persistent approvals
- Never-ask-again option for low-risk

---

## Step 13.2: Audit Logging

Create comprehensive audit trail:
- Log all tool executions with inputs/outputs
- Log all memory operations
- Log all agent spawns and completions
- Structured JSON logging
- Configurable retention

---

## Step 13.3: Input Sanitization

Implement security measures:
- Path traversal prevention
- Command injection prevention
- Prompt injection defenses for RAG
- Content length limits
- Rate limiting

---

## Step 13.4: Data Encryption

Protect sensitive data:
- SQLCipher for database encryption
- Encrypt OAuth tokens at rest
- Secure memory for API keys
- Clear sensitive data on shutdown

---

# Part 14: Testing & Deployment

## Step 14.1: Unit Tests

Create tests for:
- Memory operations (CRUD)
- Tool execution (mocked)
- Event bus (pub/sub)
- WebSocket communication
- Message parsing

---

## Step 14.2: Integration Tests

Create tests for:
- Full message flow (user → orchestrator → response)
- Agent delegation and completion
- Memory recall accuracy
- Error handling and recovery

---

## Step 14.3: E2E Tests

Create tests for:
- UI interactions (send message, receive response)
- Voice recording and transcription
- Settings changes
- Connection recovery

---

## Step 14.4: macOS Distribution

Prepare for distribution:
- Code signing with Apple Developer certificate
- Notarization for Gatekeeper
- DMG creation with background and layout
- Auto-update mechanism (Tauri updater plugin)

---

## Step 14.5: Release Process

Document release workflow:
- Version bumping
- Changelog generation
- Build and sign
- Upload to distribution channel
- Update feed for auto-updater

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
│   ├── orchestrator/       # Main agent
│   ├── process_manager/    # Agent spawning
│   ├── memory/             # Memory system
│   ├── leads/              # Domain leads
│   ├── workers/            # Worker agents
│   ├── tools/              # Tool system
│   └── voice/              # Voice features
├── data/                   # Local data storage
└── scripts/                # Development scripts
```

---

*Document Version: 2.1*
*Created: 2025-12-25*
*Type: High-level implementation guide (no code blocks)*
