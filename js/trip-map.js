(function () {
  var map = null;
  var overlays = [];
  var sdkPromise = null;

  function clearOverlays() {
    overlays.forEach(function (item) {
      if (item && item.setMap) item.setMap(null);
    });
    overlays = [];
  }

  function setNote(note, text) {
    if (!note) return;
    note.hidden = !text;
    note.textContent = text || '';
  }

  function loadSdk(appKey) {
    if (window.kakao && window.kakao.maps && window.kakao.maps.LatLng) {
      return Promise.resolve();
    }
    if (sdkPromise) return sdkPromise;

    sdkPromise = new Promise(function (resolve, reject) {
      var script = document.createElement('script');
      script.src =
        'https://dapi.kakao.com/v2/maps/sdk.js?appkey=' +
        encodeURIComponent(appKey) +
        '&autoload=false';
      script.async = true;
      script.onload = function () {
        if (!window.kakao || !window.kakao.maps || !window.kakao.maps.load) {
          reject(new Error('kakao maps missing after script load'));
          return;
        }
        window.kakao.maps.load(function () {
          if (!window.kakao.maps.LatLng) {
            reject(new Error('kakao maps modules not ready'));
            return;
          }
          resolve();
        });
      };
      script.onerror = function () {
        reject(
          new Error(
            'sdk script blocked — Kakao Developers에서 JavaScript 키 사이트 도메인에 현재 주소를 등록했는지 확인하세요'
          )
        );
      };
      document.head.appendChild(script);
    }).catch(function (err) {
      // allow retry on next recommend
      sdkPromise = null;
      throw err;
    });

    return sdkPromise;
  }

  function fetchJsKey() {
    return fetch('/api/public_config')
      .then(function (res) {
        return res.json();
      })
      .then(function (data) {
        return (data && data.kakaoJsKey) || '';
      });
  }

  function addMarker(kakaoMaps, position, title) {
    var marker = new kakaoMaps.Marker({
      position: position,
      map: map,
      title: title || '',
    });
    overlays.push(marker);
    if (title) {
      var iw = new kakaoMaps.InfoWindow({
        content:
          '<div style="padding:6px 8px;font-size:12px;white-space:nowrap;">' +
          String(title)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;') +
          '</div>',
      });
      iw.open(map, marker);
      overlays.push(iw);
    }
    return marker;
  }

  function renderRoute(route) {
    var container = document.getElementById('trip-map');
    var note = document.getElementById('trip-map-note');
    if (!container) return;

    if (!route || !route.origin || !route.destination) {
      container.hidden = true;
      setNote(note, '지도에 표시할 출발/도착 좌표가 없습니다.');
      return;
    }

    fetchJsKey()
      .then(function (appKey) {
        if (!appKey) {
          container.hidden = true;
          setNote(
            note,
            '지도 표시를 위해 Vercel에 KAKAO_JS_KEY를 설정하세요. 아래 링크로도 경로를 열 수 있습니다.'
          );
          return null;
        }
        // unhide before Map() so Kakao can measure size
        container.hidden = false;
        setNote(note, '지도를 불러오는 중…');
        return loadSdk(appKey).then(function () {
          return appKey;
        });
      })
      .then(function (appKey) {
        if (!appKey) return;
        var kakaoMaps = window.kakao.maps;
        var center = new kakaoMaps.LatLng(route.destination.lat, route.destination.lng);

        if (!map) {
          map = new kakaoMaps.Map(container, { center: center, level: 8 });
        } else {
          map.setCenter(center);
        }
        // after was-hidden containers
        if (map.relayout) map.relayout();

        clearOverlays();

        var bounds = new kakaoMaps.LatLngBounds();
        var o = new kakaoMaps.LatLng(route.origin.lat, route.origin.lng);
        var d = new kakaoMaps.LatLng(route.destination.lat, route.destination.lng);
        addMarker(kakaoMaps, o, '출발 · ' + (route.origin.name || ''));
        addMarker(kakaoMaps, d, '도착 · ' + (route.destination.name || ''));
        bounds.extend(o);
        bounds.extend(d);

        if (
          route.site &&
          route.site.lat &&
          route.site.lng &&
          (Math.abs(route.site.lat - route.destination.lat) > 0.0005 ||
            Math.abs(route.site.lng - route.destination.lng) > 0.0005)
        ) {
          var s = new kakaoMaps.LatLng(route.site.lat, route.site.lng);
          addMarker(kakaoMaps, s, '탐방지 · ' + (route.site.name || ''));
          bounds.extend(s);
        }

        var linePath = [];
        var path = route.path || [];
        if (path.length >= 2) {
          path.forEach(function (pt) {
            var latlng = new kakaoMaps.LatLng(pt.lat, pt.lng);
            linePath.push(latlng);
            bounds.extend(latlng);
          });
        } else {
          linePath = [o, d];
        }

        var polyline = new kakaoMaps.Polyline({
          path: linePath,
          strokeWeight: 5,
          strokeColor: '#1a6b52',
          strokeOpacity: 0.85,
          strokeStyle: 'solid',
        });
        polyline.setMap(map);
        overlays.push(polyline);
        map.setBounds(bounds);
        if (map.relayout) map.relayout();
        setNote(note, '');
      })
      .catch(function (err) {
        container.hidden = true;
        var detail = err && err.message ? String(err.message) : '';
        var tip =
          '카카오 지도를 불러오지 못했습니다. Kakao Developers → 앱 → 플랫폼(Web)에 ' +
          'https://tongil-mission-web.vercel.app 도메인을 등록했는지 확인하세요. 아래 링크로도 경로를 열 수 있습니다.';
        if (detail) tip += ' (' + detail + ')';
        setNote(note, tip);
      });
  }

  function externalLink(route) {
    if (!route || !route.origin || !route.destination) return '';
    var o = route.origin;
    var d = route.destination;
    return (
      'https://map.kakao.com/link/from/' +
      encodeURIComponent(o.name || '출발') +
      ',' +
      o.lat +
      ',' +
      o.lng +
      '/to/' +
      encodeURIComponent(d.name || '도착') +
      ',' +
      d.lat +
      ',' +
      d.lng
    );
  }

  window.TongilTripMap = {
    renderRoute: renderRoute,
    externalLink: externalLink,
    clear: function () {
      clearOverlays();
      var container = document.getElementById('trip-map');
      var note = document.getElementById('trip-map-note');
      if (container) container.hidden = true;
      setNote(note, '');
    },
  };
})();
