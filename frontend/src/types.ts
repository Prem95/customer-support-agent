export type Role = "customer" | "agent";

export interface ChatMessage {
  role: Role;
  content: string;
  ts?: string | null;
}

export interface KnowledgeRef {
  doc_id: string;
  title: string;
  snippet: string;
  score: number;
}

export interface SidebarUpdate {
  intent: string;
  intent_confidence: number;
  reasoning: string;
  suggested_response: string;
  knowledge: KnowledgeRef[];
  missing_info: string[];
  next_action: string;
  summary: string;
  degraded: boolean;
}

export interface ConversationSummary {
  conversation_id: string;
  label: string | null;
}

export type ServerEvent =
  | { type: "message"; message: ChatMessage }
  | { type: "typing"; role: Role }
  | { type: "workflow_stage"; stage: string }
  | { type: "workflow_update"; sidebar: SidebarUpdate }
  | { type: "error"; detail: string };

export const EMPTY_SIDEBAR: SidebarUpdate = {
  intent: "unknown",
  intent_confidence: 0,
  reasoning: "",
  suggested_response: "",
  knowledge: [],
  missing_info: [],
  next_action: "",
  summary: "",
  degraded: false,
};
