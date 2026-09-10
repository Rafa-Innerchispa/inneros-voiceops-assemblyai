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
  liveVoiceBtn: $("liveVoiceBtn"), stopVoiceBtn: $("stopVoiceBtn"), voiceAgentStatus: $("voiceAgentStatus"), agentTranscript: $("agentTranscript")
};

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
  } else if (truth === "SYNTHETIC") {
    els.reasoningTitle.textContent = "Offline-safe reasoner";
    setState(els.amdState, "SYNTHETIC", "warning");
  } else {
    els.reasoningTitle.textContent = "InnerOS reasoning route";
    setState(els.amdState, "ROUTED", "active");
  }
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
    row("Action", proposal.action_type), row("Priority", proposal.payload?.priority || "—"),
    row("Reason", proposal.payload?.reason_code || "—"), row("Approval", proposal.requires_approval ? "REQUIRED" : "NOT REQUIRED")
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
  els.sessionId.textContent = state.session_id; els.correlationId.textContent = state.correlation_id;
  if (!voiceAgent.liveTranscriptActive) els.transcript.textContent = state.transcript || "No transcript yet.";
  if (state.transcript && !voiceAgent.liveTranscriptActive) setState(els.voiceState, "FINAL TRANSCRIPT", "ready");
  else if (!voiceAgent.ready) setState(els.voiceState, "READY", "ready");
  renderGuardian(state.guardian); renderRoute(state.route); renderProposal(state); renderTimeline(state.timeline);
  els.approveBtn.disabled = !state.pending_approval; els.ambiguousBtn.disabled = !state.pending_approval; els.runBtn.disabled = state.pending_approval;
  if (state.action) els.demoStatus.textContent = `Completed: ${state.action.action_id}. Evidence sealed for replay.`;
  else if (state.approval && !state.approval.approved) els.demoStatus.textContent = "Ambiguous authorization was blocked. Explicit approval is still required.";
  else if (state.pending_approval) {
    const provider = state.route?.provider === "local-amd-5" ? "AMD .5" : "the demo reasoner";
    els.demoStatus.textContent = `${provider} proposal is ready. InnerOS is waiting for explicit human approval.`;
  } else els.demoStatus.textContent = state.proposal ? "Action proposed." : "Ready for an operational intent.";
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

els.runBtn.addEventListener("click", () => postTranscript("/api/intent", "Ralphi, revisa la incidencia del acceso norte y abre una orden tecnica si corresponde."));
els.approveBtn.addEventListener("click", () => postTranscript("/api/approve", "Si, autorizo."));
els.ambiguousBtn.addEventListener("click", () => postTranscript("/api/approve", "Si crees que hace falta."));
els.resetBtn.addEventListener("click", async () => render(await api("/api/reset", {method: "POST", body: "{}"})));
els.evidenceBtn.addEventListener("click", async () => { els.dialogTitle.textContent = "Decision Evidence Bundle"; els.jsonOutput.textContent = JSON.stringify(await api("/api/evidence"), null, 2); els.dialog.showModal(); });
els.replayBtn.addEventListener("click", async () => { els.dialogTitle.textContent = "Forensic Replay · Captured Evidence Only"; els.jsonOutput.textContent = JSON.stringify(await api("/api/replay"), null, 2); els.dialog.showModal(); });
els.closeDialog.addEventListener("click", () => els.dialog.close());

const voiceAgent = {
  ws: null, mediaStream: null, audioCtx: null, processor: null, source: null, silentGain: null,
  ready: false, sessionId: null, lastFinalUserTranscript: "", pendingToolCalls: [], scheduledAudio: [], nextPlaybackTime: 0,
  liveTranscriptActive: false
};

const voiceAgentTools = [
  {type: "function", name: "inspect_and_propose_action", description: "Inspect the current normalized Physical Guardian incident through InnerOS and request a bounded action proposal. This tool never executes the consequential action.", parameters: {type: "object", properties: {intent: {type: "string", description: "The user's operational intent."}}, required: ["intent"]}},
  {type: "function", name: "approve_pending_action", description: "Submit the user's explicit authorization phrase to the InnerOS approval gate. Never call for ambiguous, implied, conditional, or agent-generated approval.", parameters: {type: "object", properties: {authorization_phrase: {type: "string", description: "The exact authorization phrase spoken by the user."}}, required: ["authorization_phrase"]}}
];

