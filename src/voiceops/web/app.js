const $ = (id) => document.getElementById(id);

const els = {
  runBtn: $("runBtn"), approveBtn: $("approveBtn"), ambiguousBtn: $("ambiguousBtn"), resetBtn: $("resetBtn"),
  evidenceBtn: $("evidenceBtn"), replayBtn: $("replayBtn"), closeDialog: $("closeDialog"),
  dialog: $("jsonDialog"), dialogTitle: $("dialogTitle"), jsonOutput: $("jsonOutput"),
  demoStatus: $("demoStatus"), voiceState: $("voiceState"), guardianState: $("guardianState"), amdState: $("amdState"), actionState: $("actionState"),
  transcript: $("transcript"), guardianEmpty: $("guardianEmpty"), guardianData: $("guardianData"),
  reasoningTitle: $("reasoningTitle"), routeProvider: $("routeProvider"), routeModel: $("routeModel"),
  routePolicy: $("routePolicy"), routeFallback: $("routeFallback"), routeTruth: $("routeTruth"),
  proposalEmpty: $("proposalEmpty"), proposalData: $("proposalData"), approvalGate: $("approvalGate"), actionResult: $("actionResult"),
  timeline: $("timeline"), htrBox: $("htrBox"), sessionId: $("sessionId"), correlationId: $("correlationId"),
  liveVoiceBtn: $("liveVoiceBtn"), stopVoiceBtn: $("stopVoiceBtn"), voiceAgentStatus: $("voiceAgentStatus"), agentTranscript: $("agentTranscript"),
  coreActionLabel: $("coreActionLabel"),
  orbitAssembly: $("orbitAssembly"), orbitRecall: $("orbitRecall"), orbitSystem: $("orbitSystem"), orbitReason: $("orbitReason"), orbitPermit: $("orbitPermit"), orbitProof: $("orbitProof"),
  connAssembly: $("connAssembly"), connMemory: $("connMemory"), connSystem: $("connSystem"), connReason: $("connReason"), connGuardian: $("connGuardian"),
  memoryBeforeTruth: $("memoryBeforeTruth"), memoryBeforeProvider: $("memoryBeforeProvider"), memoryBeforeCount: $("memoryBeforeCount"), memoryBeforeSummary: $("memoryBeforeSummary"),
  memoryAfterTruth: $("memoryAfterTruth"), memoryAfterProvider: $("memoryAfterProvider"), memoryAfterCount: $("memoryAfterCount"), memoryAfterSummary: $("memoryAfterSummary"),
  flowVoice: $("flowVoice"), flowMemory: $("flowMemory"), flowReason: $("flowReason"), flowApprove: $("flowApprove"), flowAct: $("flowAct"), flowVerify: $("flowVerify"), flowShare: $("flowShare"),
  deploymentBadge: $("deploymentBadge"), cloudPlaneCard: $("cloudPlaneCard"), localPlaneCard: $("localPlaneCard"),
  runtimeModeLabel: $("runtimeModeLabel"), runtimeCompute: $("runtimeCompute"), runtimeInference: $("runtimeInference"), runtimeBoundary: $("runtimeBoundary"),
  provVoiceProvider: $("provVoiceProvider"), provVoiceWs: $("provVoiceWs"), provSession: $("provSession"),
  provEvents: $("provEvents"), provFrames: $("provFrames"), provReason: $("provReason"), provReasonDetail: $("provReasonDetail"),
  provFallbackBadge: $("provFallbackBadge"), provAction: $("provAction"), provActionDetail: $("provActionDetail"),
  translationDirection: $("translationDirection"), translationUser: $("translationUser"), translationAgent: $("translationAgent"),
  verifyVoicePath: $("verifyVoicePath"), verifyFallback: $("verifyFallback"), verifyAction: $("verifyAction")
};
let currentState = null;

async function api(path, options = {}) {
  const response = await fetch(path, {headers: {"Content-Type": "application/json"}, ...options});
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
  return payload;
}

function setState(el, label, kind = "") {
  el.textContent = label;
  el.className = `state ${kind}`.trim();
}

function row(label, value) {
  const div = document.createElement("div");
  div.className = "data-row";
  const left = document.createElement("span");
  left.textContent = label;
  const right = document.createElement("strong");
  right.textContent = value ?? "—";
  div.append(left, right);
  return div;
}

function renderConnections(state = {}) {
  if (els.connAssembly) els.connAssembly.textContent = state.assemblyai_voice_agent_enabled ? "LIVE" : "OFF";
  const memoryMode = state.shared_memory?.bridge?.mode || "unknown";
  if (els.connMemory) els.connMemory.textContent = memoryMode === "live" ? "LIVE" : memoryMode.toUpperCase();
  const systemOk = Boolean(state.live_system?.bridge?.ok);
  if (els.connSystem) els.connSystem.textContent = systemOk ? "LIVE" : "CHECK";
  if (els.connReason) els.connReason.textContent = state.deployment?.local_inference ? "LOCAL" : "SAFE";
  if (els.connGuardian) els.connGuardian.textContent = "EVENT BRIDGE";
}

function renderDeployment(profile = {}) {
  if (!profile || !profile.mode) return;
  const isCloud = profile.mode === "cloud_run";
  const isLocal = profile.mode === "sovereign_local";

  if (els.deploymentBadge) {
    els.deploymentBadge.textContent = `● ${profile.label || "RUNTIME"}`;
    els.deploymentBadge.className = "badge deployment-badge";
    if (isCloud) els.deploymentBadge.classList.add("cloud-active");
    if (isLocal) els.deploymentBadge.classList.add("local-active");
  }
  if (els.cloudPlaneCard) els.cloudPlaneCard.classList.toggle("is-active", isCloud);
  if (els.localPlaneCard) els.localPlaneCard.classList.toggle("is-active", isLocal);
  if (els.runtimeModeLabel) els.runtimeModeLabel.textContent = profile.surface || profile.label || "VoiceOps runtime";
  if (els.runtimeCompute) els.runtimeCompute.textContent = profile.compute || "—";
  if (els.runtimeInference) els.runtimeInference.textContent = profile.inference || "—";
  if (els.runtimeBoundary) els.runtimeBoundary.textContent = profile.data_boundary || "—";
}

