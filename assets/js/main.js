/* ============================================================
   Thunder Research Group — behaviour
   ============================================================ */
(function () {
  'use strict';

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- Theme ---------- */
  var root = document.documentElement;
  var stored = null;
  try { stored = localStorage.getItem('trg-theme'); } catch (e) {}
  if (stored) root.setAttribute('data-theme', stored);

  function toggleTheme() {
    var next = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    root.setAttribute('data-theme', next);
    try { localStorage.setItem('trg-theme', next); } catch (e) {}
    document.dispatchEvent(new CustomEvent('themechange'));
  }
  var themeBtn = document.querySelector('[data-theme-toggle]');
  if (themeBtn) themeBtn.addEventListener('click', toggleTheme);

  /* ---------- Header state + mobile nav ---------- */
  var header = document.querySelector('.header');
  var nav = document.getElementById('nav');
  var menuBtn = document.querySelector('[data-menu]');

  if (header) {
    var onScroll = function () { header.classList.toggle('is-stuck', window.scrollY > 8); };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }
  if (menuBtn && nav) {
    menuBtn.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      menuBtn.setAttribute('aria-expanded', String(open));
    });
    nav.addEventListener('click', function (e) {
      if (e.target.closest('a')) { nav.classList.remove('open'); menuBtn.setAttribute('aria-expanded', 'false'); }
    });
  }

  /* ---------- Scroll reveal ---------- */
  var revealables = document.querySelectorAll('[data-reveal]');
  if (!('IntersectionObserver' in window) || reduced) {
    revealables.forEach(function (el) { el.classList.add('in'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    revealables.forEach(function (el, i) {
      if (!el.style.getPropertyValue('--d')) el.style.setProperty('--d', ((i % 5) * 70) + 'ms');
      io.observe(el);
    });
  }

  /* ---------- Publication / people filtering ---------- */
  var filterBar = document.querySelector('[data-filters]');
  if (filterBar) {
    var targets = document.querySelectorAll('[data-div]');
    filterBar.addEventListener('click', function (e) {
      var btn = e.target.closest('.filter');
      if (!btn) return;
      var key = btn.dataset.filter;
      filterBar.querySelectorAll('.filter').forEach(function (b) {
        b.setAttribute('aria-pressed', String(b === btn));
      });
      targets.forEach(function (t) {
        var show = key === 'all' || t.dataset.div === key || (t.dataset.tags || '').split(' ').indexOf(key) > -1;
        t.style.display = show ? '' : 'none';
      });
    });
  }

  /* ---------- Hero field: two-source interference, drawn as contour lines ----------
     A physical wave field rather than the usual particle mesh — slow, quiet,
     and it actually means something next to "quantum".                        */
  var canvas = document.querySelector('.hero-canvas');
  if (canvas && canvas.getContext) {
    var ctx = canvas.getContext('2d');
    var w = 0, h = 0, dpr = 1, raf = 0, t = 0;
    var stroke = '#7fd7e6', warm = '#e8ab6f';

    function readColors() {
      var cs = getComputedStyle(document.documentElement);
      stroke = (cs.getPropertyValue('--cs') || '#7fd7e6').trim();
      warm = (cs.getPropertyValue('--ds') || '#e8ab6f').trim();
    }

    function resize() {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      var r = canvas.getBoundingClientRect();
      w = Math.max(1, r.width); h = Math.max(1, r.height);
      canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function draw() {
      ctx.clearRect(0, 0, w, h);

      var rows = Math.max(16, Math.round(h / 26));
      var step = Math.max(6, Math.round(w / 190));
      // two coherent sources, slowly breathing
      var ax = w * 0.24, ay = h * (0.52 + 0.05 * Math.sin(t * 0.21));
      var bx = w * 0.82, by = h * (0.34 + 0.06 * Math.cos(t * 0.17));
      var k = 0.021, amp = Math.min(26, h / 26);

      ctx.lineWidth = 1;
      ctx.lineJoin = 'round';

      for (var r = 0; r < rows; r++) {
        var baseY = (r + 0.5) * (h / rows);
        // fade rows toward the top and the far right so text stays readable
        var vert = Math.pow(r / rows, 1.35);
        var alpha = 0.055 + 0.16 * vert;
        var blend = r / rows; // ice -> ember down the field
        ctx.strokeStyle = blend > 0.72 ? warm : stroke;
        ctx.globalAlpha = blend > 0.72 ? alpha * 0.55 : alpha;

        ctx.beginPath();
        for (var x = -step; x <= w + step; x += step) {
          var d1 = Math.hypot(x - ax, baseY - ay);
          var d2 = Math.hypot(x - bx, baseY - by);
          var wave = Math.sin(d1 * k - t * 1.15) + Math.sin(d2 * k - t * 0.92);
          var damp = 1 / (1 + d1 * 0.0022) + 1 / (1 + d2 * 0.0022);
          var y = baseY + wave * amp * 0.5 * damp;
          if (x <= -step) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }
        ctx.stroke();
      }
      ctx.globalAlpha = 1;
    }

    function loop() { t += 0.0075; draw(); raf = requestAnimationFrame(loop); }
    function start() { if (!raf && !reduced) raf = requestAnimationFrame(loop); }
    function stop() { if (raf) { cancelAnimationFrame(raf); raf = 0; } }

    readColors(); resize(); draw();
    if (reduced) { t = 1.4; draw(); } else start();

    var rt;
    window.addEventListener('resize', function () {
      clearTimeout(rt);
      rt = setTimeout(function () { resize(); draw(); }, 120);
    });
    document.addEventListener('visibilitychange', function () { document.hidden ? stop() : start(); });
    document.addEventListener('themechange', function () { readColors(); draw(); });
  }

  /* ---------- Year stamp ---------- */
  document.querySelectorAll('[data-year]').forEach(function (el) {
    el.textContent = new Date().getFullYear();
  });
})();
