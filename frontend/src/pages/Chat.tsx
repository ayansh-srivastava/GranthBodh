import { useRef, useState, useEffect, type ChangeEvent, type FormEvent } from "react";
import {
  Power,
  ArrowUp,
  BotMessageSquare,
  BookOpen,
  FileText,
  Plus,
  Loader2,
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
  const [loadingDocuments, setLoadingDocuments] = useState(false);

  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [conversationsPage, setConversationsPage] = useState<number>(1);
  const [totalConversationPages, setTotalConversationPages] = useState<number>(0);
  const [loadingConversations, setLoadingConversations] = useState(false);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);

  const [message, setMessage] = useState("");

  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [messagesPage, setMessagesPage] = useState<number>(1);
  const [totalMessagesPages, setTotalMessagesPages] = useState<number>(1);
  const [loadingMessages, setLoadingMessages] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const messageListRef = useRef<HTMLDivElement>(null);

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
      setLoadingDocuments(true);
      try {
        const response = await getDocuments(documentsPage);
        setDocuments((prevDocuments) => [
          ...prevDocuments,
          ...response.documents,
        ]);
        setTotalDocuments(response.total_count);
      } catch (error) {
        console.error("Error fetching documents:", error);
      } finally {
        setLoadingDocuments(false);
      }
    };
    if (documentsPage === 1) {
      fetchDocuments();
    }
  }, []);

  const loadMoreDocuments = () => {
    if (documents.length < totalDocuments && !loadingDocuments) {
      setLoadingDocuments(true);
      getDocuments(documentsPage + 1)
        .then((response) => {
          setDocuments((prevDocuments) => [
            ...prevDocuments,
            ...response.documents,
          ]);
          setDocumentsPage((prevPage) => prevPage + 1);
        })
        .catch((error) => {
          console.error("Error fetching documents:", error);
        })
        .finally(() => {
          setLoadingDocuments(false);
        });
    }
  };

  useEffect(() => {
    const fetchConversations = async () => {
      setLoadingConversations(true);
      try {
        const response = await getConversations(conversationsPage);
        setConversations((prevConversations) => [
          ...prevConversations,
          ...response.conversations,
        ]);
        setTotalConversationPages(response.total_pages);
      } catch (error) {
        console.error("Error fetching conversations:", error);
      } finally {
        setLoadingConversations(false);
      }
    };
    if (conversationsPage === 1) {
      fetchConversations();
    }
  }, []);

  const loadMoreConversations = () => {
    if (!loadingConversations) {
      setLoadingConversations(true);
      getConversations(conversationsPage + 1)
        .then((response) => {
          setConversations((prevConversations) => [
            ...prevConversations,
            ...response.conversations,
          ]);
          setConversationsPage((prevPage) => prevPage + 1);
        })
        .catch((error) => {
          console.error("Error fetching conversations:", error);
        })
        .finally(() => {
          setLoadingConversations(false);
        });
    }
  };

  const newConversation = () => {
    setActiveConversationId(null);
    setMessages([]);
    setMessagesPage(1);
  };

  const fetchMessages = async (conversationId: string, page: number = 1) => {
    setLoadingMessages(true);
    try {
      const response = await getMessages(conversationId, page);
      setMessages((prevMessages) => [...response.messages, ...prevMessages]);
      setMessagesPage(page);
      setTotalMessagesPages(response.total_pages);
    } catch (error) {
      console.error("Error fetching messages:", error);
    } finally {
      setLoadingMessages(false);
    }
  };

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

  useEffect(() => {
    const messageList = messageListRef.current;
    if (messageList) {
      // Use setTimeout to ensure DOM is updated before scrolling
      setTimeout(() => {
        messageList.scrollTop = messageList.scrollHeight;
      }, 0);
    }
  }, [messages]);


  // Infinite scroll handler
  useEffect(() => {
    const messageList = messageListRef.current;
    if (!messageList || !activeConversationId) return;

    const handleScroll = () => {
      if (messageList.scrollTop < 100 && !loadingMessages && messagesPage < totalMessagesPages) {
        const nextPage = messagesPage + 1;
        setMessagesPage(nextPage);
        fetchMessages(activeConversationId, nextPage);
      }
    };

    messageList.addEventListener("scroll", handleScroll);
    return () => messageList.removeEventListener("scroll", handleScroll);
  }, [activeConversationId, messagesPage, loadingMessages]);

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

            {/* Load more conversations */}
            {conversationsPage < totalConversationPages && (
            <button
              className="load-more-btn"
              onClick={loadMoreConversations}
              disabled={loadingConversations}
            >
              {loadingConversations ? (
                <>
                  <Loader2 size={14} className="spin" />
                  <span>Loading...</span>
                </>
              ) : (
                <span>Load more</span>
              )}
            </button>)}
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

          {/* Load more documents */}
          {documents.length < totalDocuments && (
            <button
              className="load-more-btn"
              onClick={loadMoreDocuments}
              disabled={loadingDocuments}
            >
              {loadingDocuments ? (
                <>
                  <Loader2 size={14} className="spin" />
                  <span>Loading...</span>
                </>
              ) : (
                <span>Load more</span>
              )}
            </button>
          )}

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
            <div className="message-list h-2" ref={messageListRef}>
              {loadingMessages && (
                <div className="loading-indicator">
                  <Loader2 size={18} className="spin" />
                  <span>Loading messages...</span>
                </div>
              )}
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