(function () {
  const ID = 'nuclide-read-aloud';

  // Toggle off if already running
  if (document.getElementById(ID)) {
    speechSynthesis.cancel();
    document.getElementById(ID).remove();
    document.body.style.paddingTop = _prevPadding || '';
    return;
  }

  // ── Text extraction ──────────────────────────────────────────────────────
  function extractText() {
    const selectors = [
      'article',
      '[role="main"]',
      'main',
      '#mw-content-text',       // Wikipedia
      '.article-body',
      '.post-content',
      '.entry-content',
      '.story-body',
      '#content',
      '.content',
    ];
    for (const sel of selectors) {
      const el = document.querySelector(sel);
      if (el && el.innerText.trim().length > 200) {
        const clone = el.cloneNode(true);
        clone.querySelectorAll(
          'script,style,nav,footer,.sidebar,figure,sup,.mw-editsection,table'
        ).forEach(e => e.remove());
        return clone.innerText.replace(/\n{3,}/g, '\n\n').trim();
      }
    }
    return document.body.innerText.trim();
  }

  // ── State ────────────────────────────────────────────────────────────────
  const rawText = extractText();
  // Split on sentence boundaries, keep chunks ≤400 chars
  const chunks = rawText.match(/[^.!?\n]{1,400}(?:[.!?\n]+|$)/g) || [rawText];
  let idx = 0;
  let playing = false;
  let voices = [];
  const _prevPadding = document.body.style.paddingTop;

  // ── Voice loading ────────────────────────────────────────────────────────
  function loadVoices() {
    const all = speechSynthesis.getVoices();
    voices = all.filter(v => v.lang.startsWith('en'));
    if (!voices.length) voices = all;
    return voices;
  }

  // ── UI ───────────────────────────────────────────────────────────────────
  const bar = document.createElement('div');
  bar.id = ID;
  Object.assign(bar.style, {
    position: 'fixed', top: '0', left: '0', right: '0', zIndex: '2147483647',
    background: '#12122a', color: '#dde', fontFamily: 'system-ui,sans-serif',
    fontSize: '13px', display: 'flex', alignItems: 'center', gap: '10px',
    padding: '6px 14px', boxShadow: '0 2px 10px rgba(0,0,0,0.5)',
    borderBottom: '2px solid #2a2a6a',
  });

  function mkBtn(text, fn) {
    const b = document.createElement('button');
    b.textContent = text;
    Object.assign(b.style, {
      background: '#1e1e4a', color: '#dde', border: '1px solid #444',
      borderRadius: '4px', padding: '4px 11px', fontSize: '13px', cursor: 'pointer',
    });
    b.onmouseover = () => b.style.background = '#2d2d6a';
    b.onmouseout  = () => b.style.background = '#1e1e4a';
    b.onclick = fn;
    return b;
  }

  function mkSelect(styles) {
    const s = document.createElement('select');
    Object.assign(s.style, {
      background: '#1e1e4a', color: '#dde', border: '1px solid #444',
      borderRadius: '4px', padding: '4px 8px', fontSize: '13px',
      ...styles,
    });
    return s;
  }

  const tag      = document.createElement('span');
  tag.textContent = 'READ ALOUD';
  Object.assign(tag.style, { color: '#5599ff', fontWeight: '700', letterSpacing: '1px', fontSize: '11px' });

  const playBtn  = mkBtn('▶', togglePlay);
  const stopBtn  = mkBtn('■', stop);
  const backBtn  = mkBtn('«', () => { idx = Math.max(0, idx - 2); if (playing) { speechSynthesis.cancel(); speak(); } });
  const fwdBtn   = mkBtn('»', () => { if (playing) { speechSynthesis.cancel(); } });

  const voiceSel = mkSelect({ maxWidth: '220px' });
  const speedSel = mkSelect({ width: '70px' });
  [['0.75×','0.75'],['1×','1'],['1.25×','1.25'],['1.5×','1.5'],['1.75×','1.75'],['2×','2']].forEach(([l,v]) => {
    const o = new Option(l, v);
    if (v === '1') o.selected = true;
    speedSel.add(o);
  });

  const prog = document.createElement('span');
  Object.assign(prog.style, { fontSize: '11px', color: '#778', minWidth: '60px' });

  const closeBtn = mkBtn('✕', close);
  closeBtn.style.marginLeft = 'auto';
  closeBtn.style.color = '#f88';

  bar.append(tag, backBtn, playBtn, fwdBtn, stopBtn, voiceSel, speedSel, prog, closeBtn);
  document.body.prepend(bar);
  document.body.style.paddingTop = '40px';

  // ── Voice select population ──────────────────────────────────────────────
  function populateVoices() {
    const mv = loadVoices();
    voiceSel.innerHTML = '';
    mv.forEach((v, i) => {
      const label = v.name
        .replace(/^(?:Microsoft|Google) /, '')
        .replace(/ Online$/, '')
        .replace(/ \(Natural\)$/, '')
        .replace(/ - /, ' · ');
      voiceSel.add(new Option(label, i));
    });
  }
  populateVoices();
  speechSynthesis.onvoiceschanged = populateVoices;

  // ── Playback ─────────────────────────────────────────────────────────────
  function speak() {
    if (idx >= chunks.length) { stop(); return; }
    const utt = new SpeechSynthesisUtterance(chunks[idx]);
    utt.voice = voices[parseInt(voiceSel.value)] || voices[0];
    utt.rate  = parseFloat(speedSel.value);
    utt.onend   = () => { idx++; updateProg(); if (playing) speak(); };
    utt.onerror = () => { idx++; if (playing) speak(); };
    speechSynthesis.speak(utt);
    updateProg();
  }

  function updateProg() {
    prog.textContent = `${Math.min(idx + 1, chunks.length)} / ${chunks.length}`;
  }

  function togglePlay() {
    if (playing) {
      playing = false;
      playBtn.textContent = '▶';
      speechSynthesis.pause();
    } else {
      playing = true;
      playBtn.textContent = '⏸';
      speechSynthesis.paused ? speechSynthesis.resume() : speak();
    }
  }

  function stop() {
    playing = false;
    idx = 0;
    speechSynthesis.cancel();
    playBtn.textContent = '▶';
    updateProg();
  }

  function close() {
    stop();
    bar.remove();
    document.body.style.paddingTop = _prevPadding;
  }

  updateProg();
})();
