# AssemblyAI Voice Agent Hackathon — Submission Package

## Final title

**InnerOS VoiceOps — Voice That Remembers**

## Short description

AssemblyAI powers realtime voice while InnerOS recalls outcomes, requires explicit approval, executes with a single-use permit, and proves the result. VoiceOps runs on Google Cloud Run or sovereign local infrastructure with AMD/Qwen inference.

## Long description

Most voice agents stop at conversation or forget what happened after a tool call. InnerOS VoiceOps crosses both boundaries: from spoken intent to governed execution, and from verified execution to reusable operational memory.

A user speaks naturally. AssemblyAI provides the realtime voice layer with turn handling, speech context, tool calling and interruption-aware interaction. InnerOS then treats the finalized transcript as evidence, not as automatic authorization. The system inspects operational state, proposes a bounded action, requests explicit approval and issues a short-lived single-use Voice Execution Permit bound to the exact session, event, transcript, proposal, state and action.

Only after that permit validates can the demo action execute. Every step is captured in Decision Evidence, replayable afterwards, with Human Time Returned separated into measured and estimated claims. After the result is recorded, VoiceOps creates a bounded verified-outcome memory record. Personal Brain curates it before Cognee storage, and a second correlation-bound recall demonstrates that another agent can remember what VoiceOps actually did.

The project is local-first. AMD .5/Qwen provides the private reasoning path in the live local stack. AssemblyAI is a reusable platform provider rather than a product-specific secret. WhatsApp voice notes use the same reusable Voice Fabric with managed AssemblyAI STT and local Whisper fallback. Physical Guardian contributes sanitized `NormalizedEvent` incidents without duplicating camera logic inside VoiceOps.

For judging, we expose **two real deployment profiles from the same application**. The managed profile runs on Google Cloud Run with a safe synthetic reasoner, synthetic memory lane and no production writes. The sovereign-local profile is served from our local infrastructure and routes reasoning to the local AMD/Qwen runtime while preserving the same approval, evidence and replay contract. AssemblyAI remains the realtime voice layer for the judged voice path; local sovereignty refers to application hosting, operational data boundaries and model inference rather than falsely claiming AssemblyAI itself runs offline.

This dual deployment is part of the product story, not two separate demos: **Voice -> Memory -> Reason -> Approval -> Action -> Verify -> Shared Recall** behaves the same while the execution plane changes.

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
- Google Cloud Run managed deployment + Cloudflare custom domain
- Sovereign local/edge deployment with AMD/Qwen local inference
- Python 3.11/3.12

## Public links

- Repository: `https://github.com/Rafa-Innerchispa/inneros-voiceops-assemblyai`
- Managed cloud showcase: `https://voiceops-cloud.creatorcore.ai/` — Google Cloud Run
- Sovereign local showcase: `https://voiceops.creatorcore.ai/` — local server + AMD/Qwen reasoning

Both URLs serve the same VoiceOps governance UX and truth-label the runtime currently serving the page. Video and pitch-deck URLs should be inserted here after media upload; do not invent placeholders in the final organizer form.

## Maintained product lineage after the hackathon build

The submission repository remains the public hackathon artifact. Reusable product work continued in the maintained repositories rather than turning the contest branch into a second product:

- `Rafa-Innerchispa/inneros-voiceops` at `8d9df1872541619f94ca1879d27ed7311b0850f2`: conversational AssemblyAI runtime fails closed unless the SDK and server-side credential are available; the maintained runtime includes the SIP/RTP conversational transport.
- `Rafa-Innerchispa/inneros-fieldops-agents-for-humans` at `295581e5b8932ff2713483c79beaf24e3adb84a2`: VoiceOps verbal approval enters the normal FieldOps governance path and independent verifier; an invalid approval artifact fails closed.
- Owner-confirmed telephony state: `READY_OWNER_CONFIRMED_E2E_CALLING`. The release process deliberately does not reconfigure UCM/SIP/RTP/routes/Tailscale to re-prove an already working path.

## Judge flow

1. Open the two deployment URLs side by side and show that the UI is the same while the active runtime card changes from **GOOGLE CLOUD RUN** to **SOVEREIGN LOCAL**.
2. On the cloud surface, show the managed-service profile and judge-safe boundary.
3. On the local surface, run the governed demo and show **AMD / Qwen local** as the inference route after the intent is processed.
4. Submit an operational intent such as: `Review the north access incident and create a technical work order if appropriate.`
5. Observe the **BEFORE ACTION / RECALL** panel and its truth label.
6. Observe that the system proposes an action but does not execute it.
7. Try an ambiguous phrase such as `If you think it is necessary.` The action stays blocked and no memory write occurs.
8. Give explicit authorization: `Yes, I authorize it.`
9. Observe the bounded work order, execution-permit evidence, correlation/session identifiers and HTR result.
10. Open Evidence / Replay and inspect the chronological decision trail.

