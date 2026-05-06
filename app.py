import os

from flask import Flask, jsonify, render_template_string, request, session

from Chatbot_Ecommerce_Apparel import generate_response, new_state, setup_chatbot


app = Flask(__name__)
app.secret_key = "apparel-support-demo"
chatbot = setup_chatbot()


PAGE_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>EcommerceSupportBot</title>
  <style>
    :root {
      --bg: #1e1e1e;
      --panel: #252526;
      --panel-2: #2d2d30;
      --ink: #d4d4d4;
      --muted: #9da1a6;
      --line: #3c3c3c;
      --user: #0e639c;
      --bot: #333337;
      --input: #1f1f1f;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Consolas, "Courier New", monospace;
      background: var(--bg);
      color: var(--ink);
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 20px;
    }
    .shell {
      width: min(820px, 100%);
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 6px;
      overflow: hidden;
      box-shadow: 0 18px 40px rgba(0, 0, 0, 0.35);
    }
    .topbar {
      padding: 14px 18px;
      border-bottom: 1px solid var(--line);
      background: var(--panel-2);
    }
    h1 {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
    }
    .sub {
      margin-top: 4px;
      color: var(--muted);
      font-size: 13px;
    }
    #messages {
      height: 460px;
      overflow-y: auto;
      padding: 16px;
      display: grid;
      gap: 10px;
      background: var(--bg);
    }
    .row {
      display: grid;
      gap: 4px;
    }
    .label {
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    .bubble {
      max-width: 88%;
      padding: 10px 12px;
      border-radius: 6px;
      line-height: 1.45;
      font-size: 14px;
      border: 1px solid var(--line);
      white-space: pre-wrap;
    }
    .user {
      justify-items: end;
    }
    .user .bubble {
      background: var(--user);
      color: #f5f9ff;
      border-color: #1177bb;
    }
    .bot .bubble {
      background: var(--bot);
      color: var(--ink);
    }
    form {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 12px;
      padding: 14px 16px;
      border-top: 1px solid var(--line);
      background: var(--panel);
    }
    input {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 12px;
      font: inherit;
      color: var(--ink);
      background: var(--input);
    }
    button {
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 12px 16px;
      font: inherit;
      cursor: pointer;
      background: var(--panel-2);
      color: var(--ink);
    }
    .send {
      min-width: 88px;
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="topbar">
      <h1>EcommerceSupportBot</h1>
      <div class="sub">Ask about shirts, hoodies, shipping, returns, and order status. *VS code themed.</div>
    </section>
    <section id="messages">
      <div class="row bot">
        <div class="label">Bot</div>
        <div class="bubble">Hi there! How can I assist you with our apparel store today?</div>
      </div>
    </section>
    <form id="chat-form">
      <input id="message-input" name="message" placeholder="Try: do you have a black shirt in medium" autocomplete="off">
      <button class="send" type="submit">Send</button>
    </form>
  </main>
  <script>
    const form = document.getElementById("chat-form");
    const input = document.getElementById("message-input");
    const messages = document.getElementById("messages");

    function addMessage(role, text) {
      const row = document.createElement("div");
      row.className = "row " + role;

      const label = document.createElement("div");
      label.className = "label";
      label.textContent = role === "user" ? "You" : "Bot";

      const bubble = document.createElement("div");
      bubble.className = "bubble";
      bubble.textContent = text;

      row.appendChild(label);
      row.appendChild(bubble);
      messages.appendChild(row);
      messages.scrollTop = messages.scrollHeight;
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const message = input.value.trim();
      if (!message) return;

      addMessage("user", message);
      input.value = "";

      const response = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message })
      });

      const data = await response.json();
      addMessage("bot", data.reply);
    });
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(PAGE_HTML)


@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.get_json(force=True).get("message", "").strip()
    if not user_input:
        return jsonify({"reply": "Please type a message."})

    state = session.get("chat_state", new_state())
    reply = generate_response(user_input, chatbot, state)
    session["chat_state"] = state
    return jsonify({"reply": reply})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
