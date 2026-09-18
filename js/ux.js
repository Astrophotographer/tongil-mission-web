(function () {
  var KEY = 'tongil-visit-count';

  function bump() {
    var n = 0;
    try {
      n = parseInt(localStorage.getItem(KEY) || '0', 10) || 0;
      n += 1;
      localStorage.setItem(KEY, String(n));
    } catch (e) {
      n = 1;
    }
    var el = document.getElementById('visit-count');
    if (el) el.textContent = String(n);
  }

  function revealSections() {
    var nodes = document.querySelectorAll('.section');
    if (!('IntersectionObserver' in window)) {
      nodes.forEach(function (n) {
        n.classList.add('is-visible');
      });
      return;
    }
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );
    nodes.forEach(function (n) {
      n.classList.add('reveal');
      io.observe(n);
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    bump();
    revealSections();
  });
})();
