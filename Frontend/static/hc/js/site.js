// HolyCross — small progressive enhancements (no dependencies beyond Bootstrap).
document.addEventListener("DOMContentLoaded", function () {
  // Auto-show Django message toasts.
  document.querySelectorAll(".toast").forEach(function (el) {
    bootstrap.Toast.getOrCreateInstance(el, { delay: 6000 }).show();
  });

  // Animated counters.
  var counters = document.querySelectorAll("[data-count]");
  if ("IntersectionObserver" in window && counters.length) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target, target = parseInt(el.dataset.count, 10), suffix = el.dataset.suffix || "";
        var start = performance.now(), duration = 1200;
        function tick(now) {
          var p = Math.min((now - start) / duration, 1);
          el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3))).toLocaleString() + suffix;
          if (p < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
        observer.unobserve(el);
      });
    }, { threshold: 0.4 });
    counters.forEach(function (el) { observer.observe(el); });
  }

  // Confirm destructive actions.
  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (!window.confirm(form.dataset.confirm)) e.preventDefault();
    });
  });
});
