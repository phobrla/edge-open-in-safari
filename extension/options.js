const STORAGE_KEY = "openInSafariSettings";
const DEFAULTS = {
  host: "10.211.55.2",
  port: 51888,
  token: "changeme123456",
  path: "/open",
  useHttps: false
};

function getEl(id) { return document.getElementById(id); }
function setStatus(msg) {
  const s = getEl("status");
  s.textContent = msg;
}

function loadSettings() {
  chrome.storage.sync.get([STORAGE_KEY], (res) => {
    const st = { ...DEFAULTS, ...(res[STORAGE_KEY] || {}) };
    getEl("host").value = st.host;
    getEl("port").value = st.port;
    getEl("token").value = st.token;
    getEl("https").checked = !!st.useHttps;
    setStatus("Loaded settings.");
  });
}

function saveSettings() {
  const st = {
    host: getEl("host").value.trim() || DEFAULTS.host,
    port: parseInt(getEl("port").value, 10) || DEFAULTS.port,
    token: getEl("token").value || DEFAULTS.token,
    useHttps: !!getEl("https").checked,
    path: DEFAULTS.path
  };
  chrome.storage.sync.set({ [STORAGE_KEY]: st }, () => {
    setStatus("Saved.");
  });
}

async function testConnection() {
  setStatus("Testing...");
  const st = await new Promise((resolve) => {
    chrome.storage.sync.get([STORAGE_KEY], (res) => resolve({ ...DEFAULTS, ...(res[STORAGE_KEY] || {}) }));
  });
  const scheme = st.useHttps ? "https" : "http";
  const url = `${scheme}://${st.host}:${st.port}/ping`;
  try {
    const res = await fetch(url, { headers: { "X-OpenInSafari-Token": st.token } });
    const txt = await res.text();
    setStatus(`GET ${url}\nHTTP ${res.status}\n${txt}`);
  } catch (e) {
    setStatus(`Error: ${e}`);
  }
}

document.addEventListener("DOMContentLoaded", loadSettings);
getEl("save").addEventListener("click", saveSettings);
getEl("test").addEventListener("click", testConnection);