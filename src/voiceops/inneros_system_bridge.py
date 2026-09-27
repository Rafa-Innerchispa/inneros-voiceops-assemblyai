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
    "ha_get_entity",
    "ha_home_status",
    "alarm_intelbras_status",
    "dmx_status",
    "raul_catalog_status",
}

APPROVAL_GATED_WRITE_TOOLS = {
    "ha_turn_on_light",
    "ha_turn_off_light",
    "dmx_set_scene",
    "dmx_blackout",
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
}

_CAMERA_RE = re.compile(r"\b(camera|cameras|camara|cámaras|cam|video|videovigilancia)\b", re.I)


def _normalize_for_broker(text: str) -> str:
    normalized = text.strip()
    replacements = (
        (r"\bturn on\b", "enciende"),
        (r"\bswitch on\b", "enciende"),
        (r"\bturn off\b", "apaga"),
        (r"\bswitch off\b", "apaga"),
        (r"\blights\b", "luces"),
        (r"\blight\b", "luz"),
        (r"\bhome status\b", "estado de la casa"),
        (r"\bhouse status\b", "estado de la casa"),
        (r"\bsmart home\b", "domotica"),
    )
    for pattern, replacement in replacements:
        normalized = re.sub(pattern, replacement, normalized, flags=re.I)
    return normalized


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
            result["source_truth"] = "LIVE"
            result["original_query"] = text[:600]
            result["browser_credentials_exposed"] = False
        return result

    def execute(self, proposal: dict[str, Any]) -> dict[str, Any]:
        tool = str(proposal.get("tool") or "")
        args = dict(proposal.get("args") or {})
        if tool not in APPROVAL_GATED_WRITE_TOOLS:
            return {"ok": False, "error": "write_tool_not_approval_gated", "tool": tool}
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
                "protected_writes": sorted(PROTECTED_WRITE_TOOLS),
            }
        self._health_cache = (now, result)
        return result
