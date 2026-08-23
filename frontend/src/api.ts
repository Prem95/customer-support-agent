import type { ChatMessage, ConversationSummary, SidebarUpdate } from "./types";

export async function fetchConversations(): Promise<ConversationSummary[]> {
  const res = await fetch("/api/conversations");
  if (!res.ok) throw new Error(`failed to load conversations: ${res.status}`);
  return res.json();
}

export async function deleteConversation(conversationId: string): Promise<void> {
  const res = await fetch(`/api/conversations/${conversationId}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`failed to delete conversation: ${res.status}`);
}

export async function addKnowledge(title: string, content: string): Promise<void> {
  const res = await fetch("/api/knowledge", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, content }),
  });
  if (!res.ok) throw new Error(`failed to add knowledge: ${res.status}`);
}

export async function fetchMessages(conversationId: string): Promise<ChatMessage[]> {
  const res = await fetch(`/api/conversations/${conversationId}/messages`);
  if (!res.ok) throw new Error(`failed to load messages: ${res.status}`);
  return res.json();
}

export async function fetchSidebar(conversationId: string): Promise<SidebarUpdate> {
  const res = await fetch(`/api/conversations/${conversationId}/sidebar`);
  if (!res.ok) throw new Error(`failed to load sidebar: ${res.status}`);
  return res.json();
}

export function websocketUrl(conversationId: string): string {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  return `${protocol}://${window.location.host}/ws/${conversationId}`;
}
