(function () {
  'use strict';
  var doc = document;
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  // cursor glow
  var glow = doc.querySelector('.glow');
  window.addEventListener('pointermove', function (e) {
    glow.style.setProperty('--mx', e.clientX + 'px');
    glow.style.setProperty('--my', e.clientY + 'px');
  }, { passive: true });

  // card spotlight
  doc.querySelectorAll('.box, .wu').forEach(function (el) {
    el.addEventListener('pointermove', function (e) {
      var r = el.getBoundingClientRect();
      el.style.setProperty('--x', (e.clientX - r.left) + 'px');
      el.style.setProperty('--y', (e.clientY - r.top) + 'px');
    });
  });

  // mobile menu
  var burger = doc.querySelector('.burger'), menu = doc.getElementById('menu');
  if (burger && menu) {
    burger.addEventListener('click', function () {
      var open = menu.classList.toggle('open');
      burger.setAttribute('aria-expanded', open);
    });
    menu.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') { menu.classList.remove('open'); burger.setAttribute('aria-expanded', 'false'); }
    });
  }

  // reveal on scroll
  var items = doc.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && !reduce) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { threshold: 0.12 });
    items.forEach(function (el) { io.observe(el); });
  } else {
    items.forEach(function (el) { el.classList.add('in'); });
  }

  // count-up
  var counters = doc.querySelectorAll('[data-count]');
  if ('IntersectionObserver' in window && !reduce) {
    var co = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        var el = e.target, to = +el.dataset.count, suf = el.dataset.suffix || '', t0 = performance.now();
        (function step(t) {
          var p = Math.min(1, (t - t0) / 1100), v = Math.round(to * (1 - Math.pow(1 - p, 3)));
          el.textContent = v + suf;
          if (p < 1) requestAnimationFrame(step);
        })(t0);
        co.unobserve(el);
      });
    }, { threshold: 0.6 });
    counters.forEach(function (el) { co.observe(el); });
  }

  // writeup filters
  var chips = doc.querySelectorAll('.filters button'), cards = doc.querySelectorAll('.wu');
  chips.forEach(function (b) {
    b.addEventListener('click', function () {
      chips.forEach(function (x) { x.classList.toggle('on', x === b); });
      var f = b.dataset.f;
      cards.forEach(function (c) { c.hidden = !(f === 'all' || c.dataset.kind === f); });
    });
  });

  // terminal
  var out = doc.getElementById('term-body');
  if (!out) return;
  var script = [
    ['cmd', 'whoami'],
    ['out', '0xsila  //  Sila Yahia, junior pentester'],
    ['cmd', 'cat certs.txt'],
    ['ok', '[x] eJPT  (INE Security)'],
    ['ok', '[x] CRTA  (CyberWarfare Labs)'],
    ['cmd', 'hackerone --reputation'],
    ['out', '500+ points · responsible disclosure'],
    ['cmd', 'ls ./writeups'],
    ['out', 'idor/  mass-assignment/  response-manipulation/\nbusiness-logic/  nexthunt/  nextrace/'],
    ['cmd', 'cat languages.txt'],
    ['out', 'Arabic, Kabyle (native) · French, English (B2)'],
    ['cmd', 'echo $STATUS'],
    ['ok', 'open to internship · April 2027']
  ];
  function esc(s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;'); }
  function render(upto, partial) {
    var h = '';
    for (var i = 0; i < upto; i++) h += line(script[i], script[i][1]);
    if (partial !== null) h += line(script[upto], partial) + '<span class="caret"></span>';
    else h += '<span class="p">$</span> <span class="caret"></span>';
    out.innerHTML = h;
  }
  function line(l, txt) {
    var t = esc(txt);
    if (l[0] === 'cmd') return '<span class="p">$</span> ' + t + '\n';
    return '<span class="' + (l[0] === 'ok' ? 'g' : 'o') + '">' + t + '</span>\n';
  }
  if (reduce) { render(script.length, null); return; }
  var i = 0, c = 0;
  (function tick() {
    if (i >= script.length) { render(i, null); return; }
    var l = script[i];
    if (l[0] === 'cmd') {
      c++;
      render(i, l[1].slice(0, c));
      if (c >= l[1].length) { i++; c = 0; setTimeout(tick, 280); } else setTimeout(tick, 38);
    } else {
      i++; render(i, null); setTimeout(tick, 160);
    }
  })();
})();