function voiceAgentConfig() {
  return {type: "session.update", session: {
    system_prompt: [
      "You are the spoken interface for InnerOS VoiceOps. Keep replies short and operational.",
      "For an operational incident, call inspect_and_propose_action.",
      "If it reports requires_approval=true, explain the proposal and ask for explicit human authorization.",
      "Never infer approval from conditional or vague language and never treat your own words as authorization.",
      "Only after explicit user authorization may you call approve_pending_action.",
      "After success, state the work order id and that decision evidence was recorded."
    ].join(" "),
    greeting: "InnerOS VoiceOps is ready. Tell me what operational issue you want me to inspect.",
    output: {voice: "anna", format: {encoding: "audio/pcm"}}, input: {format: {encoding: "audio/pcm"}}, tools: voiceAgentTools
  }};
}

function setLiveStatus(text, kind = "") { els.voiceAgentStatus.textContent = text; els.voiceAgentStatus.className = kind ? `live-status ${kind}` : "live-status"; }

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
  const binary = atob(data); const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
  const pcm = new Int16Array(bytes.buffer); const buffer = voiceAgent.audioCtx.createBuffer(1, pcm.length, 24000);
  const channel = buffer.getChannelData(0); for (let i = 0; i < pcm.length; i += 1) channel[i] = pcm[i] / 32768;
  const source = voiceAgent.audioCtx.createBufferSource(); source.buffer = buffer; source.connect(voiceAgent.audioCtx.destination);
  const startAt = Math.max(voiceAgent.audioCtx.currentTime, voiceAgent.nextPlaybackTime); source.start(startAt);
  voiceAgent.nextPlaybackTime = startAt + buffer.duration; voiceAgent.scheduledAudio.push(source);
  source.onended = () => { voiceAgent.scheduledAudio = voiceAgent.scheduledAudio.filter((item) => item !== source); };
}

function flushVoicePlayback() {
  for (const source of voiceAgent.scheduledAudio) { try { source.stop(); } catch (_) {} }
  voiceAgent.scheduledAudio = []; if (voiceAgent.audioCtx) voiceAgent.nextPlaybackTime = voiceAgent.audioCtx.currentTime;
}

async function executeVoiceTool(call) {
  const exactUserText = voiceAgent.lastFinalUserTranscript.trim();
  if (!exactUserText) return {error: "no finalized user transcript available for tool binding"};
  if (call.name === "inspect_and_propose_action") return api("/api/tool/inspect-and-propose", {method: "POST", body: JSON.stringify({intent: exactUserText})});
  if (call.name === "approve_pending_action") return api("/api/tool/approve-pending", {method: "POST", body: JSON.stringify({authorization_phrase: exactUserText})});
  return {error: `unsupported tool: ${call.name}`};
}

async function flushToolCalls() {
  if (!voiceAgent.ws || voiceAgent.ws.readyState !== WebSocket.OPEN) return;
  const calls = voiceAgent.pendingToolCalls.splice(0);
  for (const call of calls) {
    let result; try { result = await executeVoiceTool(call); await refresh(); } catch (err) { result = {error: err.message}; }
    voiceAgent.ws.send(JSON.stringify({type: "tool.result", call_id: call.call_id, result: JSON.stringify(result)}));
  }
}

