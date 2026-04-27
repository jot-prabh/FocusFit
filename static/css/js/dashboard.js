// dashboard.js — loads LAST, initializes all modules

// ── Toast (defined here, used everywhere via window.showToast) ───────────
window.showToast = function(message) {
  const toast = document.getElementById("toast");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2500);
};

// ── Start everything once the page HTML is ready ─────────────────────────
document.addEventListener("DOMContentLoaded", function () {
  loadScreenTime();
  loadTasks();
  initFitness();
  loadRecommendation();
});