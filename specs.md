# Emperor AI Assistant - Frontend Specifications

## Project Overview

Emperor is a premium AI assistant desktop application built with Tauri, React, and TypeScript. The frontend features a luxurious gold and black color scheme with extremely polished UI/UX. The application provides a chat interface with voice input capabilities.

## Architecture

### Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Desktop Shell | Tauri | 2.x |
| Frontend Framework | React | 18.3.x |
| Language | TypeScript | 5.6.x |
| Styling | Tailwind CSS | 4.x |
| State Management | Zustand | 5.x |
| Data Fetching | TanStack React Query | 5.x |
| UI Primitives | Radix UI | Latest |
| Icons | Lucide React | Latest |
| Build Tool | Vite | 6.x |

### Directory Structure

```
Emperor/
├── src/                      # React frontend source
│   ├── components/           # React components
│   │   ├── ui/              # Base UI components (Button, Input, etc.)
│   │   ├── ChatPanel.tsx    # Main chat interface
│   │   ├── ChatMessage.tsx  # Individual message component
│   │   ├── Sidebar.tsx      # Navigation sidebar
│   │   └── StatusBar.tsx    # Connection status bar
│   ├── hooks/               # Custom React hooks
│   │   └── useWebSocket.ts  # WebSocket communication
│   ├── stores/              # Zustand state stores
│   │   └── conversationStore.ts
│   ├── lib/                 # Utility functions
│   │   └── utils.ts         # cn(), formatTime(), generateId()
│   ├── types/               # TypeScript type definitions
│   │   └── index.ts
│   ├── assets/              # Static assets
│   ├── App.tsx              # Main application component
│   ├── main.tsx             # React entry point
│   └── index.css            # Global styles and theme
├── src-tauri/               # Tauri Rust backend
│   ├── src/
│   │   ├── main.rs         # Tauri entry point
│   │   └── lib.rs          # Rust library
│   ├── icons/              # App icons
│   └── tauri.conf.json     # Tauri configuration
├── backend/                 # Python backend (future)
├── public/                  # Static public assets
├── index.html              # HTML template
├── package.json            # Node dependencies
├── tailwind.config.js      # Tailwind configuration (if separate)
├── vite.config.ts          # Vite configuration
└── tsconfig.json           # TypeScript configuration
```

### Component Hierarchy

```
App
├── QueryClientProvider
│   └── div (flex layout)
│       ├── Sidebar
│       │   ├── Header (Emperor branding)
│       │   ├── New Chat Button
│       │   └── Navigation (Chat, History, Memory, Settings)
│       └── Main Content
│           ├── StatusBar
│           └── ChatPanel
│               ├── ScrollArea (messages)
│               │   ├── Welcome Screen (empty state)
│               │   ├── ChatMessage[] (message list)
│               │   └── Typing Indicator
│               ├── MicrophoneButton (side of chat)
│               └── Input Area
│                   ├── Input field
│                   └── Send Button
```

## Key Design Decisions

### 1. Gold & Black Color Palette

**Rationale:** Creates a premium, luxurious feel befitting the "Emperor" branding. Gold conveys wealth and power; black provides sophistication and depth.

**Palette:**
- Primary Gold: `#D4AF37` - Main accent color
- Light Gold: `#F4E4BA` - Highlights, hover states
- Dark Gold: `#B8860B` - Pressed states, borders
- Accent Gold: `#FFD700` - Pure gold for emphasis
- Text Gold: `#E5C87A` - Readable gold for text
- Primary Black: `#0A0A0A` - Main backgrounds
- Secondary Black: `#1A1A1A` - Cards, elevated surfaces
- Tertiary Black: `#2D2D2D` - Subtle elevations

### 2. Microphone Placement

**Rationale:** Voice input is a primary interaction method. Placing the microphone button prominently on the side of the chat area (not buried in the input) emphasizes this capability.

**Implementation:**
- Floating button on right side of chat panel
- Large hit target (48-64px)
- Gold styling to draw attention
- Prominent visual feedback during recording

### 3. Tailwind CSS v4

**Rationale:** Latest Tailwind version with improved performance and @theme directive for CSS variables.

**Implementation:**
- Theme defined in `index.css` using `@theme` block
- CSS custom properties for colors
- Dark mode as default

### 4. Zustand for State Management

**Rationale:** Lightweight, simple API, TypeScript-first. Perfect for the scope of this application without Redux boilerplate.

**Stores:**
- `conversationStore`: Messages, typing state, connection status

### 5. WebSocket Communication

**Rationale:** Real-time bidirectional communication for chat messages and streaming responses.

**Implementation:**
- Custom `useWebSocket` hook
- Auto-reconnect with exponential backoff
- Event-based message handling

## Non-Obvious Constraints

1. **Tauri Window**: Must set `class="dark"` on HTML element for dark mode
2. **Drag Region**: Status bar must have `-webkit-app-region: drag` for window dragging
3. **User Selection**: Disabled by default except in input elements
4. **Minimum Window Size**: 380x500 pixels enforced in `tauri.conf.json`
5. **Accessibility**: All interactive elements must have visible focus states

## Explicit Assumptions

1. Backend Python server will run on `ws://localhost:8765/ws`
2. All communication uses JSON format over WebSocket
3. Dark mode is the only supported theme
4. macOS is the primary target platform
5. Voice input will use system microphone permissions

## Coding Invariants

### CSS/Styling
- All colors MUST use CSS custom properties from the theme
- Gold accents on ALL interactive elements
- Minimum contrast ratio 4.5:1 for text
- Transitions: 150-300ms with cubic-bezier easing
- No inline styles except for dynamic values

### Components
- All UI components in `src/components/ui/`
- Feature components in `src/components/`
- Use `cn()` utility for conditional classes
- Memoize expensive components

### State
- All state through Zustand stores
- No prop drilling beyond 2 levels
- WebSocket events update store directly

### Animations
- All animations must be 60fps capable
- Respect `prefers-reduced-motion`
- Use CSS transitions over JS animations when possible

## Color Reference (Quick Access)

```css
/* Gold Palette */
--gold-primary: #D4AF37;
--gold-light: #F4E4BA;
--gold-dark: #B8860B;
--gold-accent: #FFD700;
--gold-text: #E5C87A;

/* Black Palette */
--black-primary: #0A0A0A;
--black-secondary: #1A1A1A;
--black-tertiary: #2D2D2D;

/* Semantic */
--background: #0A0A0A;
--foreground: #F4E4BA;
--card: #1A1A1A;
--border: #2D2D2D;
--ring: #D4AF37;
```
