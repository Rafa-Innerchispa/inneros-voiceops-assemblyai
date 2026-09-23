# InnerOS VoiceOps — AssemblyAI Voice Agent Hackathon 2026

<!-- INNEROS-NARRATIVE:START -->
> **InnerOS role:** R&D / Hackathon Validation  
> **Lifecycle:** Submission repository  
> **Lineage:** AssemblyAI Voice Agent Hackathon 2026; reusable voice, approval, and evidence capabilities flow into the maintained VoiceOps product.
>
> VoiceOps makes speech an interface to governed InnerOS execution rather than a standalone chatbot experience.
>
> **InnerOS principle:** hackathons are validation environments. Reusable capabilities are extracted into maintained products and platform layers rather than treated as disconnected one-off projects.
<!-- INNEROS-NARRATIVE:END -->


> **Speak. Recall. Decide. Approve. Act. Verify. Remember.**

InnerOS VoiceOps is a local-first voice control plane for service operations and physical-world workflows. AssemblyAI provides realtime speech understanding; InnerOS provides context, shared operational memory, routing, policy, approval, execution, verification, and evidence. Verified outcomes can be curated into the same Personal Brain/Cognee memory fabric used by other agents.

This is the canonical hackathon repository for the **AssemblyAI Voice Agent Hackathon 2026** on lablab.ai.

## Hackathon facts

- Organizer: lablab.ai + AssemblyAI
- Format: fully online
- Build window: **September 1–30, 2026**
- Prize pool: **USD 10,000** ($5,000 cash + $5,000 AssemblyAI credits)
- Registration: open throughout the build window
- Event: https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon
- Participation/application: **approved**
- Repository: `Rafa-Innerchispa/inneros-voiceops-assemblyai`

## Product thesis

We are not building another generic voice chatbot.

**Voice is the interface. Governed execution is the product.**

The demo proves this chain:

```text
Human voice
    |
    v
AssemblyAI realtime STT
    |
    v
InnerOS Voice Gateway
    |
    +--> recall prior verified outcome (Personal Brain / Cognee)
    +--> context / policy / tenant
    +--> Resource Fabric routing
    |      |
    |      +--> local AMD inference preferred
    |      +--> external fallback only when required
    |
    v
Governed capability / MCP boundary
    |
    v
Explicit approval gate
    |
    v
Action execution
    |
    v
Audit evidence + replay + HTR
    |
    v
Curated verified outcome -> shared operational memory
    |
    v
Cross-agent recall + human-readable completion result
```

## Demo story

Primary demo scenario:

> “Ralphi, tenemos una alarma en el acceso norte. Revisa qué ocurre y abre una orden para el técnico si corresponde.”

VoiceOps should:

1. transcribe the request with AssemblyAI realtime speech;
2. receive normalized operational context from the appropriate InnerOS domain boundary;
3. route reasoning local-first;
4. propose a bounded action;
5. require explicit verbal approval before the consequential step;
6. create a **synthetic/demo work order**;
7. expose routing, decision, approval, action, replay, and HTR evidence;
8. report completion;
9. curate the verified outcome into shared operational memory;
10. prove that a second agent can recall the same correlation-bound outcome.

The public demo must never require customer PII, production credentials, or destructive actions.

## Verified state — September 22, 2026

