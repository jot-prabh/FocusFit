// auth.js — handles any client-side auth helpers
// (The actual login/signup logic runs in Flask via form POST)
// This file is a good place to add future client-side validation.

document.addEventListener("DOMContentLoaded", function () {

  // If a signup form exists, check passwords match before submitting
  const signupForm = document.querySelector("form[action='/signup']");
  if (signupForm) {
    signupForm.addEventListener("submit", function (e) {
      const name     = document.getElementById("name").value.trim();
      const email    = document.getElementById("email").value.trim();
      const password = document.getElementById("password").value;

      if (!name || !email || !password) {
        e.preventDefault();
        showAuthError("Please fill in all fields.");
        return;
      }

      if (password.length < 4) {
        e.preventDefault();
        showAuthError("Password must be at least 4 characters.");
      }
    });
  }

  // If a login form exists, basic empty-field check
  const loginForm = document.querySelector("form[action='/login']");
  if (loginForm) {
    loginForm.addEventListener("submit", function (e) {
      const email    = document.getElementById("email").value.trim();
      const password = document.getElementById("password").value;

      if (!email || !password) {
        e.preventDefault();
        showAuthError("Please enter your email and password.");
      }
    });
  }
});

// Show or create an error message on the auth card
function showAuthError(message) {
  let errDiv = document.querySelector(".error-msg");
  if (!errDiv) {
    errDiv = document.createElement("div");
    errDiv.className = "error-msg";
    const card = document.querySelector(".auth-card");
    const h2   = card.querySelector("h2");
    card.insertBefore(errDiv, h2.nextSibling);
  }
  errDiv.textContent = message;
}