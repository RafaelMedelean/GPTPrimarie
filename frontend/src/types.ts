// src/types.ts

export interface Feedback {
  qualityRating: boolean | null;  // Yes/No for quality (true/false)
  structureRating: boolean | null; // Yes/No for structure (true/false)
  qualityComment: string;  // Quality feedback comment
  structureComment: string; // Structure feedback comment
}

// Define a type for question items in the admin dashboard
export interface QuestionWithFeedback {
  id: string;
  conversation_id: string;
  question: string;
  response: string;
  asked_at: string | Date;
  has_feedback: boolean;
  quality_rating: number | null; // 1 for Yes, 0 for No
  structure_rating: number | null; // 1 for Yes, 0 for No
  quality_comment: string;
  structure_comment: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  feedback: Feedback | null;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string | Date;
  updatedAt: string | Date;
  user_id?: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: string;  // "user" or "admin"
  avatar?: string;
  admin: boolean;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// Admin types
export interface UserStats {
  id: string;
  username: string;
  email: string;
  role: string;
  conversation_count: number;
  message_count: number;
}

export interface FeedbackStats {
  total_feedback_count: number;
  quality_stats: {
    yes_percentage: number;
    no_percentage: number;
  };
  structure_stats: {
    yes_percentage: number;
    no_percentage: number;
  };
}

export interface DashboardData {
  total_users: number;
  total_conversations: number;
  total_messages: number;
  feedback_stats: FeedbackStats;
  user_stats: UserStats[];
}