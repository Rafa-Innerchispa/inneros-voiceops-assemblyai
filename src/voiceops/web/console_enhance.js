(() => {
  const translations = new Map([
    ["Governed voice execution.","Ejecución por voz gobernada."],
    ["Speak naturally. InnerOS recalls context, reasons locally, asks for permission, acts once, verifies the result and keeps the proof.","Habla con naturalidad. InnerOS recupera contexto, razona localmente, pide permiso, actúa una sola vez, verifica el resultado y conserva la evidencia."],
    ["LIVE READS · APPROVAL-GATED ACTIONS","LECTURAS EN VIVO · ACCIONES CON APROBACIÓN"],
    ["LOCAL-FIRST","LOCAL-FIRST"],
    ["Ready for live voice.","Listo para voz en vivo."],
    ["Speech is evidence. Memory is context. Approval is authorization.","La voz es evidencia. La memoria es contexto. La aprobación es autorización."],
    ["Live voice is the primary demo.","La voz en vivo es la demostración principal."],
    ["Run judge-safe fallback","Ejecutar fallback seguro"],
    ["Yes, authorize","Sí, autorizo"],
    ["Try ambiguity","Probar ambigüedad"],
    ["Reset","Reiniciar"],
    ["AUTHORIZED ACTIONS","ACCIONES AUTORIZADAS"],
    ["Three governed action families. Everything else fails closed.","Tres familias de acciones gobernadas. Todo lo demás se bloquea por defecto."],
    ["LIGHTS","LUCES"],
    ["Turn one exact Home Assistant light on or off. Approval is still required before execution.","Enciende o apaga una luz exacta de Home Assistant. La aprobación sigue siendo obligatoria antes de ejecutar."],
    ["Prepare ON","Preparar ENCENDER"],
    ["Prepare OFF","Preparar APAGAR"],
    ["CAMERA RESTART","REINICIAR CÁMARA"],
    ["Restart only a camera with an explicitly configured safe restart adapter. No adapter means no action.","Reinicia solo una cámara con un adaptador seguro configurado explícitamente. Sin adaptador, no hay acción."],
    ["Prepare restart","Preparar reinicio"],
    ["NETWORK RESTART","REINICIAR RED"],
    ["Restart exactly one allowlisted UniFi device. Connectivity may drop temporarily.","Reinicia exactamente un dispositivo UniFi permitido. La conectividad puede interrumpirse temporalmente."],
    ["Select an action to prepare a governed proposal.","Selecciona una acción para preparar una propuesta gobernada."],
    ["Technical proof and replay","Prueba técnica y reproducción"],
    ["LOG OUT","SALIR"]
  ]);
  const reverse = new Map([...translations].map(([a,b]) => [b,a]));
  let lang = localStorage.getItem("voiceops_ui_lang") || "en";
  const toggle = document.getElementById("consoleLangToggle");

  function translateTextMap(map) {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const nodes=[]; while(walker.nextNode()) nodes.push(walker.currentNode);
    for(const node of nodes){
      const trimmed=node.nodeValue.trim();
      if(map.has(trimmed)) node.nodeValue=node.nodeValue.replace(trimmed,map.get(trimmed));
    }
  }
  function applyLang(next){
    if(next===lang) return;
    translateTextMap(next==="es"?translations:reverse);
    lang=next; localStorage.setItem("voiceops_ui_lang",lang);
    document.documentElement.lang=lang;
    if(toggle) toggle.textContent=lang==="en"?"ES":"EN";
  }
  if(lang==="es"){ const before=lang; lang="en"; applyLang(before); }
  if(toggle) toggle.addEventListener("click",()=>applyLang(lang==="en"?"es":"en"));

  const preview=document.getElementById("actionPreview");
  async function prepare(command){
    if(preview) preview.textContent=lang==="es"?"Consultando el estado real…":"Reading live state…";
    try{
      const res=await fetch("/api/tool/propose-system-action",{method:"POST",credentials:"same-origin",headers:{"Content-Type":"application/json"},body:JSON.stringify({command})});
      if(res.status===401){location.replace("/");return}
      const data=await res.json();
      if(preview){
        if(data.requires_approval){
          const p=data.proposal||{};
          preview.textContent=(lang==="es"?"Propuesta lista: ":"Proposal ready: ")+(p.tool||"action")+" · "+JSON.stringify(p.args||{})+" · "+(lang==="es"?"autoriza por voz o con Permit.":"authorize by voice or Permit.");
        }else{
          preview.textContent=data.live_result?.restart_message||data.message||(lang==="es"?"No hay una acción segura disponible para ese objetivo.":"No safe action is available for that target.");
        }
      }
    }catch{if(preview)preview.textContent=lang==="es"?"No se pudo consultar VoiceOps.":"VoiceOps query failed."}
  }
  document.getElementById("lightOnBtn")?.addEventListener("click",()=>prepare("Turn on light "+document.getElementById("lightTarget").value));
  document.getElementById("lightOffBtn")?.addEventListener("click",()=>prepare("Turn off light "+document.getElementById("lightTarget").value));
  document.getElementById("cameraRestartBtn")?.addEventListener("click",()=>prepare("Restart camera "+document.getElementById("cameraTarget").value));
  document.getElementById("networkRestartBtn")?.addEventListener("click",()=>prepare("Restart "+document.getElementById("networkTarget").value));

  document.getElementById("logoutBtn")?.addEventListener("click",async()=>{
    await fetch("/api/auth/logout",{method:"POST",credentials:"same-origin"}).catch(()=>{});
    location.replace("/");
  });

  async function liveIntel(){
    try{
      const res=await fetch("/api/state",{credentials:"same-origin",cache:"no-store"});
      if(res.status===401){location.replace("/");return}
      const state=await res.json();
      const bridge=state.live_system?.bridge||{};
      const el=document.getElementById("liveIntelSummary");
      if(el){
        const network=(bridge.network_restart_targets||[]).length;
        const cameras=bridge.camera_restart_target_count||0;
        el.textContent=(bridge.home_assistant_live?"Home Assistant LIVE":"Home Assistant unavailable")+" · "+network+" network restart targets · "+cameras+" camera restart adapters · 3 write families";
      }
    }catch{}
  }
  liveIntel();
})();