# InnerOS VoiceOps — AssemblyAI Voice Agent Hackathon 2026

> **Voice is the interface. Governed execution is the product.**

InnerOS VoiceOps turns natural voice into controlled, verifiable actions across real infrastructure.

AssemblyAI provides the realtime voice experience. InnerOS adds live system context, local-first reasoning, operational memory, explicit human approval, bounded execution, verification, and evidence.

This repository is the canonical submission for the **AssemblyAI Voice Agent Hackathon 2026**.

---

## Live demo

### Sovereign local demo

**https://voiceops.creatorcore.ai/**

This is the primary judged demo.

It runs the VoiceOps application on local infrastructure and uses a local Qwen reasoner while keeping AssemblyAI as the realtime voice layer.

### Managed cloud showcase

**https://voiceops-cloud.creatorcore.ai/**

The cloud profile demonstrates the same product and governance UX with a safe managed deployment profile.

### Judge access

Use the **Judge Access / Log In** button on the landing page.

- Username: `voiceops-judge`
- Password: supplied privately in the hackathon submission form
- Allow microphone access in the browser
- Start the live VoiceOps session from the central control

No password, API key, token, or private infrastructure credential is committed to this repository.

---

## What to try

A simple live test:

1. Ask: **“What lights are currently on?”**
2. Ask: **“Turn off the kitchen light.”**
3. VoiceOps should propose the action and wait for approval.
4. Say: **“Yes, authorize.”**
5. VoiceOps issues a single-use permit, executes only the approved action, and verifies the resulting state.

Other useful questions include:

- “What cameras are currently available?”
- “What is the Intelbras alarm status?”
- “What is the current UniFi and Wi-Fi status?”
- “What is the status of the local servers?”

---

## Product thesis

Most voice assistants stop at conversation.

VoiceOps is designed to continue safely into the physical world:

```text
VOICE
  ↓
RECALL
  ↓
REASON
  ↓
PROPOSE
  ↓
HUMAN APPROVAL
  ↓
SINGLE-USE PERMIT
  ↓
ACT
  ↓
VERIFY
  ↓
REMEMBER
```

The important part is not simply that an AI can call a tool.

The important part is that the system knows:

- what the user asked;
- what live state was observed;
- what action was proposed;
- whether a human explicitly approved it;
- exactly what capability was permitted;
- whether the action really executed;
- what state was observed afterward;
- and what evidence should be preserved.

---

## Current live capabilities

### Realtime voice

- AssemblyAI realtime voice session
- live transcription
- natural conversational replies
- browser microphone input
- tool calling from the voice agent
- compact asynchronous tool results to avoid blocking conversational turns

### Local-first reasoning

- local Qwen reasoner for the sovereign deployment
- operational routing remains inside the InnerOS boundary where practical
- external services are used only where the product explicitly requires them, such as AssemblyAI for realtime voice

### Live system reads

The sovereign demo can read current state from connected InnerOS capabilities, including:

- Home Assistant
- lights and switches
- cameras exposed through Home Assistant
- Intelbras alarm state
- UniFi / Wi-Fi state
- local server and infrastructure health
- verified operational memory

### Governed physical actions

The demo does **not** expose unrestricted Home Assistant service execution.

Only bounded, allowlisted capabilities are eligible for VoiceOps approval and execution.

Currently demonstrated:

- light control
- selected network restart actions

Camera restart remains fail-closed unless a dedicated safe adapter is available.

A model cannot turn a memory result into authorization, bypass the approval gate, or replace a single-use execution permit.

---

## Real execution path

The sovereign live path is:

```text
Human voice
    │
    ▼
AssemblyAI realtime voice
    │
    ▼
VoiceOps browser session
    │
    ▼
InnerOS Voice Gateway
    │
    ├── verified context / memory
    ├── live system reads
    ├── local Qwen reasoning
    └── governed capability routing
            │
            ▼
      Action proposal
            │
            ▼
      Explicit human approval
            │
            ▼
      Single-use execution permit
            │
            ▼
      Allowlisted action
            │
            ▼
      Post-action verification
            │
            ▼
      Evidence + operational memory
```

