(function () {
  var form = document.getElementById('fact-form');
  if (!form) return;

  var questionEl = document.getElementById('fact-question');
  var submitBtn = document.getElementById('fact-submit');
  var statusEl = document.getElementById('fact-status');
  var resultEl = document.getElementById('fact-result');
  var inFlight = false;

  function setStatus(text) {
    if (statusEl) statusEl.textContent = text;
  }

  function clearResult() {
    if (resultEl) resultEl.textContent = '';
  }

  function runCheck() {
    if (inFlight) return;

    var question = (questionEl && questionEl.value ? questionEl.value : '').trim();
    if (!question) {
      setStatus('필수값을 입력하세요');
      clearResult();
      return;
    }

    clearResult();
    setStatus('응답을 기다리는 중…');
    inFlight = true;
    if (submitBtn) submitBtn.disabled = true;

    fetch('/api/fact_check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: question }),
    })
      .then(function (res) {
        return res.json().then(function (data) {
          return { res: res, data: data };
        });
      })
      .then(function (_ref) {
        var res = _ref.res;
        var data = _ref.data;
        if (!res.ok || !data.ok) {
          setStatus('잠시 후 다시 시도하세요');
          clearResult();
          return;
        }
        setStatus('');
        if (resultEl && data.result) {
          resultEl.textContent = data.result.answer || '';
        }
        if (window.TongilHistory) {
          window.TongilHistory.add(
            'fact_check',
            question,
            (data.result && data.result.answer) || ''
          );
        }
      })
      .catch(function () {
        setStatus('잠시 후 다시 시도하세요');
        clearResult();
      })
      .finally(function () {
        inFlight = false;
        if (submitBtn) submitBtn.disabled = false;
      });
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    runCheck();
  });

  form.querySelectorAll('[data-example]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var example = btn.getAttribute('data-example') || '';
      if (questionEl) questionEl.value = example;
      runCheck();
    });
  });
})();