function renderGuardian(guardian) {
  if (!guardian || !Object.keys(guardian).length) {
    els.guardianEmpty.classList.remove("hidden");
    els.guardianData.classList.add("hidden");
    els.guardianData.replaceChildren();
    setState(els.guardianState, "WAITING");
    return;
  }
  els.guardianEmpty.classList.add("hidden");
  els.guardianData.classList.remove("hidden");
  els.guardianData.replaceChildren(
    row("Contract", guardian.contract_projection || "NormalizedEvent"),
    row("Event", guardian.event_type), row("Severity", guardian.severity),
    row("Source", guardian.source_id), row("Zone", guardian.zone_id), row("Owner", guardian.contract_owner)
  );
  setState(els.guardianState, "EVENT RECEIVED", "ready");
}

function renderRoute(route) {
  if (!route || !Object.keys(route).length) {
    els.reasoningTitle.textContent = "InnerOS reasoner";
    els.routeProvider.textContent = "—"; els.routeModel.textContent = "—"; els.routePolicy.textContent = "—";
    els.routeFallback.textContent = "—"; els.routeTruth.textContent = "—";
    setState(els.amdState, "WAITING");
    return;
  }
  const provider = route.provider || "unknown";
  const model = route.model || "deterministic fixture";
  const policy = route.policy || route.execution_policy || "local_first";
  const fallback = route.external_fallback ?? route.external_needed ?? false;
  const truth = route.truth || (provider === "local-amd-5" ? "LIVE" : "UNCLASSIFIED");
  els.routeProvider.textContent = provider; els.routeModel.textContent = model; els.routePolicy.textContent = policy;
  els.routeFallback.textContent = fallback ? "YES" : "NONE"; els.routeTruth.textContent = truth;
  if (provider === "local-amd-5" && truth === "LIVE_MODEL_RESPONSE") {
    els.reasoningTitle.textContent = "AMD .5 local reasoning";
    setState(els.amdState, "AMD .5 LIVE", "active");
  } else if (provider === "local-intel-4" && truth === "LIVE_MODEL_RESPONSE") {
    els.reasoningTitle.textContent = "Intel / Qwen local reasoning";
    setState(els.amdState, "QWEN LOCAL", "active");
  } else if (truth === "SYNTHETIC") {
    els.reasoningTitle.textContent = "Offline-safe reasoner";
    setState(els.amdState, "SYNTHETIC", "warning");
  } else {
    els.reasoningTitle.textContent = "InnerOS reasoning route";
    setState(els.amdState, "ROUTED", "active");
  }
}

function truthKind(truth) {
  if (truth === "LIVE") return "success";
  if (truth === "SYNTHETIC" || truth === "REPLAY") return "warning";
  if (truth === "UNVERIFIED") return "blocked";
  return "";
}

function setFlow(el, active, complete = false) {
  if (!el) return;
  el.className = "flow-step";
  if (complete) el.classList.add("complete");
  else if (active) el.classList.add("active");
}

function setOrbit(el, active, complete = false) {
  if (!el) return;
  el.classList.toggle("active", Boolean(active) && !complete);
  el.classList.toggle("complete", Boolean(complete));
}

function renderMemory(state) {
  const shared = state.shared_memory || {};
  const before = shared.before_action || {};
  const writeback = shared.writeback || {};
  const cross = shared.cross_agent_recall || {};

  const beforeTruth = before.truth || "WAITING";
  setState(els.memoryBeforeTruth, beforeTruth, truthKind(beforeTruth));
  els.memoryBeforeProvider.textContent = before.provider || shared.bridge?.provider || "—";
  els.memoryBeforeCount.textContent = before.count ?? "—";
  const firstBefore = Array.isArray(before.hits) && before.hits.length ? before.hits[0] : null;
  els.memoryBeforeSummary.textContent = firstBefore?.summary || (
    before.status === "unavailable"
      ? "Live shared memory is unavailable for this run. No memory is treated as authorization."
      : "No prior operational memory recalled yet."
  );

  const afterTruth = cross.truth || writeback.truth || "WAITING";
  setState(els.memoryAfterTruth, afterTruth, truthKind(afterTruth));
  els.memoryAfterProvider.textContent = cross.provider || writeback.provider || shared.bridge?.provider || "—";
  els.memoryAfterCount.textContent = cross.count ?? (writeback.stored ? 0 : "—");
  const firstAfter = Array.isArray(cross.hits) && cross.hits.length ? cross.hits[0] : null;
  els.memoryAfterSummary.textContent = firstAfter?.summary || (
    writeback.stored
      ? `Verified outcome stored as ${writeback.memory_id || "shared memory"}; waiting for recall proof.`
      : "A verified outcome will be stored only after explicit approval and recorded execution."
  );

  setFlow(els.flowVoice, Boolean(state.transcript), Boolean(state.transcript));
  setFlow(els.flowMemory, Boolean(before.status), Boolean(before.count));
  setFlow(els.flowReason, Boolean(state.route && Object.keys(state.route).length), Boolean(state.proposal));
  setFlow(els.flowApprove, Boolean(state.pending_approval || state.approval), Boolean(state.approval?.approved));
  setFlow(els.flowAct, Boolean(state.action), Boolean(state.action));
  setFlow(els.flowVerify, Boolean(writeback.status || state.action), Boolean(writeback.verification_passed));
  setFlow(els.flowShare, Boolean(cross.status), Boolean(cross.count));
  setOrbit(els.orbitAssembly, Boolean(state.transcript) || voiceAgent.ready, Boolean(state.transcript));
  setOrbit(els.orbitRecall, Boolean(before.status), Boolean(before.count));
  setOrbit(els.orbitSystem, Boolean(state.live_system?.last_query), Boolean(state.live_system?.last_query?.ok));
  setOrbit(els.orbitReason, Boolean(state.route && Object.keys(state.route).length), Boolean(state.proposal));
  setOrbit(els.orbitPermit, Boolean(state.pending_approval || state.approval), Boolean(state.action));
  setOrbit(els.orbitProof, Boolean(state.action || writeback.status), Boolean(writeback.verification_passed || state.action));
}

