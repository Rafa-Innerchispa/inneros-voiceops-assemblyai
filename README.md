# InnerOS VoiceOps — AssemblyAI Voice Agent Hackathon 2026

> **Speak an intent. InnerOS safely turns it into real-world execution, and proves exactly what happened.**

InnerOS VoiceOps is a governed voice control plane for real-world service operations, buildings, security systems, field workflows, and enterprise tools. It uses AssemblyAI for real-time speech understanding, InnerOS for orchestration and policy, local-first reasoning on our AMD infrastructure, MCP tools for execution, and Audit Fabric / Forensic Replay for evidence.

This repository is the canonical hackathon workspace for the **AssemblyAI Voice Agent Hackathon 2026** on lablab.ai.

## Hackathon facts

- Event: AssemblyAI — Voice Agent Hackathon
- Organizer: lablab.ai + AssemblyAI
- Format: fully online, month-long challenge
- Build window: **September 1–30, 2026**
- Registration: open throughout the build window
- Prize pool: **USD 10,000** total, split between cash and AssemblyAI credits
- Event: https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon
- Repo owner: Rafa-Innerchispa
- Project status: ACTIVE / BUILDING

## Why we are building this

We are not building another generic voice chatbot. VoiceOps is a voice interface for governed execution.

The demo should prove this chain:

1. A human speaks an operational intent.
2. AssemblyAI transcribes it in real time.
3. InnerOS resolves context, policy, tenant, tools, and routing.
4. A local model is preferred whenever capability and policy allow it.
5. MCP tools execute a real or synthetic operational workflow.
6. Human approval is required for governed actions when policy says so.
7. Audit Fabric records decision evidence, routing evidence, actions, outputs, and timestamps.
8. Human Time Returned (HTR) quantifies how much manual work was reduced.
9. Forensic Replay can reconstruct what the agent saw and did without rewriting history.
10. The user receives a spoken result.

## Core demo story

A recommended synthetic demo scenario is a technical-service/building operation:

> “Ralphi, tenemos una alarma en el acceso norte. Revisa qué ocurre y abre una orden para el técnico si corresponde.”

Expected flow:

- realtime transcription;
- operational context lookup;
- safe reasoning and tool routing;
- alarm/camera/access state inspection using synthetic or demo-safe data;
- explicit approval gate before consequential action;
- work order creation;
- technician assignment / follow-up;
- evidence bundle generation;
- HTR calculation;
- spoken completion summary.

The demo must never require production credentials, customer PII, or destructive actions.

## Product positioning

**InnerOS VoiceOps: The Governed Voice Control Plane for the Physical World**

Voice is the interface, not the product. The product is the execution layer behind it.

Differentiators:

- local-first model routing;
- real tool execution through MCP;
- human approval gates;
- physical-world / service-operations workflows;
- decision and routing evidence;
- forensic replay;
- Human Time Returned metrics;
- tenant-aware policy and authorization;
- AssemblyAI used as a first-class realtime speech layer, not merely a logo in the stack.

## Architecture

```text
Human voice
    |
    v
AssemblyAI realtime STT
    |
    v
InnerOS Voice Gateway
    |
    +--> Context / tenant / policy
    +--> Resource Fabric routing
    |      |
    |      +--> Local AMD inference (preferred)
    |      +--> External fallback only when required
    |
    v
MCP capability layer
    |
    +--> Service Operations
    +--> VigilOS / building-security demo adapters
    +--> Quote / visit / work-order flows
    +--> Workforce adapter (optional)
    +--> Email / messaging / other approved integrations
    |
    v
Approval gates + action execution
    |
    v
Audit Fabric / Forensic Replay / HTR
    |
    v
TTS response
```

See `docs/ARCHITECTURE.md` for the detailed boundaries and implementation contract.

## Local-first rule

This project follows the InnerOS local-first development policy:

- prefer direct execution on local infrastructure;
- prefer local AMD inference when capability allows;
- use external model/agent providers only for unsupported capability, recovery, or a verified blocker;
- no unnecessary cloud spend;
- no production writes during hackathon development unless explicitly approved;
- never weaken auth, tenant isolation, auditability, or approval gates just to make the demo easier.

## What we reuse vs. what is new

### Reused / integrated InnerOS capabilities

- MCP control plane and tool routing;
- Resource Fabric / local-first routing;
- AMD local inference infrastructure;
- Service Operations workflow work;
- Audit Fabric contracts;
- Forensic Replay / Evidence Bundles;
- Human Time Returned instrumentation;
- correlation IDs / decision evidence / routing evidence;
- approval and tenant-safety concepts.

### Hackathon-specific work

- AssemblyAI realtime streaming adapter;
- Voice Gateway session/orchestration layer;
- dynamic speech context integration where useful;
- interruption / turn handling;
- voice-safe approval UX;
- end-to-end voice demo flow;
- hackathon demo tenant and synthetic fixtures;
- public deployment/demo package;
- hackathon pitch, video, submission copy, and evidence.

