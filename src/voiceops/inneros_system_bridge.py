from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Callable


INNEROS_PROVIDER_PYTHON_ENV = "VOICEOPS_INNEROS_PROVIDER_PYTHON"
INNEROS_PLATFORM_PATH_ENV = "VOICEOPS_INNEROS_PLATFORM_PATH"

READ_ONLY_TOOLS = {
    "hybrid_search",
    "get_context_summary",
    "get_unified_stack_status",
    "get_server_status",
    "get_infrastructure_status",
    "fleet_overview",
    "bootstrap_context",
    "get_operational_runbooks",
    "resolve_client",
    "list_clients",
    "resolve_party",
    "list_ops_tasks",
    "mcp_version",
    "get_whatsapp_status",
    "list_monitored_emails",
    "ha_list_entities",
    "ha_list_devices",
    "ha_list_entity_registry",
    "ha_get_entity",
    "ha_home_status",
    "alarm_intelbras_status",
    "dmx_status",
    "raul_catalog_status",
}

APPROVAL_GATED_WRITE_TOOLS = {
    "ha_turn_on_light",
    "ha_turn_off_light",
    "voiceops_restart_network_device",
    "voiceops_restart_camera",
}

PROTECTED_WRITE_TOOLS = {
    "ha_call_service",
    "send_whatsapp_message",
    "send_whatsapp_draft",
    "create_quote_draft",
    "update_quote_draft",
    "trigger_email_poll",
    "vero_dispatch",
    "raul_dispatch",
    "quote_client",
    "invoice_client",
    "technical_report_client",
    "dmx_set_scene",
    "dmx_blackout",
}

NETWORK_RESTART_TARGETS = {
    "estudio": "button.estudio_restart",
    "cuarto": "button.cuarto_restart",
    "living": "button.living_restart",
    "u6": "button.living_restart",
    "u7": "button.u7_lite_restart",
    "u7 living": "button.u7_lite_restart",
    "gateway": "button.cloud_gateway_ultra_ralphi_restart",
    "router": "button.cloud_gateway_ultra_ralphi_restart",
    "cloud gateway": "button.cloud_gateway_ultra_ralphi_restart",
    "cloud gateway ultra": "button.cloud_gateway_ultra_ralphi_restart",
}

_CAMERA_RE = re.compile(r"\b(camera|cameras|camara|cámaras|cam|video|videovigilancia)\b", re.I)
_RESTART_RE = re.compile(r"\b(restart|reboot|reinicia|reiniciar|reinicie|reset)\b", re.I)


def _camera_restart_targets() -> dict[str, str]:
    raw = os.getenv("VOICEOPS_CAMERA_RESTART_TARGETS", "").strip()
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    result: dict[str, str] = {}
    for alias, entity_id in payload.items():
        alias_text = str(alias).strip().lower()
        entity_text = str(entity_id).strip()
        if alias_text and re.fullmatch(r"button\.[a-z0-9_]+_restart", entity_text):
            result[alias_text] = entity_text
    return result


def _normalize_for_broker(text: str) -> str:
    normalized = text.strip()
    replacements = (
        (r"\bturn on\b", "enciende"),
        (r"\bswitch on\b", "enciende"),
        (r"\bturn off\b", "apaga"),
        (r"\bswitch off\b", "apaga"),
        (r"\blights\b", "luces"),
        (r"\blight\b", "luz"),
        (r"\bkitchen\b", "cocina"),
        (r"\bliving room\b", "living"),
        (r"\bbedroom\b", "cuarto"),
        (r"\bstudy\b", "estudio"),
        (r"\boffice\b", "oficina"),
        (r"\bentrance\b", "entrada"),
        (r"\bstorage room\b", "bodega"),
        (r"\bhome status\b", "estado de la casa"),
        (r"\bhouse status\b", "estado de la casa"),
        (r"\bsmart home\b", "domotica"),
    )
    for pattern, replacement in replacements:
        normalized = re.sub(pattern, replacement, normalized, flags=re.I)
    return normalized


def _restart_proposal(text: str) -> dict[str, Any] | None:
    lowered = text.lower()
    if not _RESTART_RE.search(lowered):
        return None

    if _CAMERA_RE.search(lowered):
        matches = [
            (alias, entity)
            for alias, entity in _camera_restart_targets().items()
            if alias in lowered
        ]
        if len(matches) == 1:
            alias, entity = matches[0]
            return {
                "tool": "voiceops_restart_camera",
                "args": {"target": alias, "entity_id": entity},
            }
        return None

    matches = [
        (alias, entity)
        for alias, entity in NETWORK_RESTART_TARGETS.items()
        if alias in lowered
    ]
    unique: dict[str, str] = {}
    for alias, entity in matches:
        unique[entity] = alias
    if len(unique) != 1:
        return None
    entity, alias = next(iter(unique.items()))
    return {
        "tool": "voiceops_restart_network_device",
        "args": {"target": alias, "entity_id": entity},
    }


