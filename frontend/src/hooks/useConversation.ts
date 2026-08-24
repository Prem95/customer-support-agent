import { useCallback, useEffect, useRef, useState } from "react";
import { fetchMessages, fetchSidebar, websocketUrl } from "../api";
import type { ChatMessage, Role, ServerEvent, SidebarUpdate } from "../types";
import { EMPTY_SIDEBAR } from "../types";

export interface ConversationState {
  connected: boolean;
  messages: ChatMessage[];
  sidebar: SidebarUpdate;
  activeStage: string | null;
  doneStages: string[];
  running: boolean;
  error: string | null;
  typingRole: Role | null;
  sendMessage: (role: Role, content: string) => void;
  sendTyping: (role: Role) => void;
}

const TYPING_THROTTLE_MS = 1500;
const TYPING_VISIBLE_MS = 3000;

export function useConversation(conversationId: string): ConversationState {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sidebar, setSidebar] = useState<SidebarUpdate>(EMPTY_SIDEBAR);
  const [activeStage, setActiveStage] = useState<string | null>(null);
  const [doneStages, setDoneStages] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [typingRole, setTypingRole] = useState<Role | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const typingTimer = useRef<number | undefined>(undefined);
  const lastTypingSent = useRef(0);

  useEffect(() => {
    let disposed = false;
    let socket: WebSocket;
    let retryTimer: number | undefined;

    // restore server-side state on load/refresh
    Promise.all([fetchMessages(conversationId), fetchSidebar(conversationId)])
      .then(([storedMessages, storedSidebar]) => {
        if (disposed) return;
        setMessages((prev) => (prev.length ? prev : storedMessages));
        setSidebar(storedSidebar);
      })
      .catch(() => undefined);

    const connect = () => {
      socket = new WebSocket(websocketUrl(conversationId));
      socketRef.current = socket;

      socket.onopen = () => setConnected(true);
      socket.onclose = () => {
        setConnected(false);
        if (!disposed) retryTimer = window.setTimeout(connect, 2000);
      };
      socket.onmessage = (raw) => {
        const event: ServerEvent = JSON.parse(raw.data);
        switch (event.type) {
          case "message":
            setMessages((prev) => [...prev, event.message]);
            setTypingRole((prev) => (prev === event.message.role ? null : prev));
            if (event.message.role === "customer") {
              setDoneStages([]);
              setRunning(true);
            }
            break;
          case "typing":
            setTypingRole(event.role);
            window.clearTimeout(typingTimer.current);
            typingTimer.current = window.setTimeout(() => setTypingRole(null), TYPING_VISIBLE_MS);
            break;
          case "workflow_stage":
            setActiveStage(event.stage);
            setDoneStages((prev) => (prev.includes(event.stage) ? prev : [...prev, event.stage]));
            setError(null);
            break;
          case "workflow_update":
            setSidebar(event.sidebar);
            setActiveStage(null);
            setRunning(false);
            break;
          case "error":
            setError(event.detail);
            setActiveStage(null);
            setRunning(false);
            break;
        }
      };
    };

    connect();
    return () => {
      disposed = true;
      window.clearTimeout(retryTimer);
      window.clearTimeout(typingTimer.current);
      socket.close();
    };
  }, [conversationId]);

  const sendMessage = useCallback((role: Role, content: string) => {
    const trimmed = content.trim();
    const socket = socketRef.current;
    if (!trimmed || !socket || socket.readyState !== WebSocket.OPEN) return;
    socket.send(JSON.stringify({ type: "message", message: { role, content: trimmed } }));
  }, []);

  const sendTyping = useCallback((role: Role) => {
    const socket = socketRef.current;
    const now = Date.now();
    if (!socket || socket.readyState !== WebSocket.OPEN) return;
    if (now - lastTypingSent.current < TYPING_THROTTLE_MS) return;
    lastTypingSent.current = now;
    socket.send(JSON.stringify({ type: "typing", role }));
  }, []);

  return {
    connected,
    messages,
    sidebar,
    activeStage,
    doneStages,
    running,
    error,
    typingRole,
    sendMessage,
    sendTyping,
  };
}
