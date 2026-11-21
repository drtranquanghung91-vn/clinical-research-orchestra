/* Poster preflight: runs on load, marks the DOM for poster_build / poster_preflight.
   - every img and inline <svg data-raster>: natural size, and the DRAWN (contained) size in cm (data-placed-w-cm / -h-cm);
   - every .box: an attribute data-overflow set to 1 when its content is cut off, data-box-w-cm / data-box-h-cm,
     data-font-pt (the smallest computed font size of any text in it, in pt; inline <svg> text is skipped);
   - every .col: data-fill = content height / available height;
   - document.body.dataset.preflight = "done". */
(function () {
  var PX_PER_CM = 37.7953;
  function contained(boxW, boxH, w, h) {
    // size of a w x h picture drawn "contain" (meet) inside boxW x boxH
    if (!(w > 0) || !(h > 0)) { return [boxW, boxH]; }
    var s = Math.min(boxW / w, boxH / h);
    return [w * s, h * s];
  }
  function placed(el, w, h) {
    var r = el.getBoundingClientRect();
    var d = contained(r.width, r.height, w, h);
    el.setAttribute("data-placed-w-cm", (d[0] / PX_PER_CM).toFixed(3));
    el.setAttribute("data-placed-h-cm", (d[1] / PX_PER_CM).toFixed(3));
  }
  function natural(el, w, h) {
    el.setAttribute("data-natural-w", String(w));
    el.setAttribute("data-natural-h", String(h));
  }
  function svgAspect(svg) {
    var vb = svg.viewBox && svg.viewBox.baseVal;
    if (vb && vb.width > 0 && vb.height > 0) { return [vb.width, vb.height]; }
    var r = svg.getBoundingClientRect();
    return [r.width, r.height];
  }
  function minFontPt(root) {
    var min = Infinity;
    var all = [root].concat(Array.prototype.slice.call(root.querySelectorAll("*")));
    for (var i = 0; i < all.length; i++) {
      var el = all[i];
      if (el.closest && el.closest("svg")) { continue; }
      var has = false;
      for (var n = el.firstChild; n; n = n.nextSibling) {
        if (n.nodeType === 3 && /\S/.test(n.nodeValue)) { has = true; break; }
      }
      if (!has) { continue; }
      var px = parseFloat(window.getComputedStyle(el).fontSize);
      if (px > 0 && px * 0.75 < min) { min = px * 0.75; }
    }
    return min === Infinity ? null : min;
  }
  function run() {
    var pending = 0;
    function finish() {
      if (pending > 0) { return; }
      var boxes = document.querySelectorAll(".box");
      for (var i = 0; i < boxes.length; i++) {
        var b = boxes[i];
        if (b.scrollHeight > b.clientHeight + 1 || b.scrollWidth > b.clientWidth + 1) {
          b.setAttribute("data-overflow", "1");
        }
        var fpt = minFontPt(b);
        if (fpt !== null) { b.setAttribute("data-font-pt", fpt.toFixed(2)); }
        b.setAttribute("data-box-w-cm", (b.clientWidth / PX_PER_CM).toFixed(3));
        b.setAttribute("data-box-h-cm", (b.clientHeight / PX_PER_CM).toFixed(3));
      }
      var cols = document.querySelectorAll(".col");
      for (var c = 0; c < cols.length; c++) {
        var col = cols[c];
        var top = col.getBoundingClientRect().top;
        var bottom = top;
        for (var k = 0; k < col.children.length; k++) {
          var rb = col.children[k].getBoundingClientRect().bottom;
          if (rb > bottom) { bottom = rb; }
        }
        col.setAttribute("data-fill", col.clientHeight > 0 ? ((bottom - top) / col.clientHeight).toFixed(3) : "0");
      }
      document.body.dataset.preflight = "done";
    }
    var imgs = document.querySelectorAll("img");
    for (var i = 0; i < imgs.length; i++) {
      (function (img) {
        var ready = function () {
          natural(img, img.naturalWidth || 0, img.naturalHeight || 0);
          placed(img, img.naturalWidth, img.naturalHeight);
        };
        if (img.complete && img.naturalWidth) {
          ready();
        } else {
          pending++;
          var done = function () { ready(); pending--; finish(); };
          img.addEventListener("load", done);
          img.addEventListener("error", done);
        }
      })(imgs[i]);
    }
    var svgs = document.querySelectorAll("svg[data-raster]");
    for (var j = 0; j < svgs.length; j++) {
      (function (svg) {
        var a = svgAspect(svg);
        placed(svg, a[0], a[1]);
        pending++;
        var probe = new Image();
        var done = function () { natural(svg, probe.naturalWidth || 0, probe.naturalHeight || 0); pending--; finish(); };
        probe.onload = done;
        probe.onerror = done;
        probe.src = svg.getAttribute("data-raster");
      })(svgs[j]);
    }
    finish();
  }
  if (document.readyState === "complete") { run(); } else { window.addEventListener("load", run); }
})();
