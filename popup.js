// Originally located at C:\Users\phobrla\source\repos\Open in Safari\popup.js
document.getElementById('openinsafari').addEventListener('click', () => {
  chrome.runtime.sendMessage({ action: 'openinsafari' });
});