function renderProposal(state) {
  const proposal = state.proposal;
  els.approvalGate.classList.add("hidden"); els.actionResult.classList.add("hidden");
  if (!proposal) {
    els.proposalEmpty.classList.remove("hidden"); els.proposalData.classList.add("hidden");
    els.proposalData.replaceChildren(); setState(els.actionState, "WAITING"); return;
  }
  els.proposalEmpty.classList.add("hidden"); els.proposalData.classList.remove("hidden");
  els.proposalData.replaceChildren(
    row("Action", proposal.action_type),
    row("Target", proposal.payload?.name_or_entity || proposal.payload?.entity_id || proposal.payload?.scene || proposal.payload?.priority || "—"),
    row("Reason", proposal.payload?.reason_code || (proposal.action_type?.startsWith("ha_") || proposal.action_type?.startsWith("dmx_") ? "LIVE SYSTEM ACTION" : "—")),
    row("Approval", proposal.requires_approval ? "REQUIRED" : "NOT REQUIRED")
  );
  if (state.action) {
    setState(els.actionState, "EXECUTED", "success"); els.actionResult.classList.remove("hidden");
    els.actionResult.textContent = `✓ ${state.action.action_id} · ${state.action.status.toUpperCase()}`;
  } else if (state.approval && !state.approval.approved) {
    setState(els.actionState, "BLOCKED", "blocked"); els.approvalGate.classList.remove("hidden");
    els.approvalGate.textContent = `BLOCKED · ${state.approval.reason}`;
  } else if (state.pending_approval) {
    setState(els.actionState, "APPROVAL REQUIRED", "warning"); els.approvalGate.classList.remove("hidden");
    els.approvalGate.textContent = "HUMAN APPROVAL REQUIRED · ACTION NOT EXECUTED";
  } else setState(els.actionState, "PROPOSED", "active");
}

function renderTimeline(items = []) {
  els.timeline.replaceChildren();
  if (!items.length) {
    const div = document.createElement("div"); div.className = "empty"; div.textContent = "Evidence timeline will appear here.";
    els.timeline.append(div); return;
  }
  const start = new Date(items[0].at).getTime();
  items.forEach((item) => {
    const t = Math.max(0, new Date(item.at).getTime() - start);
    const div = document.createElement("div"); div.className = "timeline-item";
    const time = document.createElement("div"); time.className = "timeline-time"; time.textContent = `+${(t / 1000).toFixed(3)}s`;
    const body = document.createElement("div"); const kind = document.createElement("div"); kind.className = "timeline-kind";
    kind.textContent = item.kind.replaceAll("_", " ").toUpperCase();
    const detail = document.createElement("div"); detail.className = "timeline-detail"; const safe = {...(item.data || {})};
    if (safe.snapshot) safe.snapshot = "[captured normalized Guardian snapshot]";
    if (safe.transcript) safe.transcript = `“${safe.transcript}”`; detail.textContent = JSON.stringify(safe);
    body.append(kind, detail); div.append(time, body); els.timeline.append(div);
  });
}

function render(state) {
  currentState = state;
  renderDeployment(state.deployment);
  renderConnections(state);
  renderProvenance(state);
  els.sessionId.textContent = state.session_id; els.correlationId.textContent = state.correlation_id;
  if (!voiceAgent.liveTranscriptActive) els.transcript.textContent = state.transcript || "No transcript yet.";
  if (state.transcript && !voiceAgent.liveTranscriptActive) setState(els.voiceState, "FINAL TRANSCRIPT", "ready");
  else if (!voiceAgent.ready) setState(els.voiceState, "READY", "ready");
  renderGuardian(state.guardian); renderRoute(state.route); renderMemory(state); renderProposal(state); renderTimeline(state.timeline);
  els.approveBtn.disabled = !state.pending_approval; els.ambiguousBtn.disabled = !state.pending_approval; els.runBtn.disabled = state.pending_approval;
  if (state.action) els.demoStatus.textContent = `Completed: ${state.action.action_id}. Evidence sealed for replay.`;
  else if (state.approval && !state.approval.approved) els.demoStatus.textContent = "Ambiguous authorization was blocked. Explicit approval is still required.";
  else if (state.pending_approval) {
    const isLiveAction = String(state.proposal?.action_type || "").startsWith("ha_") || String(state.proposal?.action_type || "").startsWith("dmx_");
    els.demoStatus.textContent = isLiveAction
      ? "Live action ready. Say “Sí, autorizo” / “Yes, authorize” or press Permit + Act."
      : "Proposal ready. InnerOS is waiting for explicit human approval.";
  } else els.demoStatus.textContent = state.proposal ? "Action proposed." : "Ready for a live system question or action.";
  if (state.htr) {
    const saved = Math.max(0, Math.round(state.htr.saved_seconds));
    els.htrBox.innerHTML = `<strong>HTR ${state.htr.classification}</strong> · ${saved}s returned · VoiceOps active ${state.htr.human_active_seconds.toFixed(2)}s`;
  } else els.htrBox.textContent = "HTR appears after an approved action.";
  if (state.assemblyai_voice_agent_enabled === false && !voiceAgent.ready) {
    els.liveVoiceBtn.title = "Start the server with --enable-live-assemblyai and configure ASSEMBLYAI_API_KEY server-side.";
  }
}

async function refresh() { try { render(await api("/api/state")); } catch (err) { els.demoStatus.textContent = `Error: ${err.message}`; } }
async function postTranscript(path, transcript) {
  els.demoStatus.textContent = "Processing governed execution trace…";
  try { render(await api(path, {method: "POST", body: JSON.stringify({transcript})})); }
  catch (err) { els.demoStatus.textContent = `Error: ${err.message}`; }
}

