// screenTime.js — screen time card logic

let screenChart = null;

function showToast(msg) {
  if (window.showToast && window.showToast !== showToast) { window.showToast(msg); return; }
  const t = document.getElementById("toast");
  if (!t) return;
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 2500);
}

async function loadScreenTime() {
  try {
    const res  = await fetch("/api/screen-time");
    const data = await res.json();
    updateScreenCard(data.log, data.today);
  } catch(e) {
    console.error("loadScreenTime error:", e);
  }
}

async function logScreenTime() {
  const input = document.getElementById("screen-input");
  const mins  = parseInt(input.value);

  if (!input.value || isNaN(mins) || mins < 0) {
    alert("Please enter a valid number of minutes!");
    return;
  }

  try {
    const res  = await fetch("/api/screen-time", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ minutes: mins }),
    });
    const data = await res.json();
        updateScreenCard(data.log, data.today);
    input.value = "";
    alert("Screen time logged! 📱");

    if (typeof loadRecommendation === "function") {
      loadRecommendation();
    }
  } catch(e) {
    console.error("logScreenTime error:", e);
    alert("Something went wrong. Check the console.");
  }
}

function updateScreenCard(log, today) {
  const numEl = document.getElementById("today-minutes");
  if (numEl) numEl.textContent = today;

  const badge = document.getElementById("screen-badge");
  if (badge) {
    if (today > 90) {
      badge.className   = "warning-badge";
      badge.textContent = "⚠️ High usage – take a break!";
    } else if (today > 60) {
      badge.className   = "warning-badge";
      badge.textContent = "🙁 Getting high – slow down";
    } else {
      badge.className   = "ok-badge";
      badge.textContent = "✅ Looking good";
    }
  }

  const labels = log.length ? log.map((_, i) => "Day " + (i + 1)) : ["No data"];
  const values = log.length ? log : [0];

  if (screenChart) {
    screenChart.data.labels            = labels;
    screenChart.data.datasets[0].data  = values;
    screenChart.update();
  } else {
    const canvas = document.getElementById("screenChart");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    screenChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [{
          label:                "Screen Time (mins)",
          data:                 values,
          borderColor:          "#e88fa0",
          backgroundColor:      "rgba(247, 197, 208, 0.25)",
          borderWidth:          2,
          pointRadius:          4,
          pointBackgroundColor: "#e88fa0",
          tension:              0.4,
          fill:                 true,
        }]
      },
      options: {
        responsive:          true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, grid: { color: "#f0e6d6" }, ticks: { font: { size: 11 }, color: "#9a8a8a" } },
          x: { grid: { display: false },                      ticks: { font: { size: 11 }, color: "#9a8a8a" } },
        }
      }
    });
  }
}

window.loadScreenTime = loadScreenTime;
window.logScreenTime  = logScreenTime;