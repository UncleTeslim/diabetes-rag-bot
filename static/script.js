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
  div.className = `p-2 rounded-md whitespace-pre-wrap max-w-full break-words ${
    role === "user" 
      ? "bg-blue-700 text-white self-end"
      : "bg-gray-700 text-white self-start prose prose-invert prose-sm"
  }`;

  
  if (role === "bot") {
    const renderedText = marked.parse(text); 
    div.innerHTML = renderedText;
  } else {
    div.textContent = text;
  }


  const lists = div.querySelectorAll("ul, ol");
  lists.forEach((list) => {
    // Apply Tailwind's list styles for both ordered and unordered lists
    list.classList.add("list-inside", "ml-4");  
    if (list.tagName === "UL") {
      list.classList.add("list-disc");  
    } else {
      list.classList.add("list-decimal");  
    }
  });

  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}



function removeLastBotPlaceholder() {
  const messages = chat.querySelectorAll(".self-start");
  if (messages.length > 0) {
    chat.removeChild(messages[messages.length - 1]);
  }
}
