// Open in Safari (Mac via Parallels) - Background service worker
// Handles action click, context menus, and keyboard command to send the current URL to the Mac helper.
//
// Default settings; user can override in options page.
const DEFAULTS = {
  host: "10.211.55.2",
  port: 51888,
  token: "changeme123456",
  path: "/open",
  useHttps: false
};

const STORAGE_KEY = "openInSafariSettings";
const CONTEXT_MENU_ID = "open-in-safari-context";

// Utility: get settings from storage with defaults
async function getSettings() {
  return new Promise((resolve) => {
    chrome.storage.sync.get([STORAGE_KEY], (res) => {
      const stored = res[STORAGE_KEY] || {};
      resolve({ ...DEFAULTS, ...stored });
    });
  });
}

// Utility: send notification
function notify(title, message) {
  try {
    chrome.notifications.create({
      type: "basic",
      iconUrl: "icon128.png",
      title,
      message
    }, () => {});
  } catch (e) {
    // Fallback: set badge
    chrome.action.setBadgeText({ text: "!" });
    chrome.action.setBadgeBackgroundColor({ color: "#d9534f" });
    setTimeout(() => chrome.action.setBadgeText({ text: "" }), 3000);
  }
}

// Build target URL for helper
function buildHelperUrl(settings) {
  const scheme = settings.useHttps ? "https" : "http";
  const host = settings.host;
  const port = settings.port;
  const path = settings.path || "/open";
  return `${scheme}://${host}:${port}${path}`;
}

// POST to helper to open the URL in Safari
async function sendOpenRequest(targetUrl) {
  const settings = await getSettings();
  const helperUrl = buildHelperUrl(settings);

  try {
    const res = await fetch(helperUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-OpenInSafari-Token": settings.token
      },
      body: JSON.stringify({ url: targetUrl })
    });

    if (!res.ok) {
      const text = await res.text();
      notify("Open in Safari failed", `HTTP ${res.status}: ${text || "Unknown error"}`);
      return;
    }
    notify("Opened in Safari", targetUrl);
  } catch (err) {
    notify("Open in Safari error", String(err));
  }
}

// Handle toolbar button
chrome.action.onClicked.addListener(async (tab) => {
  if (!tab || !tab.url) {
    notify("No tab URL", "Unable to read current tab URL.");
    return;
  }
  await sendOpenRequest(tab.url);
});

// Context menu
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: CONTEXT_MENU_ID,
    title: "Open in Safari (Mac)",
    contexts: ["page", "link", "image", "video", "audio", "selection"]
  }, () => { /* no-op */ });
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== CONTEXT_MENU_ID) return;
  const url = info.linkUrl || info.srcUrl || (tab && tab.url);
  if (!url) {
    notify("No URL", "Nothing to open.");
    return;
  }
  await sendOpenRequest(url);
});

// Keyboard command
chrome.commands.onCommand.addListener(async (command) => {
  if (command !== "open-in-safari") return;
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || !tab.url) {
    notify("No tab URL", "Unable to read current tab URL.");
    return;
  }
  await sendOpenRequest(tab.url);
});