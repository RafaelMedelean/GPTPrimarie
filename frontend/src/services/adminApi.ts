import { Conversation, DashboardData, FeedbackStats, User, UserStats, QuestionWithFeedback } from '../types';

// API base URL - using window.location to determine hostname
const getApiUrl = () => {
  const { protocol, hostname } = window.location;
  return `${protocol}//${hostname}:8000`;
};

const API_URL = getApiUrl();

// Helper function to handle API responses
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorDetail = '';
    try {
      const errorData = await response.json();
      errorDetail = errorData.detail || `Status: ${response.status} ${response.statusText}`;
    } catch (e) {
      errorDetail = `Status: ${response.status} ${response.statusText}`;
    }
    console.error('API error:', errorDetail);
    throw new Error(errorDetail);
  }
  
  // Check if the response has content
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return await response.json() as T;
  }
  
  return {} as T;
}

// Get the stored token
function getToken(): string | null {
  return localStorage.getItem('token');
}

// Admin API calls
export const adminApi = {
  // Get all users
  async getAllUsers(): Promise<User[]> {
    const token = getToken();
    if (!token) {
      throw new Error('Not authenticated');
    }
    
    const response = await fetch(`${API_URL}/admin/users`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });
    
    return handleResponse<User[]>(response);
  },
  
  // Get all conversations
  async getAllConversations(): Promise<Conversation[]> {
    const token = getToken();
    if (!token) {
      throw new Error('Not authenticated');
    }
    
    const response = await fetch(`${API_URL}/admin/conversations`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });
    
    return handleResponse<Conversation[]>(response);
  },
  
  // Get user statistics
  async getUserStats(): Promise<UserStats[]> {
    const token = getToken();
    if (!token) {
      throw new Error('Not authenticated');
    }
    
    const response = await fetch(`${API_URL}/admin/stats/users`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });
    
    return handleResponse<UserStats[]>(response);
  },
  
  // Get feedback statistics
  async getFeedbackStats(): Promise<FeedbackStats> {
    const token = getToken();
    if (!token) {
      throw new Error('Not authenticated');
    }
    
    const response = await fetch(`${API_URL}/admin/stats/feedback`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });
    
    return handleResponse<FeedbackStats>(response);
  },
  
  // Get dashboard data
  async getDashboardData(): Promise<DashboardData> {
    const token = getToken();
    if (!token) {
      throw new Error('Not authenticated');
    }
    
    const response = await fetch(`${API_URL}/admin/dashboard`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });
    
    return handleResponse<DashboardData>(response);
  },
  
  async getQuestions(): Promise<QuestionWithFeedback[]> {
    const token = getToken();
    if (!token) {
      throw new Error('Not authenticated');
    }
    
    const response = await fetch(`${API_URL}/admin/questions`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });
    
    return handleResponse<QuestionWithFeedback[]>(response);
  },
  // Check if user is admin
  async isAdmin(): Promise<boolean> {
    try {
      const token = getToken();
      if (!token) {
        console.log("No authentication token found");
        return false;
      }
      
      console.log("Checking admin status with token:", token.substring(0, 10) + "...");
      
      const response = await fetch(`${API_URL}/users/me`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
      
      if (!response.ok) {
        console.error("Admin check failed:", response.status, response.statusText);
        return false;
      }
      
      const user = await response.json();
      console.log("User data from /users/me:", user);
      
      // Check both ways (role === "admin" and role property exists)
      const isAdminUser = user.role === "admin" || user.admin === true;
      console.log("Is admin user:", isAdminUser, "Role:", user.role, "Admin property:", user.admin);
      
      return isAdminUser;
    } catch (error) {
      console.error("Error checking admin status:", error);
      return false;
    }
  }
};

export default adminApi;