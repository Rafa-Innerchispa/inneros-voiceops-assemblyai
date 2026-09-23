# Canonical Demo Script — Voice + Shared Operational Memory

## Goal

Demonstrate a realtime AssemblyAI voice request that can recall prior operational context, become governed execution, require explicit approval, produce replayable evidence, and write only the **verified outcome** back into shared agent memory.

## One-line story

**The voice agent remembers what happened, knows what it is allowed to do, acts only with explicit approval, and proves the result to the next agent.**

## Scene

Synthetic technical-services/building environment for the public judge surface. No customer data, production credentials, or destructive actions. The recorded live-local proof may use Personal Brain/Cognee and local AMD/Qwen while preserving the same truth labels.

## 90-second judge flow

### 0–12 s · Voice

**User:** “Ralphi, review the north access incident and create a technical work order if appropriate.”

AssemblyAI supplies the realtime voice layer. The UI marks **VOICE** complete.

### 12–25 s · Recall + reason

VoiceOps queries shared operational memory before reasoning.

- public judge mode: truth-labeled `SYNTHETIC` memory;
- live-local mode: Personal Brain / Cognee returns `LIVE` curated memory.

The UI shows the provider, truth class, hit count and one bounded memory summary. The reasoner receives that context, but memory cannot authorize anything.

### 25–38 s · Proposal

VoiceOps proposes the bounded work-order action and stops at the approval gate.

**VoiceOps:** “I found a prior related operational outcome and the current north-access incident requires follow-up. I can create a bounded technical work order. Do you authorize it?”

### 38–48 s · Ambiguity fails closed

**User:** “If you think it is necessary.”

Expected result: **BLOCKED**. No permit, no action, no memory writeback.

### 48–62 s · Explicit approval

**User:** “Yes, I authorize it.”

VoiceOps creates the short-lived, single-use execution permit bound to session, event, exact approval transcript, proposal and state.

### 62–75 s · Action + evidence

The judge-safe synthetic work order is created. Decision Evidence / Replay / HTR update.

### 75–90 s · Remember + cross-agent proof

Only now does VoiceOps create a bounded verified-outcome record. The record excludes the raw transcript and private infrastructure details.

The UI shows:

`VERIFIED WRITEBACK -> memory receipt -> CROSS-AGENT RECALL`

A second recall by correlation ID proves the stored outcome can be retrieved from the shared memory lane.

## What the judge should notice

- AssemblyAI is visibly the voice front door.
- Memory is consulted **before** reasoning but never bypasses approval.
- Ambiguous authorization fails closed.
- The execution permit is single-use.
- The outcome is remembered **after** verification, not before.
- The same outcome is recallable by another agent.
- Every memory/provider state carries a truth label such as `LIVE`, `REPLAY`, `SYNTHETIC`, or `UNVERIFIED`.

## Boson boundary

Boson/Higgs work from the separate September 18 prototype proves VoiceOps can support another speech provider, but it is not part of the judged primary path here. AssemblyAI remains the hackathon voice technology.

## Demo fallback

If browser microphone permissions fail, use the deterministic fixture button. The public fallback remains visibly synthetic. Do not describe synthetic memory or synthetic work-order execution as production/live.

## Forbidden shortcuts

- fake live Cognee claims from the public Cloud Run surface;
- treating remembered text as authorization;
- storing raw approval transcripts in shared memory;
- fake tool results presented as production results;
- hidden manual clicks that actually perform the workflow;
- precomputed HTR labeled MEASURED without evidence;
- customer/security data.
