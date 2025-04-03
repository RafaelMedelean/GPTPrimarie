import React, { useState, useEffect } from 'react';
import { User, Conversation, Message } from '../types';
import Login from './Login';
import Signup from './Signup';
import Chat from './chat';
import ConversationList from './ConversationList';
import AdminDashboard from './AdminDashboard';
import { authApi, conversationApi } from '../services/api';
import { adminApi } from '../services/adminApi';
import '../styles/layout.css';

export default function Layout() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showSignup, setShowSignup] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);
  const [showAdminDashboard, setShowAdminDashboard] = useState(false);

  // Check authentication status and load user data on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        if (authApi.isAuthenticated()) {
          const userData = await authApi.getCurrentUser();
          setUser(userData);
          setIsAuthenticated(true);
          
          // Check if user is admin
          const adminStatus = await adminApi.isAdmin();
          setIsAdmin(adminStatus);
          
          // Load conversations
          const conversationsData = await conversationApi.getConversations();
          setConversations(conversationsData);
          
          // Set the first conversation as active if there is one
          if (conversationsData.length > 0 && !activeConversationId) {
            setActiveConversationId(conversationsData[0].id);
          }
        }
      } catch (error) {
        console.error('Authentication check failed:', error);
        authApi.logout();
        setIsAuthenticated(false);
      } finally {
        setIsLoading(false);
      }
    };
    
    checkAuth();
  }, [activeConversationId]);

  // Handle login
  const handleLogin = async () => {
    try {
      const userData = await authApi.getCurrentUser();
      setUser(userData);
      setIsAuthenticated(true);
      
      // Load conversations
      const conversationsData = await conversationApi.getConversations();
      setConversations(conversationsData);
      
      // Set the first conversation as active if there is one
      if (conversationsData.length > 0) {
        setActiveConversationId(conversationsData[0].id);
      }
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  // Handle signup
  const handleSignup = async () => {
    try {
      const userData = await authApi.getCurrentUser();
      setUser(userData);
      setIsAuthenticated(true);
    } catch (error) {
      console.error('Signup failed:', error);
    }
  };

  // Handle logout
  const handleLogout = () => {
    authApi.logout();
    setIsAuthenticated(false);
    setUser(null);
    setConversations([]);
    setActiveConversationId(null);
  };

  // Handle creating a new conversation
  const handleNewConversation = async () => {
    try {
      const newConversation = await conversationApi.createConversation();
      setConversations([newConversation, ...conversations]);
      setActiveConversationId(newConversation.id);
      setIsMobileMenuOpen(false); // Close mobile menu when starting new conversation
    } catch (error) {
      console.error('Failed to create conversation:', error);
    }
  };

  // Handle selecting a conversation
  const handleSelectConversation = (conversationId: string) => {
    setActiveConversationId(conversationId);
    setIsMobileMenuOpen(false); // Close mobile menu when selecting a conversation
  };

  // Handle saving a conversation
  const handleSaveConversation = async (messages: Message[]) => {
    if (!activeConversationId) return;
    
    try {
      await conversationApi.updateConversation(activeConversationId, { messages });
      
      // Refresh conversations list
      const conversationsData = await conversationApi.getConversations();
      setConversations(conversationsData);
    } catch (error) {
      console.error('Failed to save conversation:', error);
    }
  };

  // Toggle mobile menu
  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  // If not authenticated, show login or signup
  if (!isAuthenticated) {
    return showSignup
      ? <Signup onSignup={handleSignup} onSwitchToLogin={() => setShowSignup(false)} />
      : <Login onLogin={handleLogin} onSwitchToSignup={() => setShowSignup(true)} />;
  }

  // Show admin dashboard if requested
  if (showAdminDashboard) {
    return <AdminDashboard />;
  }

  // Get the active conversation
  const activeConversation = conversations.find(c => c.id === activeConversationId);

  return (
    <div className="layout-container">
      {/* Header */}
      <header className="layout-header">
        <div className="header-left">
          <button className="menu-button" onClick={toggleMobileMenu}>
            ☰
          </button>
          <h1 className="app-title">AI Chat</h1>
        </div>
        <div className="header-right">
          {user && (
            <div className="user-info">
              <span className="username">{user.username}</span>
              {isAdmin && (
                <button
                  className="admin-button"
                  onClick={() => setShowAdminDashboard(true)}
                >
                  Admin Dashboard
                </button>
              )}
              <button className="logout-button" onClick={handleLogout}>
                Logout
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Main content */}
      <div className="layout-content">
        {/* Sidebar - hidden on mobile unless menu is open */}
        <div className={`layout-sidebar ${isMobileMenuOpen ? 'mobile-open' : ''}`}>
          <ConversationList
            conversations={conversations}
            activeConversationId={activeConversationId}
            onSelectConversation={handleSelectConversation}
            onNewConversation={handleNewConversation}
          />
        </div>

        {/* Chat area */}
        <div className="layout-chat">
          {activeConversation ? (
            <Chat
              conversationId={activeConversation.id}
              initialMessages={activeConversation.messages}
              onSaveConversation={handleSaveConversation}
            />
          ) : (
            <div className="empty-state">
              <h2>No conversation selected</h2>
              <p>Select a conversation from the sidebar or start a new one</p>
              <button 
                className="new-chat-button"
                onClick={handleNewConversation}
              >
                Start New Chat
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}