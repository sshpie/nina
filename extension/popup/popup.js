const STORE = 'nina_prefs';

const voiceSel  = document.getElementById('voiceSel');
const rateSel   = document.getElementById('rateSel');
const injectBtn = document.getElementById('injectBtn');

// Load voices via a hidden iframe pointing to an empty page
// (popup has its own speech context)
let voices = [];
function loadVoices() {
  voices = speechSynthesis.getVoices().filter(v => v.name.includes('Microsoft'));
  if (!voices.length) voices = speechSynthesis.getVoices();
  voiceSel.innerHTML = '';
  voices.forEach((v, i) => {
    const label = v.name
      .replace('Microsoft ', '')
      .replace(' Online', '')
      .replace(' (Natural)', '')
      .replace(/ - .+/, '');
    voiceSel.add(new Option(label, i));
  });
  // Restore saved pref
  chrome.storage.local.get(STORE, data => {
    if (data[STORE]) {
      if (data[STORE].voiceIdx !== undefined) voiceSel.value = data[STORE].voiceIdx;
      if (data[STORE].rate !== undefined) rateSel.value = data[STORE].rate;
    }
  });
}

if (speechSynthesis.getVoices().length > 0) loadVoices();
speechSynthesis.onvoiceschanged = loadVoices;

// Save prefs on change
voiceSel.addEventListener('change', savePrefs);
rateSel.addEventListener('change', savePrefs);

function savePrefs() {
  chrome.storage.local.set({
    [STORE]: {
      voiceIdx: parseInt(voiceSel.value),
      rate: rateSel.value,
    }
  });
}

// Inject/toggle the content script bar on the active tab
injectBtn.addEventListener('click', () => {
  chrome.tabs.query({ active: true, currentWindow: true }, tabs => {
    if (!tabs[0]) return;
    chrome.scripting.executeScript({
      target: { tabId: tabs[0].id },
      files: ['content/content.js'],
    }).catch(() => {
      // Already injected via content_scripts — just send a toggle message
      chrome.tabs.sendMessage(tabs[0].id, { action: 'toggle' });
    });
  });
  window.close();
});
