// Configuration
const API_URL = "http://localhost:8000/ask";

// DOM Elements
const toggleButton = document.getElementById("toggleChat");
const closeButton = document.getElementById("closeChat");
const chatWidget = document.getElementById("chatWidget");
const messagesContainer = document.getElementById("messages");
const questionInput = document.getElementById("questionInput");
const sendButton = document.getElementById("sendButton");
const statusIndicator = document.getElementById("statusIndicator");

// State
let isProcessing = false;

// Event Listeners
toggleButton.addEventListener("click", openWidget);
closeButton.addEventListener("click", closeWidget);
sendButton.addEventListener("click", handleSendQuestion);
questionInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter" && !isProcessing) {
    handleSendQuestion();
  }
});

// Functions
function openWidget() {
  chatWidget.classList.remove("hidden");
  toggleButton.classList.add("hidden");
  questionInput.focus();
}

function closeWidget() {
  chatWidget.classList.add("hidden");
  toggleButton.classList.remove("hidden");
}

async function handleSendQuestion() {
  const question = questionInput.value.trim();

  if (!question || isProcessing) {
    return;
  }

  // Add user message
  addMessage(question, "user");
  questionInput.value = "";

  // Show loading state
  setProcessing(true);

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question }),
    });

    if (!response.ok) {
      throw new Error(`Erreur HTTP: ${response.status}`);
    }

    const data = await response.json();

    // Add bot response
    addMessage(data.answer, "bot", data.sources);
  } catch (error) {
    console.error("Error:", error);
  } finally {
    setProcessing(false);
  }
}

function addMessage(text, type) {
  const messageDiv = document.createElement("div");
  messageDiv.className = `message ${type}-message`;

  const contentDiv = document.createElement("div");
  contentDiv.className = "message-content";
  contentDiv.textContent = text;

  messageDiv.appendChild(contentDiv);

  messagesContainer.appendChild(messageDiv);
  scrollToBottom();
}

function extractPageTitle(url) {
  try {
    const parts = url.split("/").filter(Boolean);
    const lastPart = parts[parts.length - 1];
    return decodeURIComponent(
      lastPart.replace(".html", "").replace(/-|_/g, " ")
    );
  } catch {
    return url;
  }
}

function setProcessing(processing) {
  isProcessing = processing;
  sendButton.disabled = processing;
  questionInput.disabled = processing;

  if (processing) {
    statusIndicator.classList.remove("hidden");
  } else {
    statusIndicator.classList.add("hidden");
    questionInput.focus();
  }
}

function scrollToBottom() {
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Auto-focus on load if widget is open
if (!chatWidget.classList.contains("hidden")) {
  questionInput.focus();
}
