import { useEffect, useRef, useState } from "react";
import type { ChatMessage, Role } from "../types";

interface Props {
  messages: ChatMessage[];
  connected: boolean;
  role: Role;
  typingRole: Role | null;
  onSend: (role: Role, content: string) => void;
  onTyping: (role: Role) => void;
  exportHref?: string;
}

function timeOf(ts?: string | null): string {
  if (!ts) return "";
  return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function ChatWindow({
  messages,
  connected,
  role,
  typingRole,
  onSend,
  onTyping,
  exportHref,
}: Props) {
  const [draft, setDraft] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const otherTyping = typingRole !== null && typingRole !== role;

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, otherTyping]);

  const send = () => {
    if (!draft.trim()) return;
    onSend(role, draft);
    setDraft("");
  };

  return (
    <section className="panel chat">
      <header className="panel-header">
        <h2>Conversation</h2>
        <div className="chat-head-right">
          {exportHref && (
            <a className="btn-mini" href={exportHref} download title="Download conversation with metadata">
              Export
            </a>
          )}
          <span
            className={connected ? "dot dot-on" : "dot dot-off"}
            title={connected ? "connected" : "reconnecting"}
          />
        </div>
      </header>

      <div className="messages" ref={scrollRef}>
        {messages.length === 0 && (
          <p className="empty">
            {role === "agent" ? "Waiting for the customer." : "How can we help?"}
          </p>
        )}
        {messages.map((message, index) => (
          <div
            key={index}
            className={`message ${message.role === role ? "message-own" : "message-other"}`}
          >
            <span className="message-role">{message.role}</span>
            <div className="message-body">{message.content}</div>
            {message.ts && <span className="msg-time">{timeOf(message.ts)}</span>}
          </div>
        ))}
        {otherTyping && (
          <div className="message message-other">
            <span className="message-role">{typingRole}</span>
            <div className="message-body typing-dots" aria-label={`${typingRole} is typing`}>
              <span />
              <span />
              <span />
            </div>
          </div>
        )}
      </div>

      <div className="composer">
        <input
          value={draft}
          onChange={(e) => {
            setDraft(e.target.value);
            if (e.target.value) onTyping(role);
          }}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder={role === "agent" ? "Reply to the customer…" : "Type a message…"}
        />
        <button className="btn" onClick={send} disabled={!draft.trim()}>
          Send
        </button>
      </div>
    </section>
  );
}