| Capability | State | Truth boundary |
| --- | --- | --- |
| Voice Gateway session/correlation/turn state | ✅ Implemented | Tested locally |
| Explicit approval semantics | ✅ Implemented | Ambiguous/negated approval fails closed |
| Synthetic service workflow | ✅ Implemented | No production work-order writes |
| Audit evidence | ✅ Implemented | Synthetic/demo-safe evidence |
| Captured-state replay | ✅ Implemented | Replays captured evidence, not current state |
| HTR | ✅ Implemented | `MEASURED` vs `ESTIMATED` retained |
| AssemblyAI v3 realtime adapter | ✅ Implemented | Lifecycle/turn/context behavior tested |
| PCM16 mono 16 kHz audio contract | ✅ Implemented | WAV validation + microphone source support |
| Judge-facing one-screen UI | ✅ Implemented | Synthetic mode clearly labeled |
| Resource Fabric local-first route | ✅ Verified | `local-amd-5` selected |
| AMD .5 live bounded inference | ✅ Verified separately | Qwen on local vLLM; external fallback false |
| Automated tests | ✅ **107/107 PASS** | Shared-memory submission branch verification, 2026-09-22/23 |
| `compileall` | ✅ PASS | `src` + `tests`, 2026-09-22 |
| `git diff --check` | ✅ PASS | 2026-09-22 |
| Live AssemblyAI provider session | ✅ Verified | Captured in the private/local live stack; public demo remains intentionally synthetic |
| Voice-to-governed-action E2E | ✅ Verified | AssemblyAI -> InnerOS -> local AMD/Qwen -> verbal approval -> action -> Evidence/Replay |
| Public judge URL | ✅ Deployed | `https://voiceops.creatorcore.ai/` |
| Maintained VoiceOps product | ✅ Advanced after hackathon branch | `Rafa-Innerchispa/inneros-voiceops` |
| Governed FieldOps verbal-approval bridge | ✅ Integrated | `Rafa-Innerchispa/inneros-fieldops-agents-for-humans` |
| Shared operational memory bridge | ✅ Implemented | Personal Brain/Cognee live-local; truth-labeled synthetic fallback for public judging |
| Cross-agent recall | ✅ Test-covered | Verified outcome can be recalled by correlation ID after writeback |
| Pitch deck / demo video / final organizer submit | ⏳ Pending | Presentation / organizer packaging only |

### Important live truth boundary

The private/local stack has captured the live AssemblyAI -> InnerOS -> AMD .5 -> explicit approval -> governed action -> evidence loop. The public judge service deliberately remains a synthetic, production-write-disabled surface; it must not be described as using the private AMD runtime or as exposing production telephony/building controls.

The maintained VoiceOps product later completed the conversational SIP/RTP runtime and owner-confirmed end-to-end calling. That product-lineage work lives in `Rafa-Innerchispa/inneros-voiceops`; it is referenced here as post-hackathon evolution, not misrepresented as code contained in this submission repository.

No API key may be committed, printed, copied into screenshots, or stored in public evidence.

## Local-first rule

This project follows the InnerOS local-first policy:

- execute directly on local infrastructure whenever practical;
- prefer local AMD inference when capability and policy allow it;
- use external models/agents only for unsupported capability or a verified blocker;
- avoid unnecessary cloud spend;
- never weaken authorization, approval, tenant isolation, or evidence to make a demo easier.

## AssemblyAI integration

The hackathon adapter uses AssemblyAI as a first-class realtime speech layer:

- v3 realtime streaming contract;
- partial vs final turn handling;
- explicit connection lifecycle;
- controlled final-turn routing into VoiceOps;
- `agent_context` refresh after InnerOS replies;
- explicit `disconnect(terminate=True)` shutdown;
- secret-safe preflight behavior;
- PCM16 mono 16 kHz validation;
- bounded evidence that excludes the API key.

See `docs/LIVE_RUNBOOK.md`.

## InnerOS boundaries

VoiceOps does not duplicate the rest of InnerOS.

### Reused / integrated capabilities

- Resource Fabric and local-first routing;
- AMD .5 inference infrastructure;
- MCP/capability boundaries;
- service-operations concepts;
- Audit Fabric contracts;
- Forensic Replay / evidence bundles;
- Human Time Returned instrumentation;
- correlation and routing evidence;
- approval and tenant-safety concepts.

### New hackathon work

- AssemblyAI realtime adapter;
- voice session / turn state;
- voice approval UX;
- audio sources and validation;
- live demo harness;
- judge-facing web UI;
- synthetic VoiceOps workflow;
- hackathon evidence/runbooks.

Existing InnerOS capabilities are described as **reused/integrated**, not falsely claimed as hackathon-built work.

## Cross-repo boundary

Physical Guardian owns perception and normalized physical incidents/action candidates.

VoiceOps owns speech, turn handling, approval semantics, voice-to-capability routing, and presentation of execution evidence.

Service Operations owns the real work-order lifecycle.

Personal Brain owns the curated shared-memory/Cognee surface. VoiceOps can send only a bounded verified outcome over a loopback-only contract; raw transcripts, credentials, customer payloads and private infrastructure details are excluded.

The hackathon demo binds these boundaries through safe/synthetic adapters rather than copying domain logic into this repository.


## Shared operational memory

VoiceOps now demonstrates a bounded memory cycle around governed execution:

`Voice -> Recall -> Reason -> Approval -> Action -> Verify -> Remember -> Cross-agent recall`

