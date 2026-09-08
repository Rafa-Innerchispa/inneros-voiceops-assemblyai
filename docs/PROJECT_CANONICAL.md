# Project Canonical — InnerOS VoiceOps

Last canonical reset: 2026-09-08

## One-sentence product

InnerOS VoiceOps turns spoken operational intent into governed, auditable real-world execution using AssemblyAI realtime speech plus InnerOS local-first orchestration.

## Hackathon objective

Build and submit a working voice-agent experience for the AssemblyAI Voice Agent Hackathon without creating a disposable parallel architecture. Every useful component should remain usable by InnerOS after the event.

## Product thesis

The important interface shift is not “AI that can talk.” It is reducing the distance between human intention and safe execution. VoiceOps should let a person state an operational objective naturally, while InnerOS handles context, routing, approvals, tools, evidence, and follow-up.

## Canonical name

- Product: **InnerOS VoiceOps**
- Submission descriptor: **The Governed Voice Control Plane for the Physical World**
- Repository: `Rafa-Innerchispa/inneros-voiceops-assemblyai`

Do not create a second repository for the same hackathon unless this document is explicitly amended.

## Canonical technical choices

1. AssemblyAI is the realtime speech recognition layer.
2. InnerOS remains the orchestration/control plane.
3. Local AMD inference is preferred when capability and policy allow it.
4. MCP is the capability/tool execution boundary.
5. Existing domain systems are integrated through adapters; their business logic is not copied here.
6. Audit Fabric / Forensic Replay provide evidence contracts.
7. HTR measures returned human time with MEASURED and ESTIMATED clearly separated.
8. TTS is pluggable; prefer local where practical, but do not block the hackathon on a perfect local TTS stack.
9. Public demo data is synthetic.
10. Consequential actions require explicit policy/approval gates.

## Existing capabilities to integrate, not duplicate

- InnerOS control plane
- Resource Fabric / routing
- MCP tools and authorization
- AMD .5 local inference
- InnerOps Service Operations
- VigilOS / security-domain adapters where demo-safe
- Workforce integration where useful
- QuoteOps / Smart Quoter where useful
- Audit Fabric
- Forensic Replay
- Human Time Returned

## New hackathon capabilities

- AssemblyAI streaming client/adapter
- voice session state machine
- turn/interruption handling
- voice approval interaction
- dynamic speech context where supported
- judge-facing demo UI
- synthetic VoiceOps scenario
- hackathon evidence and metrics

## Demo invariant

The primary demo must complete one coherent workflow. Avoid a menu of half-working features.

Recommended scenario:

1. User reports or asks about an operational alarm/problem by voice.
2. VoiceOps transcribes and identifies the relevant asset/site context.
3. InnerOS inspects demo-safe state.
4. The system proposes an action.
5. User approves verbally.
6. A work order or equivalent operational action is created.
7. Audit evidence and HTR appear.
8. VoiceOps reports completion.

## Winning narrative

**Intent → Governed Execution → Evidence → Human Time Returned**

Every feature shown in the demo should strengthen at least one of those four words.

## Truth policy

Never overclaim:

- pre-existing InnerOS work is “reused/integrated,” not “built during the hackathon”;
- only captured timing is MEASURED;
- estimates remain ESTIMATED;
- experimental integrations are labeled experimental;
- public demo does not imply production deployment;
- deterministic replay means replaying captured evidence deterministically where possible, not promising identical stochastic LLM prose.

## Development policy

Local-first execution. Use local dev/runtime and local models first. External agents/models are fallback for unsupported capability or verified blockers. Keep changes isolated and auditable. No unnecessary cloud spend.

## Scope freeze rule

After the core E2E workflow passes, new features enter only if they materially improve judging criteria and do not threaten the demo. Stability beats feature accumulation.

## Resume protocol

On any future session, read in this order:

1. README.md
2. docs/PROJECT_CANONICAL.md
3. docs/ROADMAP.md
4. docs/HACKATHON_CHECKLIST.md
5. docs/ARCHITECTURE.md
6. latest commits/issues/evidence

Then continue from the first incomplete P0 item. Do not redesign the project from memory.