els.runBtn.addEventListener("click", () => {
  voiceAgent.fallbackActivations += 1;
  renderProvenance(currentState || {});
  postTranscript("/api/intent", "Ralphi, revisa la incidencia del acceso norte y abre una orden tecnica si corresponde.");
});
els.approveBtn.addEventListener("click", async () => {
  try {
    const result = await api("/api/tool/approve-pending", {method: "POST", body: JSON.stringify({authorization_phrase: "Sí, autorizo. Yes, authorize."})});
    await refresh();
    notifyVoiceAgentOfExternalAction(result, "button");
    els.agentTranscript.textContent = result.action ? `Authorized · ${result.action.action_id} · ${result.action.status} · model context updated` : "Authorization processed.";
  } catch (err) { els.demoStatus.textContent = `Error: ${err.message}`; }
});
els.ambiguousBtn.addEventListener("click", () => postTranscript("/api/approve", "Si crees que hace falta."));
els.resetBtn.addEventListener("click", async () => render(await api("/api/reset", {method: "POST", body: "{}"})));
els.evidenceBtn.addEventListener("click", async () => { els.dialogTitle.textContent = "Decision Evidence Bundle"; els.jsonOutput.textContent = JSON.stringify(await api("/api/evidence"), null, 2); els.dialog.showModal(); });
els.replayBtn.addEventListener("click", async () => { els.dialogTitle.textContent = "Forensic Replay · Captured Evidence Only"; els.jsonOutput.textContent = JSON.stringify(await api("/api/replay"), null, 2); els.dialog.showModal(); });
els.closeDialog.addEventListener("click", () => els.dialog.close());

const voiceAgent = {
  ws: null, mediaStream: null, audioCtx: null, processor: null, source: null, silentGain: null,
  ready: false, sessionId: null, lastFinalUserTranscript: "", pendingToolCalls: [], handledToolCallIds: new Set(), scheduledAudio: [], nextPlaybackTime: 0,
  liveTranscriptActive: false, eventCount: 0, audioFramesSent: 0, detectedLanguage: "auto",
  fallbackActivations: 0, lastExternalActionResult: null,
  configuredVoice: null, configuredLanguage: null, turnFinalAt: 0, replyStartedAt: 0, firstAudioAt: 0
};

const systemStatusTool = {
  type: "function", name: "query_live_inneros", execution_mode: "interactive",
  description: "Use this for current or real-time questions about InnerOS, Home Assistant, cameras, lights, switches, servers, infrastructure, clients, tasks, DMX, alarm status, or any connected system. This tool is read-only. Never invent a device, incident, or current state.",
  parameters: {type: "object", properties: {}, required: []}
};
const systemActionTool = {
  type: "function", name: "propose_live_inneros_action", execution_mode: "interactive",
  description: "Use this when the user asks to change a real connected system, such as turning a Home Assistant light on/off or applying a DMX scene. This only proposes the exact action and MUST NOT execute it. After a proposal, ask for explicit approval by voice or the Permit + Act planet.",
  parameters: {type: "object", properties: {}, required: []}
};
const inspectTool = {
  type: "function", name: "inspect_and_propose_action", execution_mode: "interactive",
  description: "Judge-safe synthetic work-order fallback only. Do not use this for normal live voice questions or real devices. Use query_live_inneros for real current state.",
  parameters: {type: "object", properties: {}, required: []}
};
const recallTool = {
  type: "function", name: "recall_verified_context", execution_mode: "interactive",
  description: "Call this for questions about memory, prior verified outcomes, what InnerOS remembers, or operational history. It is read-only and never authorizes an action.",
  parameters: {type: "object", properties: {}, required: []}
};
const approveTool = {
  type: "function", name: "approve_pending_action", execution_mode: "interactive",
  description: "Call this only when an action proposal is already pending AND the user's latest finalized words explicitly authorize it, for example 'sí, autorizo'. Never call it for vague, conditional, implied, or agent-generated approval.",
  parameters: {type: "object", properties: {}, required: []}
};

function voiceAgentConfig() {
  const uiLanguage = localStorage.getItem("voiceops_ui_lang") === "es" ? "es" : "en";
  const voice = uiLanguage === "es" ? "lola" : "alba";
  const languageCodes = uiLanguage === "es" ? ["es", "en"] : ["en", "es"];
  voiceAgent.configuredVoice = voice;
  voiceAgent.configuredLanguage = uiLanguage;
  return {type: "session.update", session: {
    system_prompt: [
      `You are the InnerOS VoiceOps voice interface. The preferred session language is ${uiLanguage === "es" ? "Spanish" : "English"}. Detect the language of each finalized user turn. If the turn is English, answer only in fluent natural English. If the turn is Spanish, answer only in natural Latin American Spanish. Never answer with generic small-talk when the user asks who you are: identify yourself briefly as InnerOS VoiceOps. Do not drift between languages unless the user clearly code-switches.`,
      "For CURRENT or REAL-TIME state of InnerOS, Home Assistant, cameras, lights, switches, servers, clients, tasks, DMX or alarm status, call query_live_inneros. Never invent a device, incident, or system state.",
      "For remembered or historical verified outcomes, call recall_verified_context.",
      "For a request that CHANGES a connected live system, call propose_live_inneros_action. Never claim the change happened until approve_pending_action returns a completed live result.",
      "When an action is pending, clearly tell the user they can say 'Sí, autorizo' / 'Yes, authorize' OR press the Permit + Act planet.",
      "Do not use the synthetic work-order fallback during normal live voice conversation.",
      "Keep answers short, concrete, and based on tool results."
    ].join(" "),
    greeting: uiLanguage === "es" ? "VoiceOps listo." : "VoiceOps ready.",
    output: {voice, format: {encoding: "audio/pcm"}, volume: 100},
    input: {
      format: {encoding: "audio/pcm"},
      keyterms: ["InnerOS", "VoiceOps", "Ralphi", "Home Assistant", "AssemblyAI", "Cognee", "DMX", "Intelbras", "sí autorizo", "yes authorize"],
      language_codes: ["en", "es"],
      transcription_mode: "min_latency",
      transcription_prompt: "InnerOS VoiceOps for smart homes and buildings. Expect Home Assistant, MCP, AssemblyAI, cameras, lights, networks, permits and verification.",
      voice_focus: "near-field",
      turn_detection: {interrupt_response: true}
    },
    tools: [systemStatusTool, recallTool, systemActionTool]
  }};
}

function phaseUpdate(phase) {
  if (phase === "approval") return {type: "session.update", session: {
    system_prompt: "A live action is pending. Reply in the user's language. Explain the exact proposed action and say clearly: you can say 'Sí, autorizo' / 'Yes, authorize' OR press the Permit + Act planet. If the latest user turn explicitly authorizes, including 'autorizar', 'autoriza', 'autorizo', 'authorize' or 'approve', call approve_pending_action. Never claim success before the tool result.",
    tools: [systemStatusTool, recallTool, approveTool]
  }};
  return {type: "session.update", session: {
    system_prompt: "The governed operation is complete. Reply in the user's language and confirm only what the tool result proves. You may continue with read-only live queries or propose a new live action, which requires a new approval.",
    tools: [systemStatusTool, recallTool, systemActionTool]
  }};
}

