# AssemblyAI Voice Agent Hackathon — Submission Package

## Final title

**InnerOS VoiceOps — Voice That Remembers**

## Short description

AssemblyAI powers realtime voice while InnerOS recalls prior verified outcomes, requires explicit approval, executes with a single-use permit, proves the result, and shares only the verified outcome with Personal Brain/Cognee.

## Long description

Most voice agents stop at conversation or forget what happened after a tool call. InnerOS VoiceOps crosses both boundaries: from spoken intent to governed execution, and from verified execution to reusable operational memory.

A user speaks naturally. AssemblyAI provides the realtime voice layer with turn handling, speech context, tool calling and interruption-aware interaction. InnerOS then treats the finalized transcript as evidence, not as automatic authorization. The system inspects operational state, proposes a bounded action, requests explicit approval and issues a short-lived single-use Voice Execution Permit bound to the exact session, event, transcript, proposal, state and action.

Only after that permit validates can the demo action execute. Every step is captured in Decision Evidence, replayable afterwards, with Human Time Returned separated into measured and estimated claims. After the result is recorded, VoiceOps creates a bounded verified-outcome memory record. Personal Brain curates it before Cognee storage, and a second correlation-bound recall demonstrates that another agent can remember what VoiceOps actually did.

The project is local-first. AMD .5/Qwen provides the private reasoning path in the live local stack. AssemblyAI is a reusable platform provider rather than a product-specific secret. WhatsApp voice notes use the same reusable Voice Fabric with managed AssemblyAI STT and local Whisper fallback. Physical Guardian contributes sanitized `NormalizedEvent` incidents without duplicating camera logic inside VoiceOps.

For judging, the public Cloud Run surface intentionally runs a safe synthetic reasoner, synthetic memory lane, and no production writes. The live-local stack can use Personal Brain/Cognee plus AssemblyAI and AMD .5. This keeps the public demo honest while showing the architecture that matters: **Voice -> Memory -> Reason -> Approval -> Action -> Verify -> Shared Recall**.

## What is novel

VoiceOps does not equate a tool call, a remembered fact, or a model recommendation with permission. It recalls prior verified outcomes before reasoning, but creates a cryptographically bound, short-lived, single-use execution permit only after exact finalized speech and explicit approval. After execution, only the bounded verified outcome is curated into shared memory. The result is a closed operational loop where Agent A can act and Agent B can later remember without memory ever becoming authorization.

## Technologies

- AssemblyAI Voice Agents / Streaming v3
- semantic turn detection and end-of-turn handling
- keyterms and dynamic `agent_context`
- tool calling and interruption/barge-in handling
- session lifecycle/resume capabilities
- PII redaction, entity detection and content moderation capabilities
- InnerOS Resource Fabric and governance layer
- AMD Radeon AI PRO R9700 node `.5` with local Qwen reasoning
- Voice Execution Permits: HMAC, TTL, event/transcript/proposal/state/action binding, single-use consumption
- WhatsApp / Evolution reusable Voice Fabric with local Whisper fallback
- Physical Guardian sanitized `NormalizedEvent` contract
- Decision Evidence / Forensic Replay / Human Time Returned
- Personal Brain / Cognee shared operational memory bridge
- truth-labeled memory states: LIVE / REPLAY / SYNTHETIC / UNVERIFIED
- Google Cloud Run + Cloudflare public judge surface
- Python 3.11/3.12

## Public links

- Repository: `https://github.com/Rafa-Innerchispa/inneros-voiceops-assemblyai`
- Demo: `https://voiceops.creatorcore.ai/`

Video and pitch-deck URLs should be inserted here after media upload; do not invent placeholders in the final organizer form.

## Maintained product lineage after the hackathon build

The submission repository remains the public hackathon artifact. Reusable product work continued in the maintained repositories rather than turning the contest branch into a second product:

- `Rafa-Innerchispa/inneros-voiceops` at `8d9df1872541619f94ca1879d27ed7311b0850f2`: conversational AssemblyAI runtime fails closed unless the SDK and server-side credential are available; the maintained runtime includes the SIP/RTP conversational transport.
- `Rafa-Innerchispa/inneros-fieldops-agents-for-humans` at `295581e5b8932ff2713483c79beaf24e3adb84a2`: VoiceOps verbal approval enters the normal FieldOps governance path and independent verifier; an invalid approval artifact fails closed.
- Owner-confirmed telephony state: `READY_OWNER_CONFIRMED_E2E_CALLING`. The release process deliberately does not reconfigure UCM/SIP/RTP/routes/Tailscale to re-prove an already working path.

