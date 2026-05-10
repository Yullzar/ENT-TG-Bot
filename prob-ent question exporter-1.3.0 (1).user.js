// ==UserScript==
// @name         prob-ent question exporter
// @namespace    https://prob-ent.testcenter.kz/
// @version      1.3.0
// @description  Collects questions, auto-answers variants, and exports results for prob-ent.
// @match        https://prob-ent.testcenter.kz/*
// @grant        GM_addStyle
// @grant        GM_registerMenuCommand
// @grant        GM_getValue
// @grant        GM_setValue
// @grant        GM_deleteValue
// ==/UserScript==

(function () {
  'use strict';
  // const importedStore =  ;
  // GM_setValue('prob-ent-exporter-data-v2', JSON.stringify(importedStore.store));
  // alert('База импортирована!');
  const SELECTORS = {
    questionButtons: '.quest-numbers .num-item',
    questionNumber: '.quest-info-parent .ml-auto',
    sectionTitle: '.quest-info-parent .p-n span',
    questionRoot: '#currentQuest .quest-text',
    answerBox: '#currentQuest .answer-box',
    answerLabels: '#currentQuest .answer-box label',
  };

  const STORE_KEY = 'prob-ent-exporter-data-v2';
  const LETTERS = ['A', 'B', 'C', 'D'];
  const SKIP_RANGE = { start: 31, end: 40 };
  const MAX_COLLECT_QUESTION = 30;
  const AUTOPILOT_CYCLES = 24; // Количество циклов для полного автопилота
  const IIN = 666666666666;
  /*
  Вссемирная история - Основы права : 2 DONE
  Химия и Физика : 5 DONE
  Био Гео : 7 DONE
  Англ Всемирка : 12 - DONE
  Кказахский язык и литература : 15 DONE
  Русский язык русская литераатураа : 16 DONE
  Мат ИНФО : 17 - DONE
  */
  const SUBJECT_INDEX = '15';

  const state = {
    running: false,
    panel: null,
    status: null,
    buttons: {},
  };

  const autopilotConfig = {
    mode: 'all', // 'all' - все предметы, 'last-2-profile' - только 2 профильных предмета
    // В режиме 'last-2-profile' пропускаются первые 3 предмета:
    // Математическая грамотность, История Казахстана, Грамотность чтения
  };

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  function normalizeText(value) {
    return (value || '').replace(/\s+/g, ' ').trim();
  }

  function normalizeSectionTitle(value) {
    return normalizeText(value).replace(/^(Раздел|Бөлім)\s*:\s*/i, '').trim();
  }

  function sanitizeFilePart(value) {
    return normalizeSectionTitle(value)
      .replace(/[<>:"/\\|?*]+/g, '')
      .replace(/\s+/g, '_')
      .replace(/_+/g, '_')
      .replace(/^_+|_+$/g, '')
      .slice(0, 80);
  }

  function createEmptyStore() {
    return {
      version: 2,
      subjects: {},
      pendingRun: null,
      updatedAt: null,
    };
  }

  function loadStore() {
    const raw = GM_getValue(STORE_KEY, '');
    if (!raw) {
      return createEmptyStore();
    }

    try {
      const parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== 'object') {
        return createEmptyStore();
      }
      return {
        ...createEmptyStore(),
        ...parsed,
        subjects: parsed.subjects || {},
      };
    } catch (error) {
      console.warn('[prob-ent exporter] Failed to parse stored data', error);
      return createEmptyStore();
    }
  }

  function saveStore(store) {
    const payload = {
      ...store,
      updatedAt: new Date().toISOString(),
    };
    GM_setValue(STORE_KEY, JSON.stringify(payload));
  }

  function resetStore() {
    GM_deleteValue(STORE_KEY);
  }

  function hashString(value) {
    let hash = 0x811c9dc5;
    const text = value || '';

    for (let i = 0; i < text.length; i += 1) {
      hash ^= text.charCodeAt(i);
      hash = Math.imul(hash, 0x01000193);
    }

    return `00000000${(hash >>> 0).toString(16)}`.slice(-8);
  }

  function getQuestionIndex() {
    const node = document.querySelector(SELECTORS.questionNumber);
    const value = normalizeText(node?.textContent || '');
    const match = value.match(/\d+/);
    return match ? Number(match[0]) : null;
  }

  function getSectionTitle() {
    return normalizeText(document.querySelector(SELECTORS.sectionTitle)?.textContent || '');
  }

  function getSectionName() {
    return normalizeSectionTitle(getSectionTitle());
  }

  function getQuestionRoot() {
    return document.querySelector(SELECTORS.questionRoot);
  }

  function getAnswerBox() {
    return document.querySelector(SELECTORS.answerBox);
  }

  function extractChoiceAnswers(answerBox) {
    return Array.from(answerBox?.querySelectorAll('label') || []).map((label, index) => {
      const letter = normalizeText(label.querySelector('.p-letter')?.textContent || '');
      const answerNode = label.querySelector('.p-answer');
      return {
        index: index + 1,
        letter,
        text: normalizeText(answerNode?.textContent || ''),
        html: answerNode ? answerNode.innerHTML.trim() : '',
      };
    });
  }

  function extractMatchingAnswers(answerBox) {
    return Array.from(answerBox?.querySelectorAll('tr') || [])
      .map((row, index) => {
        const promptCell = row.querySelector('.answer-item') || row.cells?.[0] || null;
        const letter = normalizeText(
          promptCell?.querySelector('.p-letter-match-answer, .p-letter')?.textContent || ''
        );

        const promptNode =
          promptCell?.querySelector('.p-match-answer, .p-answer') ||
          promptCell;

        const controlNode = row.querySelector('.ngx-dropdown-button span, select, input, textarea');

        return {
          index: index + 1,
          letter,
          text: normalizeText(promptNode?.textContent || ''),
          html: promptNode ? promptNode.innerHTML.trim() : '',
          inputPreview: normalizeText(controlNode?.textContent || controlNode?.value || ''),
        };
      })
      .filter((item) => item.text.length > 0 || item.letter.length > 0);
  }

  function detectQuestionType(choiceAnswers, matchingAnswers) {
    if (matchingAnswers.length > 0) {
      return 'matching';
    }

    if (choiceAnswers.length > 0) {
      return 'choice';
    }

    return 'unknown';
  }

  function readQuestionSnapshot() {
    const questionRoot = getQuestionRoot();
    const answerBox = getAnswerBox();
    const choiceAnswers = extractChoiceAnswers(answerBox);
    const matchingAnswers = extractMatchingAnswers(answerBox);
    const questionType = detectQuestionType(choiceAnswers, matchingAnswers);
    const answers = matchingAnswers.length > 0 ? matchingAnswers : choiceAnswers;

    return {
      questionIndex: getQuestionIndex(),
      section: getSectionTitle(),
      questionType,
      questionText: normalizeText(questionRoot?.textContent || ''),
      questionHtml: questionRoot ? questionRoot.innerHTML.trim() : '',
      answerText: normalizeText(answerBox?.textContent || ''),
      answerHtml: answerBox ? answerBox.innerHTML.trim() : '',
      answers,
    };
  }

  function getSnapshotKey(snapshot) {
    return [snapshot.questionText, snapshot.answerText].join('\u241f');
  }

  function getVariantKey(snapshot) {
    return hashString(getSnapshotKey(snapshot));
  }

  function ensureSubjectData(store, subjectKey) {
    if (!store.subjects[subjectKey]) {
      store.subjects[subjectKey] = {
        variants: {},
        variantOrder: [],
      };
    }

    if (!store.subjects[subjectKey].variantOrder) {
      store.subjects[subjectKey].variantOrder = [];
    }

    return store.subjects[subjectKey];
  }

  function ensureVariantData(subjectData, variantKey, snapshot) {
    if (!subjectData.variants[variantKey]) {
      if (!subjectData.variantOrder.includes(variantKey)) {
        subjectData.variantOrder.push(variantKey);
      }
      subjectData.variants[variantKey] = {
        key: variantKey,
        firstQuestionText: snapshot.questionText,
        firstQuestionKey: getSnapshotKey(snapshot),
        questions: {},
        seenCount: 0,
        lastLetter: null,
        createdAt: new Date().toISOString(),
      };
    }

    const variantData = subjectData.variants[variantKey];
    if (!Number.isFinite(variantData.seenCount)) {
      if (variantData.letter) {
        variantData.seenCount = 1;
        variantData.lastLetter = variantData.letter;
      } else {
        variantData.seenCount = 0;
      }
    }

    return variantData;
  }

  function shouldSkipQuestionIndex(index) {
    return index >= SKIP_RANGE.start && index <= SKIP_RANGE.end;
  }

  function shouldStoreQuestion(snapshot) {
    if (!snapshot || !Number.isFinite(snapshot.questionIndex)) {
      return false;
    }

    if (shouldSkipQuestionIndex(snapshot.questionIndex)) {
      return false;
    }

    return true;
  }

  function storeSnapshot(store, subjectKey, variantKey, letter, snapshot) {
    if (!shouldStoreQuestion(snapshot)) {
      return;
    }

    const subjectData = ensureSubjectData(store, subjectKey);
    const variantData = ensureVariantData(subjectData, variantKey, snapshot);
    const existing = variantData.questions[snapshot.questionIndex] || {};

    variantData.questions[snapshot.questionIndex] = {
      questionIndex: snapshot.questionIndex,
      questionType: snapshot.questionType,
      questionText: snapshot.questionText,
      questionHtml: snapshot.questionHtml,
      answerText: snapshot.answerText,
      answerHtml: snapshot.answerHtml,
      answers: snapshot.answers,
      selectedLetter: letter,
      result: existing.result ?? null,
      correctLetter: existing.correctLetter ?? null,
      updatedAt: new Date().toISOString(),
    };
  }

  function getQuestionButtons() {
    const seen = new Set();
    return Array.from(document.querySelectorAll(SELECTORS.questionButtons))
      .map((node) => {
        const id = Number(node.id || normalizeText(node.textContent || ''));
        return Number.isFinite(id) ? { id, node } : null;
      })
      .filter(Boolean)
      .filter((item) => {
        if (seen.has(item.id)) {
          return false;
        }
        seen.add(item.id);
        return true;
      })
      .sort((left, right) => left.id - right.id);
  }

  function resolveQuestionNode(id) {
    let currentNode = document.getElementById(String(id));
    if (!currentNode) {
      currentNode = Array.from(document.querySelectorAll(SELECTORS.questionButtons))
        .find((node) => {
          const nid = Number(node.id || normalizeText(node.textContent || ''));
          return Number.isFinite(nid) && nid === id;
        }) || null;
    }

    return currentNode;
  }

  function findNextSubjectButton() {
    return Array.from(document.querySelectorAll('button'))
      .find((button) => normalizeText(button.textContent || '').startsWith('Следующий предмет')) || null;
  }

  function selectAnswerLetter(letter) {
    const normalizedLetter = normalizeText(letter).toUpperCase();
    const labels = Array.from(document.querySelectorAll(SELECTORS.answerLabels));
    const target = labels.find((label) => {
      const labelLetter = normalizeText(label.querySelector('.p-letter')?.textContent || '').toUpperCase();
      return labelLetter.startsWith(normalizedLetter);
    });

    if (!target) {
      return false;
    }

    const input = target.querySelector('input');
    if (input && input.checked) {
      return true;
    }

    target.click();
    return true;
  }

  function isQuestPage() {
    return Boolean(document.querySelector(SELECTORS.questionRoot) && document.querySelector(SELECTORS.answerBox));
  }

  function isResultsPage() {
    return Boolean(document.querySelector('app-answersmap') || document.querySelector('#results'));
  }

  function clickNode(node) {
    node.scrollIntoView({ block: 'center', inline: 'center' });
    node.click();
  }

  async function waitForQuestion(targetIndex, previousKey, timeoutMs = 15000) {
    const startedAt = Date.now();

    while (Date.now() - startedAt < timeoutMs) {
      const snapshot = readQuestionSnapshot();
      const currentKey = getSnapshotKey(snapshot);
      if (
        snapshot.questionIndex === targetIndex &&
        snapshot.questionText.length > 0 &&
        snapshot.answerHtml.length > 0 &&
        currentKey !== previousKey
      ) {
        return snapshot;
      }
      await sleep(120);
    }

    throw new Error(`Timeout while waiting for question ${targetIndex}`);
  }

  function downloadJson(data, fileName) {
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: 'application/json;charset=utf-8',
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = fileName;
    anchor.rel = 'noopener';
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function setStatus(text) {
    if (state.status) {
      state.status.textContent = text;
    }
  }

  function setRunning(running) {
    state.running = running;
    Object.values(state.buttons).forEach((button) => {
      button.disabled = running;
    });
  }

  async function exportQuestions() {
    if (state.running) {
      return;
    }

    const buttons = getQuestionButtons().filter((item) => item.id <= MAX_COLLECT_QUESTION);
    if (!buttons.length) {
      setStatus('Не нашел кнопки вопросов на странице.');
      return;
    }

    setRunning(true);
    setStatus(`Найдено вопросов: ${buttons.length}`);

    const originalSnapshot = readQuestionSnapshot();
    const collected = [];
    let previousKey = getSnapshotKey(originalSnapshot);

    try {
      if (
        originalSnapshot.questionIndex === buttons[0]?.id &&
        originalSnapshot.questionText.length > 0 &&
        shouldStoreQuestion(originalSnapshot)
      ) {
        collected.push(originalSnapshot);
      }

      const startIndex = collected.length > 0 ? 1 : 0;

      for (let index = startIndex; index < buttons.length; index += 1) {
        const { id } = buttons[index];
        setStatus(`Вопрос ${index + 1} из ${buttons.length}`);

        // Resolve the current button element at click-time. Some SPA frameworks
        // may reorder or recreate the button elements, so using the original
        // node reference can click the wrong item. Find by id first, then
        // fallback to scanning buttons by text/id.
        const currentNode = resolveQuestionNode(id);

        if (!currentNode) {
          setStatus(`Не нашёл кнопку для вопроса ${id}, пропускаю`);
          // still wait a bit to avoid tight loop
          await sleep(150);
          continue;
        }

        clickNode(currentNode);
        const snapshot = await waitForQuestion(id, previousKey);
        previousKey = getSnapshotKey(snapshot);

        if (shouldStoreQuestion(snapshot)) {
          collected.push(snapshot);
        }

        await sleep(150);
      }

      if (originalSnapshot.questionIndex && originalSnapshot.questionIndex !== collected[0]?.questionIndex) {
        const restore = buttons.find((item) => item.id === originalSnapshot.questionIndex);
        if (restore) {
          clickNode(restore.node);
          await waitForQuestion(originalSnapshot.questionIndex).catch(() => undefined);
        }
      }

      const payload = {
        source: location.href,
        exportedAt: new Date().toISOString(),
        total: collected.length,
        questions: collected,
      };

      const subjectFromSnapshot = collected[0]?.section || originalSnapshot.section || '';
      const subjectPart = sanitizeFilePart(subjectFromSnapshot) || 'unknown_subject';
      const fileName = `prob-ent-${subjectPart}-${Date.now()}.json`;
      downloadJson(payload, fileName);
      setStatus(`Готово: сохранено ${collected.length} вопросов.`);
    } catch (error) {
      console.error('[prob-ent exporter]', error);
      setStatus(`Ошибка: ${error.message}`);
    } finally {
      setRunning(false);
    }
  }

  async function collectSubject(store, subjectKey) {
    const buttons = getQuestionButtons().filter((item) => item.id <= MAX_COLLECT_QUESTION);
    if (!buttons.length) {
      setStatus(`Нет вопросов для предмета: ${subjectKey}`);
      return null;
    }

    let previousKey = '';
    let snapshot = readQuestionSnapshot();

    if (snapshot.questionIndex !== buttons[0]?.id) {
      const firstNode = resolveQuestionNode(buttons[0]?.id);
      if (firstNode) {
        clickNode(firstNode);
        snapshot = await waitForQuestion(buttons[0].id, previousKey);
      }
    }

    if (!snapshot) return null;

    previousKey = getSnapshotKey(snapshot);
    const variantKey = getVariantKey(snapshot);
    const subjectData = ensureSubjectData(store, subjectKey);
    const variantData = ensureVariantData(subjectData, variantKey, snapshot);
    const runIndex = Number.isFinite(variantData.seenCount) ? variantData.seenCount : 0;
    const letter = LETTERS[runIndex % LETTERS.length] || LETTERS[0];

    let startIndex = 0;
    if (snapshot.questionIndex === buttons[0]?.id && shouldStoreQuestion(snapshot)) {
      if (!selectAnswerLetter(letter)) {
        setStatus(`Не нашёл вариант ${letter} для вопроса ${snapshot.questionIndex}`);
      }
      storeSnapshot(store, subjectKey, variantKey, letter, snapshot);
      startIndex = 1;
    }

    for (let index = startIndex; index < buttons.length; index += 1) {
      const { id } = buttons[index];
      setStatus(`(${subjectKey}) Вопрос ${id} из ${buttons.length}`);

      const currentNode = resolveQuestionNode(id);
      if (!currentNode) {
        setStatus(`Не нашёл кнопку для вопроса ${id}, пропускаю`);
        await sleep(150);
        continue;
      }

      clickNode(currentNode);
      snapshot = await waitForQuestion(id, previousKey);
      previousKey = getSnapshotKey(snapshot);

      if (shouldStoreQuestion(snapshot)) {
        if (!selectAnswerLetter(letter)) {
          setStatus(`Не нашёл вариант ${letter} для вопроса ${id}`);
        }
        storeSnapshot(store, subjectKey, variantKey, letter, snapshot);
      }

      await sleep(120);
    }

    variantData.seenCount = runIndex + 1;
    variantData.lastLetter = letter;
    variantData.lastSeenAt = new Date().toISOString();

    return { variantKey, letter };
  }

  async function goToNextSubject(currentSubject) {
    const nextButton = findNextSubjectButton();
    if (!nextButton) {
      return false;
    }

    clickNode(nextButton);
    const startedAt = Date.now();

    while (Date.now() - startedAt < 15000) {
      const nextSubject = getSectionName();
      if (nextSubject && nextSubject !== currentSubject) {
        return true;
      }
      await sleep(200);
    }

    return false;
  }

  async function runAutoSubjectsLogic() {
    setStatus('Старт авто-прохода...');
    const store = loadStore();
    const run = {
      startedAt: new Date().toISOString(),
      subjects: {},
      subjectOrder: [],
    };

    const visited = new Set();
    let safetyCounter = 0;
    const skipSubjects = ['Математическая грамотность', 'История Казахстана', 'Грамотность чтения'];

    while (safetyCounter < 10) {
      const subjectKey = getSectionName();
      if (!subjectKey || visited.has(subjectKey)) {
        break;
      }

      visited.add(subjectKey);
      run.subjectOrder.push(subjectKey);

      // В режиме last-2-profile пропускаем первые 3 предмета
      if (autopilotConfig.mode === 'last-2-profile' && skipSubjects.includes(subjectKey)) {
        setStatus(`Пропускаем предмет: ${subjectKey}`);
        const moved = await goToNextSubject(subjectKey);
        if (!moved) {
          break;
        }
        await sleep(400);
        safetyCounter += 1;
        continue;
      }

      const subjectResult = await collectSubject(store, subjectKey);
      if (subjectResult) {
        run.subjects[subjectKey] = subjectResult;
        saveStore(store);
      }

      const moved = await goToNextSubject(subjectKey);
      if (!moved) {
        break;
      }

      await sleep(400);
      safetyCounter += 1;
    }

    store.pendingRun = run;
    saveStore(store);

    const aps = Number(GM_getValue('prob_ent_autopilot', '0'));
    if (aps > 0) {
      // In manual mode, we'd wait for user to click finish test.
      // Click Finish Test button auto logic here
      const endBtn = Array.from(document.querySelectorAll('button')).find((b) => normalizeText(b.textContent || '').includes('Завершить тест'));
      if (endBtn) {
         endBtn.click();
         await sleep(500);
         // Find confirm finish test if inside modal
         const confBtn = Array.from(document.querySelectorAll('button')).find((b) => normalizeText(b.textContent || '').includes('Подтвердить'));
         if (confBtn) {
            confBtn.click();
         }
      }
    } else {
        setStatus('Авто-проход завершен. Откройте таблицу баллов и сохраните результаты.');
    }
  }

  async function runAutoSubjects() {
    if (state.running) {
      return;
    }

    if (!isQuestPage()) {
      setStatus('Откройте страницу с вопросами.');
      return;
    }

    setRunning(true);

    try {
      await runAutoSubjectsLogic();
    } catch (error) {
      console.error('[prob-ent exporter]', error);
      setStatus(`Ошибка: ${error.message}`);
    } finally {
      setRunning(false);
    }
  }

  function extractResultsFromPage() {
    const blocks = Array.from(document.querySelectorAll('div.block.mb-10.bg-white'));
    const results = {};

    blocks.forEach((block) => {
      if (!/Данные тестирования/i.test(block.textContent || '')) {
        return;
      }

      const subjectName = normalizeSectionTitle(block.querySelector('.title-item span')?.textContent || '');
      if (!subjectName) {
        return;
      }

      const items = [];
      block.querySelectorAll('.maloy-block').forEach((item) => {
        const cells = item.querySelectorAll('div');
        if (cells.length < 3) {
          return;
        }

        const questionIndex = Number(normalizeText(cells[0]?.textContent || ''));
        const answer = normalizeText(cells[1]?.textContent || '');
        const resultValue = Number(normalizeText(cells[2]?.textContent || ''));

        if (!Number.isFinite(questionIndex) || !Number.isFinite(resultValue)) {
          return;
        }

        items.push({ questionIndex, answer, result: resultValue });
      });

      if (items.length) {
        results[subjectName] = items;
      }
    });

    return results;
  }

  function parseResultsFromPage() {
    if (!isResultsPage()) {
      setStatus('Откройте страницу таблицы баллов.');
      return;
    }

    const store = loadStore();
    const pendingRun = store.pendingRun;
    if (!pendingRun || !pendingRun.subjects) {
      setStatus('Нет сохраненного прогона. Запустите авто-проход сначала.');
      return;
    }

    const results = extractResultsFromPage();
    const now = new Date().toISOString();
    let updated = 0;

    Object.keys(results).forEach((subjectName) => {
      const subjectKey = normalizeSectionTitle(subjectName);
      const runInfo = pendingRun.subjects[subjectKey];
      if (!runInfo) {
        return;
      }

      const subjectData = ensureSubjectData(store, subjectKey);
      const variantData = subjectData.variants[runInfo.variantKey];
      if (!variantData) {
        return;
      }

      results[subjectName].forEach((entry) => {
        if (shouldSkipQuestionIndex(entry.questionIndex)) {
          return;
        }

        if (!variantData.questions[entry.questionIndex]) {
          variantData.questions[entry.questionIndex] = {
            questionIndex: entry.questionIndex,
            questionType: 'choice',
            questionText: '',
            answers: [],
          };
        }

        const question = variantData.questions[entry.questionIndex];
        question.selectedLetter = runInfo.letter;
        question.answerFromResults = entry.answer;
        question.result = entry.result;
        if (entry.result === 1) {
          question.correctLetter = runInfo.letter;
        }
        question.resultUpdatedAt = now;
        updated += 1;
      });
    });

    store.pendingRun = null;
    saveStore(store);
    setStatus(`Результаты сохранены: ${updated}.`);
  }

  function exportStoredData() {
    const store = loadStore();
    const payload = {
      exportedAt: new Date().toISOString(),
      store,
    };

    downloadJson(payload, `prob-ent-store-${Date.now()}.json`);
    setStatus('База экспортирована.');
  }

  function createPanel() {
    if (state.panel) {
      return;
    }

    if (!isQuestPage() && !isResultsPage()) {
      return;
    }

    const panel = document.createElement('div');
    panel.id = 'prob-ent-exporter-panel';
    panel.innerHTML = `
      <div class="title">prob-ent helper</div>
      <div class="status">Готово</div>
    `;

    document.body.appendChild(panel);

    const addButton = (label, handler, className = '') => {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = `action ${className}`.trim();
      button.textContent = label;
      button.addEventListener('click', handler);
      panel.appendChild(button);
      return button;
    };

    state.panel = panel;
    state.status = panel.querySelector('.status');


    if (isQuestPage()) {
      state.buttons.exportCurrent = addButton('Собрать текущий предмет', exportQuestions);
      state.buttons.auto = addButton('Авто-проход предметов', runAutoSubjects);
      state.buttons.answerFromDb = addButton('Ответить по базе', answerFromDatabase);
    }
  // --- Автоответ по базе ---
  async function answerFromDatabase() {
    if (state.running) return;

    setRunning(true);
    setStatus('Ответ по базе...');

    try {
      // Только чтение! Не изменять базу!
      const store = JSON.parse(JSON.stringify(loadStore()));
      const subjectKey = getSectionName();
      if (!subjectKey) {
        setStatus('Не определён предмет.');
        setRunning(false);
        return;
      }
      const subjectData = store.subjects[subjectKey];
      if (!subjectData || !subjectData.variantOrder.length) {
        setStatus('Нет данных по предмету в базе.');
        setRunning(false);
        return;
      }
      // --- Поиск наиболее похожего варианта по тексту первого вопроса ---
      const buttons = getQuestionButtons().filter((item) => item.id <= MAX_COLLECT_QUESTION);
      if (!buttons.length) {
        setStatus('Нет вопросов на странице.');
        setRunning(false);
        return;
      }
      const firstSnapshot = readQuestionSnapshot();
      let bestVariantKey = null;
      let bestScore = -1;
      for (const vKey of subjectData.variantOrder) {
        const vData = subjectData.variants[vKey];
        if (!vData || !vData.questions) continue;
        // Сравниваем текст первого вопроса на совпадение
        const q1 = vData.questions[buttons[0].id];
        if (!q1) continue;
        let score = 0;
        if (q1.questionText && firstSnapshot.questionText && q1.questionText === firstSnapshot.questionText) score += 10;
        if (q1.questionHtml && firstSnapshot.questionHtml && q1.questionHtml === firstSnapshot.questionHtml) score += 20;
        // Можно добавить сравнение по длине текста, по наличию ключевых слов и т.д.
        if (score > bestScore) {
          bestScore = score;
          bestVariantKey = vKey;
        }
      }
      if (!bestVariantKey) {
        setStatus('Не удалось подобрать вариант в базе.');
        setRunning(false);
        return;
      }
      const variantData = subjectData.variants[bestVariantKey];
      const questions = variantData.questions;
      let previousKey = '';
      for (let i = 0; i < buttons.length; i++) {
        const { id, node } = buttons[i];
        clickNode(node);
        await sleep(200);
        const snapshot = readQuestionSnapshot();
        previousKey = getSnapshotKey(snapshot);
        const q = questions[id];
        // Сравниваем текст вопроса для большей точности
        if (q && q.correctLetter && q.questionText && snapshot.questionText && q.questionText === snapshot.questionText) {
          selectAnswerLetter(q.correctLetter);
        }
        setStatus(`Ответ по базе: ${i + 1} из ${buttons.length}`);
        await sleep(120);
      }
      setStatus('Ответ по базе завершён. Проверьте и завершите тест.');
    } catch (e) {
      setStatus('Ошибка: ' + (e?.message || e));
    } finally {
      setRunning(false);
    }
  }

    if (isResultsPage()) {
      state.buttons.parseResults = addButton('Сохранить результаты', parseResultsFromPage);
    }

    state.buttons.exportStore = addButton('Экспорт базы', exportStoredData, 'secondary');

    const aps = Number(GM_getValue('prob_ent_autopilot', '0'));
    if (aps > 0) {
      state.buttons.autopilotStop = addButton(`Остановить АВТО (${aps})`, () => {
        GM_setValue('prob_ent_autopilot', 0);
        location.reload();
      }, 'secondary');
    } else {
      state.buttons.autopilotStart = addButton(`Полная автоматизация (${AUTOPILOT_CYCLES})`, () => {
        GM_setValue('prob_ent_autopilot', AUTOPILOT_CYCLES);
        location.reload();
      }, 'secondary');
    }
  }

  GM_addStyle(`
    #prob-ent-exporter-panel {
      position: fixed;
      right: 16px;
      bottom: 16px;
      z-index: 2147483647;
      width: 240px;
      padding: 12px;
      border: 1px solid #1f4b99;
      border-radius: 12px;
      background: rgba(10, 22, 48, 0.96);
      color: #ffffff;
      font: 13px/1.4 Arial, sans-serif;
      box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35);
    }

    #prob-ent-exporter-panel .title {
      font-weight: 700;
      margin-bottom: 8px;
    }

    #prob-ent-exporter-panel .status {
      min-height: 36px;
      margin-bottom: 10px;
      color: #c7d9ff;
    }

    #prob-ent-exporter-panel .action {
      width: 100%;
      padding: 8px 10px;
      margin-top: 8px;
      border: 0;
      border-radius: 8px;
      background: #4ea1ff;
      color: #fff;
      font-weight: 700;
      cursor: pointer;
    }

    #prob-ent-exporter-panel .action.secondary {
      background: #263a63;
      color: #d6e1ff;
    }

    #prob-ent-exporter-panel .action:disabled {
      cursor: wait;
      opacity: 0.7;
    }
  `);

  async function performAutopilotStep() {
    const aps = Number(GM_getValue('prob_ent_autopilot', '0'));
    if (aps <= 0) return;

    const mode = GM_getValue('prob_ent_autopilot_mode', 'all');
    autopilotConfig.mode = mode;

    setStatus(`АВТОПИЛОТ (Осталось ${aps})`);
    const path = window.location.pathname;

    if (path === '/' || path === '/auth') {
      const loginInput = document.querySelector('#main_login');
      if (loginInput && !loginInput.value) {
        loginInput.value = IIN;
        loginInput.dispatchEvent(new Event('input'));
        await sleep(500);
        const loginBtn = document.querySelector('button[type="submit"]');
        if (loginBtn && !loginBtn.disabled) loginBtn.click();
      }
    } else if (path.includes('/agreement')) {
      const typeSelect = document.querySelector('input[formcontrolname="testTypeId"][value="33"]');
      if (typeSelect && !typeSelect.checked) typeSelect.click();

      const langSelect = document.querySelector('select[formcontrolname="testLanguageId"]');
      if (langSelect && langSelect.value === "0") {
        langSelect.value = '2'; // Русский
        langSelect.dispatchEvent(new Event('change'));
      }

      const subjSelect = document.querySelector('select[formcontrolname="profileSubjectPairId"]');
      if (subjSelect && subjSelect.value === "0") {
        subjSelect.value = SUBJECT_INDEX; // Профили
        subjSelect.dispatchEvent(new Event('change'));
      }

      await sleep(500);
      const confBtn = Array.from(document.querySelectorAll('button')).find(b => normalizeText(b.textContent || '').includes('Подтвердить корректность данных'));
      if (confBtn && !confBtn.disabled) confBtn.click();
    } else if (path.includes('/test-rules')) {
      const check = document.querySelector('input#rulesCheck');
      if (check && !check.checked) {
        check.click();
        await sleep(500);
      }
      const startBtn = document.querySelector('input[value="Начать тестирование"]');
      if (startBtn && !startBtn.disabled) startBtn.click();
    } else if (path.includes('/test/quest/')) {
      // Если нужно пропустить этот предмет (режим last-2-profile)
      if (autopilotConfig.mode === 'last-2-profile') {
        const currentSubject = getSectionName();
        const skipSubjects = ['Математическая грамотность', 'История Казахстана', 'Грамотность чтения'];
        if (currentSubject && skipSubjects.includes(currentSubject)) {
          // Пропустить этот предмет - нажать "Следующий предмет"
          const nextBtn = findNextSubjectButton();
          if (nextBtn) {
            clickNode(nextBtn);
            await sleep(400); // Ждем загрузки следующего предмета
            return; // Возвращаемся, следующий цикл обработает новый предмет
          }
        }
      }
      const captchaInput = document.querySelector('input[formcontrolname="nanoCaptcha"]');
      if (captchaInput) {
        const findFinishButton = () => Array.from(document.querySelectorAll('button')).find((b) => {
          const text = normalizeText(b.textContent || '');
          return text.includes('Завершить тест!') || text.includes('Закончить тест!');
        });

        let endBtn = findFinishButton();
        if (!endBtn) {
          // Value starts at 0; step up until finish button appears.
          let currentValue = Number(captchaInput.value || 0);
          if (!Number.isFinite(currentValue)) currentValue = 0;

          for (let i = 0; i < 24; i += 1) {
            if (typeof captchaInput.stepUp === 'function') {
              captchaInput.stepUp();
              currentValue = Number(captchaInput.value || currentValue + 1);
            } else {
              currentValue += 1;
              captchaInput.value = String(currentValue);
            }

            captchaInput.dispatchEvent(new Event('input', { bubbles: true }));
            captchaInput.dispatchEvent(new Event('change', { bubbles: true }));
            await sleep(250);

            endBtn = findFinishButton();
            if (endBtn) break;
          }
        }

        if (endBtn) {
          endBtn.click();
          await sleep(800);
          const confirmBtn = Array.from(document.querySelectorAll('button')).find((b) => {
            const text = normalizeText(b.textContent || '');
            return text.includes('Подтвердить') || text === 'Да' || text === 'Ок' || text === 'OK';
          });
          if (confirmBtn) confirmBtn.click();
        }
      } else if (!state.running) {
        // Find if we are on quests
        // Since we are running AutoSubjects async, prevent double trigger
        setRunning(true);
        try {
           await runAutoSubjectsLogic();
        } finally {
           setRunning(false);
        }
      }
    } else if (path.includes('/test/answer-map') || isResultsPage()) {
      if (!state.running) {
          setRunning(true);
          parseResultsFromPage();
          await sleep(1200); // Visual cue
          const storeAfter = loadStore();
          if (!storeAfter.pendingRun) {
            GM_setValue('prob_ent_autopilot', aps - 1);
            setRunning(false);
            if (aps - 1 > 0) {
              window.location.href = '/';
            } else {
              setStatus('Цикл завершен!');
            }
          } else {
            setStatus('Жду таблицу баллов...');
            setRunning(false);
          }
      }
    }
  }

  // Add auto checking loop
  setInterval(() => {
     performAutopilotStep().catch(e => console.error(e));
  }, 3000);

  GM_registerMenuCommand(`Запустить полный автопилот (${AUTOPILOT_CYCLES})`, () => {
    GM_setValue('prob_ent_autopilot', AUTOPILOT_CYCLES);
    location.reload();
  });
  GM_registerMenuCommand('Остановить автопилот', () => {
    GM_setValue('prob_ent_autopilot', 0);
    location.reload();
  });
  GM_registerMenuCommand('Автопилот: все предметы', () => {
    GM_setValue('prob_ent_autopilot_mode', 'all');
    GM_setValue('prob_ent_autopilot', AUTOPILOT_CYCLES);
    location.reload();
  });
  GM_registerMenuCommand('Автопилот: только 2 профильных', () => {
    GM_setValue('prob_ent_autopilot_mode', 'last-2-profile');
    GM_setValue('prob_ent_autopilot', AUTOPILOT_CYCLES);
    location.reload();
  });
  GM_registerMenuCommand('Собрать текущий предмет', exportQuestions);
  GM_registerMenuCommand('Авто-проход предметов', runAutoSubjects);
  GM_registerMenuCommand('Сохранить результаты', parseResultsFromPage);
  GM_registerMenuCommand('Экспорт базы', exportStoredData);
  GM_registerMenuCommand('Сбросить базу', () => {
    resetStore();
    setStatus('База очищена.');
  });
  createPanel();
})();