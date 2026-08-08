// Forward keyboard command to the active tab's content script
chrome.commands.onCommand.addListener(command => {
  if (command !== 'toggle-nina') return;
  chrome.tabs.query({ active: true, currentWindow: true }, tabs => {
    if (tabs[0]) {
      chrome.tabs.sendMessage(tabs[0].id, { action: 'toggle' }).catch(() => {});
    }
  });
});