Both judge surfaces keep `production_writes=false`. The cloud surface uses synthetic reasoning; the sovereign-local surface uses the verified local AMD/Qwen runtime.

## 75-second spoken pitch

Voice agents are good at talking. The harder problem is remembering what really happened without confusing memory with permission to act.

We also built VoiceOps so deployment is a customer choice, not an architectural fork. The same governed interface runs in Google Cloud Run for a managed service, or on sovereign local infrastructure with AMD/Qwen inference and customer-controlled operational data.

InnerOS VoiceOps uses AssemblyAI as the realtime voice layer. Before reasoning, it can recall a prior verified operational outcome from shared memory. InnerOS then inspects current state and asks our local AMD/Qwen reasoning layer what should happen next. But memory and recommendations are context, not authorization.

Before any consequential action, VoiceOps requires explicit approval and creates a short-lived, single-use execution permit cryptographically bound to the session, the incident, the exact approval transcript, the proposal and the state the agent saw. Ambiguous approval fails closed. Interruption does not become accidental execution.

Then we create the bounded demo action and preserve the entire decision as replayable evidence. Only after the result exists do we curate a verified-outcome record into Personal Brain/Cognee. A second agent can recall the same correlation-bound outcome. The result is a voice agent designed not just to answer, but to remember verified operations, act safely, and prove what happened.

## Demo recording outline

- 0–10 s: split-screen proof of Cloud Run vs Sovereign Local, same VoiceOps UI
- 10–25 s: AssemblyAI voice request + prior memory recall
- 25–38 s: proposal appears, ambiguous approval is rejected
- 38–52 s: explicit approval, single-use permit, action result
- 52–68 s: verified outcome writeback + cross-agent recall
- 68–80 s: Evidence / Replay and HTR
- 80–90 s: architecture card: AssemblyAI + InnerOS + Personal Brain/Cognee + local reasoning + governed execution

## Evidence-backed claims allowed in submission

- 111/111 tests PASS on the dual-deployment submission branch, including deployment-profile and LabLab field-limit checks.
- Explicit approval fails closed for ambiguous phrases.
- Voice Execution Permit is bound and single-use.
- Managed Cloud Run and sovereign-local judge surfaces are both deployed on custom `creatorcore.ai` hostnames and return a working `/api/state`.
- Reusable AssemblyAI provider preflight is PASS with credentials kept server-side.
- The sovereign-local web runtime is configured for `local-amd-5` / Qwen inference; prior captured local live E2E includes AssemblyAI STT -> InnerOS -> AMD .5 -> approval -> bounded action -> Evidence/Replay -> spoken completion.
- Reusable WhatsApp Voice Fabric has AssemblyAI routing and local Whisper fallback tests PASS.

## Claims to avoid

- Do not claim the Cloud Run profile uses AMD .5 or live Cognee; it runs the synthetic reasoner. AMD/Qwen local inference belongs to the sovereign-local profile.
- Do not claim live AssemblyAI is enabled on the public revision until a Secret Manager binding is deployed.
- Do not claim production work-order or building-control writes; the hackathon action is bounded/synthetic.
- Use `/health` and `/api/state` as the verified cloud endpoints. The custom cloud hostname currently returns 404 for `/healthz`, so do not use that path as evidence.

## Submission status

Technical build: **ready**.

Final submission verification: **111/111 tests PASS**, Python 3.11/3.12 CI PASS, `compileall` PASS, `git diff --check` PASS, deployment-profile coverage included, no telephony mutation, no external model spend. Personal Brain loopback verified-outcome receiver merged independently after green CI.

Still manual before organizer submission:

- attach/create the team/project entry on the event page if not already attached
- capture final judge screenshots
- record/upload demo video
- upload pitch deck/media if the form accepts them
- paste the final copy/links into the lablab.ai submission form
- verify the organizer's exact closing hour before final submit

Internal freeze target: **September 29, 2026 at 22:00 America/Guayaquil**. The event build window is September 1–30, 2026; the accessible official page previously did not expose an exact closing hour, so the project should not depend on late September 30.
