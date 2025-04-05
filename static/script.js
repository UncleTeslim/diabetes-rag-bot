const form = document.getElementById("chat-form");
const input = document.getElementById("user-input");
const chat = document.getElementById("chat");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const userMessage = input.value.trim();
  if (!userMessage) return;

  appendMessage("user", userMessage);
  input.value = "";

  appendMessage("bot", "⏳ Thinking...");

  try {
    const res = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: userMessage }),
    });

    const data = await res.json();
    removeLastBotPlaceholder();
    appendMessage("bot", data.answer || "⚠️ No answer.");
  } catch (err) {
    removeLastBotPlaceholder();
    appendMessage("bot", "⚠️ There was an error getting a response.");
  }
});

function appendMessage(role, text) {
  const div = document.createElement("div");
  div.className = `p-2 rounded-md ${
    role === "user" ? "bg-blue-700 text-white self-end" : "bg-gray-700 text-white self-start"
  }`;
  div.textContent = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

function removeLastBotPlaceholder() {
  const messages = chat.querySelectorAll(".self-start");
  if (messages.length > 0) {
    chat.removeChild(messages[messages.length - 1]);
  }
}