function setLiveStatus(text, kind = "") { els.voiceAgentStatus.textContent = text; els.voiceAgentStatus.className = kind ? `live-status ${kind}` : "live-status"; }


function detectTurnLanguage(text = "") {
  const normalized = String(text).toLowerCase();
  const spanishSignals = [" el "," la "," los "," las "," que "," por "," para "," quiero "," necesito "," enciende "," apaga "," reinicia "," cámara "," luz "," sí "," autorizo "," casa "];
  const englishSignals = [" the "," is "," are "," turn "," on "," off "," restart "," camera "," light "," please "," yes "," authorize "," home "," network "];
  const padded = ` ${normalized} `;
  const es = spanishSignals.reduce((score, token) => score + (padded.includes(token) ? 1 : 0), 0);
  const en = englishSignals.reduce((score, token) => score + (padded.includes(token) ? 1 : 0), 0);
  if (es === en) return voiceAgent.detectedLanguage === "auto" ? "en" : voiceAgent.detectedLanguage;
  return es > en ? "es" : "en";
}

function renderProvenance(state = currentState || {}) {
  if (els.provVoiceProvider) {
    const voiceLabel = voiceAgent.configuredVoice ? ` · ${voiceAgent.configuredVoice}` : "";
    els.provVoiceProvider.textContent = voiceAgent.ready ? `AssemblyAI · LIVE${voiceLabel}` : (state.assemblyai_voice_agent_enabled ? "AssemblyAI · READY" : "AssemblyAI · OFF");
  }
  if (els.provVoiceWs) els.provVoiceWs.textContent = voiceAgent.ws ? "wss://agents.assemblyai.com/v1/ws" : "wss://agents.assemblyai.com · not connected";
  if (els.provSession) els.provSession.textContent = voiceAgent.sessionId || "OFFLINE";
  if (els.provEvents) els.provEvents.textContent = String(voiceAgent.eventCount);
  if (els.provFrames) els.provFrames.textContent = String(voiceAgent.audioFramesSent);

  const route = state.route || {};
  const deployment = state.deployment || {};
  const provider = route.provider || (deployment.local_inference ? "local-intel-4" : "unknown");
  const model = route.model || deployment.inference || "Local Qwen";
  if (els.provReason) els.provReason.textContent = provider.includes("local") ? "InnerOS · Local" : provider;
  if (els.provReasonDetail) els.provReasonDetail.textContent = model;

  const fallback = Boolean(route.external_fallback ?? route.external_needed ?? false) || voiceAgent.fallbackActivations > 0;
  if (els.provFallbackBadge) {
    els.provFallbackBadge.textContent = fallback ? "FALLBACK · ACTIVE" : "FALLBACK · NONE";
    els.provFallbackBadge.className = `provenance-badge ${fallback ? "warning" : "safe"}`;
  }
  if (els.verifyFallback) els.verifyFallback.textContent = fallback ? "ACTIVE" : "NONE";
  if (els.verifyVoicePath) {
    const wsState = voiceAgent.ws?.readyState === WebSocket.OPEN ? "WS CONNECTED" : (state.assemblyai_voice_agent_enabled ? "READY" : "OFF");
    els.verifyVoicePath.textContent = `AssemblyAI · ${wsState}`;
  }

  const action = state.action || voiceAgent.lastExternalActionResult?.action || null;
  if (els.provAction) els.provAction.textContent = action ? `${action.action_id || action.tool || "action"} · ${String(action.status || "completed").toUpperCase()}` : "No action yet";
  if (els.verifyAction) els.verifyAction.textContent = action ? `${action.action_type || action.tool || "action"} · ${String(action.status || "completed").toUpperCase()}` : "No action yet";
  if (els.provActionDetail) {
    if (action) els.provActionDetail.textContent = "explicit permit · executed · verified";
    else els.provActionDetail.textContent = "approval · execution · verification";
  }
}

function notifyVoiceAgentOfExternalAction(result, source = "button") {
  voiceAgent.lastExternalActionResult = result || {};
  renderProvenance(currentState || {});
  const action = result?.action || {};
  const summary = {
    source,
    action_id: action.action_id || null,
    status: action.status || result?.status || "completed",
    verification: result?.verification || result?.live_result || null
  };
  if (voiceAgent.ws && voiceAgent.ws.readyState === WebSocket.OPEN) {
    const lang = voiceAgent.detectedLanguage === "es" ? "Spanish" : "English";
    voiceAgent.ws.send(JSON.stringify({type: "session.update", session: {
      system_prompt: `A governed action was just executed outside the voice tool-call path via ${source}. Treat this as authoritative verified runtime context for the next turn. Result: ${JSON.stringify(summary)}. Respond in ${lang}. Never claim anything beyond this verified result.`
    }}));
  }
}

function setVoiceCoreState(state, statusText = "") {
  if (!els.liveVoiceBtn) return;
  els.liveVoiceBtn.dataset.state = state;
  const active = ["connecting", "ready", "user-speaking", "agent-speaking"].includes(state);
  els.liveVoiceBtn.setAttribute("aria-label", active ? "Stop live voice" : "Start live voice");
  if (els.coreActionLabel) {
    if (state === "idle") els.coreActionLabel.textContent = "PRESS FOR LIVE VOICE";
    else if (state === "connecting") els.coreActionLabel.textContent = "CONNECTING…";
    else if (state === "error") els.coreActionLabel.textContent = "PRESS TO RETRY";
    else els.coreActionLabel.textContent = "PRESS TO STOP";
  }
  if (statusText) setLiveStatus(statusText, state === "error" ? "blocked" : active ? "active" : "");
}

