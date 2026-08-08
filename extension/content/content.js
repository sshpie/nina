(() => {
  const ID      = 'nina-ext-bar';
  const STORE   = 'nina_prefs';
  const ACCENT  = '#4a7aff';

  // ── Toggle on/off ──────────────────────────────────────────────────────────
  if (document.getElementById(ID)) {
    ninaStop();
    document.getElementById(ID).remove();
    document.documentElement.style.marginTop = '';
    return;
  }

  // ── Text extraction ────────────────────────────────────────────────────────
  function extractText() {
    const selectors = [
      'article', '[role="main"]', 'main',
      '#mw-content-text',        // Wikipedia
      '.article-body', '.post-content', '.entry-content',
      '.story-body', '.article__body', '.post__content',
      '#content', '.content',
    ];
    for (const sel of selectors) {
      const el = document.querySelector(sel);
      if (el && el.innerText.trim().length > 200) {
        const clone = el.cloneNode(true);
        clone.querySelectorAll(
          'script,style,nav,footer,aside,.sidebar,figure,sup,' +
          '.mw-editsection,.advertisement,.related-articles,table'
        ).forEach(e => e.remove());
        return clone.innerText.replace(/\n{3,}/g, '\n\n').trim();
      }
    }
    return document.body.innerText.trim().substring(0, 50000);
  }

  // Split on paragraph breaks and sentence boundaries
  function toChunks(text) {
    const paras = text.split(/\n\n+/).filter(p => p.trim().length > 0);
    const out   = [];
    for (const p of paras) {
      // Further split long paragraphs at sentence boundaries
      const sentences = p.match(/[^.!?]{1,500}[.!?]+|[^.!?]{1,500}$/g) || [p];
      out.push(...sentences.map(s => s.trim()).filter(Boolean));
    }
    return out;
  }

  // ── State ──────────────────────────────────────────────────────────────────
  const chunks  = toChunks(extractText());
  let idx       = 0;
  let playing   = false;
  let paused    = false;
  let msVoices  = [];
  let prefs     = { voiceIdx: 0, rate: '+0%' };

  // Load saved prefs
  chrome.storage.local.get(STORE, data => {
    if (data[STORE]) prefs = { ...prefs, ...data[STORE] };
    applyPrefs();
  });

  function savePrefs() {
    chrome.storage.local.set({ [STORE]: prefs });
  }

  function applyPrefs() {
    if (voiceSel && msVoices.length > prefs.voiceIdx) {
      voiceSel.value = prefs.voiceIdx;
    }
    if (rateSel) rateSel.value = prefs.rate;
  }

  // ── Build bar ─────────────────────────────────────────────────────────────
  const bar = document.createElement('div');
  bar.id    = ID;

  // Controls
  const makeBtn = (label, title, fn) => {
    const b = document.createElement('button');
    b.className   = 'nina-btn';
    b.textContent = label;
    b.title       = title;
    b.addEventListener('click', fn);
    return b;
  };

  const label    = document.createElement('span');
  label.className = 'nina-label';
  label.textContent = 'NINA';

  const backBtn  = makeBtn('«', 'Back',  () => { idx = Math.max(0, idx - 2); if (playing) { speechSynthesis.cancel(); speakChunk(); } });
  const playBtn  = makeBtn('▶', 'Play',  togglePlay);
  const fwdBtn   = makeBtn('»', 'Skip',  () => { speechSynthesis.cancel(); });
  const stopBtn  = makeBtn('■', 'Stop',  ninaStop);

  const voiceSel = document.createElement('select');
  voiceSel.className = 'nina-select nina-voice-sel';
  voiceSel.title = 'Voice';
  voiceSel.addEventListener('change', () => {
    prefs.voiceIdx = parseInt(voiceSel.value);
    savePrefs();
    if (playing) { speechSynthesis.cancel(); speakChunk(); }
  });

  const rateSel = document.createElement('select');
  rateSel.className = 'nina-select';
  rateSel.title = 'Speed';
  [['0.75×','0.75'],['1×','1'],['1.25×','1.25'],['1.5×','1.5'],['1.75×','1.75'],['2×','2']].forEach(([l, v]) => {
    const o = new Option(l, v);
    if (v === '1') o.selected = true;
    rateSel.add(o);
  });
  rateSel.addEventListener('change', () => {
    prefs.rate = rateSel.value;
    savePrefs();
    if (playing) { speechSynthesis.cancel(); speakChunk(); }
  });

  const prog = document.createElement('span');
  prog.className = 'nina-prog';

  const closeBtn = makeBtn('✕', 'Close', () => {
    ninaStop();
    bar.remove();
    document.documentElement.style.marginTop = '';
  });
  closeBtn.className += ' nina-close';

  bar.append(label, backBtn, playBtn, fwdBtn, stopBtn, voiceSel, rateSel, prog, closeBtn);
  document.body.prepend(bar);
  document.documentElement.style.marginTop = '44px';

  // ── Voice loading ──────────────────────────────────────────────────────────
  function populateVoices() {
    const all = speechSynthesis.getVoices();
    msVoices  = all.filter(v => v.name.includes('Microsoft'));
    if (!msVoices.length) msVoices = all;

    voiceSel.innerHTML = '';
    msVoices.forEach((v, i) => {
      const display = v.name
        .replace('Microsoft ', '')
        .replace(' Online', '')
        .replace(' (Natural)', '')
        .replace(/ - .+/, '');
      voiceSel.add(new Option(display, i));
    });
    applyPrefs();
    updateProg();
  }

  if (speechSynthesis.getVoices().length > 0) {
    populateVoices();
  }
  speechSynthesis.addEventListener('voiceschanged', populateVoices);

  // ── Playback ───────────────────────────────────────────────────────────────
  function speakChunk() {
    if (idx >= chunks.length) { ninaStop(); return; }
    const utt   = new SpeechSynthesisUtterance(chunks[idx]);
    utt.voice   = msVoices[parseInt(voiceSel.value)] || msVoices[0] || null;
    utt.rate    = parseFloat(rateSel.value);
    utt.onend   = () => { idx++; updateProg(); if (playing) speakChunk(); };
    utt.onerror = () => { idx++; if (playing) speakChunk(); };
    speechSynthesis.speak(utt);
    updateProg();
    highlightChunk(idx);
  }

  function togglePlay() {
    if (playing) {
      playing = false;
      paused  = true;
      speechSynthesis.pause();
      playBtn.textContent = '▶';
    } else if (paused) {
      playing = true;
      paused  = false;
      playBtn.textContent = '⏸';
      speechSynthesis.resume();
    } else {
      playing = true;
      playBtn.textContent = '⏸';
      speakChunk();
    }
  }

  function ninaStop() {
    playing = false;
    paused  = false;
    idx     = 0;
    speechSynthesis.cancel();
    if (playBtn) playBtn.textContent = '▶';
    clearHighlight();
    updateProg();
  }

  function updateProg() {
    if (prog) prog.textContent = chunks.length ? `${Math.min(idx + 1, chunks.length)}/${chunks.length}` : '';
  }

  // ── Highlight current paragraph ────────────────────────────────────────────
  let _hlEl = null;

  function highlightChunk(i) {
    clearHighlight();
    const chunk = chunks[i];
    if (!chunk || chunk.length < 10) return;
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const search = chunk.substring(0, 40).trim();
    let node;
    while ((node = walker.nextNode())) {
      if (node.textContent.includes(search)) {
        const span = document.createElement('mark');
        span.className = 'nina-hl';
        span.id        = 'nina-hl-current';
        const range    = document.createRange();
        const idx_in   = node.textContent.indexOf(search);
        range.setStart(node, idx_in);
        range.setEnd(node, Math.min(idx_in + chunk.length, node.textContent.length));
        try {
          range.surroundContents(span);
          span.scrollIntoView({ block: 'center', behavior: 'smooth' });
          _hlEl = span;
        } catch (_) {}
        break;
      }
    }
  }

  function clearHighlight() {
    const existing = document.getElementById('nina-hl-current');
    if (existing) {
      const parent = existing.parentNode;
      while (existing.firstChild) parent.insertBefore(existing.firstChild, existing);
      parent.removeChild(existing);
    }
    _hlEl = null;
  }

  // ── Keyboard shortcut (Ctrl+Shift+U) ──────────────────────────────────────
  document.addEventListener('keydown', e => {
    if (e.ctrlKey && e.shiftKey && e.key === 'U') {
      e.preventDefault();
      togglePlay();
    }
  });

  // ── Message handler for popup ──────────────────────────────────────────────
  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg.action === 'getVoices') {
      const names = msVoices.map(v =>
        v.name.replace('Microsoft ', '').replace(' Online', '').replace(' (Natural)', '').replace(/ - .+/, '')
      );
      sendResponse({ voices: names });
    }
    if (msg.action === 'toggle') {
      togglePlay();
      sendResponse({ ok: true });
    }
    return true;
  });

  updateProg();
})();
