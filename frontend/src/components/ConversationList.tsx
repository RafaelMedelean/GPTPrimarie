import "../styles/conversation.css";
import { Conversation } from "../types";

interface ConversationListProps {
  conversations: Conversation[];
  activeConversationId: string | null;
  onSelectConversation: (conversationId: string) => void;
  onNewConversation: () => void;
}

export default function ConversationList({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
}: ConversationListProps) {
  return (
    <div className="conversation-sidebar">
      <div className="conversation-header">
        <h2>Conversations</h2>
        <button className="new-chat-button" onClick={onNewConversation}>
          New Chat
        </button>
      </div>

      <div className="conversation-list">
        {conversations.length === 0 ? (
          <div className="no-conversations">
            <p>No conversations yet</p>
            <p>Start a new chat to begin</p>
          </div>
        ) : (
          conversations.map((conversation) => (
            <div
              key={conversation.id}
              className={`conversation-item ${
                activeConversationId === conversation.id ? "active" : ""
              }`}
              onClick={() => onSelectConversation(conversation.id)}
            >
              <div className="conversation-title">{conversation.title}</div>
              <div className="conversation-date">
                {conversation.updatedAt
                  ? formatDate(typeof conversation.updatedAt === 'string'
                      ? new Date(conversation.updatedAt)
                      : conversation.updatedAt)
                  : "No date"}
              </div>
              <div className="conversation-preview">
                {getConversationPreview(conversation)}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// Helper function to format date
function formatDate(date: Date): string {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  if (date >= today) {
    return `Today, ${date.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    })}`;
  } else if (date >= yesterday) {
    return `Yesterday, ${date.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    })}`;
  } else {
    return date.toLocaleDateString([], { month: "short", day: "numeric" });
  }
}

// Helper function to get a preview of the conversation
function getConversationPreview(conversation: Conversation): string {
  const lastMessage = conversation.messages[conversation.messages.length - 1];
  if (!lastMessage) return "No messages";

  // Truncate the message if it's too long
  const maxLength = 30;
  const content = lastMessage.content;

  if (content.length <= maxLength) {
    return content;
  }

  return content.substring(0, maxLength) + "...";
}
