(() => {
  const THEME_PARAM = '__theme';
  const THEME_STORAGE_KEY = 'nutrichat-theme';

  function getCurrentTheme() {
    const url = new URL(window.location.href);
    const themeFromUrl = url.searchParams.get(THEME_PARAM);
    if (themeFromUrl === 'dark' || themeFromUrl === 'light') return themeFromUrl;

    const storedTheme = window.localStorage?.getItem(THEME_STORAGE_KEY);
    if (storedTheme === 'dark' || storedTheme === 'light') return storedTheme;

    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    return prefersDark ? 'dark' : 'light';
  }

  function applyTheme(theme) {
    const normalized = theme === 'dark' ? 'dark' : 'light';
    const isDark = normalized === 'dark';

    document.documentElement.dataset.ncTheme = normalized;
    document.documentElement.classList.toggle('nc-theme-dark', isDark);
    document.documentElement.classList.toggle('nc-theme-light', !isDark);

    if (document.body) {
      document.body.dataset.ncTheme = normalized;
      document.body.classList.toggle('nc-theme-dark', isDark);
      document.body.classList.toggle('nc-theme-light', !isDark);
    }

    document
      .querySelectorAll('#nutrichat-app, #main-container, #nc-app-shell, .nc-shell')
      .forEach((root) => {
        root.dataset.ncTheme = normalized;
        root.classList.toggle('nc-theme-dark', isDark);
        root.classList.toggle('nc-theme-light', !isDark);
      });

    const toggle = document.getElementById('theme-toggle');
    if (toggle) toggle.checked = isDark;
  }

  applyTheme(getCurrentTheme());

  function setFieldValue(rootId, value) {
    const root = document.getElementById(rootId);
    if (!root) return false;

    const checkbox = root.querySelector('input[type="checkbox"]');
    if (checkbox) {
      checkbox.checked = Boolean(value);
      checkbox.dispatchEvent(new Event('input', { bubbles: true }));
      checkbox.dispatchEvent(new Event('change', { bubbles: true }));
      return true;
    }

    const field = root.querySelector('textarea, input');
    if (!field) return false;

    const proto = field instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
    if (setter) setter.call(field, String(value));
    else field.value = String(value);

    field.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: String(value) }));
    field.dispatchEvent(new Event('change', { bubbles: true }));
    return true;
  }

  function clickBackendSubmit() {
    const root = document.getElementById('backend-submit');
    const button = root?.querySelector('button') || root;
    if (!button || button.disabled) return false;
    button.click();
    return true;
  }

  function getVisibleSubmitButton() {
    return document.getElementById('nc-submit');
  }

  function getBackendSubmitButton() {
    const root = document.getElementById('backend-submit');
    return root?.querySelector('button') || root;
  }

  function setSubmitBusy(isBusy) {
    const button = getVisibleSubmitButton();
    if (!button) return;

    button.disabled = isBusy;
    button.setAttribute('aria-disabled', String(isBusy));
    button.classList.toggle('is-loading', isBusy);
  }

  function syncSubmitButtonState() {
    const visibleButton = getVisibleSubmitButton();
    const backendButton = getBackendSubmitButton();
    if (!visibleButton || !backendButton) return;

    if (backendButton.disabled) {
      visibleButton.dataset.backendBusySeen = 'true';
      setSubmitBusy(true);
      return;
    }

    if (visibleButton.dataset.backendBusySeen === 'true') {
      delete visibleButton.dataset.backendBusySeen;
      setSubmitBusy(false);
    }
  }

  function attachSubmitStateObserver() {
    syncSubmitButtonState();

    const backendButton = getBackendSubmitButton();
    if (!backendButton || backendButton.dataset.submitStateBound === 'true') return;
    backendButton.dataset.submitStateBound = 'true';

    const observer = new MutationObserver(syncSubmitButtonState);
    observer.observe(backendButton, {
      attributes: true,
      attributeFilter: ['disabled', 'aria-disabled', 'class'],
    });
  }

  function submitQuestion() {
    const visibleButton = getVisibleSubmitButton();
    if (visibleButton?.disabled) return;

    syncAllToBackend();
    setSubmitBusy(true);

    if (!clickBackendSubmit()) {
      setSubmitBusy(false);
    }
  }

  function syncAdvancedValue(input) {
    if (!input) return;

    const card = input.closest('.nc-control-card') || input.closest('label');
    const output = card?.querySelector(`output[for="${input.id}"]`) || card?.querySelector('output');
    if (output) output.textContent = input.value;

    if (input.type === 'range') {
      const min = Number.parseFloat(input.min || '0');
      const max = Number.parseFloat(input.max || '100');
      const value = Number.parseFloat(input.value || String(min));
      const progress = max > min ? ((value - min) / (max - min)) * 100 : 0;
      input.style.setProperty('--nc-range-progress', `${Math.max(0, Math.min(100, progress))}%`);
    }
  }

  function getSelectedModeValue() {
    const advancedMode = document.getElementById('nc-advanced-mode');
    if (advancedMode?.value) return advancedMode.value;

    const active = document.querySelector('.nc-mode-option.active');
    return active?.dataset.value || 'Hybrid RRF, no reranker';
  }

  function setAdvancedModeValue(value) {
    const advancedMode = document.getElementById('nc-advanced-mode');
    if (advancedMode && value) advancedMode.value = value;
    syncAdvancedModePickerFromValue(value);
  }

  function syncModePickerFromValue(value) {
    const current = document.getElementById('nc-mode-current');
    document.querySelectorAll('.nc-mode-option').forEach((item) => {
      const isActive = item.dataset.value === value;
      item.classList.toggle('active', isActive);
      item.setAttribute('aria-selected', isActive ? 'true' : 'false');
      if (isActive && current) current.textContent = item.dataset.label || item.textContent.trim();
    });
  }

  function syncAdvancedModePickerFromValue(value) {
    if (!value) return;

    const current = document.getElementById('nc-advanced-mode-current');
    const nativeOption = Array.from(document.querySelectorAll('#nc-advanced-mode option')).find(
      (option) => option.value === value
    );
    let selectedLabel = nativeOption?.textContent?.trim() || value;

    document.querySelectorAll('.nc-advanced-mode-option').forEach((item) => {
      const isActive = item.dataset.value === value;
      item.classList.toggle('active', isActive);
      item.setAttribute('aria-selected', isActive ? 'true' : 'false');
      if (isActive) selectedLabel = item.dataset.label || item.textContent.trim();
    });

    if (current) current.textContent = selectedLabel;
  }

  function syncAllToBackend() {
    const question = document.getElementById('nc-question')?.value || '';
    const system = getSelectedModeValue();
    const temperature = document.getElementById('nc-temperature')?.value || '0.2';
    const maxNewTokens = document.getElementById('nc-max-new-tokens')?.value || '512';
    const finalK = document.getElementById('nc-final-k')?.value || '3';
    const candidateK = document.getElementById('nc-candidate-k')?.value || '10';
    const streaming = Boolean(document.getElementById('nc-streaming')?.checked);

    setFieldValue('backend-query', question);
    setFieldValue('backend-system-choice', system);
    setFieldValue('backend-temperature', temperature);
    setFieldValue('backend-max-new-tokens', maxNewTokens);
    setFieldValue('backend-final-k', finalK);
    setFieldValue('backend-candidate-k', candidateK);
    setFieldValue('backend-use-streaming', streaming);
  }

  function updateCounter() {
    const question = document.getElementById('nc-question');
    const counter = document.getElementById('question-counter');
    if (!question || !counter) return;
    counter.textContent = `${question.value.length} / 1000`;
  }

  function attachThemeToggle() {
    const toggle = document.getElementById('theme-toggle');
    if (!toggle) return;

    applyTheme(getCurrentTheme());

    if (toggle.dataset.themeBound === 'true') return;
    toggle.dataset.themeBound = 'true';

    toggle.addEventListener('change', () => {
      const newTheme = toggle.checked ? 'dark' : 'light';
      window.localStorage?.setItem(THEME_STORAGE_KEY, newTheme);
      applyTheme(newTheme);

      // Keep the same Gradio behavior as your previous app: Gradio reads
      // ?__theme=dark/light on page load, so reload with that parameter.
      const url = new URL(window.location.href);
      url.searchParams.set(THEME_PARAM, newTheme);
      window.location.replace(url.toString());
    });
  }

  function attachModePicker(shell) {
    const button = document.getElementById('nc-mode-button');
    const menu = document.getElementById('nc-mode-menu');
    const current = document.getElementById('nc-mode-current');
    if (!button || !menu || !current) return;

    function closeMenu() {
      menu.hidden = true;
      button.setAttribute('aria-expanded', 'false');
    }

    function openMenu() {
      menu.hidden = false;
      button.setAttribute('aria-expanded', 'true');
    }

    button.addEventListener('click', (event) => {
      event.stopPropagation();
      if (menu.hidden) openMenu();
      else closeMenu();
    });

    menu.querySelectorAll('.nc-mode-option').forEach((option) => {
      option.addEventListener('click', () => {
        menu.querySelectorAll('.nc-mode-option').forEach((item) => {
          item.classList.remove('active');
          item.setAttribute('aria-selected', 'false');
        });
        option.classList.add('active');
        option.setAttribute('aria-selected', 'true');
        current.textContent = option.dataset.label || option.textContent.trim();
        const selectedValue = option.dataset.value || 'Hybrid RRF, no reranker';
        setAdvancedModeValue(selectedValue);
        setFieldValue('backend-system-choice', selectedValue);
        closeMenu();
      });
    });

    document.addEventListener('click', (event) => {
      if (!shell.contains(event.target)) return;
      if (!button.contains(event.target) && !menu.contains(event.target)) closeMenu();
    });

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') closeMenu();
    });
  }

  function attachAdvancedModeSelect() {
    const advancedMode = document.getElementById('nc-advanced-mode');
    if (!advancedMode || advancedMode.dataset.modeBound === 'true') return;
    advancedMode.dataset.modeBound = 'true';

    advancedMode.addEventListener('change', () => {
      syncAdvancedModePickerFromValue(advancedMode.value);
      syncModePickerFromValue(advancedMode.value);
      setFieldValue('backend-system-choice', advancedMode.value);
      syncAllToBackend();
    });

    syncAdvancedModePickerFromValue(advancedMode.value);
  }

  function attachAdvancedModePicker(shell) {
    const button = document.getElementById('nc-advanced-mode-button');
    const menu = document.getElementById('nc-advanced-mode-menu');
    if (!button || !menu || button.dataset.modePickerBound === 'true') return;
    button.dataset.modePickerBound = 'true';

    function closeMenu() {
      menu.hidden = true;
      button.setAttribute('aria-expanded', 'false');
    }

    function openMenu() {
      menu.hidden = false;
      button.setAttribute('aria-expanded', 'true');
    }

    button.addEventListener('click', (event) => {
      event.stopPropagation();
      if (menu.hidden) openMenu();
      else closeMenu();
    });

    menu.querySelectorAll('.nc-advanced-mode-option').forEach((option) => {
      option.addEventListener('click', () => {
        const selectedValue = option.dataset.value || 'Hybrid RRF, no reranker';
        setAdvancedModeValue(selectedValue);
        syncModePickerFromValue(selectedValue);
        setFieldValue('backend-system-choice', selectedValue);
        syncAllToBackend();
        closeMenu();
      });
    });

    document.addEventListener('click', (event) => {
      if (!shell.contains(event.target)) return;
      if (!button.contains(event.target) && !menu.contains(event.target)) closeMenu();
    });

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') closeMenu();
    });
  }

  function resetAdvancedDefaults() {
    const defaults = {
      mode: 'Hybrid RRF, no reranker',
      temperature: '0.2',
      maxNewTokens: '512',
      finalK: '3',
      candidateK: '10',
      streaming: true,
    };

    setAdvancedModeValue(defaults.mode);
    syncModePickerFromValue(defaults.mode);

    const temperature = document.getElementById('nc-temperature');
    const maxNewTokens = document.getElementById('nc-max-new-tokens');
    const finalK = document.getElementById('nc-final-k');
    const candidateK = document.getElementById('nc-candidate-k');
    const streaming = document.getElementById('nc-streaming');

    if (temperature) temperature.value = defaults.temperature;
    if (maxNewTokens) maxNewTokens.value = defaults.maxNewTokens;
    if (finalK) finalK.value = defaults.finalK;
    if (candidateK) candidateK.value = defaults.candidateK;
    if (streaming) streaming.checked = defaults.streaming;

    [temperature, maxNewTokens, finalK, candidateK].forEach(syncAdvancedValue);
    syncAllToBackend();
  }

  function attachAdvancedReset() {
    const resetButton = document.getElementById('nc-reset-defaults');
    if (!resetButton || resetButton.dataset.resetBound === 'true') return;
    resetButton.dataset.resetBound = 'true';

    resetButton.addEventListener('click', (event) => {
      event.preventDefault();
      event.stopPropagation();
      resetAdvancedDefaults();
    });
  }

  function setActiveAppTab(tabName) {
    const selected = tabName || 'ask';

    document.querySelectorAll('.nc-app-tab[data-app-tab]').forEach((tab) => {
      const isActive = tab.dataset.appTab === selected;
      tab.classList.toggle('active', isActive);
      tab.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });

    document.querySelectorAll('.nc-tab-panel[data-tab-panel]').forEach((panel) => {
      const isActive = panel.dataset.tabPanel === selected;
      panel.hidden = !isActive;
      panel.classList.toggle('active', isActive);
    });

    document.querySelectorAll('.nc-ask-results-panel').forEach((askOutputs) => {
      askOutputs.hidden = selected !== 'ask';
      askOutputs.classList.toggle('active', selected === 'ask');
    });
  }

  function attachAppTabs(shell) {
    if (!shell) return;

    const activeTab = shell.querySelector('.nc-app-tab.active')?.dataset.appTab || 'ask';
    setActiveAppTab(activeTab);

    shell.querySelectorAll('.nc-app-tab[data-app-tab]').forEach((tab) => {
      if (tab.dataset.appTabBound === 'true') return;
      tab.dataset.appTabBound = 'true';
      tab.addEventListener('click', () => {
        setActiveAppTab(tab.dataset.appTab || 'ask');
      });
    });
  }

  function attachExampleTabs() {
    document.querySelectorAll('.nc-example-tabs [data-tab]').forEach((tab) => {
      if (tab.dataset.exampleTabBound === 'true') return;
      tab.dataset.exampleTabBound = 'true';

      tab.addEventListener('click', () => {
        const target = tab.dataset.tab;
        document.querySelectorAll('.nc-example-tabs [data-tab]').forEach((item) => {
          const isActive = item === tab;
          item.classList.toggle('active', isActive);
          item.setAttribute('aria-selected', isActive ? 'true' : 'false');
        });
        document.querySelectorAll('.nc-example-grid[data-panel]').forEach((panel) => {
          panel.hidden = panel.dataset.panel !== target;
        });
      });
    });
  }

  function attachExampleCards() {
    document.querySelectorAll('.nc-example-card[data-question]').forEach((card) => {
      if (card.dataset.exampleBound === 'true') return;
      card.dataset.exampleBound = 'true';

      card.addEventListener('click', () => {
        const value = card.getAttribute('data-question') || '';
        const questionBox = document.getElementById('nc-question');
        if (!questionBox) return;
        questionBox.value = value;
        questionBox.focus();
        updateCounter();
        setFieldValue('backend-query', value);
      });
    });
  }

  function copyTextFallback(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.setAttribute('readonly', '');
    textArea.style.position = 'fixed';
    textArea.style.opacity = '0';
    document.body.appendChild(textArea);
    textArea.select();

    try {
      return document.execCommand('copy');
    } catch (_error) {
      return false;
    } finally {
      textArea.remove();
    }
  }

  function attachCitationCopy() {
    document.querySelectorAll('[data-copy-citation]').forEach((button) => {
      if (button.dataset.copyBound === 'true') return;
      button.dataset.copyBound = 'true';

      button.addEventListener('click', async () => {
        const citation = document.querySelector('.nc-citation-box code')?.textContent?.trim();
        if (!citation) return;

        let copied = false;
        try {
          if (navigator.clipboard?.writeText) {
            await navigator.clipboard.writeText(citation);
            copied = true;
          } else {
            copied = copyTextFallback(citation);
          }
        } catch (_error) {
          copied = copyTextFallback(citation);
        }

        if (!copied) return;
        const label = button.querySelector('[data-copy-label]');
        if (label) label.textContent = 'Copied!';
        button.classList.add('is-copied');
        window.clearTimeout(button.copyResetTimer);
        button.copyResetTimer = window.setTimeout(() => {
          if (label) label.textContent = 'Copy Citation';
          button.classList.remove('is-copied');
        }, 1800);
      });
    });
  }

  function attachNutriChatUi() {
    const shell = document.querySelector('.nc-shell');
    attachThemeToggle();
    attachSubmitStateObserver();
    attachAppTabs(shell);
    attachCitationCopy();
    if (!shell || shell.dataset.bound === 'true') return;
    shell.dataset.bound = 'true';

    const question = document.getElementById('nc-question');
    question?.addEventListener('input', () => {
      updateCounter();
      setFieldValue('backend-query', question.value);
    });
    question?.addEventListener('keydown', (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
        event.preventDefault();
        submitQuestion();
      }
    });
    updateCounter();

    attachModePicker(shell);
    attachAdvancedModeSelect();
    attachAdvancedModePicker(shell);
    attachAdvancedReset();
    attachExampleTabs();
    attachExampleCards();

    ['nc-temperature', 'nc-max-new-tokens', 'nc-final-k', 'nc-candidate-k'].forEach((id) => {
      const input = document.getElementById(id);
      syncAdvancedValue(input);
      input?.addEventListener('input', () => {
        syncAdvancedValue(input);
        syncAllToBackend();
      });
    });

    document.getElementById('nc-streaming')?.addEventListener('change', syncAllToBackend);

    document.getElementById('nc-submit')?.addEventListener('click', submitQuestion);

    syncAllToBackend();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', attachNutriChatUi);
  } else {
    attachNutriChatUi();
  }

  const observer = new MutationObserver(() => attachNutriChatUi());
  observer.observe(document.documentElement, { childList: true, subtree: true });
})();
