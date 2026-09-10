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
  timeline: $("timeline"), htrBox: $("htrBox"), sessionId: $("sessionId"), correlationId: $("correlationId")
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: {"Content-Type": "application/json"},
    ...options
  });
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
    row("Event", guardian.event_type),
    row("Severity", guardian.severity),
    row("Source", guardian.source_id),
    row("Zone", guardian.zone_id),
    row("Owner", guardian.contract_owner)
  );
  setState(els.guardianState, "EVENT RECEIVED", "ready");
}

function renderRoute(route) {
  if (!route || !Object.keys(route).length) {
    els.reasoningTitle.textContent = "InnerOS reasoner";
    els.routeProvider.textContent = "—";
    els.routeModel.textContent = "—";
    els.routePolicy.textContent = "—";
    els.routeFallback.textContent = "—";
    els.routeTruth.textContent = "—";
    setState(els.amdState, "WAITING");
    return;
  }

  const provider = route.provider || "unknown";
  const model = route.model || "deterministic fixture";
  const policy = route.policy || route.execution_policy || "local_first";
  const fallback = route.external_fallback ?? route.external_needed ?? false;
  const truth = route.truth || (provider === "local-amd-5" ? "LIVE" : "UNCLASSIFIED");

  els.routeProvider.textContent = provider;
  els.routeModel.textContent = model;
  els.routePolicy.textContent = policy;
  els.routeFallback.textContent = fallback ? "YES" : "NONE";
  els.routeTruth.textContent = truth;

  if (provider === "local-amd-5") {
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
  els.approvalGate.classList.add("hidden");
  els.actionResult.classList.add("hidden");
  if (!proposal) {
    els.proposalEmpty.classList.remove("hidden");
    els.proposalData.classList.add("hidden");
    els.proposalData.replaceChildren();
    setState(els.actionState, "WAITING");
    return;
  }
  els.proposalEmpty.classList.add("hidden");
  els.proposalData.classList.remove("hidden");
  els.proposalData.replaceChildren(
    row("Action", proposal.action_type),
    row("Priority", proposal.payload?.priority || "—"),
    row("Reason", proposal.payload?.reason_code || "—"),
    row("Approval", proposal.requires_approval ? "REQUIRED" : "NOT REQUIRED")
  );

  if (state.action) {
    setState(els.actionState, "EXECUTED", "success");
    els.actionResult.classList.remove("hidden");
    els.actionResult.textContent = `✓ ${state.action.action_id} · ${state.action.status.toUpperCase()}`;
  } else if (state.approval && !state.approval.approved) {
    setState(els.actionState, "BLOCKED", "blocked");
    els.approvalGate.classList.remove("hidden");
    els.approvalGate.textContent = `BLOCKED · ${state.approval.reason}`;
  } else if (state.pending_approval) {
    setState(els.actionState, "APPROVAL REQUIRED", "warning");
    els.approvalGate.classList.remove("hidden");
    els.approvalGate.textContent = "HUMAN APPROVAL REQUIRED · ACTION NOT EXECUTED";
  } else {
    setState(els.actionState, "PROPOSED", "active");
  }
}

function renderTimeline(items = []) {
  els.timeline.replaceChildren();
  if (!items.length) {
    const div = document.createElement("div");
    div.className = "empty";
    div.textContent = "Evidence timeline will appear here.";
    els.timeline.append(div);
    return;
  }
  const start = new Date(items[0].at).getTime();
  items.forEach((item) => {
    const t = Math.max(0, new Date(item.at).getTime() - start);
    const div = document.createElement("div");
    div.className = "timeline-item";
    const time = document.createElement("div");
    time.className = "timeline-time";
    time.textContent = `+${(t / 1000).toFixed(3)}s`;
    const body = document.createElement("div");
    const kind = document.createElement("div");
    kind.className = "timeline-kind";
    kind.textContent = item.kind.replaceAll("_", " ").toUpperCase();
    const detail = document.createElement("div");
    detail.className = "timeline-detail";
    const safe = {...(item.data || {})};
    if (safe.snapshot) safe.snapshot = "[captured normalized Guardian snapshot]";
    if (safe.transcript) safe.transcript = `“${safe.transcript}”`;
    detail.textContent = JSON.stringify(safe);
    body.append(kind, detail);
    div.append(time, body);
    els.timeline.append(div);
  });
}

function render(state) {
  els.sessionId.textContent = state.session_id;
  els.correlationId.textContent = state.correlation_id;
  els.transcript.textContent = state.transcript || "No transcript yet.";

  if (state.transcript) setState(els.voiceState, "FINAL TRANSCRIPT", "ready");
  else setState(els.voiceState, "READY", "ready");

  renderGuardian(state.guardian);
  renderRoute(state.route);
  renderProposal(state);
  renderTimeline(state.timeline);

  els.approveBtn.disabled = !state.pending_approval;
  els.ambiguousBtn.disabled = !state.pending_approval;
  els.runBtn.disabled = state.pending_approval;

  if (state.action) {
    els.demoStatus.textContent = `Completed: ${state.action.action_id}. Evidence sealed for replay.`;
  } else if (state.approval && !state.approval.approved) {
    els.demoStatus.textContent = "Ambiguous authorization was blocked. Explicit approval is still required.";
  } else if (state.pending_approval) {
    const provider = state.route?.provider === "local-amd-5" ? "AMD .5" : "the demo reasoner";
    els.demoStatus.textContent = `${provider} proposal is ready. InnerOS is waiting for explicit human approval.`;
  } else if (state.proposal) {
    els.demoStatus.textContent = "Action proposed.";
  } else {
    els.demoStatus.textContent = "Ready for an operational intent.";
  }

  if (state.htr) {
    const saved = Math.max(0, Math.round(state.htr.saved_seconds));
    els.htrBox.innerHTML = `<strong>HTR ${state.htr.classification}</strong> · ${saved}s returned · VoiceOps active ${state.htr.human_active_seconds.toFixed(2)}s`;
  } else {
    els.htrBox.textContent = "HTR appears after an approved action.";
  }
}

async function refresh() {
  try { render(await api("/api/state")); }
  catch (err) { els.demoStatus.textContent = `Error: ${err.message}`; }
}

async function postTranscript(path, transcript) {
  els.demoStatus.textContent = "Processing governed execution trace…";
  try {
    const state = await api(path, {method: "POST", body: JSON.stringify({transcript})});
    render(state);
  } catch (err) {
    els.demoStatus.textContent = `Error: ${err.message}`;
  }
}

els.runBtn.addEventListener("click", () => postTranscript("/api/intent", "Ralphi, revisa la incidencia del acceso norte y abre una orden tecnica si corresponde."));
els.approveBtn.addEventListener("click", () => postTranscript("/api/approve", "Si, autorizo."));
els.ambiguousBtn.addEventListener("click", () => postTranscript("/api/approve", "Si crees que hace falta."));
els.resetBtn.addEventListener("click", async () => render(await api("/api/reset", {method: "POST", body: "{}"})));
els.evidenceBtn.addEventListener("click", async () => {
  els.dialogTitle.textContent = "Decision Evidence Bundle";
  els.jsonOutput.textContent = JSON.stringify(await api("/api/evidence"), null, 2);
  els.dialog.showModal();
});
els.replayBtn.addEventListener("click", async () => {
  els.dialogTitle.textContent = "Forensic Replay · Captured Evidence Only";
  els.jsonOutput.textContent = JSON.stringify(await api("/api/replay"), null, 2);
  els.dialog.showModal();
});
els.closeDialog.addEventListener("click", () => els.dialog.close());

refresh();
