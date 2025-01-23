// Originally located at C:\Users\phobrla\source\repos\Open in Safari\background.js
chrome.action.onClicked.addListener((tab) => {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const activeTab = tabs[0];
    const url = activeTab.url;

    // Send the URL to the native messaging host
    chrome.runtime.sendNativeMessage('com.cupofjune.openinsafari', { url: url }, (response) => {
      if (chrome.runtime.lastError) {
        console.error(chrome.runtime.lastError.message);
      } else {
        console.log('Response from native app:', response);
      }
    });
  });
});