## Judge flow

1. Open the public demo.
2. Reset the demo state.
3. Submit an operational intent such as: `Review the north access incident and create a technical work order if appropriate.`
4. Observe the **BEFORE ACTION / RECALL** panel and its truth label.
5. Observe that the system proposes an action but does not execute it.
6. Try an ambiguous phrase such as `If you think it is necessary.` The action stays blocked and no memory write occurs.
7. Give explicit authorization: `Yes, I authorize it.`
8. Observe the synthetic work order, execution-permit evidence, correlation/session identifiers and HTR result.
9. Observe **VERIFIED WRITEBACK** and **CROSS-AGENT RECALL** by correlation ID.
10. Open Evidence / Replay and inspect the chronological decision trail.

The public surface has `production_writes=false`. It is intentionally judge-safe.

## 75-second spoken pitch

Voice agents are good at talking. The harder problem is remembering what really happened without confusing memory with permission to act.

InnerOS VoiceOps uses AssemblyAI as the realtime voice layer. Before reasoning, it can recall a prior verified operational outcome from shared memory. InnerOS then inspects current state and asks our local AMD/Qwen reasoning layer what should happen next. But memory and recommendations are context, not authorization.

Before any consequential action, VoiceOps requires explicit approval and creates a short-lived, single-use execution permit cryptographically bound to the session, the incident, the exact approval transcript, the proposal and the state the agent saw. Ambiguous approval fails closed. Interruption does not become accidental execution.

Then we create the bounded demo action and preserve the entire decision as replayable evidence. Only after the result exists do we curate a verified-outcome record into Personal Brain/Cognee. A second agent can recall the same correlation-bound outcome. The result is a voice agent designed not just to answer, but to remember verified operations, act safely, and prove what happened.

## Demo recording outline

- 0–10 s: problem statement and one-screen cognitive loop
- 10–25 s: AssemblyAI voice request + prior memory recall
- 25–38 s: proposal appears, ambiguous approval is rejected
- 38–52 s: explicit approval, single-use permit, action result
- 52–68 s: verified outcome writeback + cross-agent recall
- 68–80 s: Evidence / Replay and HTR
- 80–90 s: architecture card: AssemblyAI + InnerOS + Personal Brain/Cognee + local reasoning + governed execution

## Evidence-backed claims allowed in submission

- 108/108 tests PASS on the final submission branch, including LabLab field-limit checks.
- Explicit approval fails closed for ambiguous phrases.
- Voice Execution Permit is bound and single-use.
- Public judge surface is deployed and returns a working `/api/state`.
- Reusable AssemblyAI provider preflight is PASS with credentials kept server-side.
- Prior captured local live E2E includes AssemblyAI STT -> InnerOS -> AMD .5 -> approval -> synthetic action -> Evidence/Replay -> spoken completion.
- Reusable WhatsApp Voice Fabric has AssemblyAI routing and local Whisper fallback tests PASS.

## Claims to avoid

- Do not claim the public Cloud Run revision currently uses AMD .5 or live Cognee; it runs the synthetic reasoner and should use the truth-labeled synthetic memory lane unless a new deployment is explicitly verified.
- Do not claim live AssemblyAI is enabled on the public revision until a Secret Manager binding is deployed.
- Do not claim production work-order or building-control writes; the hackathon action is bounded/synthetic.
- Do not claim `/healthz` is healthy until its current 404 discrepancy is fixed; `/api/state` is the verified operational endpoint.

## Submission status

Technical build: **ready**.

Final submission verification: **108/108 tests PASS**, `compileall` PASS, `git diff --check` PASS, committed-secret regression test and LabLab field-limit checks included, no telephony mutation, no external model spend. Personal Brain loopback verified-outcome receiver merged independently after green CI.

Still manual before organizer submission:

- attach/create the team/project entry on the event page if not already attached
- capture final judge screenshots
- record/upload demo video
- upload pitch deck/media if the form accepts them
- paste the final copy/links into the lablab.ai submission form
- verify the organizer's exact closing hour before final submit

Internal freeze target: **September 29, 2026 at 22:00 America/Guayaquil**. The event build window is September 1–30, 2026; the accessible official page previously did not expose an exact closing hour, so the project should not depend on late September 30.