function pcm16Base64(floatSamples, inputRate) {
  const ratio = inputRate / 24000; const outputLength = Math.max(1, Math.floor(floatSamples.length / ratio));
  const pcm = new Int16Array(outputLength);
  for (let i = 0; i < outputLength; i += 1) {
    const sample = Math.max(-1, Math.min(1, floatSamples[Math.min(floatSamples.length - 1, Math.floor(i * ratio))]));
    pcm[i] = sample < 0 ? Math.round(sample * 32768) : Math.round(sample * 32767);
  }
  const bytes = new Uint8Array(pcm.buffer); let binary = "";
  for (let i = 0; i < bytes.length; i += 0x8000) binary += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(binary);
}

function playVoiceAgentAudio(data) {
  if (!voiceAgent.audioCtx) return;
  setVoiceCoreState("agent-speaking", "INNEROS SPEAKING · PRESS CORE TO STOP");
  setState(els.voiceState, "SPEAKING", "active");
  const binary = atob(data); const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
  const pcm = new Int16Array(bytes.buffer); const buffer = voiceAgent.audioCtx.createBuffer(1, pcm.length, 24000);
  const channel = buffer.getChannelData(0); for (let i = 0; i < pcm.length; i += 1) channel[i] = pcm[i] / 32768;
  const source = voiceAgent.audioCtx.createBufferSource(); source.buffer = buffer; source.connect(voiceAgent.audioCtx.destination);
  const startAt = Math.max(voiceAgent.audioCtx.currentTime, voiceAgent.nextPlaybackTime); source.start(startAt);
  voiceAgent.nextPlaybackTime = startAt + buffer.duration; voiceAgent.scheduledAudio.push(source);
  source.onended = () => {
    voiceAgent.scheduledAudio = voiceAgent.scheduledAudio.filter((item) => item !== source);
    if (!voiceAgent.scheduledAudio.length && voiceAgent.ready) {
      setVoiceCoreState("ready", `LIVE · ${voiceAgent.sessionId}`);
      setState(els.voiceState, "LISTENING", "ready");
    }
  };
}

function flushVoicePlayback() {
  for (const source of voiceAgent.scheduledAudio) { try { source.stop(); } catch (_) {} }
  voiceAgent.scheduledAudio = []; if (voiceAgent.audioCtx) voiceAgent.nextPlaybackTime = voiceAgent.audioCtx.currentTime;
}

async function executeVoiceTool(call) {
  const exactUserText = voiceAgent.lastFinalUserTranscript.trim();
  if (!exactUserText) return {error: "no finalized user transcript available for tool binding"};
  if (call.name === "query_live_inneros") return api("/api/tool/system-query", {method: "POST", body: JSON.stringify({query: exactUserText})});
  if (call.name === "propose_live_inneros_action") return api("/api/tool/propose-system-action", {method: "POST", body: JSON.stringify({command: exactUserText})});
  if (call.name === "recall_verified_context") return api("/api/tool/recall", {method: "POST", body: JSON.stringify({query: exactUserText})});
  if (call.name === "inspect_and_propose_action") return api("/api/tool/inspect-and-propose", {method: "POST", body: JSON.stringify({intent: exactUserText})});
  if (call.name === "approve_pending_action") return api("/api/tool/approve-pending", {method: "POST", body: JSON.stringify({authorization_phrase: exactUserText})});
  return {error: `unsupported tool: ${call.name}`};
}

async function flushToolCalls() {
  if (!voiceAgent.ws || voiceAgent.ws.readyState !== WebSocket.OPEN) return;
  const calls = voiceAgent.pendingToolCalls.splice(0);
  for (const call of calls) {
    if (call.name === "recall_verified_context") setOrbit(els.orbitRecall, true, false);
    if (call.name === "query_live_inneros") setOrbit(els.orbitSystem, true, false);
    if (call.name === "propose_live_inneros_action") {
      setOrbit(els.orbitSystem, true, false);
      setOrbit(els.orbitReason, true, false);
    }
    if (call.name === "inspect_and_propose_action") setOrbit(els.orbitReason, true, false);
    if (call.name === "approve_pending_action") setOrbit(els.orbitPermit, true, false);
    let result; try { result = await executeVoiceTool(call); await refresh(); } catch (err) { result = {error: err.message}; }
    if ((call.name === "propose_live_inneros_action" || call.name === "inspect_and_propose_action") && !result.error) {
      voiceAgent.ws.send(JSON.stringify(phaseUpdate(result.requires_approval ? "approval" : "complete")));
    } else if (call.name === "approve_pending_action") {
      voiceAgent.ws.send(JSON.stringify(phaseUpdate("complete")));
    }
    voiceAgent.ws.send(JSON.stringify({type: "tool.result", call_id: call.call_id, result: JSON.stringify(result)}));
    voiceAgent.handledToolCallIds.add(call.call_id);
  }
}