---

## Why this matters

The architecture is intended for environments where AI should help operate real systems without being granted unrestricted control.

Examples include:

- buildings
- residential towers
- offices
- field operations
- network infrastructure
- security systems
- smart-home and automation environments

The same pattern can extend to other bounded capabilities as safe adapters are added.

---

## Truth boundaries

VoiceOps deliberately distinguishes between a capability being implemented and a capability being safe to execute.

### Sovereign local profile

The local judge surface can connect to live Home Assistant and infrastructure state. Selected allowlisted actions can perform real physical changes after explicit approval.

### Managed cloud profile

The managed Cloud Run showcase uses safe demo boundaries where private local infrastructure is not reachable.

### Fail closed

If a safe execution adapter is unavailable, VoiceOps does not simulate success.

It returns a protected or unavailable result instead.

---

## AssemblyAI integration

AssemblyAI is the realtime voice layer used by the judged voice experience.

The current implementation includes:

- realtime voice websocket session
- temporary browser token issuance
- microphone PCM streaming
- transcript events
- agent replies
- audio playback
- tool calling
- tool-result round trips
- timeout/error visibility
- no browser exposure of the permanent provider API key

AssemblyAI provides the conversational realtime interface. InnerOS provides governed access to systems and actions.

---

## Repository structure

```text
src/voiceops/
  adapters/                 provider and reasoning adapters
  web/                      judge-facing UI
  gateway.py                session and turn orchestration
  approval.py               explicit approval semantics
  execution_permit.py       single-use governed permits
  inneros_system_bridge.py  live InnerOS / Home Assistant capability bridge
  shared_memory.py          verified memory bridge
  audit.py                  evidence and replay support
  webapp.py                 authenticated judge web application

tests/                      automated verification
docs/                       architecture and operational documentation
evidence/                   sanitized evidence/checkpoints
scripts/                    repository utilities
Dockerfile                  managed deployment image
```

---

## Local development

Requirements:

- Python 3.11+

Install:

```bash
python3 -m pip install -e '.[dev]'
```

Run tests:

```bash
python3 -m pytest tests -q
python3 -m compileall -q src tests
git diff --check
```

Run the judge-facing web application:

```bash
voiceops-web
```

For a live AssemblyAI environment, provide the API key through the runtime environment only:

```text
ASSEMBLYAI_API_KEY=<server-side secret>
```

Never commit provider credentials.

---

## Security model

VoiceOps follows a simple rule:

**Memory is context, not authority.**

The system therefore separates:

- read access;
- reasoning;
- proposals;
- human approval;
- execution permits;
- execution;
- verification.

Consequential actions must cross the approval and permit boundaries.

The public repository must not contain:

- API keys
- passwords
- session tokens
- private customer data
- private recordings
- unrestricted infrastructure credentials

---

## Hackathon validation

The submission has demonstrated:

- live AssemblyAI voice
- local-first InnerOS reasoning
- live Home Assistant reads
- live UniFi reads
- approval-gated actions
- real light-control execution
- single-use execution permits
- post-action verification
- evidence-oriented workflow
- browser-visible tool execution status
- protected failure behavior when a safe adapter is unavailable

Recent final fixes merged to `main` include:

- full live Home Assistant / UniFi routing
- governed live action routing
- specific UniFi target resolution
- tool-call stall repair
- compact asynchronous tool-result handling

---

## Related deployment profiles

- Sovereign local: https://voiceops.creatorcore.ai/
- Managed cloud: https://voiceops-cloud.creatorcore.ai/

The same canonical application is used with different runtime truth boundaries.

---

## License

Apache-2.0. See `LICENSE`.