The public judge surface defaults to a deterministic **SYNTHETIC** memory lane so the demo never pretends that Cloud Run can reach the private Cognee runtime. In the live-local stack, set `VOICEOPS_SHARED_MEMORY_MODE=live` and `PERSONAL_BRAIN_URL=http://127.0.0.1:8230`; VoiceOps then uses Personal Brain's loopback-only verified-outcome endpoints backed by its configured Cognee memory adapter.

Memory is context, never authorization. A remembered outcome cannot satisfy an approval gate, create an execution permit, or mark an action verified.

## Quick start

Requirements:

- Python 3.11+

Install development dependencies:

```bash
python3 -m pip install -e '.[dev]'
```

Run tests:

```bash
python3 -m pytest tests -q
python3 -m compileall -q src tests
git diff --check
```

Run the deterministic local demo:

```bash
voiceops-demo
```

Run the judge-facing web UI:

```bash
voiceops-web
```

The offline UI defaults to deterministic/synthetic reasoning and must remain visibly labeled as such.

## Live AssemblyAI run

Install the AssemblyAI integration:

```bash
python3 -m pip install -e '.[assemblyai]'
```

Microphone support:

```bash
python3 -m pip install -e '.[microphone]'
```

Provide the key through a secure runtime environment, **never through Git**:

```text
ASSEMBLYAI_API_KEY=<server-side secret>
```

Preflight:

```bash
voiceops-live --preflight
```

Controlled PCM16 mono 16 kHz WAV:

```bash
voiceops-live --wav path/to/demo.wav --evidence evidence/live_wav_e2e.json
```

Microphone:

```bash
voiceops-live --microphone --evidence evidence/live_microphone_e2e.json
```

See `docs/LIVE_RUNBOOK.md` before any live provider run.

## Evidence

Current evidence includes:

- AMD .5 local reasoning proof;
- Resource Fabric local route proof;
- live-audio implementation checkpoint;
- integration-boundary review;
- judge UI checkpoint;
- deterministic tests for approval, audit, gateway E2E, AssemblyAI adapter, AMD adapter, audio, web UI, and HTTP flow.

Evidence is intentionally truth-sensitive. A component being implemented does not automatically mean an external provider session has been executed.

## Repository map

```text
src/voiceops/              VoiceOps application
  adapters/                AssemblyAI + local AMD boundaries
  web/                     Judge-facing static UI
  gateway.py               Session/turn orchestration
  approval.py              Explicit approval semantics
  audit.py                 Evidence integration
  audio.py                 WAV/microphone sources
  live_demo.py             Live AssemblyAI harness
  webapp.py                Judge demo server
  workflows.py             Synthetic governed workflow

tests/                     Automated verification
docs/                      Architecture, runbooks, demo/submission docs
evidence/                  Sanitized checkpoints and measured evidence
```

## Security and truth policy

- Never commit API keys, tokens, credential-bearing URLs, customer identifiers, or private recordings.
- Public evidence uses synthetic or explicitly sanitized data.
- `MEASURED` means backed by captured measurements.
- `ESTIMATED` stays labeled as an estimate.
- Replay never silently fetches current state and presents it as historical state.
- Public demo actions remain synthetic unless a separate production authorization model is introduced outside the hackathon surface.

## Definition of done

The technical core is submission-ready. Final organizer closure now requires only:

- [x] live AssemblyAI / governed-action evidence;
- [x] exact-current-tree automated verification;
- [x] bounded committed-secret regression scan;
- [x] public judge-safe URL;
- [x] final submission copy and judge instructions;
- [ ] cover / architecture media;
- [ ] fresh judge screenshots;
- [ ] demo video;
- [ ] pitch deck/media upload if accepted by the organizer form;
- [ ] verify team/project attachment on lablab.ai;
- [ ] final lablab.ai submission.

The canonical detailed checklist is `docs/HACKATHON_CHECKLIST.md`.

## Canonical resume order

When resuming development, read:

1. `README.md`
2. `docs/PROJECT_CANONICAL.md`
3. `docs/HACKATHON_CHECKLIST.md`
4. `docs/LIVE_RUNBOOK.md`
5. `docs/ARCHITECTURE.md`
6. `docs/DEMO_SCRIPT.md`
7. latest files under `evidence/`

Then continue from the first incomplete P0 item instead of redesigning the project from memory.

## License

Apache-2.0. See `LICENSE`.
