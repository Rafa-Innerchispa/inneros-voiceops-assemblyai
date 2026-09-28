const copy = {
  en: {
    headline:"Governed voice operations for real systems.",
    subhead:"Live intelligence from InnerOS. Explicit approval before action. Verification after execution.",
    pillLive:"LIVE SYSTEM INTELLIGENCE",pillPermit:"EXPLICIT PERMIT",pillVerify:"VERIFIED ACTIONS",
    capReadTitle:"Read live state",capReadBody:"Home Assistant, UniFi, cameras, lights, servers and safe operational context.",
    capActTitle:"Three authorized actions",capActBody:"Lights, supported camera restart, and exact-target network restart.",
    capGovTitle:"Governed execution",capGovBody:"Read → Diagnose → Propose → Approve → Execute → Verify.",
    checking:"Checking secure gateway…",welcome:"Welcome to VoiceOps",authCopy:"Authenticate before entering the operational console.",
    oauthButton:"Continue with InnerOS OAuth",judgeAccess:"JUDGE ACCESS",username:"Username",password:"Password",
    enterJudge:"Enter demo console",security:"Judge sessions are restricted. No generic admin tools are exposed, and every consequential action still requires an explicit single-use permit.",
    footer:"Sovereign local runtime · Central authentication",invalid:"Invalid judge credentials.",unavailable:"Judge access is not configured.",ready:"Secure gateway ready",signed:"Session found. Opening console…"
  },
  es: {
    headline:"Operaciones por voz gobernadas para sistemas reales.",
    subhead:"Inteligencia en vivo desde InnerOS. Aprobación explícita antes de actuar. Verificación después de ejecutar.",
    pillLive:"INTELIGENCIA DEL SISTEMA EN VIVO",pillPermit:"PERMISO EXPLÍCITO",pillVerify:"ACCIONES VERIFICADAS",
    capReadTitle:"Leer estado real",capReadBody:"Home Assistant, UniFi, cámaras, luces, servidores y contexto operativo seguro.",
    capActTitle:"Tres acciones autorizadas",capActBody:"Luces, reinicio de cámara compatible y reinicio de red con objetivo exacto.",
    capGovTitle:"Ejecución gobernada",capGovBody:"Leer → Diagnosticar → Proponer → Aprobar → Ejecutar → Verificar.",
    checking:"Comprobando acceso seguro…",welcome:"Bienvenido a VoiceOps",authCopy:"Autentícate antes de entrar a la consola operativa.",
    oauthButton:"Continuar con OAuth de InnerOS",judgeAccess:"ACCESO PARA JUECES",username:"Usuario",password:"Contraseña",
    enterJudge:"Entrar a la consola demo",security:"Las sesiones de jueces están restringidas. No se exponen herramientas administrativas genéricas y toda acción relevante requiere un permiso explícito de un solo uso.",
    footer:"Runtime local soberano · Autenticación central",invalid:"Credenciales de juez incorrectas.",unavailable:"El acceso de jueces no está configurado.",ready:"Acceso seguro listo",signed:"Sesión encontrada. Abriendo consola…"
  }
};
let lang = localStorage.getItem("voiceops_ui_lang") || "en";
const applyLang=()=>{document.documentElement.lang=lang;document.querySelectorAll("[data-i18n]").forEach(el=>{const key=el.dataset.i18n;if(copy[lang][key])el.textContent=copy[lang][key]});document.getElementById("langToggle").textContent=lang==="en"?"ES":"EN"};
document.getElementById("langToggle").addEventListener("click",()=>{lang=lang==="en"?"es":"en";localStorage.setItem("voiceops_ui_lang",lang);applyLang()});
applyLang();

const statusEl=document.getElementById("systemStatus");
const oauthButton=document.getElementById("oauthButton");
const form=document.getElementById("judgeForm");
const errorEl=document.getElementById("errorMessage");

async function loadSession(){
  try{
    const res=await fetch("/api/auth/session",{credentials:"same-origin",cache:"no-store"});
    const data=await res.json();
    if(data.authenticated){statusEl.textContent=copy[lang].signed;location.replace("/console");return}
    statusEl.textContent=copy[lang].ready;
    if(!data.auth?.oauth_configured){oauthButton.classList.add("disabled");oauthButton.setAttribute("aria-disabled","true")}
    if(!data.auth?.judge_configured){form.querySelector("button").disabled=true}
  }catch{statusEl.textContent="Secure gateway unavailable"}
}
loadSession();

form.addEventListener("submit",async(e)=>{
  e.preventDefault();errorEl.textContent="";
  const payload={username:document.getElementById("username").value,password:document.getElementById("password").value};
  const res=await fetch("/api/auth/judge-login",{method:"POST",credentials:"same-origin",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
  if(res.ok){location.replace("/console");return}
  const data=await res.json().catch(()=>({}));
  errorEl.textContent=data.error==="invalid_credentials"?copy[lang].invalid:copy[lang].unavailable;
});
