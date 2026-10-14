// site.js — the small client of a GAKS site: sort a table, filter its rows,
// and search the corpus. A plain script, so it runs from file://.
(function () {
  'use strict';

  function cellValue(row, i) {
    var c = row.cells[i];
    if (!c) return '';
    return c.hasAttribute('data-sort') ? c.getAttribute('data-sort') : c.textContent.trim();
  }

  function sortable(table) {
    var heads = table.tHead ? table.tHead.rows[0].cells : [];
    Array.prototype.forEach.call(heads, function (th, i) {
      th.tabIndex = 0;
      th.title = 'Sort by this column';
      function go() {
        var asc = th.getAttribute('aria-sort') !== 'ascending';
        Array.prototype.forEach.call(heads, function (h) { h.removeAttribute('aria-sort'); });
        th.setAttribute('aria-sort', asc ? 'ascending' : 'descending');
        var body = table.tBodies[0];
        var rows = Array.prototype.slice.call(body.rows);
        rows.sort(function (a, b) {
          var x = cellValue(a, i), y = cellValue(b, i);
          var nx = parseFloat(x), ny = parseFloat(y);
          var r = (!isNaN(nx) && !isNaN(ny) && String(nx) === x && String(ny) === y) ? nx - ny : x.localeCompare(y);
          return asc ? r : -r;
        });
        rows.forEach(function (r) { body.appendChild(r); });
      }
      th.addEventListener('click', go);
      th.addEventListener('keydown', function (e) { if (e.key === 'Enter') go(); });
    });
  }

  function filters(box) {
    var wrap = box.nextElementSibling;
    var table = wrap && wrap.querySelector('table');
    if (!table) return;
    var text = box.querySelector('[data-filter]');
    var state = box.querySelector('[data-filter-state]');
    var count = box.querySelector('[data-filter-count]');
    function apply() {
      var q = text ? text.value.toLowerCase().trim() : '';
      var s = state ? state.value : '';
      var n = 0;
      Array.prototype.forEach.call(table.tBodies[0].rows, function (r) {
        var ok = (!q || r.textContent.toLowerCase().indexOf(q) >= 0) && (!s || r.getAttribute('data-state') === s);
        r.hidden = !ok;
        if (ok) n++;
      });
      if (count) count.textContent = n + ' rows';
    }
    if (text) text.addEventListener('input', apply);
    if (state) state.addEventListener('change', apply);
  }

  function search() {
    var input = document.getElementById('search-q');
    var out = document.getElementById('search-results');
    var index = window.GAKS_SEARCH;
    if (!input || !out || !index) return;
    var lower = index.map(function (d) {
      return { t: d.t.toLowerCase(), i: d.i.toLowerCase(), x: d.x.toLowerCase() };
    });
    function snippet(text, at) {
      var a = Math.max(0, at - 60);
      return (a > 0 ? '…' : '') + text.slice(a, at + 120) + (at + 120 < text.length ? '…' : '');
    }
    function run() {
      var q = input.value.toLowerCase().trim();
      out.textContent = '';
      if (q.length < 2) return;
      var terms = q.split(/\s+/);
      var hits = [];
      for (var k = 0; k < index.length; k++) {
        var L = lower[k], score = 0, ok = true;
        for (var j = 0; j < terms.length; j++) {
          var t = terms[j];
          var inT = L.t.indexOf(t) >= 0, inI = L.i.indexOf(t) >= 0, inX = L.x.indexOf(t) >= 0;
          if (!inT && !inI && !inX) { ok = false; break; }
          score += (inT ? 10 : 0) + (inI ? 6 : 0) + (inX ? 1 : 0);
        }
        if (ok && terms.length > 1) score += (L.t.indexOf(q) >= 0 ? 20 : 0) + (L.x.indexOf(q) >= 0 ? 3 : 0);
        if (ok) hits.push({ k: k, score: score });
      }
      hits.sort(function (a, b) { return b.score - a.score || index[a.k].t.localeCompare(index[b.k].t); });
      var head = document.createElement('p');
      head.className = 'muted';
      head.textContent = hits.length + (hits.length === 1 ? ' page' : ' pages') + (hits.length > 50 ? ', the first 50 shown' : '');
      out.appendChild(head);
      var ul = document.createElement('ul');
      hits.slice(0, 50).forEach(function (h) {
        var d = index[h.k];
        var li = document.createElement('li');
        var a = document.createElement('a');
        a.href = d.h;
        a.textContent = d.t;
        li.appendChild(a);
        var id = document.createElement('span');
        id.className = 'muted';
        id.textContent = ' ' + d.i;
        li.appendChild(id);
        if (d.s) {
          var b = document.createElement('span');
          b.className = 'badge state-' + d.s;
          b.textContent = d.s;
          li.appendChild(document.createTextNode(' '));
          li.appendChild(b);
        }
        var at = lower[h.k].x.indexOf(terms[0]);
        if (at >= 0) {
          var p = document.createElement('div');
          p.className = 'snippet';
          p.textContent = snippet(d.x, at);
          li.appendChild(p);
        }
        ul.appendChild(li);
      });
      out.appendChild(ul);
    }
    input.addEventListener('input', run);
    var q = new URLSearchParams(window.location.search).get('q');
    if (q) { input.value = q; run(); }
    var top = document.querySelector('.topsearch input');
    if (top && q) top.value = q;
  }

  document.addEventListener('DOMContentLoaded', function () {
    Array.prototype.forEach.call(document.querySelectorAll('table.sortable'), sortable);
    Array.prototype.forEach.call(document.querySelectorAll('.filters'), filters);
    search();
  });
})();
