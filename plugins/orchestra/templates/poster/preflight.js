/* Poster preflight: runs on load, marks the DOM for poster_build / poster_preflight.
   Reads placed size of every image (and inline <svg data-raster="...">), flags .box overflow, sets body.dataset.preflight. */
(function () {
  var PX_PER_CM = 37.7953;
  function placed(el) {
    var r = el.getBoundingClientRect();
    el.setAttribute("data-placed-w-cm", (r.width / PX_PER_CM).toFixed(3));
    el.setAttribute("data-placed-h-cm", (r.height / PX_PER_CM).toFixed(3));
  }
  function natural(el, w, h) {
    el.setAttribute("data-natural-w", String(w));
    el.setAttribute("data-natural-h", String(h));
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
      }
      document.body.dataset.preflight = "done";
    }
    var imgs = document.querySelectorAll("img");
    for (var i = 0; i < imgs.length; i++) {
      (function (img) {
        placed(img);
        if (img.complete && img.naturalWidth) {
          natural(img, img.naturalWidth, img.naturalHeight);
        } else {
          pending++;
          var done = function () { natural(img, img.naturalWidth || 0, img.naturalHeight || 0); pending--; finish(); };
          img.addEventListener("load", done);
          img.addEventListener("error", done);
        }
      })(imgs[i]);
    }
    var svgs = document.querySelectorAll("svg[data-raster]");
    for (var j = 0; j < svgs.length; j++) {
      (function (svg) {
        placed(svg);
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
