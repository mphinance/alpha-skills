---
name: portable-memory-core
description: >
  A meta-skill that establishes a 'One Brain' portable memory folder (.agent/).
  It persists context, user preferences, identity rules, and execution history 
  across different AI harnesses (Claude Code, Cursor, Windsurf, OpenClaw).
---

# Portable Memory Core

*"Never explain yourself twice."*

This skill enforces the `One Brain` protocol. Instead of scattering your preferences across dozens of system prompts, it centralizes them into a portable `.agent/` directory that any LLM runner can hook into.

## Core Directives

1. **Memory Synchronization:** Upon startup, read from `.agent/memory.yaml`.
2. **Context Passing:** Whenever the user switches contexts (e.g., from Cursor to OpenClaw), this skill ensures the new context loads the latest state from `.agent/state.json`.
3. **Identity Enforcement:** Enforces the `IDENTITY.md` rules (e.g., "Caveman mode", "No em dashes", "Substack voice") universally across all generated code and text.
4. **Harness Agnostic:** Works seamlessly whether the upstream harness is Claude CLI, a custom Python script, or a GUI.

## Usage

When activated, you will automatically:
- Load `.agent/preferences.yaml`
- Update `.agent/history.json` with the current session summary.
- Export relevant variables to the local workspace.
