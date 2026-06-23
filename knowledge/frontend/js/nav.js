/**
 * 侧边栏导航 — 滚动高亮 + 平滑滚动
 */
(function() {
  'use strict';

  const navLinks = document.querySelectorAll('.sidebar-nav a');
  const headings = [];
  document.querySelectorAll('h2[id], h3[id]').forEach(function(h) { headings.push(h); });

  window.addEventListener('scroll', function() {
    var current = '';
    headings.forEach(function(h) {
      if (window.scrollY >= h.offsetTop - 120) current = h.id;
    });
    navLinks.forEach(function(a) {
      a.classList.toggle('active', a.getAttribute('href') === '#' + current);
    });
  });

  navLinks.forEach(function(a) {
    a.addEventListener('click', function(e) {
      e.preventDefault();
      var target = document.querySelector(a.getAttribute('href'));
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
})();
