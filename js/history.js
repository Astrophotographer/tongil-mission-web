(function () {
  var KEY = 'tongil-mission-history-v1';
  var MAX = 20;

  function load() {
    try {
      var raw = localStorage.getItem(KEY);
      var list = raw ? JSON.parse(raw) : [];
      return Array.isArray(list) ? list : [];
    } catch (e) {
      return [];
    }
  }

  function save(list) {
    try {
      localStorage.setItem(KEY, JSON.stringify(list.slice(0, MAX)));
    } catch (e) {
      /* quota */
    }
  }

  function render() {
    var listEl = document.getElementById('history-list');
    var emptyEl = document.getElementById('history-empty');
    if (!listEl) return;
    var items = load();
    listEl.textContent = '';
    if (!items.length) {
      if (emptyEl) emptyEl.hidden = false;
      return;
    }
    if (emptyEl) emptyEl.hidden = true;
    items.forEach(function (item) {
      var li = document.createElement('li');
      li.className = 'history-item';
      var title = document.createElement('strong');
      title.textContent = labelFor(item.kind);
      var when = document.createElement('time');
      when.textContent = item.at || '';
      var preview = document.createElement('p');
      preview.textContent = item.summary || '';
      li.appendChild(title);
      li.appendChild(when);
      li.appendChild(preview);
      listEl.appendChild(li);
    });
  }

  function labelFor(kind) {
    if (kind === 'fact_check') return '팩트체크';
    if (kind === 'trip') return '탐방 추천';
    if (kind === 'inquiry') return '문의';
    return kind || '기록';
  }

  function notifyServer(kind, input, summary) {
    return fetch('/api/save_result', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ kind: kind, input: input || '', summary: summary || '' }),
    }).catch(function () {
      /* local history still kept */
    });
  }

  window.TongilHistory = {
    add: function (kind, input, summary) {
      var entry = {
        kind: kind,
        input: (input || '').slice(0, 500),
        summary: (summary || '').slice(0, 800),
        at: new Date().toLocaleString('ko-KR'),
      };
      var list = load();
      list.unshift(entry);
      save(list);
      render();
      notifyServer(kind, entry.input, entry.summary);
    },
    render: render,
  };

  document.addEventListener('DOMContentLoaded', function () {
    render();
    var clearBtn = document.getElementById('history-clear');
    if (clearBtn) {
      clearBtn.addEventListener('click', function () {
        save([]);
        render();
      });
    }

    var inquiryForm = document.getElementById('inquiry-form');
    if (inquiryForm) {
      inquiryForm.addEventListener('submit', function (e) {
        e.preventDefault();
        var nameEl = document.getElementById('inquiry-name');
        var msgEl = document.getElementById('inquiry-message');
        var statusEl = document.getElementById('inquiry-status');
        var name = (nameEl && nameEl.value ? nameEl.value : '').trim();
        var message = (msgEl && msgEl.value ? msgEl.value : '').trim();
        if (!name || !message) {
          if (statusEl) statusEl.textContent = '필수값을 입력하세요';
          return;
        }
        if (statusEl) statusEl.textContent = '응답을 기다리는 중…';
        var summary = name + ': ' + message;
        window.TongilHistory.add('inquiry', name, summary);
        if (statusEl) {
          statusEl.textContent =
            '문의가 기록되었습니다. (웹훅이 설정돼 있으면 알림도 전송됩니다)';
        }
        if (msgEl) msgEl.value = '';
      });
    }
  });
})();
