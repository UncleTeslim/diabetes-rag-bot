/* ═══════════════════════════════════════════════════════════════════
   DiaWise – Chat UI Logic  v4
   Streaming (SSE via fetch ReadableStream), localStorage persistence,
   onboarding profile flow, evidence panel, follow-up chips, mode toggle.
═══════════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  // ── Constants ────────────────────────────────────────────────────
  const STORAGE_KEY  = 'diawise_history';
  const MODE_KEY     = 'diawise_mode';
  const PROFILE_KEY  = 'diawise_profile';
  const MAX_HISTORY  = 100;

  // ── DOM refs ─────────────────────────────────────────────────────
  const feedEl         = document.getElementById('dw-feed');
  const welcomeEl      = document.getElementById('dw-welcome');
  const followupsEl    = document.getElementById('dw-followups');
  const chatForm       = document.getElementById('dw-form');
  const inputEl        = document.getElementById('dw-input');
  const sendBtn        = document.getElementById('dw-send-btn');
  const clearBtn       = document.getElementById('dw-clear-btn');
  const evidenceEl     = document.getElementById('dw-evidence');
  const evidenceBody   = document.getElementById('dw-evidence-body');
  const evidenceClose  = document.getElementById('dw-evidence-close');
  const evidenceToggle = document.getElementById('dw-evidence-toggle-btn');
  const modeButtons    = document.querySelectorAll('.dw-mode-toggle__btn');
  const starterChips   = document.querySelectorAll('.dw-starter-chip');
  const onboardingEl   = document.getElementById('dw-onboarding');
  const onboardingForm = document.getElementById('dw-onboarding-form');

  // ── State ─────────────────────────────────────────────────────────
  let currentMode = localStorage.getItem(MODE_KEY) || 'learning';
  let isLoading   = false;
  let history     = [];

  // ── Init ──────────────────────────────────────────────────────────
  function init() {
    if (!feedEl || !chatForm) return;
    const profile = getProfile();
    if (!profile || !profile.name) {
      showOnboarding();
    } else {
      bootChat();
    }
  }

  function bootChat() {
    applyMode(currentMode);
    // Personalise welcome greeting if profile exists
    const profile = getProfile();
    if (profile && profile.name && welcomeEl) {
      const h2 = welcomeEl.querySelector('h2');
      if (h2) {
        h2.className = 'dw-welcome__greeting';
        h2.textContent = `Hi ${profile.name}, ask me anything about diabetes`;
      }
    }
    loadHistory();
    bindEvents();
    if (inputEl) {
      sendBtn.disabled = true;
      inputEl.focus();
    }
  }

  // ── Profile ───────────────────────────────────────────────────────
  function getProfile() {
    try { return JSON.parse(localStorage.getItem(PROFILE_KEY) || 'null'); }
    catch (_) { return null; }
  }

  function saveProfile(p) {
    localStorage.setItem(PROFILE_KEY, JSON.stringify(p));
  }

  // ── Onboarding ────────────────────────────────────────────────────
  function showOnboarding() {
    if (!onboardingEl) { bootChat(); return; }
    onboardingEl.classList.add('active');
    requestAnimationFrame(() => {
      const first = onboardingEl.querySelector('input[type=text], input[type=number]');
      if (first) first.focus();
    });
    bindOnboarding();
  }

  function hideOnboarding() {
    if (onboardingEl) onboardingEl.classList.remove('active');
    bootChat();
  }

  function bindOnboarding() {
    if (!onboardingForm) return;

    // Gender buttons
    const genderBtns = onboardingForm.querySelectorAll('.dw-gender-btn');
    genderBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        genderBtns.forEach(b => b.classList.remove('selected'));
        btn.classList.toggle('selected',
          !btn.classList.contains('selected') || true);
        btn.classList.add('selected');
      });
    });

    onboardingForm.addEventListener('submit', e => {
      e.preventDefault();
      const nameEl = document.getElementById('ob-name');
      const name   = (nameEl && nameEl.value.trim()) || '';
      if (!name) {
        if (nameEl) {
          nameEl.focus();
          nameEl.classList.add('dw-input-error');
          setTimeout(() => nameEl.classList.remove('dw-input-error'), 1600);
        }
        return;
      }
      const ageEl   = document.getElementById('ob-age');
      const age     = (ageEl && ageEl.value.trim()) || '';
      const selected = onboardingForm.querySelector('.dw-gender-btn.selected');
      const gender  = selected ? selected.dataset.value : '';

      saveProfile({ name, age, gender });
      hideOnboarding();
    });
  }

  // ── Mode ──────────────────────────────────────────────────────────
  function applyMode(mode) {
    currentMode = mode;
    localStorage.setItem(MODE_KEY, mode);
    modeButtons.forEach(btn => {
      const active = btn.dataset.mode === mode;
      btn.classList.toggle('active', active);
      btn.setAttribute('aria-pressed', String(active));
    });
  }

  // ── localStorage history ──────────────────────────────────────────
  function saveHistory() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(history.slice(-MAX_HISTORY))); }
    catch (_) {}
  }

  function loadHistory() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed) || parsed.length === 0) return;
      history = parsed;
      hideWelcome();
      history.forEach(entry => {
        if (entry.role === 'user') appendUserBubble(entry.text, false);
        else appendBotBubble(entry, false);
      });
      scrollBottom();
      const lastBot = [...history].reverse().find(e => e.role === 'bot');
      if (lastBot) renderEvidence(lastBot);
    } catch (_) { history = []; }
  }

  // ── Event bindings ────────────────────────────────────────────────
  function bindEvents() {
    chatForm.addEventListener('submit', handleSubmit);

    inputEl.addEventListener('input', () => {
      autoResize();
      sendBtn.disabled = inputEl.value.trim().length === 0;
    });

    inputEl.addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (!sendBtn.disabled && !isLoading) chatForm.dispatchEvent(new Event('submit'));
      }
    });

    if (clearBtn) clearBtn.addEventListener('click', clearHistory);

    modeButtons.forEach(btn => btn.addEventListener('click', () => applyMode(btn.dataset.mode)));

    starterChips.forEach(chip => {
      chip.addEventListener('click', () => {
        inputEl.value = chip.textContent.trim();
        sendBtn.disabled = false;
        autoResize();
        chatForm.dispatchEvent(new Event('submit'));
      });
    });

    if (evidenceToggle) evidenceToggle.addEventListener('click', toggleEvidence);
    if (evidenceClose)  evidenceClose.addEventListener('click',  closeEvidence);
  }

  // ── Auto-resize ───────────────────────────────────────────────────
  function autoResize() {
    inputEl.style.height = 'auto';
    inputEl.style.height = Math.min(inputEl.scrollHeight, 160) + 'px';
  }

  // ── Evidence panel ────────────────────────────────────────────────
  function toggleEvidence() {
    evidenceEl.classList.contains('open') ? closeEvidence() : openEvidence();
  }

  function openEvidence() {
    if (!evidenceEl) return;
    evidenceEl.classList.add('open');
    evidenceEl.setAttribute('aria-hidden', 'false');
    if (evidenceToggle) evidenceToggle.setAttribute('aria-expanded', 'true');
  }

  function closeEvidence() {
    if (!evidenceEl) return;
    evidenceEl.classList.remove('open');
    evidenceEl.setAttribute('aria-hidden', 'true');
    if (evidenceToggle) evidenceToggle.setAttribute('aria-expanded', 'false');
  }

  function resetEvidence() {
    if (!evidenceBody) return;
    evidenceBody.innerHTML = '<p class="dw-evidence-empty">Sources retrieved for the current answer will appear here.</p>';
  }

  function renderEvidence(data) {
    if (!evidenceBody) return;
    evidenceBody.innerHTML = '';

    if (data.safety_note) {
      const note = document.createElement('div');
      note.className = 'dw-safety-note';
      note.innerHTML = `<span class="dw-safety-note__icon" aria-hidden="true">⚠️</span><span>${escapeHTML(data.safety_note)}</span>`;
      evidenceBody.appendChild(note);
    }

    const sources = Array.isArray(data.sources) ? data.sources : [];
    if (sources.length > 0) {
      const isRetrieved = data.retrieved !== false;
      const card = document.createElement('div');
      card.className = 'dw-source-card ' + (isRetrieved ? 'dw-source-card--retrieved' : 'dw-source-card--general');
      const items = sources.map(s =>
        `<div class="dw-source-item">
          <svg class="dw-source-item__icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          ${escapeHTML(s)}
        </div>`
      ).join('');
      card.innerHTML = `
        <div class="dw-source-card__head">${isRetrieved ? '✓ From knowledge base' : '◯ General knowledge'}</div>
        <div class="dw-source-card__body">${items}</div>`;
      evidenceBody.appendChild(card);
    } else {
      resetEvidence();
      return;
    }

    // Follow-ups chip bar
    const followups = Array.isArray(data.followups) ? data.followups : [];
    if (followups.length > 0 && followupsEl) {
      followupsEl.innerHTML = '';
      const label = document.createElement('div');
      label.className = 'dw-followups__label';
      label.textContent = 'Continue exploring';
      followupsEl.appendChild(label);
      followups.forEach(q => {
        const chip = document.createElement('button');
        chip.type = 'button';
        chip.className = 'dw-followup-chip';
        chip.textContent = q;
        chip.addEventListener('click', () => {
          inputEl.value = q;
          sendBtn.disabled = false;
          autoResize();
          chatForm.dispatchEvent(new Event('submit'));
        });
        followupsEl.appendChild(chip);
      });
    }
  }

  // ── Clear ─────────────────────────────────────────────────────────
  function clearHistory() {
    if (!confirm('Clear all chat history? This cannot be undone.')) return;
    history = [];
    localStorage.removeItem(STORAGE_KEY);
    feedEl.innerHTML = '';
    if (followupsEl) followupsEl.innerHTML = '';
    resetEvidence();
    closeEvidence();
    showWelcome();
  }

  // ── Welcome ───────────────────────────────────────────────────────
  function hideWelcome() {
    if (welcomeEl) welcomeEl.style.display = 'none';
  }

  function showWelcome() {
    if (welcomeEl) {
      welcomeEl.style.display = '';
      feedEl.appendChild(welcomeEl);
    }
  }

  function setLoading(val) {
    isLoading       = val;
    sendBtn.disabled = val;
    sendBtn.classList.toggle('loading', val);
  }

  // ── Streaming submit ──────────────────────────────────────────────
  async function handleSubmit(e) {
    e.preventDefault();
    const question = inputEl.value.trim();
    if (!question || isLoading) return;

    hideWelcome();
    if (followupsEl) followupsEl.innerHTML = '';
    appendUserBubble(question, true);
    inputEl.value = '';
    inputEl.style.height = 'auto';
    setLoading(true);

    // Create a live streaming bubble (with typing indicator until first token)
    let { container: bubbleContainer, textEl, typingEl } = createStreamingBubble();
    let accumulatedText = '';

    try {
      const response = await fetch('/ask', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          question,
          mode:    currentMode,
          profile: getProfile() || {},
        }),
      });

      if (!response.ok || !response.body) {
        throw new Error('Server returned ' + response.status);
      }

      const reader  = response.body.getReader();
      const decoder = new TextDecoder();
      let   buffer  = '';
      let   done    = false;

      while (!done) {
        const { done: streamDone, value } = await reader.read();
        if (streamDone) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop(); // keep incomplete trailing chunk

        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith('data: ')) continue;
          let event;
          try { event = JSON.parse(line.slice(6)); } catch { continue; }

          if (event.error) {
            throw new Error(event.error);
          }

          if (event.token) {
            // Remove typing indicator the moment the first token arrives
            if (typingEl) { typingEl.remove(); typingEl = null; }
            accumulatedText += event.token;
            // Plain text during streaming for performance
            textEl.textContent = accumulatedText;
            scrollBottom();
          }

          if (event.done) {
            done = true;
            // Finalize bubble with markdown
            const bubble = bubbleContainer.querySelector('.dw-msg__bubble');
            if (bubble) {
              bubble.innerHTML = renderMarkdownLite(event.answer || accumulatedText);
            }
            const isEmergency = !!event.emergency;
            if (isEmergency) bubbleContainer.classList.add('dw-msg--emergency');

            const entry = { role: 'bot', ...event };
            history.push(entry);
            saveHistory();
            renderEvidence(event);
            openEvidence();
            scrollBottom();
          }
        }
      }
    } catch (err) {
      bubbleContainer.remove();
      const errEntry = {
        role:        'bot',
        answer:      err.message || 'Something went wrong. Please try again.',
        sources:     [], followups: [], retrieved: false,
        safety_note: 'For educational purposes only.',
      };
      appendBotBubble(errEntry, true);
    } finally {
      setLoading(false);
    }
  }

  // ── Bubble helpers ────────────────────────────────────────────────
  /** Creates a bot bubble with a typing indicator + text node for live streaming into */
  function createStreamingBubble() {
    const container = document.createElement('div');
    container.className = 'dw-msg dw-msg--bot';
    container.setAttribute('role', 'listitem');

    const avatar = document.createElement('div');
    avatar.className = 'dw-msg__avatar';
    avatar.setAttribute('aria-hidden', 'true');
    avatar.textContent = 'DW';

    const bubble = document.createElement('div');
    bubble.className = 'dw-msg__bubble dw-msg__bubble--streaming';

    // Typing indicator — shown while waiting for first token, then removed
    const typingEl = document.createElement('div');
    typingEl.className = 'dw-typing';
    typingEl.innerHTML = '<span></span><span></span><span></span>';
    bubble.appendChild(typingEl);

    const textEl = document.createTextNode('');
    bubble.appendChild(textEl);

    container.appendChild(avatar);
    container.appendChild(bubble);
    feedEl.appendChild(container);
    scrollBottom();
    return { container, textEl, typingEl };
  }

  function appendUserBubble(text, save) {
    const div = document.createElement('div');
    div.className = 'dw-msg dw-msg--user';
    div.setAttribute('role', 'listitem');
    div.innerHTML = `
      <div class="dw-msg__avatar" aria-hidden="true">You</div>
      <div class="dw-msg__bubble">${escapeHTML(text)}</div>`;
    feedEl.appendChild(div);
    scrollBottom();
    if (save) { history.push({ role: 'user', text }); saveHistory(); }
  }

  /** Used when replaying history (not streaming) */
  function appendBotBubble(entry, save) {
    const div = document.createElement('div');
    div.className = 'dw-msg dw-msg--bot' + (entry.emergency ? ' dw-msg--emergency' : '');
    div.setAttribute('role', 'listitem');
    div.innerHTML = `
      <div class="dw-msg__avatar" aria-hidden="true">DW</div>
      <div class="dw-msg__bubble">${renderMarkdownLite(entry.answer || entry.text || '')}</div>`;
    feedEl.appendChild(div);
    scrollBottom();
    if (save) { history.push({ role: 'bot', ...entry }); saveHistory(); }
  }

  function scrollBottom() {
    if (feedEl) feedEl.scrollTop = feedEl.scrollHeight;
  }

  // ── Markdown-lite renderer (XSS-safe) ────────────────────────────
  function renderMarkdownLite(text) {
    let s = escapeHTML(text);
    s = s.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    s = s.replace(/__(.*?)__/g, '<strong>$1</strong>');
    s = s.replace(/\*(.*?)\*/g, '<em>$1</em>');
    s = s.replace(/`([^`]+)`/g, '<code>$1</code>');
    s = s.replace(/^[-*]\s+(.+)$/gm, '<li>$1</li>');
    s = s.replace(/(<li>[\s\S]*?<\/li>)/g, '<ul>$1</ul>');
    s = s.replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>');
    s = s.replace(/\n{2,}/g, '</p><p>');
    s = s.replace(/\n/g, '<br/>');
    return '<p>' + s + '</p>';
  }

  // ── HTML escape ───────────────────────────────────────────────────
  function escapeHTML(str) {
    if (str == null) return '';
    return String(str)
      .replace(/&/g,  '&amp;')
      .replace(/</g,  '&lt;')
      .replace(/>/g,  '&gt;')
      .replace(/"/g,  '&quot;')
      .replace(/'/g,  '&#039;');
  }

  // ── Boot ──────────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', init);

})();
