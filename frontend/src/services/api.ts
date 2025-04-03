import { User, Conversation, Message, Feedback } from '../types';

// Get the base API URL
const getBaseUrl = () => {
  // For production, use window.location to determine the API URL
  const { protocol, hostname } = window.location;
  // Use port 8000 for the backend API, even if frontend is on a different port
  return `${protocol}//${hostname}:8000`;
};

const API_BASE_URL = getBaseUrl();

// Helper function to handle API responses
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'An error occurred');
  }
  
  // Check if the response has content
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return await response.json() as T;
  }
  
  return {} as T;
}

// Get the stored token
const getToken = () => {
  return localStorage.getItem('token') || sessionStorage.getItem('token');
};

// Set the token in local storage
function setToken(token: string): void {
  localStorage.setItem('token', token);
}

// Clear the token from local storage
function clearToken(): void {
  localStorage.removeItem('token');
}

// Authentication API calls
export const authApi = {
  // Login user
  async login(username: string, password: string): Promise<{ access_token: string }> {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await fetch(`${API_BASE_URL}/token`, {
      method: 'POST',
      body: formData,
    });
    
    const data = await handleResponse<{ access_token: string, token_type: string }>(response);
    setToken(data.access_token);
    return { access_token: data.access_token };
  },
  
  // Register user
  async register(username: string, email: string, password: string, admin: boolean): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/users`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username,
        email,
        password,
        role: admin ? "admin" : "user"
      }),
    });
    
    return handleResponse<User>(response);
  },
  
  // Get current user
  async getCurrentUser(): Promise<User> {
    const token = getToken();
    if (!token) {
      throw new Error('Not authenticated');
    }
    
    const response = await fetch(`${API_BASE_URL}/users/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    
    return handleResponse<User>(response);
  },
  
  // Logout user
  logout(): void {
    clearToken();
  },
  
  // Check if user is authenticated
  isAuthenticated(): boolean {
    return !!getToken();
  },
};

// Conversation API calls
export const conversationApi = {
  // Get all conversations
  async getConversations(): Promise<Conversation[]> {
    const token = getToken();
    if (!token) {
      throw new Error('Not authenticated');
    }
    
    const response = await fetch(`${API_BASE_URL}/conversations`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    
    return handleResponse<Conversation[]>(response);
  },
  
  // Get a specific conversation
  async getConversation(id: string): Promise<Conversation> {
    const token = getToken();
    if (!token) {
      throw new Error('Not authenticated');
    }
    
    const response = await fetch(`${API_BASE_URL}/conversations/${id}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    
    return handleResponse<Conversation>(response);
  },
  
  // Create a new conversation
  async createConversation(title: string = 'New Conversation'): Promise<Conversation> {
    const token = getToken();
    if (!token) {
      throw new Error('Not authenticated');
    }
    
    const response = await fetch(`${API_BASE_URL}/conversations`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ title, messages: [] }),
    });
    
    return handleResponse<Conversation>(response);
  },
  
  // Update a conversation
  async updateConversation(id: string, data: { title?: string, messages?: Message[] }): Promise<Conversation> {
    const token = getToken();
    if (!token) {
      throw new Error('Not authenticated');
    }
    
    const response = await fetch(`${API_BASE_URL}/conversations/${id}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    return handleResponse<Conversation>(response);
  },
  
  // Delete a conversation
  async deleteConversation(id: string): Promise<void> {
    const token = getToken();
    if (!token) {
      throw new Error('Not authenticated');
    }
    
    const response = await fetch(`${API_BASE_URL}/conversations/${id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    
    return handleResponse<void>(response);
  },
};

// Chat API calls
export const chatApi = {
  // Send a message and get a response
  async sendMessage(message: string, conversationId?: string): Promise<{ message: string, conversation_id: string }> {
    const token = getToken();
    if (!token) {
      throw new Error('Not authenticated');
    }
    
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message, conversation_id: conversationId }),
    });
    
    return handleResponse<{ message: string, conversation_id: string }>(response);
  },
};

// Feedback API calls
export const feedbackApi = {
  // Submit feedback for a message
  async submitFeedback(
    messageId: string,
    conversationId: string,
    feedback: Feedback
  ): Promise<void> {
    console.log('Submitting feedback:', {
      messageId,
      conversationId,
      feedback
    });
    
    const token = getToken();
    if (!token) {
      throw new Error('User not authenticated');
    }
    
    // Get base URL from window location or default to localhost
    const baseUrl = window.location.port ? 
      `${window.location.protocol}//${window.location.hostname}:8000` : 
      `${window.location.protocol}//${window.location.hostname}`;
    
    try {
      const response = await fetch(`${baseUrl}/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          message_id: messageId,
          conversation_id: conversationId,
          feedback,
        }),
      });

      if (!response.ok) {
        const errorData = await response.text();
        console.error('Feedback API error:', response.status, errorData);
        throw new Error(`Failed to submit feedback: ${response.status} ${errorData}`);
      }
      
      console.log('Feedback submitted successfully');
    } catch (error) {
      console.error('Feedback submission error:', error);
      throw error;
    }
  },
};

// Export all APIs
export default {
  auth: authApi,
  conversation: conversationApi,
  chat: chatApi,
  feedback: feedbackApi,
};