async function handleVoiceAgentMessage(event) {
  const msg = JSON.parse(event.data);
  voiceAgent.eventCount += 1;
  renderProvenance(currentState || {});

  if (msg.type === "session.ready") {
    voiceAgent.ready = true;
    voiceAgent.sessionId = msg.session_id;
    setVoiceCoreState("ready", `LIVE · ${msg.session_id}`);
    setState(els.voiceState, "LISTENING", "ready");
    setOrbit(els.orbitAssembly, true, false);
    return;
  }

  if (msg.type === "input.speech.started") {
    setVoiceCoreState("user-speaking", "YOU ARE SPEAKING · ASSEMBLYAI LISTENING");
    setState(els.voiceState, "LISTENING", "active");
    setOrbit(els.orbitAssembly, true, false);
    return;
  }

  if (msg.type === "input.speech.stopped") {
    setVoiceCoreState("ready", "TURN DETECTED · PROCESSING");
    setState(els.voiceState, "TURN DETECTED", "warning");
    return;
  }

  if (msg.type === "transcript.user.delta") {
    voiceAgent.liveTranscriptActive = true;
    els.transcript.textContent = msg.text || "";
    setState(els.voiceState, "TRANSCRIBING", "active");
    return;
  }

  if (msg.type === "transcript.user") {
    voiceAgent.lastFinalUserTranscript = msg.text || "";
    voiceAgent.turnFinalAt = performance.now();
    voiceAgent.replyStartedAt = 0;
    voiceAgent.firstAudioAt = 0;
    voiceAgent.detectedLanguage = detectTurnLanguage(voiceAgent.lastFinalUserTranscript);
    els.transcript.textContent = voiceAgent.lastFinalUserTranscript || "No transcript yet.";
    if (els.translationUser) els.translationUser.textContent = voiceAgent.lastFinalUserTranscript || "Waiting for a finalized voice turn…";
    if (els.translationDirection) els.translationDirection.textContent = voiceAgent.detectedLanguage === "es" ? "ES · LIVE TURN" : "EN · LIVE TURN";
    setState(els.voiceState, "FINAL TRANSCRIPT", "ready");
    setOrbit(els.orbitAssembly, true, true);

    if (voiceAgent.ws && voiceAgent.ws.readyState === WebSocket.OPEN) {
      const langRule = voiceAgent.detectedLanguage === "es"
        ? "The user's latest finalized turn is Spanish. Reply only in natural Latin American Spanish for this turn. Keep it short."
        : "The user's latest finalized turn is English. Reply only in fluent natural English for this turn. Keep it short.";
      voiceAgent.ws.send(JSON.stringify({type: "session.update", session: {system_prompt: langRule}}));
    }
    renderProvenance(currentState || {});
    return;
  }

  if (msg.type === "reply.started") {
    voiceAgent.replyStartedAt = performance.now();
    setVoiceCoreState("agent-speaking", "INNEROS THINKING · ASSEMBLYAI LIVE");
    renderProvenance(currentState || {});
    return;
  }

  if (msg.type === "reply.audio" && msg.data) {
    if (!voiceAgent.firstAudioAt) {
      voiceAgent.firstAudioAt = performance.now();
      const firstAudioMs = voiceAgent.turnFinalAt ? Math.round(voiceAgent.firstAudioAt - voiceAgent.turnFinalAt) : null;
      if (els.provVoiceWs && firstAudioMs !== null) {
        els.provVoiceWs.textContent = `wss://agents.assemblyai.com/v1/ws · first audio ${firstAudioMs} ms`;
      }
    }
    playVoiceAgentAudio(msg.data);
    return;
  }

  if (msg.type === "transcript.agent") {
    els.agentTranscript.textContent = msg.text || "";
    if (els.translationAgent) els.translationAgent.textContent = msg.text || "";
    return;
  }

  if (msg.type === "tool.call") {
    const duplicate = voiceAgent.handledToolCallIds.has(msg.call_id) || voiceAgent.pendingToolCalls.some((call) => call.call_id === msg.call_id);
    if (!duplicate) {
      voiceAgent.pendingToolCalls.push({call_id: msg.call_id, name: msg.name});
      setLiveStatus(`TOOL REQUEST · ${msg.name}`, "active");
    }
    return;
  }

  if (msg.type === "reply.done") {
    if (msg.status === "interrupted") {
      voiceAgent.pendingToolCalls = [];
      flushVoicePlayback();
      setLiveStatus("INTERRUPTED · pending tools discarded", "warning");
    } else {
      await flushToolCalls();
      if (voiceAgent.ready && !voiceAgent.scheduledAudio.length) {
        setVoiceCoreState("ready", `LIVE · ${voiceAgent.sessionId}`);
      }
    }
    return;
  }

  if (msg.type === "session.error") {
    setVoiceCoreState("error", `ERROR · ${msg.code || "session"}: ${msg.message || "unknown"}`);
    return;
  }

  if (msg.type === "session.ended") {
    setLiveStatus("SESSION ENDED");
    cleanupVoiceAgent(false);
  }
}

async function startVoiceAgent() {
  setVoiceCoreState("connecting", "REQUESTING SHORT-LIVED TOKEN…");
  try {
    const current = await api("/api/state"); if (!current.assemblyai_voice_agent_enabled) throw new Error("Live AssemblyAI mode is disabled on this server.");
    await api("/api/reset", {method: "POST", body: "{}"}); const tokenPayload = await api("/api/assemblyai/token");
    voiceAgent.mediaStream = await navigator.mediaDevices.getUserMedia({audio: {echoCancellation: true, noiseSuppression: true, autoGainControl: true}, video: false});
    voiceAgent.audioCtx = new AudioContext({sampleRate: 24000}); await voiceAgent.audioCtx.resume();
    voiceAgent.source = voiceAgent.audioCtx.createMediaStreamSource(voiceAgent.mediaStream); voiceAgent.processor = voiceAgent.audioCtx.createScriptProcessor(2048, 1, 1);
    voiceAgent.silentGain = voiceAgent.audioCtx.createGain(); voiceAgent.silentGain.gain.value = 0;
    voiceAgent.source.connect(voiceAgent.processor); voiceAgent.processor.connect(voiceAgent.silentGain); voiceAgent.silentGain.connect(voiceAgent.audioCtx.destination);
    voiceAgent.ws = new WebSocket(`wss://agents.assemblyai.com/v1/ws?token=${encodeURIComponent(tokenPayload.token)}`);
    voiceAgent.ws.addEventListener("open", () => { setLiveStatus("CONNECTED · CONFIGURING", "active"); voiceAgent.ws.send(JSON.stringify(voiceAgentConfig())); });
    voiceAgent.ws.addEventListener("message", (event) => handleVoiceAgentMessage(event).catch((err) => setLiveStatus(`ERROR · ${err.message}`, "blocked")));
    voiceAgent.ws.addEventListener("close", () => { if (voiceAgent.ready) setLiveStatus("CONNECTION CLOSED", "warning"); cleanupVoiceAgent(false); });
    voiceAgent.ws.addEventListener("error", () => setLiveStatus("WEBSOCKET ERROR", "blocked"));
    voiceAgent.processor.onaudioprocess = (audioEvent) => {
      if (!voiceAgent.ready || !voiceAgent.ws || voiceAgent.ws.readyState !== WebSocket.OPEN) return;
      voiceAgent.ws.send(JSON.stringify({type: "input.audio", audio: pcm16Base64(audioEvent.inputBuffer.getChannelData(0), voiceAgent.audioCtx.sampleRate)}));
      voiceAgent.audioFramesSent += 1;
      if (voiceAgent.audioFramesSent % 10 === 0) renderProvenance(currentState || {});
    };
    els.stopVoiceBtn.disabled = false;
  } catch (err) { cleanupVoiceAgent(false); setVoiceCoreState("error", `OFFLINE · ${err.message}`); }
}

