const STORE = 'nina_prefs';

const voiceSel  = document.getElementById('voiceSel');
const rateSel   = document.getElementById('rateSel');
const injectBtn = document.getElementById('injectBtn');
const voiceNote = document.getElementById('voiceNote');

// Restore saved speed pref
chrome.storage.local.get(STORE, data => {
  if (data[STORE]?.rate) rateSel.value = data[STORE].rate;
});

// Request voice list from the active tab's content script
chrome.tabs.query({ active: true, currentWindow: true }, tabs => {
  if (!tabs[0]) return;
  chrome.tabs.sendMessage(tabs[0].id, { action: 'getVoices' }, response => {
    if (chrome.runtime.lastError || !response?.voices?.length) {
      // Content script not injected yet — show placeholder
      voiceSel.innerHTML = '<option value="">Set on page bar after activating</option>';
      if (voiceNote) voiceNote.textContent = 'Click "Read This Page" first to load voices.';
      return;
    }
    const voices = response.voices;
    chrome.storage.local.get(STORE, data => {
      const saved = data[STORE]?.voiceIdx || 0;
      voiceSel.innerHTML = '';
      voices.forEach((name, i) => voiceSel.add(new Option(name, i)));
      voiceSel.value = saved;
    });
  });
});

// Save prefs on change
voiceSel.addEventListener('change', savePrefs);
rateSel.addEventListener('change', savePrefs);

function savePrefs() {
  const prefs = { rate: rateSel.value };
  const v = parseInt(voiceSel.value);
  if (!isNaN(v)) prefs.voiceIdx = v;
  chrome.storage.local.set({ [STORE]: prefs });
}

// Inject / toggle Nina on the active tab
injectBtn.addEventListener('click', () => {
  chrome.tabs.query({ active: true, currentWindow: true }, tabs => {
    if (!tabs[0]) return;
    // Try toggling via message first (already injected)
    chrome.tabs.sendMessage(tabs[0].id, { action: 'toggle' }, response => {
      if (chrome.runtime.lastError) {
        // Not injected yet — inject now
        chrome.scripting.executeScript({
          target: { tabId: tabs[0].id },
          files: ['content/content.js'],
        });
      }
    });
  });
  window.close();
});
