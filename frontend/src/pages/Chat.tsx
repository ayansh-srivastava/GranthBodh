import { useRef, useState, useEffect, type ChangeEvent, type FormEvent } from "react";
import {
  Power,
  ArrowUp,
  BotMessageSquare,
  BookOpen,
  FileText,
  Plus,
} from "lucide-react";

import "./Chat.css";
import { clearSession } from "../utils.ts";
import { getDocuments, getConversations, getMessages, getAnswer, uploadDocument } from "../api.ts";
import type { MessageItem } from "../types.ts";

interface DocumentItem {
  id: string;
  filename: string;
}

interface ConversationItem {
  id: string;
  title: string;
  created_at: string;
}

export default function Chat() {

  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [documentsPage, setDocumentsPage] = useState<number>(1);
  const [totalDocuments, setTotalDocuments] = useState<number>(0);

  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [conversationsPage, setConversationsPage] = useState<number>(1);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);

  const [message, setMessage] = useState("");

  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [messagesPage, setMessagesPage] = useState<number>(1);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;

    if (!files || files.length === 0) {
      return;
    }

    uploadDocument(files[0])
      .then((response) => {
        setDocuments((prevDocuments) => [
          ...prevDocuments,
          { id: response.id, filename: response.filename },
        ]);
        setTotalDocuments((prevTotal) => prevTotal + 1);
      })
      .catch((error) => {
        console.error("Error uploading document:", error);
      });

    e.target.value = "";
  };

  const sendMessage = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    const trimmed = message.trim();

    if (!trimmed) return;
    setMessage("");
    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: trimmed,
        created_at: new Date().toISOString(),
        conversation_id: activeConversationId || "",
        id: Math.random().toString(36).substring(2, 15),
        user_id: "user-id-placeholder",
      },
    ]);
    const response = await getAnswer(trimmed, activeConversationId);
    if (!activeConversationId) {
      setConversations((prev) => [
        {
          id: response.conversation_id,
          title: trimmed.slice(0, 30) + (trimmed.length > 30 ? "..." : ""),
          created_at: new Date().toISOString(),
        },
        ...prev
      ]);
      setActiveConversationId(response.conversation_id);
    }

    setMessages((prev) => [
      ...prev,
      response.answer,
    ]);

  };

  const logout = () => {
    localStorage.removeItem("authenticated");
    clearSession();
    window.location.href = "/";
  };

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const response = await getDocuments(documentsPage);
        setDocuments((prevDocuments) => [
          ...prevDocuments,
          ...response.documents,
        ]);
        setTotalDocuments(response.total_count);
      } catch (error) {
        console.error("Error fetching documents:", error);
      }
    };
    fetchDocuments();
  }, [documentsPage]);

  const loadMoreDocuments = () => {
    if (documents.length < totalDocuments) {
      setDocumentsPage((prevPage) => prevPage + 1);
    }
  };

  useEffect(() => {
    const fetchConversations = async () => {
      try {
        const response = await getConversations(conversationsPage);
        setConversations((prevConversations) => [
          ...prevConversations,
          ...response.conversations,
        ]);
      } catch (error) {
        console.error("Error fetching conversations:", error);
      }
    };
    fetchConversations();
  }, [conversationsPage]);

  const loadMoreConversations = () => {
    setConversationsPage((prevPage) => prevPage + 1);
  };

  const newConversation = () => {
    setActiveConversationId(null);
    setMessages([]);
    setMessagesPage(1);
  };

  const fetchMessages = async (conversationId: string, page: number = 1) => {
    try {
      console.log("Fetching messages for conversation:", conversationId, "page:", page);
      const response = await getMessages(conversationId, page);
      setMessages((prevMessages) => [...prevMessages, ...response.messages]);
    } catch (error) {
      console.error("Error fetching messages:", error);
    }
  };

  const loadMoreMessages = () => {
    if (activeConversationId) {
      const nextPage = messagesPage + 1;

      setMessagesPage(nextPage);
      fetchMessages(activeConversationId, nextPage);
    }
  }

  useEffect(() => {

    const loadMessages = async () => {
      if (activeConversationId) {
        setMessages([]);
        setMessagesPage(1);
        await fetchMessages(activeConversationId);
      }
    };

    loadMessages();
}, [activeConversationId]);

  const setConversation = async (conversationId: string) => {
    if (conversationId === activeConversationId) {
      return;
    }

    setMessages([]);
    setActiveConversationId(conversationId);
    setMessagesPage(1);
  };

  return (
    <div className="chat-page">
      {/* Sidebar */}
      <aside className="chat-sidebar">
        <div className="sidebar-top">
          {/* Brand */}
          <div className="sidebar-brand">
            <div className="sidebar-logo">
              <BookOpen size={18} strokeWidth={2.5} />
            </div>

            <span>Granthbodh</span>

            <button
              className="sidebar-collapse"
              onClick={logout}
              title="Logout"
            >
              <Power size={17} />
            </button>
          </div>

          {/* New conversation */}
          <button
            className="new-conversation"
            onClick={() => newConversation()}
          >
            <BotMessageSquare size={17} />
            <span>New conversation</span>
          </button>

          {/* Recent conversations */}
          <div className="sidebar-section">
            <div className="sidebar-section-title">
              Recent conversations
            </div>

            <div className="conversation-list">
              {conversations.map((conversation) => (
                <button
                  key={conversation.id}
                  className={`conversation-item ${
                    activeConversationId === conversation.id ? "active" : ""
                  }`}
                  onClick={() => setConversation(conversation.id)}
                >
                  {conversation.title}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Knowledge base */}
        <div className="knowledge-base">
          <div className="knowledge-header">
            <span>Knowledge base</span>
            <span className="document-count">0{totalDocuments}</span>
          </div>

          <div className="document-list">
            {documents.map((document) => (
              <div className="document-item" key={document.id}>
                <FileText size={15} />
                <span>{document.filename}</span>
              </div>
            ))}
          </div>

          <input
            ref={fileInputRef}
            type="file"
            hidden
            accept=".pdf,.doc,.docx,.xlsx,.xls"
            onChange={handleFileUpload}
          />

          <button
            type="button"
            className="upload-button"
            onClick={() => fileInputRef.current?.click()}
          >
            <Plus size={15} />
            <span>Upload documents</span>
          </button>
        </div>
      </aside>

      {/* Main chat */}
      <main className="chat-main">
        {/* Top bar */}
        <header className="chat-topbar">
          <div className="ready-status">
            <span className="status-dot" />
            <span>Granthbodh is ready</span>
          </div>

          <span className="assistant-label">
            Knowledge assistant
          </span>
        </header>

        {/* Content */}
        <div className="chat-content">
          {messages.length === 0 ? (
            <div className="chat-empty">
              <div className="chat-icon">
                <BotMessageSquare
                  size={25}
                  strokeWidth={1.8}
                />
              </div>

              <h1>What would you like to understand?</h1>

              <p>
                Ask questions across your uploaded sources, discover
                <br />
                connections, or turn dense material into clear notes.
              </p>

              <div className="suggestions">
                <button
                  onClick={() =>
                    setMessage("Explain a concept")
                  }
                >
                  Explain a concept
                </button>

                <button
                  onClick={() =>
                    setMessage("Find connections")
                  }
                >
                  Find connections
                </button>
              </div>
            </div>
          ) : (
            <div className="message-list">
              {messages.map((msg, index) => (
                <div
                  key={index}
                  className={`chat-message ${msg.role}`}
                >
                  {msg.role === "assistant" && (
                    <BotMessageSquare size={18} />
                  )}

                  <div>{msg.content}</div>
                </div>
              ))}
            </div>
          )}

          {/* Input */}
          <form
            className="chat-input-container"
            onSubmit={sendMessage}
          >
            <input
              type="text"
              placeholder="Ask Granthbodh anything about your sources..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
            />

            <button
              type="submit"
              className="send-button"
              disabled={!message.trim()}
            >
              <ArrowUp size={19} strokeWidth={2} />
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}