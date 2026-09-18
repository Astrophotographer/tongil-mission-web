(function () {
  var STORAGE = 'tongil-theme';
  var root = document.documentElement;

  function apply(theme) {
    root.setAttribute('data-theme', theme);
    try {
      localStorage.setItem(STORAGE, theme);
    } catch (e) {
      /* ignore */
    }
    var btn = document.getElementById('theme-toggle');
    if (btn) {
      var dark = theme === 'dark';
      btn.setAttribute('aria-pressed', dark ? 'true' : 'false');
      btn.textContent = dark ? '라이트' : '다크';
      btn.setAttribute('aria-label', dark ? '라이트 모드로 전환' : '다크 모드로 전환');
    }
  }

  function initial() {
    try {
      var saved = localStorage.getItem(STORAGE);
      if (saved === 'dark' || saved === 'light') return saved;
    } catch (e) {
      /* ignore */
    }
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
    return 'light';
  }

  apply(initial());

  document.addEventListener('DOMContentLoaded', function () {
    var btn = document.getElementById('theme-toggle');
    if (!btn) return;
    apply(root.getAttribute('data-theme') || 'light');
    btn.addEventListener('click', function () {
      var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      apply(next);
    });
  });
})();