class InnerOSSystemBridge:
    """Server-side bridge into InnerOS' compact voice MCP executor.

    Read operations may run immediately. Any write is only proposed here; the
    caller must separately obtain explicit approval and then call execute().
    """

    def __init__(
        self,
        *,
        python_path: str | None = None,
        platform_path: str | None = None,
        timeout_seconds: float = 12.0,
        runner: Callable[..., Any] | None = None,
    ) -> None:
        self.python_path = python_path or os.getenv(INNEROS_PROVIDER_PYTHON_ENV, "").strip()
        self.platform_path = platform_path or os.getenv(INNEROS_PLATFORM_PATH_ENV, "").strip()
        self.timeout_seconds = timeout_seconds
        self._runner = runner or subprocess.run
        self._health_cache: tuple[float, dict[str, Any]] | None = None

    def configured(self) -> bool:
        return bool(
            self.python_path
            and self.platform_path
            and Path(self.python_path).is_file()
            and Path(self.platform_path).is_dir()
        )

    def _run(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.configured():
            return {"ok": False, "error": "inneros_system_bridge_not_configured"}
        helper = r'''
import json, re, sys
sys.path.insert(0, sys.argv[1])
from inneros_core_runtime import voice_mcp_executor as ex

operation = sys.argv[2]
payload = json.loads(sys.argv[3])
user = {"is_admin": True, "name": "VoiceOps Owner"}

READ = set(payload.get("read_tools") or [])
WRITES = set(payload.get("write_tools") or [])
PROTECTED = set(payload.get("protected_tools") or [])

if operation == "query":
    text = str(payload.get("text") or "")
    calls = ex.detect_tool_calls(user, text)

    # VoiceOps must prefer explicit Home Assistant intent over the broader
    # lighting/DMX heuristic used by the shared compact voice executor.
    explicit_ha = bool(re.search(
        r"\b(home assistant|smart home|dom[oó]tica|estado de la casa|house status|home status|lights?|luces?|switches?|interruptores?)\b",
        text,
        re.I,
    ))
    explicit_dmx = bool(re.search(
        r"\b(dmx|artnet|art-net|tacho|tachos|pulpo|pulpos|beam|beams|disco|blackout|escena dmx)\b",
        text,
        re.I,
    ))
    if explicit_ha and not explicit_dmx:
        calls = [(name, args) for name, args in calls if not name.startswith("dmx_")]
        calls.insert(0, ("ha_home_status", {"limit": 35}))
        if re.search(r"\b(lights?|luces?)\b", text, re.I):
            calls.insert(1, ("ha_list_entities", {"domain": "light", "limit": 30}))
        elif re.search(r"\b(switches?|interruptores?|enchufes?)\b", text, re.I):
            calls.insert(1, ("ha_list_entities", {"domain": "switch", "limit": 30}))

    if re.search(r"\b(camera|cameras|camara|cámaras|cam|video|videovigilancia)\b", text, re.I):
        calls.insert(0, ("ha_list_entities", {"domain": "camera", "limit": 30}))
    seen = set()
    detected = []
    results = []
    write_proposals = []
    protected = []
    for name, args in calls:
        if name in seen:
            continue
        seen.add(name)
        detected.append({"tool": name, "args": args})
        if name in READ:
            results.append({"tool": name, "args": args, "result": ex.call_tool(user, name, args)})
        elif name in WRITES:
            write_proposals.append({"tool": name, "args": args})
        elif name in PROTECTED:
            protected.append({"tool": name, "args": args, "reason": "dedicated_approval_adapter_required"})
    print(json.dumps({
        "ok": True,
        "query": text,
        "detected": detected,
        "results": results,
        "formatted": ex.format_tool_results(results),
        "write_proposals": write_proposals,
        "protected_proposals": protected,
        "policy": ex.mcp_policy_summary(user, include_tools=False),
    }, ensure_ascii=False, default=str))
elif operation == "execute":
    name = str(payload.get("tool") or "")
    args = dict(payload.get("args") or {})
    if name not in WRITES:
        print(json.dumps({"ok": False, "error": "write_tool_not_approval_gated", "tool": name}))
    elif name in {"voiceops_restart_network_device", "voiceops_restart_camera"}:
        entity_id = str(args.get("entity_id") or "")
        if not re.fullmatch(r"button\.[a-z0-9_]+_restart", entity_id):
            print(json.dumps({"ok": False, "error": "restart_target_not_allowlisted", "tool": name}))
        else:
            result = ex.call_tool(user, "ha_call_service", {
                "domain": "button",
                "service": "press",
                "entity_id": entity_id,
            })
            print(json.dumps({"ok": bool(result.get("ok", True)), "tool": name, "args": args, "result": result}, ensure_ascii=False, default=str))
    else:
        result = ex.call_tool(user, name, args)
        print(json.dumps({"ok": bool(result.get("ok", True)), "tool": name, "args": args, "result": result}, ensure_ascii=False, default=str))
elif operation == "health":
    result = ex.call_tool(user, "ha_home_status", {"limit": 20})
    print(json.dumps({"ok": bool(result.get("ok")), "home_assistant": result, "policy": ex.mcp_policy_summary(user, include_tools=False)}, ensure_ascii=False, default=str))
else:
    print(json.dumps({"ok": False, "error": "unsupported_operation"}))
'''
        completed = self._runner(
            [self.python_path, "-c", helper, self.platform_path, operation, json.dumps({
                **payload,
                "read_tools": sorted(READ_ONLY_TOOLS),
                "write_tools": sorted(APPROVAL_GATED_WRITE_TOOLS),
                "protected_tools": sorted(PROTECTED_WRITE_TOOLS),
            }, ensure_ascii=False)],
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
            check=False,
        )
        if int(getattr(completed, "returncode", 1)) != 0:
            return {
                "ok": False,
                "error": "inneros_system_bridge_failed",
                "detail": str(getattr(completed, "stderr", "") or "")[:240],
            }
        lines = str(getattr(completed, "stdout", "") or "").strip().splitlines()
        if not lines:
            return {"ok": False, "error": "inneros_system_bridge_empty"}
        try:
            result = json.loads(lines[-1])
        except json.JSONDecodeError:
            return {"ok": False, "error": "inneros_system_bridge_invalid_json"}
        return result if isinstance(result, dict) else {"ok": False, "error": "inneros_system_bridge_invalid_payload"}

    def query(self, text: str) -> dict[str, Any]:
        normalized = _normalize_for_broker(text)
        result = self._run("query", {"text": normalized})
        if result.get("ok"):
            proposal = _restart_proposal(text)
            if proposal:
                result["write_proposals"] = [proposal]
            elif _RESTART_RE.search(text) and (
                _CAMERA_RE.search(text)
                or re.search(r"\b(router|gateway|wifi|wi-fi|ap|access point|punto de acceso|red)\b", text, re.I)
            ):
                result["write_proposals"] = []
                result["restart_target_required"] = True
                result["restart_message"] = (
                    "Specify one exact supported target before authorization. "
                    "Camera restart is only available for explicitly configured safe adapters."
                )
            result["source_truth"] = "LIVE"
            result["original_query"] = text[:600]
            result["browser_credentials_exposed"] = False
        return result

    def execute(self, proposal: dict[str, Any]) -> dict[str, Any]:
        tool = str(proposal.get("tool") or "")
        args = dict(proposal.get("args") or {})
        if tool not in APPROVAL_GATED_WRITE_TOOLS:
            return {"ok": False, "error": "write_tool_not_approval_gated", "tool": tool}

        if tool == "voiceops_restart_network_device":
            entity_id = str(args.get("entity_id") or "")
            if entity_id not in set(NETWORK_RESTART_TARGETS.values()):
                return {"ok": False, "error": "network_restart_target_not_allowlisted", "tool": tool}
        elif tool == "voiceops_restart_camera":
            entity_id = str(args.get("entity_id") or "")
            if entity_id not in set(_camera_restart_targets().values()):
                return {"ok": False, "error": "camera_restart_target_not_allowlisted", "tool": tool}

        result = self._run("execute", {"tool": tool, "args": args})
        result["source_truth"] = "LIVE" if result.get("ok") else "UNVERIFIED"
        result["browser_credentials_exposed"] = False
        return result

    def status(self) -> dict[str, Any]:
        now = time.monotonic()
        if self._health_cache and now - self._health_cache[0] < 10.0:
            return self._health_cache[1]
        if not self.configured():
            result = {"ok": False, "configured": False, "provider": "inneros-voice-mcp"}
        else:
            health = self._run("health", {})
            result = {
                "ok": bool(health.get("ok")),
                "configured": True,
                "provider": "inneros-voice-mcp",
                "home_assistant_live": bool(health.get("ok")),
                "approval_gated_writes": sorted(APPROVAL_GATED_WRITE_TOOLS),
                "authorized_action_families": [
                    "LIGHT_CONTROL",
                    "CAMERA_RESTART",
                    "NETWORK_RESTART",
                ],
                "network_restart_targets": sorted(set(NETWORK_RESTART_TARGETS.values())),
                "camera_restart_target_count": len(_camera_restart_targets()),
                "protected_writes": sorted(PROTECTED_WRITE_TOOLS),
            }
        self._health_cache = (now, result)
        return result