async function handleVoiceAgentMessage(event) {
  const msg = JSON.parse(event.data);
  if (msg.type === "session.ready") {
    voiceAgent.ready = true; voiceAgent.sessionId = msg.session_id; setLiveStatus(`LIVE · ${msg.session_id}`, "ready"); setState(els.voiceState, "LISTENING", "ready");
  } else if (msg.type === "input.speech.started") setState(els.voiceState, "LISTENING", "active");
  else if (msg.type === "input.speech.stopped") setState(els.voiceState, "TURN DETECTED", "warning");
  else if (msg.type === "transcript.user.delta") { voiceAgent.liveTranscriptActive = true; els.transcript.textContent = msg.text || ""; setState(els.voiceState, "TRANSCRIBING", "active"); }
  else if (msg.type === "transcript.user") { voiceAgent.lastFinalUserTranscript = msg.text || ""; els.transcript.textContent = voiceAgent.lastFinalUserTranscript || "No transcript yet."; setState(els.voiceState, "FINAL TRANSCRIPT", "ready"); }
  else if (msg.type === "reply.audio" && msg.data) playVoiceAgentAudio(msg.data);
  else if (msg.type === "transcript.agent") els.agentTranscript.textContent = msg.text || "";
  else if (msg.type === "tool.call") { voiceAgent.pendingToolCalls.push({call_id: msg.call_id, name: msg.name}); setLiveStatus(`TOOL REQUEST · ${msg.name}`, "active"); }
  else if (msg.type === "reply.done") {
    if (msg.status === "interrupted") { voiceAgent.pendingToolCalls = []; flushVoicePlayback(); setLiveStatus("INTERRUPTED · pending tools discarded", "warning"); }
    else { await flushToolCalls(); if (voiceAgent.ready) setLiveStatus(`LIVE · ${voiceAgent.sessionId}`, "ready"); }
  } else if (msg.type === "session.error") setLiveStatus(`ERROR · ${msg.code || "session"}: ${msg.message || "unknown"}`, "blocked");
  else if (msg.type === "session.ended") { setLiveStatus("SESSION ENDED"); cleanupVoiceAgent(false); }
}

async function startVoiceAgent() {
  els.liveVoiceBtn.disabled = true; setLiveStatus("REQUESTING SHORT-LIVED TOKEN…", "active");
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
    };
    els.stopVoiceBtn.disabled = false;
  } catch (err) { setLiveStatus(`OFFLINE · ${err.message}`, "blocked"); cleanupVoiceAgent(false); }
}

function cleanupVoiceAgent(closeSocket = true) {
  voiceAgent.ready = false; voiceAgent.liveTranscriptActive = false; voiceAgent.pendingToolCalls = []; flushVoicePlayback();
  if (voiceAgent.processor) { voiceAgent.processor.disconnect(); voiceAgent.processor.onaudioprocess = null; }
  if (voiceAgent.source) voiceAgent.source.disconnect(); if (voiceAgent.silentGain) voiceAgent.silentGain.disconnect();
  if (voiceAgent.mediaStream) voiceAgent.mediaStream.getTracks().forEach((track) => track.stop()); if (voiceAgent.audioCtx) voiceAgent.audioCtx.close().catch(() => {});
  if (closeSocket && voiceAgent.ws && voiceAgent.ws.readyState === WebSocket.OPEN) voiceAgent.ws.close();
  voiceAgent.ws = null; voiceAgent.mediaStream = null; voiceAgent.audioCtx = null; voiceAgent.processor = null; voiceAgent.source = null; voiceAgent.silentGain = null;
  voiceAgent.sessionId = null; voiceAgent.lastFinalUserTranscript = ""; els.liveVoiceBtn.disabled = false; els.stopVoiceBtn.disabled = true;
}

function stopVoiceAgent() {
  if (voiceAgent.ws && voiceAgent.ws.readyState === WebSocket.OPEN) {
    voiceAgent.ws.send(JSON.stringify({type: "session.end"})); setLiveStatus("ENDING SESSION…", "warning"); window.setTimeout(() => cleanupVoiceAgent(true), 1500);
  } else { cleanupVoiceAgent(true); setLiveStatus("SESSION ENDED"); }
}

els.liveVoiceBtn.addEventListener("click", startVoiceAgent); els.stopVoiceBtn.addEventListener("click", stopVoiceAgent);
window.addEventListener("beforeunload", () => { if (voiceAgent.ws && voiceAgent.ws.readyState === WebSocket.OPEN) { try { voiceAgent.ws.send(JSON.stringify({type: "session.end"})); } catch (_) {} } });

refresh();
