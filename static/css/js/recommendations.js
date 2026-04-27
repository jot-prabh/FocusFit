// recommendations.js — fetches smart recommendation from Flask

async function loadRecommendation() {
  try {
    const res  = await fetch("/api/recommendation");
    const data = await res.json();
    const box  = document.getElementById("recommendation-text");
    if (box) box.textContent = data.recommendation;
  } catch(e) {
    console.error("loadRecommendation error:", e);
  }
}

window.loadRecommendation = loadRecommendation;