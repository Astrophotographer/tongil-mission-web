(function () {
  var form = document.getElementById('trip-form');
  if (!form) return;

  var dateEl = document.getElementById('date');
  var originEl = document.getElementById('origin');
  var scheduleEl = document.getElementById('schedule');
  var audienceEl = document.getElementById('audience');
  var submitBtn = document.getElementById('trip-submit');
  var statusEl = document.getElementById('trip-status');
  var resultEl = document.getElementById('trip-result');

  function setStatus(text) {
    if (statusEl) statusEl.textContent = text;
  }

  function clearResult() {
    if (resultEl) resultEl.textContent = '';
  }

  function appendHeading(parent, text) {
    var h = document.createElement('h3');
    h.textContent = text;
    parent.appendChild(h);
  }

  function appendList(parent, title, items) {
    if (!items || !items.length) return;
    appendHeading(parent, title);
    var ul = document.createElement('ul');
    items.forEach(function (item) {
      var li = document.createElement('li');
      li.textContent = item;
      ul.appendChild(li);
    });
    parent.appendChild(ul);
  }

  function renderResult(data) {
    if (!resultEl || !data) return;
    clearResult();

    var primary = data.primary || {};
    var fragment = document.createDocumentFragment();

    if (primary.recommended_site) {
      appendHeading(fragment, '추천 탐방지');
      var site = document.createElement('p');
      site.textContent = primary.recommended_site;
      fragment.appendChild(site);
    }

    if (primary.reason) {
      appendHeading(fragment, '추천 이유');
      var reason = document.createElement('p');
      reason.textContent = primary.reason;
      fragment.appendChild(reason);
    }

    appendList(fragment, '학습 목표', primary.learning_goals);
    appendList(fragment, '현장 미션', primary.field_missions);

    var places = data.places || [];
    if (places.length) {
      appendHeading(fragment, '주변 장소');
      var ul = document.createElement('ul');
      places.forEach(function (place) {
        var li = document.createElement('li');
        var parts = [place.name, place.address, place.category].filter(function (p) {
          return p;
        });
        li.textContent = parts.join(' · ');
        ul.appendChild(li);
      });
      fragment.appendChild(ul);
    }

    if (data.report_markdown) {
      appendHeading(fragment, '탐방 보고서');
      var report = document.createElement('pre');
      report.style.whiteSpace = 'pre-wrap';
      report.textContent = data.report_markdown;
      fragment.appendChild(report);
    }

    resultEl.appendChild(fragment);
  }

  function runRecommend() {
    var date = (dateEl && dateEl.value ? dateEl.value : '').trim();
    var origin = (originEl && originEl.value ? originEl.value : '').trim();
    var schedule = (scheduleEl && scheduleEl.value ? scheduleEl.value : '').trim();
    var audience = (audienceEl && audienceEl.value ? audienceEl.value : '').trim();

    if (!date || !origin || !schedule || !audience) {
      setStatus('필수값을 입력하세요');
      clearResult();
      return;
    }

    clearResult();
    setStatus('응답을 기다리는 중…');
    if (submitBtn) submitBtn.disabled = true;

    fetch('/api/trip_recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        date: date,
        origin: origin,
        schedule: schedule,
        audience: audience,
      }),
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
        var result = data.result || {};
        var warnings = result.warnings || [];
        setStatus(warnings.length ? warnings.join(' ') : '');
        renderResult(result);
      })
      .catch(function () {
        setStatus('잠시 후 다시 시도하세요');
        clearResult();
      })
      .finally(function () {
        if (submitBtn) submitBtn.disabled = false;
      });
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    runRecommend();
  });
})();
