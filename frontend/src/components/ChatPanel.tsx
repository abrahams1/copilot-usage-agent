import { useState, useRef, useEffect } from "react";
import { streamChat } from "../api/client";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send() {
    const text = input.trim();
    if (!text || streaming) return;
    setInput("");

    const userMsg: Message = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setStreaming(true);

    const assistantMsg: Message = { role: "assistant", content: "" };
    setMessages((prev) => [...prev, assistantMsg]);

    try {
      for await (const chunk of streamChat(text)) {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          updated[updated.length - 1] = { ...last, content: last.content + chunk };
          return updated;
        });
      }
    } catch (e) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: `Error: ${e instanceof Error ? e.message : "Unknown error"}`,
        };
        return updated;
      });
    } finally {
      setStreaming(false);
    }
  }

  return (
    <div className="chat-panel">
      <h3>Ask the Agent</h3>
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            Ask about M365 Copilot usage, Azure AI costs, or Copilot Studio messages.
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`chat-msg chat-msg-${m.role}`}>
            <span className="chat-role">{m.role === "user" ? "You" : "Agent"}</span>
            <span className="chat-text">{m.content}</span>
          </div>
        ))}
        {streaming && <div className="chat-typing">Agent is thinking...</div>}
        <div ref={bottomRef} />
      </div>
      <form
        className="chat-input-row"
        onSubmit={(e) => {
          e.preventDefault();
          send();
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="e.g. Which app has the most Copilot prompts?"
          disabled={streaming}
        />
        <button type="submit" disabled={streaming || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
