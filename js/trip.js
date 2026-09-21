(function () {
  var form = document.getElementById('trip-form');
  if (!form) return;

  var dateEl = document.getElementById('date');
  var originEl = document.getElementById('origin');
  var destinationEl = document.getElementById('destination');
  var scheduleEl = document.getElementById('schedule');
  var audienceEl = document.getElementById('audience');
  var submitBtn = document.getElementById('trip-submit');
  var statusEl = document.getElementById('trip-status');
  var resultEl = document.getElementById('trip-result');
  var mapLinkEl = document.getElementById('trip-map-link');
  var inFlight = false;

  function setStatus(text) {
    if (statusEl) statusEl.textContent = text;
  }

  function clearResultText() {
    if (resultEl) resultEl.textContent = '';
  }

  function clearResult() {
    clearResultText();
    if (window.TongilTripMap) window.TongilTripMap.clear();
    if (mapLinkEl) {
      mapLinkEl.hidden = true;
      mapLinkEl.removeAttribute('href');
    }
  }

  function scheduleLabel() {
    if (!scheduleEl || !scheduleEl.value) return '';
    var opt = scheduleEl.options[scheduleEl.selectedIndex];
    return (opt && opt.text ? opt.text : '').trim();
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
    clearResultText();
    if (mapLinkEl) {
      mapLinkEl.hidden = true;
      mapLinkEl.removeAttribute('href');
    }

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

    var timeline = primary.timeline || [];
    if (timeline.length) {
      appendHeading(fragment, '시간대별 탐방 코스');
      var tl = document.createElement('ol');
      tl.className = 'trip-timeline';
      timeline.forEach(function (slot) {
        var li = document.createElement('li');
        var time = slot.time || '';
        var place = slot.place || '';
        var activity = slot.activity || '';
        var parts = [];
        if (time) parts.push(time);
        if (place) parts.push(place);
        if (activity) parts.push(activity);
        li.textContent = parts.join(' · ');
        tl.appendChild(li);
      });
      fragment.appendChild(tl);
    }

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

    var route = data.route || null;
    if (window.TongilTripMap) {
      window.TongilTripMap.renderRoute(route);
      var href = window.TongilTripMap.externalLink(route);
      if (mapLinkEl && href) {
        mapLinkEl.href = href;
        mapLinkEl.hidden = false;
      }
    }
  }

  function runRecommend() {
    if (inFlight) return;

    var date = (dateEl && dateEl.value ? dateEl.value : '').trim();
    var origin = (originEl && originEl.value ? originEl.value : '').trim();
    var destination = (destinationEl && destinationEl.value ? destinationEl.value : '').trim();
    var schedule = scheduleLabel();
    var audience = (audienceEl && audienceEl.value ? audienceEl.value : '').trim();

    if (!date || !origin || !destination || !schedule || !audience) {
      setStatus('필수값을 입력하세요');
      clearResult();
      return;
    }

    clearResult();
    setStatus('응답을 기다리는 중…');
    inFlight = true;
    if (submitBtn) submitBtn.disabled = true;

    fetch('/api/trip_recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        date: date,
        origin: origin,
        destination: destination,
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
        if (window.TongilHistory) {
          var site = (result.primary && result.primary.recommended_site) || '';
          var tl = (result.primary && result.primary.timeline) || [];
          var tlPreview = tl
            .slice(0, 4)
            .map(function (s) {
              return [s.time, s.place || s.activity].filter(Boolean).join(' ');
            })
            .join(' → ');
          var summary = site
            ? '추천: ' + site + (tlPreview ? ' | 코스: ' + tlPreview : '')
            : (result.report_markdown || '').slice(0, 200);
          window.TongilHistory.add(
            'trip',
            [date, origin, '→', destination, schedule, audience].join(' '),
            summary
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
    runRecommend();
  });
})();
