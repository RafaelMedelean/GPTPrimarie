import React, { useState, useRef, useEffect } from "react";
import { Message, Feedback } from "../types";
import { chatApi, feedbackApi } from "../services/api";
import '../styles/chat.css';

interface ChatProps {
  conversationId?: string;
  initialMessages?: Message[];
  onSaveConversation?: (messages: Message[]) => void;
}

export default function Chat({ 
  conversationId, 
  initialMessages = [], 
  onSaveConversation 
}: ChatProps) {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState<string>("");
  const [qualityFeedback, setQualityFeedback] = useState<string>("");
  const [structureFeedback, setStructureFeedback] = useState<string>("");
  const [qualityRating, setQualityRating] = useState<boolean | null>(null);
  const [structureRating, setStructureRating] = useState<boolean | null>(null);
  const [activeFeedbackId, setActiveFeedbackId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Re-initialize local messages if conversation changes
  useEffect(() => {
    setMessages(initialMessages);
  }, [conversationId, initialMessages]);

  // Handle sending a new user message
  const handleSend = async (): Promise<void> => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: `${Date.now()}-user`,
      role: "user",
      content: input,
      feedback: null,
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await chatApi.sendMessage(input, conversationId);
      const aiMessage: Message = {
        id: `${Date.now()}-assistant`,
        role: "assistant",
        content: response.message,
        feedback: null,
      };
      setMessages((prev) => {
         const updatedMessages = [...prev, aiMessage];
         if (onSaveConversation) {
            onSaveConversation(updatedMessages);
         }
         return updatedMessages;
      });
    } catch (error) {
      console.error("Error fetching AI response:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // Toggle feedback form for a specific message
  const toggleFeedbackForm = (messageId: string): void => {
    if (activeFeedbackId === messageId) {
      setActiveFeedbackId(null);
      setQualityRating(null);
      setStructureRating(null);
      setQualityFeedback("");
      setStructureFeedback("");
    } else {
      setActiveFeedbackId(messageId);
      const message = messages.find(msg => msg.id === messageId);
      if (message?.feedback) {
        setQualityRating(message.feedback.qualityRating);
        setStructureRating(message.feedback.structureRating);
        setQualityFeedback(message.feedback.qualityComment || "");
        setStructureFeedback(message.feedback.structureComment || "");
      } else {
        setQualityRating(null);
        setStructureRating(null);
        setQualityFeedback("");
        setStructureFeedback("");
      }
    }
  };

  // Submit feedback for a message
  const submitFeedback = async (messageId: string): Promise<void> => {
    if (qualityRating === null || structureRating === null) {
      alert("Please provide both quality and structure ratings");
      return;
    }

    const newFeedback: Feedback = {
      qualityRating,
      structureRating,
      qualityComment: qualityFeedback,
      structureComment: structureFeedback
    };

    setMessages((prevMessages) =>
      prevMessages.map((msg) => {
        if (msg.id === messageId) {
          return { ...msg, feedback: newFeedback };
        }
        return msg;
      })
    );

    if (conversationId) {
      try {
        await feedbackApi.submitFeedback(
          messageId,
          conversationId,
          newFeedback
        );
      } catch (error) {
        console.error("Error submitting feedback:", error);
      }
    }

    setActiveFeedbackId(null);
    setQualityRating(null);
    setStructureRating(null);
    setQualityFeedback("");
    setStructureFeedback("");
  };

  return (
    <div className="chat-container">
      <div className="messages-container">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`message ${msg.role === "user" ? "user-message" : "assistant-message"}`}
          >
            <div className="message-content">
              <div className="message-role">
                {msg.role === "user" ? "You" : "Assistant"}
              </div>
              <p className="message-text">{msg.content}</p>
            </div>
            
            {msg.role === "assistant" && (
              <div className="feedback-section">
                {msg.feedback && activeFeedbackId !== msg.id && (
                  <div className="existing-feedback">
                    <div className="feedback-ratings">
                      <div className="feedback-rating">
                        Quality: <span className="rating-value">{msg.feedback.qualityRating ? "Yes" : "No"}</span>
                      </div>
                      <div className="feedback-rating">
                        Structure: <span className="rating-value">{msg.feedback.structureRating ? "Yes" : "No"}</span>
                      </div>
                    </div>
                    {(msg.feedback.qualityComment || msg.feedback.structureComment) && (
                      <div className="feedback-comments">
                        {msg.feedback.qualityComment && (
                          <div className="feedback-comment">
                            <strong>Quality:</strong> "{msg.feedback.qualityComment}"
                          </div>
                        )}
                        {msg.feedback.structureComment && (
                          <div className="feedback-comment">
                            <strong>Structure:</strong> "{msg.feedback.structureComment}"
                          </div>
                        )}
                      </div>
                    )}
                    <button 
                      className="edit-feedback-button"
                      onClick={() => toggleFeedbackForm(msg.id)}
                    >
                      Edit Feedback
                    </button>
                  </div>
                )}
                
                {!msg.feedback && activeFeedbackId !== msg.id && (
                  <button 
                    className="give-feedback-button"
                    onClick={() => toggleFeedbackForm(msg.id)}
                  >
                    Give Feedback
                  </button>
                )}
                
                {activeFeedbackId === msg.id && (
                  <div className="feedback-form">
                    <div className="feedback-section">
                      <div className="feedback-category">
                        <h4>Quality Assessment</h4>
                        <div className="rating-buttons">
                          <button 
                            className={`rating-button ${qualityRating === false ? 'rating-button-selected' : ''}`}
                            onClick={() => setQualityRating(false)}
                          >
                            No
                          </button>
                          <button 
                            className={`rating-button ${qualityRating === true ? 'rating-button-selected' : ''}`}
                            onClick={() => setQualityRating(true)}
                          >
                            Yes
                          </button>
                        </div>
                        <textarea
                          className="feedback-textarea"
                          placeholder="Provide quality feedback..."
                          value={qualityFeedback}
                          onChange={(e) => setQualityFeedback(e.target.value)}
                        />
                      </div>

                      <div className="feedback-category">
                        <h4>Structure Assessment</h4>
                        <div className="rating-buttons">
                          <button 
                            className={`rating-button ${structureRating === false ? 'rating-button-selected' : ''}`}
                            onClick={() => setStructureRating(false)}
                          >
                            No
                          </button>
                          <button 
                            className={`rating-button ${structureRating === true ? 'rating-button-selected' : ''}`}
                            onClick={() => setStructureRating(true)}
                          >
                            Yes
                          </button>
                        </div>
                        <textarea
                          className="feedback-textarea"
                          placeholder="Provide structure feedback..."
                          value={structureFeedback}
                          onChange={(e) => setStructureFeedback(e.target.value)}
                        />
                      </div>
                    </div>

                    <div className="feedback-form-buttons">
                      <button 
                        className="cancel-button"
                        onClick={() => setActiveFeedbackId(null)}
                      >
                        Cancel
                      </button>
                      <button 
                        className="submit-button"
                        onClick={() => submitFeedback(msg.id)}
                      >
                        Submit Feedback
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
        
        {isLoading && (
          <div className="message assistant-message">
            <div className="message-content">
              <div className="message-role">Assistant</div>
              <p className="message-text">Thinking...</p>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <div className="input-container">
        <input
          className="input-field"
          type="text"
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSend();
          }}
          disabled={isLoading}
        />
        <button 
          className="send-button"
          onClick={handleSend}
          disabled={isLoading || !input.trim()}
        >
          Send
        </button>
      </div>
    </div>
  );
}