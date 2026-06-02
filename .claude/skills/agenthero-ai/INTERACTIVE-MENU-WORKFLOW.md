# Interactive Menu & Agent Integration Workflow

**Version**: 2.1.4
**Date**: 2025-10-22

---

## Overview

The interactive menu system provides a **bridge** between the visual dashboard (Python) and the agenthero-ai agent (Claude CLI). It allows you to:

1. ✅ Browse topics
2. ✅ View task details
3. ✅ **Invoke the agenthero-ai agent** to execute tasks

---

## Complete Workflow

### Step 1: Launch Interactive Menu

```bash
bash cs-prj-menu.sh
# or
.\cs-prj-menu.bat
```

You'll see:
```
📋 Multi-Topic Dashboard
                     Active Topics
┌────┬──────────────────────┬──────────┬──────────┬─────────┐
│ No │ Topic                │ Progress │  Tasks   │  Last   │
├────┼──────────────────────┼──────────┼──────────┼─────────┤
│  1 │ SubsHero Website     │ ███░░░░░ │ ✅ 1/3   │  1h ago │
│  2 │ Competitor Research  │ ████████ │ ✅ 3/3   │ 20m ago │
└────┴──────────────────────┴──────────┴──────────┴─────────┘

Actions:
  1-9  → Switch to topic by number
  n    → Create new topic
  a    → Archive completed topics
  q    → Quit dashboard

Choose an action: _
```

---

### Step 2: Select a Topic (e.g., type `1`)

**Automatically shows:**
1. Topic summary (progress, stats)
2. **Detailed task list** (all tasks with status icons)

```
📌 Topic: SubsHero Single Page Website
Slug: subshero-single-page-website

Progress: 33%
Total Tasks: 3
Completed: 1
In Progress: 0
Pending: 2

📋 Task List:
  ✅ [task-001] ui-design-implementer: Create hero section
  ⏳ [task-002] ui-design-implementer: Create features section
  ⏳ [task-003] ui-design-implementer: Create pricing section

What would you like to do?
  r - Return to main menu
  c - Continue working (invoke agent)

Action: _
```

---

### Step 3: Choose Action

#### Option A: Return to Main Menu (`r`)

- Returns to the dashboard
- No changes made

#### Option B: Continue Working (`c`) **← THE KEY FEATURE**

**If topic has tasks:**
```
📋 Preparing to resume work on: SubsHero Single Page Website
✓ Found 3 task(s)
  • 2 pending

✓ Resume signal created

Next steps:
1. Exit this menu (it will exit automatically)
2. In Claude CLI, invoke the agenthero-ai agent:
   "Resume work on: SubsHero Single Page Website"

The PM agent will load this topic and execute tasks via sub-agents.

Press Enter to exit and invoke agent (or 'r' to return to menu): _
```

**If topic has NO tasks:**
```
📋 Preparing to resume work on: SubsHero Single Page Website
⚠️  No tasks in this topic yet.
The agent will ask you what you want to accomplish and create tasks.

✓ Resume signal created

Next steps:
1. Exit this menu (it will exit automatically)
2. In Claude CLI, invoke the agenthero-ai agent:
   "Resume work on: SubsHero Single Page Website"

The PM agent will load this topic and execute tasks via sub-agents.

Press Enter to exit and invoke agent (or 'r' to return to menu): _
```

**Press Enter** → Menu exits cleanly

---

### Step 4: Invoke agenthero-ai Agent in Claude CLI

**In Claude CLI, type:**
```
Resume work on: SubsHero Single Page Website
```

**OR:**
```
Continue working on SubsHero website
```

**OR:**
```
Work on topic: SubsHero Single Page Website
```

---

### Step 5: Agent Workflow

#### A. If Topic Has Tasks (Execution Mode)

```
agenthero-ai agent:

📌 Resuming topic: SubsHero Single Page Website

Found 3 tasks:
  ✅ task-001: Create hero section (completed)
  ⏳ task-002: Create features section (pending)
  ⏳ task-003: Create pricing section (pending)

I'll execute the pending tasks via sub-agents.

[Launches ui-design-implementer for task-002]
[Monitors progress]
[Updates task status]
[Launches next task]
...
```

**The PM agent:**
1. ✅ Reads resume signal (knows which topic)
2. ✅ Loads topic state and tasks
3. ✅ **Launches sub-agents** for pending/in-progress tasks
4. ✅ Monitors sub-agent execution
5. ✅ Updates task status as they complete
6. ✅ Shows progress updates

---

#### B. If Topic Has NO Tasks (Planning Mode)

```
agenthero-ai agent:

📌 Topic: SubsHero Single Page Website
Currently 0 tasks in this topic.

What would you like to accomplish? Please describe the work you need done.
```

**You respond:**
```
Create a landing page with hero section, features, pricing, and contact form
```

**Agent breaks down the work:**
```
agenthero-ai agent:

I'll break this down into tasks:
1. Design wireframe/mockup for landing page
2. Implement hero section with CTA
3. Implement features section
4. Implement pricing section
5. Implement contact form with validation
6. Deploy to staging

Creating these tasks now...

[Creates tasks using topic_manager.py]

✓ Created 6 tasks

Now executing tasks via sub-agents:
[Launches mockup-creation-agent for task-001]
...
```

**The PM agent:**
1. ✅ Asks what you want to accomplish
2. ✅ Breaks down requirements into tasks
3. ✅ **Creates tasks** in topic state
4. ✅ **Launches sub-agents** to execute tasks
5. ✅ Monitors and updates progress

