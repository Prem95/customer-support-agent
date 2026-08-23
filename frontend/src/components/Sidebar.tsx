import { useRef, useState } from "react";
import { addKnowledge } from "../api";
import type { ConversationSummary, SidebarUpdate } from "../types";

const STAGE_LABELS: Record<string, string> = {
  analyze_intent: "Analyzing intent",
  retrieve_knowledge: "Searching knowledge",
  generate_recommendations: "Drafting recommendations",
  update_summary: "Updating summary",
  handle_failure: "Recovering",
};

interface Props {
  conversations: ConversationSummary[];
  activeId: string;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  sidebar: SidebarUpdate;
  activeStage: string | null;
  error: string | null;
  onSendSuggestion: () => void;
  suggestionSent: boolean;
}

export function Sidebar({
  conversations,
  activeId,
  onSelect,
  onDelete,
  sidebar,
  activeStage,
  error,
  onSendSuggestion,
  suggestionSent,
}: Props) {
  const confidence = Math.round(sidebar.intent_confidence * 100);
  const fileRef = useRef<HTMLInputElement>(null);
  const [uploadNote, setUploadNote] = useState("");

  const onFilePicked = async (file: File | undefined) => {
    if (!file) return;
    try {
      const content = await file.text();
      await addKnowledge(file.name.replace(/\.(md|txt)$/i, ""), content);
      setUploadNote(`Added ${file.name}`);
    } catch {
      setUploadNote("Upload failed");
    }
    setTimeout(() => setUploadNote(""), 2500);
  };

  return (
    <aside className="panel side">
      <div className="conversations">
        <h3 className="side-label">Conversations</h3>
        <ul>
          {conversations.map((c) => (
            <li key={c.conversation_id} className="conv-row">
              <button
                className={c.conversation_id === activeId ? "conv active" : "conv"}
                onClick={() => onSelect(c.conversation_id)}
              >
                {c.label ?? c.conversation_id}
              </button>
              <button
                className="conv-delete"
                title="Delete conversation"
                onClick={() => onDelete(c.conversation_id)}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      </div>

      <header className="panel-header">
        <h2>Assistant</h2>
        {activeStage && <span className="stage">{STAGE_LABELS[activeStage] ?? activeStage}…</span>}
      </header>

      <div className="sections">
        {error && <p className="notice">{error}</p>}
        {sidebar.degraded && <p className="notice">Degraded, showing partial assistance.</p>}

        <section>
          <h3>Intent</h3>
          <p className="intent">
            {sidebar.intent.replaceAll("_", " ")}
            {confidence > 0 && <span className="confidence"> · {confidence}%</span>}
          </p>
          {sidebar.reasoning && <p className="muted">{sidebar.reasoning}</p>}
        </section>

        <section>
          <div className="section-head">
            <h3>Suggested response</h3>
            {sidebar.suggested_response && !sidebar.degraded && (
              <button className="btn-mini" onClick={onSendSuggestion} disabled={suggestionSent}>
                {suggestionSent ? "Sent" : "Send reply"}
              </button>
            )}
          </div>
          {sidebar.suggested_response ? (
            <p className="draft">{sidebar.suggested_response}</p>
          ) : (
            <p className="empty">Waiting for customer messages.</p>
          )}
        </section>

        <section>
          <div className="section-head">
            <h3>Knowledge</h3>
            <button
              className="btn-mini"
              title="Add a document to the knowledge base"
              onClick={() => fileRef.current?.click()}
            >
              +
            </button>
            <input
              ref={fileRef}
              type="file"
              accept=".md,.txt"
              hidden
              onChange={(e) => {
                onFilePicked(e.target.files?.[0]);
                e.target.value = "";
              }}
            />
          </div>
          {uploadNote && <p className="muted">{uploadNote}</p>}
          {sidebar.knowledge.length === 0 ? (
            <p className="empty">Nothing retrieved.</p>
          ) : (
            <ul className="knowledge">
              {sidebar.knowledge.map((ref) => (
                <li key={ref.doc_id}>
                  <details>
                    <summary>{ref.title}</summary>
                    <p className="muted">{ref.snippet}…</p>
                  </details>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section>
          <h3>Required information / documents</h3>
          {sidebar.missing_info.length === 0 ? (
            <p className="empty">Nothing flagged.</p>
          ) : (
            <ul className="plain">
              {sidebar.missing_info.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          )}
        </section>

        <section>
          <h3>Next action</h3>
          {sidebar.next_action ? <p>{sidebar.next_action}</p> : <p className="empty">None yet.</p>}
        </section>

        <section>
          <h3>Summary</h3>
          {sidebar.summary ? <p className="muted">{sidebar.summary}</p> : <p className="empty">None yet.</p>}
        </section>
      </div>
    </aside>
  );
}
