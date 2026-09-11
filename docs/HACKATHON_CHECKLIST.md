# Hackathon Checklist

Last verified: 2026-09-10

Legend:
- `[x]` verified or implemented with evidence in this repository/runtime.
- `[ ]` still required before final submission.
- Live-provider claims stay unchecked until a real provider session is captured.

## Registration
- [x] Participation/application approved for the AssemblyAI Voice Agent Hackathon.
- [ ] Team created/joined on lablab.ai and project attached to that team.
- [ ] Team/project name aligned with **InnerOS VoiceOps** on the event page.
- [x] Organizer email/announcements checked as of 2026-09-10.

## Technology
- [x] AssemblyAI is visibly and materially used through the v3 realtime adapter.
- [x] Realtime streaming lifecycle, partial/final turn handling, shutdown, and agent-context refresh are implemented and covered by tests.
- [x] Speech context / `agent_context` integration is implemented where useful.
- [x] Local-first routing is preserved and AMD .5 live local inference has separate evidence.
- [x] Failure behavior and secret handling are documented.
- [ ] Real AssemblyAI v3 session captured with provider session/termination evidence.
- [ ] Controlled WAV transcription captured end-to-end.
- [ ] Real microphone transcription captured end-to-end.
- [ ] Live STT / reasoning / action latency recorded from the same E2E run.

## Product
- [x] One complete synthetic voice-to-action workflow exists.
- [x] Approval gate is explicit and fails closed on ambiguous/negated approval.
- [x] Business outcome is visible as a synthetic/demo work order.
- [x] HTR is visible with MEASURED vs ESTIMATED truth boundaries.
- [x] Evidence/audit output is visible.
- [x] Captured-evidence replay path is visible.
- [x] Judge-facing one-screen UI exists.
- [ ] Same workflow demonstrated with a live AssemblyAI speech session.

## Safety
- [x] Synthetic demo data only in public artifacts.
- [x] No customer PII in repository evidence.
- [x] No committed AssemblyAI keys or other secrets.
- [x] Demo action target is synthetic; no production work-order writes.
- [x] Public-facing workflow cannot directly expose production building controls.
- [x] Approval/policy boundaries remain in the execution path.

## Repository
- [x] Public repository created.
- [x] README present.
- [x] Apache-2.0 license present.
- [x] Canonical project doc present.
- [x] Roadmap present.
- [x] Architecture doc present.
- [x] Demo script present.
- [x] Live runbook present.
- [x] Automated local test suite passes: **35/35** on 2026-09-10.
- [x] `python3 -m compileall -q src tests` passes on 2026-09-10.
- [x] `git diff --check` passes on 2026-09-10.
- [ ] Clean-clone setup instructions verified on a fresh environment.
- [ ] GitHub CI workflow added and green, or omission explicitly documented.
- [ ] Release / merge SHA recorded after integration to `main`.

## Presentation
- [ ] Cover image.
- [ ] Architecture image suitable for submission/media.
- [ ] Judge UI screenshots from a live or clearly labeled synthetic run.
- [ ] Pitch deck.
- [ ] Demo video.
- [ ] Spoken pitch/demo script finalized.
- [x] Concise judge testing instructions exist in `docs/JUDGE_UI.md` / runbook.

## Submission
- [ ] Final title.
- [ ] Short description.
- [ ] Long description.
- [ ] Technologies list.
- [x] Public repo URL exists.
- [ ] Public demo URL.
- [ ] Video URL.
- [ ] Pitch deck / media links.
- [ ] Team information.
- [x] Existing-vs-new work disclosure is documented in README/canonical docs.
- [ ] Final submission confirmed on lablab.ai.

## Final verification
- [ ] Open public demo in a clean browser.
- [ ] Clone repo fresh and follow README from zero.
- [x] Run local tests on current E2E branch.
- [ ] Run live AssemblyAI provider smoke test with sanitized evidence.
- [ ] Run secret scan over the exact release tree.
- [ ] Verify all public claims against captured evidence.
- [ ] Verify final deadline/timezone on organizer page immediately before submission.
- [ ] Submit before the final-day rush.

## Current P0

1. Inject/use the AssemblyAI credential server-side without committing or printing it.
2. Capture one controlled live WAV E2E, then one microphone E2E.
3. Record sanitized timing/session evidence.
4. Merge the validated E2E branch to `main`.
5. Publish judge-safe demo and finish media/submission package.