function cleanupVoiceAgent(closeSocket = true) {
  voiceAgent.ready = false; voiceAgent.liveTranscriptActive = false; voiceAgent.pendingToolCalls = []; voiceAgent.handledToolCallIds.clear(); flushVoicePlayback();
  if (voiceAgent.processor) { voiceAgent.processor.disconnect(); voiceAgent.processor.onaudioprocess = null; }
  if (voiceAgent.source) voiceAgent.source.disconnect(); if (voiceAgent.silentGain) voiceAgent.silentGain.disconnect();
  if (voiceAgent.mediaStream) voiceAgent.mediaStream.getTracks().forEach((track) => track.stop()); if (voiceAgent.audioCtx) voiceAgent.audioCtx.close().catch(() => {});
  if (closeSocket && voiceAgent.ws && voiceAgent.ws.readyState === WebSocket.OPEN) voiceAgent.ws.close();
  voiceAgent.ws = null; voiceAgent.mediaStream = null; voiceAgent.audioCtx = null; voiceAgent.processor = null; voiceAgent.source = null; voiceAgent.silentGain = null;
  voiceAgent.sessionId = null; voiceAgent.lastFinalUserTranscript = ""; voiceAgent.detectedLanguage = "auto"; els.liveVoiceBtn.disabled = false; els.stopVoiceBtn.disabled = true;
  renderProvenance(currentState || {});
  setVoiceCoreState("idle", "READY · PRESS THE CORE");
  setState(els.voiceState, "IDLE", "ready");
}

function stopVoiceAgent() {
  if (voiceAgent.ws && voiceAgent.ws.readyState === WebSocket.OPEN) {
    voiceAgent.ws.send(JSON.stringify({type: "session.end"})); setLiveStatus("ENDING SESSION…", "warning"); window.setTimeout(() => cleanupVoiceAgent(true), 1500);
  } else { cleanupVoiceAgent(true); setLiveStatus("SESSION ENDED"); }
}

els.liveVoiceBtn.addEventListener("click", () => {
  const active = voiceAgent.ready || Boolean(voiceAgent.ws) || Boolean(voiceAgent.mediaStream);
  if (active) stopVoiceAgent();
  else startVoiceAgent();
});
els.orbitAssembly.addEventListener("click", () => {
  const active = voiceAgent.ready || Boolean(voiceAgent.ws) || Boolean(voiceAgent.mediaStream);
  if (!active) startVoiceAgent();
  else {
    setOrbit(els.orbitAssembly, true, false);
    els.agentTranscript.textContent = `AssemblyAI live · session ${voiceAgent.sessionId || "connecting"} · Spanish realtime voice`;
  }
});
els.orbitSystem.addEventListener("click", async () => {
  const query = voiceAgent.lastFinalUserTranscript || currentState?.transcript || "status of Home Assistant, cameras, lights and connected InnerOS systems";
  setOrbit(els.orbitSystem, true, false);
  try {
    const result = await api("/api/tool/system-query", {method: "POST", body: JSON.stringify({query})});
    await refresh();
    els.agentTranscript.textContent = result.formatted || (result.ok ? "Live InnerOS query completed." : `System query error · ${result.error || "unknown"}`);
  } catch (err) { els.agentTranscript.textContent = `System error · ${err.message}`; }
});
els.orbitRecall.addEventListener("click", async () => {
  const query = voiceAgent.lastFinalUserTranscript || currentState?.transcript || "últimos resultados operativos verificados de VoiceOps";
  setOrbit(els.orbitRecall, true, false);
  try {
    const result = await api("/api/tool/recall", {method: "POST", body: JSON.stringify({query})});
    await refresh();
    const first = Array.isArray(result.hits) && result.hits.length ? result.hits[0] : null;
    els.agentTranscript.textContent = first?.summary || `Recall ${result.truth || "UNVERIFIED"} · ${result.count || 0} resultados`;
  } catch (err) { els.agentTranscript.textContent = `Recall error · ${err.message}`; }
});
els.orbitReason.addEventListener("click", async () => {
  setOrbit(els.orbitReason, true, false);
  const inference = currentState?.deployment?.inference || "local reasoner";
  const queryTools = currentState?.live_system?.last_query?.detected?.map((item) => item.tool).join(", ");
  els.agentTranscript.textContent = queryTools
    ? `Reason · ${inference} · last live route: ${queryTools}`
    : `Reason · ${inference} · live state is fetched before consequential actions.`;
});
els.orbitPermit.addEventListener("click", async () => {
  if (!currentState?.pending_approval) { els.agentTranscript.textContent = "Permit is locked: no action is awaiting approval. / No hay una acción pendiente."; return; }
  setOrbit(els.orbitPermit, true, false);
  try {
    const result = await api("/api/tool/approve-pending", {method: "POST", body: JSON.stringify({authorization_phrase: "Sí, autorizo. Yes, authorize."})});
    await refresh();
    notifyVoiceAgentOfExternalAction(result, "permit_button");
    els.agentTranscript.textContent = result.action ? `Autorizado · ${result.action.action_id} · ${result.action.status} · contexto del modelo actualizado` : "Autorización procesada.";
  } catch (err) { els.agentTranscript.textContent = `Permit error · ${err.message}`; }
});
els.orbitProof.addEventListener("click", async () => {
  try {
    const [evidence, replay] = await Promise.all([api("/api/evidence"), api("/api/replay")]);
    els.dialogTitle.textContent = "Verify · Decision Evidence + Replay";
    els.jsonOutput.textContent = JSON.stringify({evidence, replay}, null, 2);
    els.dialog.showModal();
    setOrbit(els.orbitProof, true, Boolean(currentState?.action));
  } catch (err) { els.agentTranscript.textContent = `Verify error · ${err.message}`; }
});
els.stopVoiceBtn.addEventListener("click", stopVoiceAgent);
window.addEventListener("beforeunload", () => { if (voiceAgent.ws && voiceAgent.ws.readyState === WebSocket.OPEN) { try { voiceAgent.ws.send(JSON.stringify({type: "session.end"})); } catch (_) {} } });

setVoiceCoreState("idle", "READY · PRESS THE CORE");
refresh();
