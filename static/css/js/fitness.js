// fitness.js — rotating exercise suggestions

var exercises = [
  { name: "5-min Stretch",     time: "Perfect for a quick desk break" },
  { name: "10-min Walk",       time: "Step outside for some fresh air" },
  { name: "Desk Yoga",         time: "Gentle seated stretches" },
  { name: "20 Jumping Jacks",  time: "Get the blood flowing!" },
  { name: "Deep Breathing",    time: "4-7-8 technique, 5 cycles" },
  { name: "Eye Rest",          time: "20-20-20 rule – look 20 ft away" },
  { name: "Neck Rolls",        time: "Release tension in 2 minutes" },
  { name: "Wall Push-ups",     time: "10 reps, great for a quick reset" },
];

var currentIndex = 0;

function initFitness() {
  showExercise(0);
}

function showExercise(index) {
  var ex = exercises[index];
  var nameEl = document.getElementById("exercise-name");
  var timeEl = document.getElementById("exercise-time");
  if (nameEl) nameEl.textContent = ex.name;
  if (timeEl) timeEl.textContent = ex.time;
}

function nextExercise() {
  currentIndex = (currentIndex + 1) % exercises.length;
  showExercise(currentIndex);
  alert("New suggestion: " + exercises[currentIndex].name + " 🌿");
}

window.initFitness  = initFitness;
window.nextExercise = nextExercise;