---

## Resume Signal File

**Location:** `.claude/agents/state/agenthero-ai/resume.json`

**Format:**
```json
{
  "slug": "subshero-single-page-website",
  "title": "SubsHero Single Page Website",
  "timestamp": "2025-10-22T10:30:00+00:00",
  "taskCount": 3
}
```

**Purpose:**
- Tells the agenthero-ai agent which topic to resume
- Provides context for the agent
- Created when user chooses option `c` in the menu

---

## Key Features

### 1. Automatic Task List Display

When you select a topic, the detailed task list is **automatically shown** (no need to choose option 'd').

**Before (v2.1.3):**
```
Choose action: 1
[Shows summary]
What would you like to do?
  r - Return
  d - View detailed task list  ← Had to choose this
  c - Continue working
```

**After (v2.1.4):**
```
Choose action: 1
[Shows summary]
[Shows detailed task list automatically]
What would you like to do?
  r - Return
  c - Continue working
```

---

### 2. Smart Resume Signal

The resume signal file provides context to the agent:
- Which topic to resume
- How many tasks exist
- Last activity timestamp

This allows the agent to:
- ✅ Load the correct topic automatically
- ✅ Decide whether to execute tasks or create new ones
- ✅ Show relevant progress information

---

### 3. Graceful Exit

When you choose `c` (continue working):
- ✅ Menu exits cleanly
- ✅ Clear instructions shown
- ✅ User invokes agent in Claude CLI
- ✅ Agent picks up where menu left off

**No context switching issues!**

---

## Multi-Tasking Support

Because sub-agents run in the **background**, you can:

1. Start work on Topic A (via agent)
2. While sub-agents are running in background
3. Open the menu again: `bash cs-prj-menu.sh`
4. Select Topic B and invoke agent
5. Now **both topics** have sub-agents running in parallel!

**The PM agent tracks:**
- Multiple topics
- Multiple sub-agents per topic
- Progress across all topics

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER                                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ├─────────────────┐
                            ↓                 ↓
                    ┌───────────────┐  ┌──────────────────┐
                    │ Bash Terminal │  │   Claude CLI     │
                    └───────────────┘  └──────────────────┘
                            │                 │
                            ↓                 ↓
              ┌─────────────────────┐  ┌─────────────────────┐
              │  Interactive Menu   │  │  agenthero-ai      │
              │  (Python Dashboard) │  │  Agent (PM)         │
              └─────────────────────┘  └─────────────────────┘
                            │                 │
                            ↓                 ↓
              ┌─────────────────────────────────────────────┐
              │     State Files (JSON)                      │
              │  - topics.json                              │
              │  - resume.json    ← Created by menu         │
              │  - pm-state.json                            │
              │  - topics/{slug}/pm-state.json              │
              └─────────────────────────────────────────────┘
                                    ↑
                                    │ (both read/write)
                                    ↓
              ┌─────────────────────────────────────────────┐
              │        Sub-Agents (Background)              │
              │  - ui-design-implementer                    │
              │  - market-research-analyst                  │
              │  - feature-comparison-analyst               │
              │  - etc.                                     │
              └─────────────────────────────────────────────┘
```

**Flow:**
1. User runs menu → Views topics and tasks
2. User chooses `c` → Menu creates `resume.json` and exits
3. User invokes agent → Agent reads `resume.json`
4. Agent loads topic state → Executes or creates tasks
5. Agent launches sub-agents → Sub-agents update task state
6. User can re-open menu → See updated progress

---

## Example Session

**Terminal 1: Interactive Menu**
```bash
$ bash cs-prj-menu.sh

📋 Multi-Topic Dashboard
  1. SubsHero Website (33% - 2 pending)

Choose action: 1

📌 Topic: SubsHero Website
📋 Task List:
  ✅ [task-001] ui-design-implementer: Hero section
  ⏳ [task-002] ui-design-implementer: Features section
  ⏳ [task-003] ui-design-implementer: Pricing section

Action: c

📋 Preparing to resume work...
✓ Resume signal created

Press Enter to exit: [Enter]

✓ Exiting menu.
```

**Claude CLI: Invoke Agent**
```
You: Resume work on: SubsHero Website

agenthero-ai agent:

📌 Resuming: SubsHero Website
Found 3 tasks (2 pending)

Executing task-002 via ui-design-implementer...
[Sub-agent launches in background]

Executing task-003 via ui-design-implementer...
[Sub-agent launches in background]

✓ All pending tasks launched
Monitoring progress...
```

**Terminal 1: Check Progress (Later)**
```bash
$ bash cs-prj-menu.sh

📋 Multi-Topic Dashboard
  1. SubsHero Website (66% - 1 in progress)  ← Updated!

Choose action: 1

📌 Topic: SubsHero Website
📋 Task List:
  ✅ [task-001] ui-design-implementer: Hero section
  ✅ [task-002] ui-design-implementer: Features section  ← Completed!
  🔄 [task-003] ui-design-implementer: Pricing section   ← In progress!
```

---

## Summary

✅ **Interactive menu** - Browse and manage topics
✅ **Auto-show tasks** - No extra steps to see details
✅ **Resume signal** - Seamless handoff to agent
✅ **Smart execution** - Agent creates or executes tasks
✅ **Multi-tasking** - Multiple topics, multiple sub-agents
✅ **Real-time updates** - See progress across sessions

**The menu is now a fully functional project management interface!**

---

**Version**: 2.1.4
**Status**: ✅ Production Ready
**Date**: 2025-10-22
