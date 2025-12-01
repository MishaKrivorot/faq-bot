/* ---------------- ЗОРІ ---------------- */
const svg = document.getElementById("stars");
function drawStars() {
  let html = "";
  for (let i = 0; i < 300; i++) {
    const x = Math.random() * 100;
    const y = Math.random() * 100;
    const r = Math.random() * 1.5;

    html += `<circle cx="${x}%" cy="${y}%" r="${r}" 
      fill="${document.body.classList.contains("dark") ? "white" : "black"}" 
      opacity="0.8"></circle>`;
  }
  svg.innerHTML = html;
}
drawStars();

/* ---------------- ТЕМА ---------------- */
document.getElementById("themeIcon").onclick = () => {
  document.body.classList.toggle("dark");
  document.body.classList.toggle("light");
  drawStars();
  document.getElementById("themeIcon").textContent =
    document.body.classList.contains("dark") ? "🌙" : "☀️";
};

/* ---------------- ВИПАДКОВІ КОМЕТИ ---------------- */
function spawnComet() {
  const comet = document.createElement("div");
  comet.className = "comet";

  comet.style.left = (-20 - Math.random() * 30) + "%";
  comet.style.top = (-20 - Math.random() * 40) + "%";
  comet.style.animationDuration = (4 + Math.random() * 4) + "s";
  comet.style.animationDelay = (Math.random() * 2) + "s";

  document.body.appendChild(comet);

  setTimeout(() => comet.remove(), 8000);
}

setInterval(spawnComet, 2500);

/* ---------------- КОРАБЛІ ---------------- */
const ships = [
  document.getElementById("ship1"),
  document.getElementById("ship2")
];

let currentShip = 0;

function cycleShips() {
  ships.forEach(s => s.style.display = "none");

  const ship = ships[currentShip];
  ship.style.display = "block";
  ship.style.top = (10 + Math.random() * 70) + "%";
  ship.style.animationDuration = (18 + Math.random() * 25) + "s";

  currentShip = (currentShip + 1) % ships.length;
}

setInterval(cycleShips, 12000);
cycleShips();

/* ---------------- ЧАТ ---------------- */
const apiUrl = "https://faq-bot-37go.onrender.com/chat/";
const messagesEl = document.getElementById("messages");
const qInput = document.getElementById("q");

function addMessage(text, who = "bot") {
  const div = document.createElement("div");
  div.className = "msg " + who;
  div.innerHTML = text;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

async function sendQuestion() {
  const q = qInput.value.trim();
  if (!q) return;

  addMessage(q, "user");
  qInput.value = "";
  addMessage("Працюю...");

  try {
    const resp = await fetch(apiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q })
    });

    const data = await resp.json();
    messagesEl.lastChild.remove();
    addMessage(data.reply, "bot");

  } catch (err) {
    messagesEl.lastChild.remove();
    addMessage("Помилка з'єднання з сервером.");
  }
}

document.getElementById("send").addEventListener("click", sendQuestion);

document.getElementById("chatForm").addEventListener("submit", function(e){
    e.preventDefault();      // ← блокуємо оновлення
    sendQuestion();
});


addMessage("Привіт! Я чат-бот. Став запитання щодо вступу чи навчання.");
