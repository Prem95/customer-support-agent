import { useEffect, useState } from "react";
import "./App.css";
import { deleteConversation, fetchConversations } from "./api";
import { ChatWindow } from "./components/ChatWindow";
import { Sidebar } from "./components/Sidebar";
import { useConversation } from "./hooks/useConversation";
import type { ConversationSummary, Role } from "./types";

function newConversationId(): string {
  // crypto.randomUUID is unavailable in non-HTTPS contexts (the demo ALB is plain HTTP)
  const id = crypto.randomUUID?.().slice(0, 8) ?? Math.random().toString(36).slice(2, 10);
  return `conv-${id}`;
}

const params = new URLSearchParams(window.location.search);
const viewerRole: Role = params.get("role") === "customer" ? "customer" : "agent";
const initialConversationId = params.get("conversation") ?? newConversationId();

interface AgentViewProps {
  conversationId: string;
  conversations: ConversationSummary[];
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
}

function AgentView({ conversationId, conversations, onSelect, onDelete }: AgentViewProps) {
  const { connected, messages, sidebar, activeStage, error, typingRole, sendMessage, sendTyping } =
    useConversation(conversationId);
  const [sentSuggestion, setSentSuggestion] = useState<string | null>(null);

  return (
    <main className="app-body">
      <Sidebar
        conversations={conversations}
        activeId={conversationId}
        onSelect={onSelect}
        onDelete={onDelete}
        sidebar={sidebar}
        activeStage={activeStage}
        error={error}
        suggestionSent={sentSuggestion === sidebar.suggested_response}
        onSendSuggestion={() => {
          sendMessage("agent", sidebar.suggested_response);
          setSentSuggestion(sidebar.suggested_response);
        }}
      />
      <ChatWindow
        messages={messages}
        connected={connected}
        role="agent"
        typingRole={typingRole}
        onSend={sendMessage}
        onTyping={sendTyping}
        exportHref={`/api/conversations/${conversationId}/export`}
      />
    </main>
  );
}

function CustomerView({ conversationId }: { conversationId: string }) {
  const { connected, messages, typingRole, sendMessage, sendTyping } =
    useConversation(conversationId);

  return (
    <main className="app-body single">
      <ChatWindow
        messages={messages}
        connected={connected}
        role="customer"
        typingRole={typingRole}
        onSend={sendMessage}
        onTyping={sendTyping}
      />
    </main>
  );
}

export default function App() {
  const [conversationId, setConversationId] = useState(initialConversationId);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);

  useEffect(() => {
    const query = new URLSearchParams({ conversation: conversationId });
    if (viewerRole === "customer") query.set("role", "customer");
    window.history.replaceState(null, "", `?${query}`);
  }, [conversationId]);

  useEffect(() => {
    if (viewerRole === "customer") return;
    const load = () => fetchConversations().then(setConversations).catch(() => undefined);
    load();
    const timer = window.setInterval(load, 4000);
    return () => window.clearInterval(timer);
  }, []);

  const removeConversation = async (id: string) => {
    await deleteConversation(id).catch(() => undefined);
    setConversations((prev) => prev.filter((c) => c.conversation_id !== id));
    if (id === conversationId) setConversationId(newConversationId());
  };

  const openCustomerView = () => {
    window.open(`?conversation=${conversationId}&role=customer`, "_blank", "noopener");
  };

  if (viewerRole === "customer") {
    return (
      <div className="app">
        <header className="app-header">
          <h1>Support Chat</h1>
        </header>
        <CustomerView key={conversationId} conversationId={conversationId} />
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Support Console</h1>
        <div className="header-right">
          <button className="btn-ghost" onClick={openCustomerView}>
            Open customer chat
          </button>
          <button className="btn-ghost" onClick={() => setConversationId(newConversationId())}>
            New conversation
          </button>
        </div>
      </header>
      <AgentView
        key={conversationId}
        conversationId={conversationId}
        conversations={conversations}
        onSelect={setConversationId}
        onDelete={removeConversation}
      />
    </div>
  );
}
