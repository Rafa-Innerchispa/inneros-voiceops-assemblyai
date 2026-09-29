const copy={
en:{
signIn:"Sign In",kicker:"REAL SYSTEMS · VERIFIED ACTIONS.",headline:'Governed Voice<br>Operations for<br><span>Real Systems</span>',
subhead:"Live intelligence. Explicit approval. Verified actions.",
summary:"InnerOS VoiceOps connects natural language to real-world operations safely, securely, and under your control.",
oauthButton:"Continue with InnerOS OAuth",judgeAccess:"Judge Access",securityLine:"Enterprise-grade security. Your data stays under your control.",
checking:"Checking secure gateway…",username:"Username",password:"Password",enterJudge:"Enter demo console",
systemsOnline:"System State",authorizedActions:"Authorized Actions",runtime:"Voice Runtime",visualCaption:"INTELLIGENCE IN SERVICE OF AN OPERATIONAL WORLD.",
authorized:"AUTHORIZED",safeAdapter:"SAFE ADAPTER",lightsTitle:"Lights",lightsBody:"Control connected lighting with explicit approval and verification.",
cameraTitle:"Camera Restart",cameraBody:"Restart supported cameras only when a verified safe adapter exists.",
networkTitle:"Network Restart",networkBody:"Restart one exact allowlisted UniFi device after explicit approval.",voiceControl:"Voice Control",
footer:"From conversation to real-world impact.",invalid:"Invalid judge credentials.",unavailable:"Judge access is not configured.",ready:"Secure gateway ready",signed:"Session found. Opening console…"
},
es:{
signIn:"Entrar",kicker:"SISTEMAS REALES · ACCIONES VERIFICADAS.",headline:'Operaciones por Voz<br>Gobernadas para<br><span>Sistemas Reales</span>',
subhead:"Inteligencia en vivo. Aprobación explícita. Acciones verificadas.",
summary:"InnerOS VoiceOps conecta lenguaje natural con operaciones del mundo real de forma segura, gobernada y bajo tu control.",
oauthButton:"Continuar con OAuth de InnerOS",judgeAccess:"Acceso para jueces",securityLine:"Seguridad de nivel empresarial. Tus datos permanecen bajo tu control.",
checking:"Comprobando acceso seguro…",username:"Usuario",password:"Contraseña",enterJudge:"Entrar a la consola demo",
systemsOnline:"Estado del sistema",authorizedActions:"Acciones autorizadas",runtime:"Runtime de voz",visualCaption:"INTELIGENCIA AL SERVICIO DE UN MUNDO OPERATIVO.",
authorized:"AUTORIZADO",safeAdapter:"ADAPTADOR SEGURO",lightsTitle:"Luces",lightsBody:"Controla iluminación conectada con aprobación explícita y verificación.",
cameraTitle:"Reiniciar Cámara",cameraBody:"Reinicia cámaras compatibles solo cuando existe un adaptador seguro verificado.",
networkTitle:"Reiniciar Red",networkBody:"Reinicia un único dispositivo UniFi permitido tras aprobación explícita.",voiceControl:"Control por Voz",
footer:"De la conversación al impacto en el mundo real.",invalid:"Credenciales de juez incorrectas.",unavailable:"El acceso de jueces no está configurado.",ready:"Acceso seguro listo",signed:"Sesión encontrada. Abriendo consola…"
}};
let lang=localStorage.getItem("voiceops_ui_lang")||"en";
const applyLang=()=>{
 document.documentElement.lang=lang;
 document.querySelectorAll("[data-i18n]").forEach(el=>{const k=el.dataset.i18n;if(copy[lang][k])el.textContent=copy[lang][k]});
 document.querySelectorAll("[data-i18n-html]").forEach(el=>{const k=el.dataset.i18nHtml;if(copy[lang][k])el.innerHTML=copy[lang][k]});
 document.getElementById("langToggle").textContent=lang==="en"?"ES":"EN";
};
document.getElementById("langToggle").addEventListener("click",()=>{lang=lang==="en"?"es":"en";localStorage.setItem("voiceops_ui_lang",lang);applyLang()});
applyLang();

const statusEl=document.getElementById("systemStatus");
const oauthButton=document.getElementById("oauthButton");
const form=document.getElementById("judgeForm");
const errorEl=document.getElementById("errorMessage");
const judgePanel=document.getElementById("judgePanel");
document.getElementById("judgeToggle").addEventListener("click",()=>judgePanel.classList.toggle("hidden"));

async function loadSession(){
 try{
  const res=await fetch("/api/auth/session",{credentials:"same-origin",cache:"no-store"});
  const data=await res.json();
  if(data.authenticated){statusEl.textContent=copy[lang].signed;location.replace("/console");return}
  statusEl.textContent=copy[lang].ready;
  if(!data.auth?.oauth_configured){oauthButton.classList.add("disabled");oauthButton.setAttribute("aria-disabled","true")}
  if(!data.auth?.judge_configured){form.querySelector("button").disabled=true}
 }catch{statusEl.textContent="Secure gateway unavailable"}
 try{
  const res=await fetch("/health",{cache:"no-store"});
  const h=await res.json();
  document.getElementById("systemLiveState").textContent=h.live_system_bridge?.home_assistant_live?"LIVE":"CHECK";
  document.getElementById("voiceRuntime").textContent=h.live_voice_enabled?"ASSEMBLYAI":"OFF";
 }catch{}
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
