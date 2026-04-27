// tasks.js — study planner card logic

async function loadTasks() {
  try {
    const res  = await fetch("/api/tasks");
    const data = await res.json();
    renderTasks(data.tasks);
  } catch(e) {
    console.error("loadTasks error:", e);
  }
}

async function addTask() {
  const subject  = document.getElementById("task-subject").value.trim();
  const deadline = document.getElementById("task-deadline").value;

  if (!subject)  { alert("Please enter a subject!"); return; }
  if (!deadline) { alert("Please pick a deadline!"); return; }

  try {
    const res  = await fetch("/api/tasks", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ subject, deadline }),
    });
    const data = await res.json();
    renderTasks(data.tasks);
    document.getElementById("task-subject").value  = "";
    document.getElementById("task-deadline").value = "";
    alert("Task added! 📚");
    loadRecommendation();
  } catch(e) {
    console.error("addTask error:", e);
  }
}

async function completeTask(index) {
  try {
    const res  = await fetch("/api/tasks/" + index + "/complete", { method: "POST" });
    const data = await res.json();
    renderTasks(data.tasks);
    alert("Task completed! ✅");
    loadRecommendation();
  } catch(e) {
    console.error("completeTask error:", e);
  }
}

function renderTasks(taskArray) {
  const list = document.getElementById("task-list");
  if (!list) return;
  list.innerHTML = "";

  if (!taskArray || taskArray.length === 0) {
    list.innerHTML = '<li style="font-size:0.85rem;color:var(--text-light);padding:0.5rem 0;">No tasks yet. Add one above!</li>';
    return;
  }

  taskArray.forEach(function(task, i) {
    const li = document.createElement("li");
    li.className = "task-item" + (task.done ? " done" : "");
    li.innerHTML =
      '<span class="task-name">' + task.subject + '</span>' +
      '<span class="task-deadline">' + task.deadline + '</span>' +
      (task.done
        ? '<span style="font-size:0.8rem;color:#7bb877;">✓ Done</span>'
        : '<button class="btn-small" onclick="completeTask(' + i + ')">Done</button>');
    list.appendChild(li);
  });
}

window.loadTasks    = loadTasks;
window.addTask      = addTask;
window.completeTask = completeTask;