We must explicitly document which changes were made during the hackathon period. Do not claim pre-existing InnerOS components were built from scratch for this event.

## Repository structure

```text
src/                    Product code
  voiceops/             VoiceOps application package
  adapters/             AssemblyAI and InnerOS adapters
  workflows/            Demo-safe governed workflows
  audit/                Hackathon-side audit integration hooks

tests/                  Unit / integration / E2E tests
fixtures/               Synthetic demo data only
docs/
  ARCHITECTURE.md        Technical architecture and boundaries
  PROJECT_CANONICAL.md   Project truth / product decisions
  ROADMAP.md             Build plan and milestone dates
  HACKATHON_CHECKLIST.md Submission and judging checklist
  DEMO_SCRIPT.md         Canonical demo story
  SUBMISSION_NOTES.md    Facts and claims safe to use publicly

evidence/               Generated non-secret benchmark/demo evidence
```

## Definition of Done

A valid hackathon-ready release requires all of the following:

- [ ] AssemblyAI realtime speech input works end-to-end.
- [ ] At least one complete governed operational workflow executes.
- [ ] Local-first inference path is demonstrated or measured.
- [ ] Consequential action has an explicit approval gate.
- [ ] Decision Evidence and Routing Evidence are visible.
- [ ] Human Time Returned is calculated with a clear MEASURED vs ESTIMATED boundary.
- [ ] Replay/evidence bundle can be inspected for the demo workflow.
- [ ] Synthetic tenant data only in public demo artifacts.
- [ ] Automated tests pass.
- [ ] Public demo URL works for judges.
- [ ] README is current.
- [ ] Architecture diagram is current.
- [ ] Pitch deck is complete.
- [ ] Demo video is recorded before deadline day.
- [ ] Submission form is drafted before deadline day.
- [ ] Final repo is public and contains an open-source license.
- [ ] No secrets are committed.

## Judging strategy

We optimize for four things:

1. **Technology use** — AssemblyAI is central to the real-time interaction, not decorative.
2. **Originality** — governed voice execution over physical/service operations rather than a generic assistant.
3. **Business value** — Human Time Returned and operational outcomes are measured.
4. **Presentation** — one short voice interaction visibly drives a complete auditable workflow.

## Current priorities

1. Bootstrap the AssemblyAI streaming adapter.
2. Create the Voice Gateway contract.
3. Bind one synthetic Service Operations / VigilOS workflow.
4. Bind audit + HTR evidence.
5. Run a local E2E demo on AMD .5.
6. Add a minimal judge-facing UI.
7. Deploy a public demo safely.
8. Record video and submit early.

## Non-goals

- Rebuild InnerOS inside this repository.
- Duplicate Workforce, Service Operations, QuoteOps, VigilOS, or Forensic Replay business logic.
- Make production building controls available publicly.
- Depend on Notion as the only source of truth.
- Use customer data in the demo.
- Claim deterministic LLM re-generation where it cannot be guaranteed.
- Optimize for architectural novelty at the expense of a working demo.

## Security and truth boundaries

- Never commit API keys, OAuth tokens, production URLs containing secrets, customer identifiers, or raw private recordings.
- Use `.env.example` for configuration names only.
- Public evidence must contain synthetic or explicitly sanitized data.
- `MEASURED` metrics must be backed by captured evidence.
- `ESTIMATED` metrics must stay visibly labeled as estimates.
- A replay must not silently fetch current data and pretend it is historical state.
- Existing InnerOS capability must be described as existing/reused, not falsely attributed to this hackathon.

## Canonical docs

Start here when resuming work:

1. `README.md`
2. `docs/PROJECT_CANONICAL.md`
3. `docs/ROADMAP.md`
4. `docs/HACKATHON_CHECKLIST.md`
5. `docs/ARCHITECTURE.md`
6. `docs/DEMO_SCRIPT.md`

If implementation and documentation disagree, update the documentation in the same PR/commit that changes the behavior.

## License

Apache-2.0. See `LICENSE`.


## Implementation checkpoint — 2026-09-08

- Voice Gateway session/correlation/turn state: implemented.
- Explicit voice approval gate: implemented and fail-closed on ambiguous or negated phrases.
- Synthetic building/service workflow: implemented; demo-only work orders execute only after approval.
- Audit evidence plus captured-state replay summary: implemented.
- HTR truth boundary: implemented with explicit `MEASURED` vs `ESTIMATED` classification.
- Local-first reasoning adapter contract: implemented; offline tests use deterministic synthetic reasoning while live InnerOS/AMD plugs in through the adapter boundary.
- AssemblyAI v3 streaming adapter: implemented with lazy optional dependency, final-turn routing, lifecycle/error evidence, and explicit `disconnect(terminate=True)` shutdown.
- Automated tests and compile checks: passing locally.
- Live AssemblyAI microphone/API-key validation: pending.
- Live InnerOS Resource Fabric / AMD .5 reasoning binding: pending.
