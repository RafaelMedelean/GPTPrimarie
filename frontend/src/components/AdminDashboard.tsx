import { useEffect, useState } from "react";
import { adminApi } from "../services/adminApi";
import "../styles/admin.css";
import { DashboardData, UserStats, QuestionWithFeedback } from "../types";

// Reusable component to display truncated text with "See More" functionality
function TruncatedCell({
  text,
  threshold = 100,
  maxHeight = "none",
}: {
  text: string;
  threshold?: number;
  maxHeight?: string | number;
}) {
  const [expanded, setExpanded] = useState(false);

  if (!text) {
    return <span className="empty-cell">-</span>;
  }

  if (text.length <= threshold) {
    return <span>{text}</span>;
  }

  return (
    <div className={`truncated-content ${expanded ? "expanded" : ""}`}>
      <div 
        className="content" 
        style={{ maxHeight: expanded ? "none" : maxHeight }}
      >
        {text}
      </div>
      <button
        onClick={() => setExpanded(!expanded)}
        className="expand-button"
      >
        {expanded ? "Show Less" : "Show More"}
      </button>
    </div>
  );
}

// Component to display yes/no as a visual indicator
function RatingIndicator({ value }: { value: number | null }) {
  if (value === null) return <span className="no-rating">Not rated</span>;
  
  return (
    <span className={`rating-indicator ${value === 1 ? "positive" : "negative"}`}>
      {value === 1 ? "Yes" : "No"}
    </span>
  );
}

export default function AdminDashboard() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(
    null
  );
  const [questions, setQuestions] = useState<QuestionWithFeedback[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<
    "overview" | "users" | "feedback" | "questions"
  >("overview");

  // Fetch dashboard data (overview, users, feedback, etc.)
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        
        // First check if user is admin
        const isAdminUser = await adminApi.isAdmin();
        if (!isAdminUser) {
          setError("You don't have admin privileges. Please contact the administrator.");
          setLoading(false);
          return;
        }
        
        console.log("Fetching dashboard data...");
        const data = await adminApi.getDashboardData();
        console.log("Dashboard data received:", data);
        setDashboardData(data);
        setError(null);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Unknown error";
        console.error("Error fetching dashboard data:", err);
        
        // Check for specific error conditions
        if (errorMessage.includes("403")) {
          setError("You don't have permission to access the admin dashboard. Your account doesn't have admin privileges.");
        } else if (errorMessage.includes("Failed to fetch")) {
          setError("Failed to connect to the server. Please check if the backend server is running and accessible.");
        } else {
          setError(
            `Failed to load dashboard data: ${errorMessage}. Make sure you have admin privileges and the backend server is running.`
          );
        }
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  // Fetch questions when the "questions" tab is active
  useEffect(() => {
    if (activeTab === "questions") {
      const fetchQuestions = async () => {
        try {
          setLoading(true);
          const data = await adminApi.getQuestions();
          setQuestions(data);
          setLoading(false);
        } catch (err) {
          console.error("Error fetching questions:", err);
          setLoading(false);
        }
      };

      fetchQuestions();
    }
  }, [activeTab]);

  if (loading) {
    return (
      <div className="admin-loading">
        <div className="spinner"></div>
        <p>Loading dashboard data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="admin-error">
        <h2>Error</h2>
        <p>{error}</p>
        <button onClick={() => (window.location.href = "/")}>
          Return to Chat
        </button>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="admin-error">
        <h2>No Data Available</h2>
        <p>Could not retrieve dashboard data.</p>
        <button onClick={() => (window.location.href = "/")}>
          Return to Chat
        </button>
      </div>
    );
  }

  return (
    <div className="admin-dashboard">
      <header className="admin-header">
        <h1>Admin Dashboard</h1>
        <button
          onClick={() => (window.location.href = "/")}
          className="back-button"
        >
          Return to Chat
        </button>
      </header>

      <nav className="admin-tabs">
        <button
          className={activeTab === "overview" ? "active" : ""}
          onClick={() => setActiveTab("overview")}
        >
          Overview
        </button>
        <button
          className={activeTab === "users" ? "active" : ""}
          onClick={() => setActiveTab("users")}
        >
          Users
        </button>
        <button
          className={activeTab === "feedback" ? "active" : ""}
          onClick={() => setActiveTab("feedback")}
        >
          Feedback
        </button>
        <button
          className={activeTab === "questions" ? "active" : ""}
          onClick={() => setActiveTab("questions")}
        >
          Questions
        </button>
      </nav>

      <div className="admin-content">
        {activeTab === "overview" && (
          <div className="overview-tab">
            <div className="stats-cards">
              <div className="stat-card">
                <h3>Total Users</h3>
                <div className="stat-value">{dashboardData.total_users}</div>
              </div>
              <div className="stat-card">
                <h3>Total Conversations</h3>
                <div className="stat-value">
                  {dashboardData.total_conversations}
                </div>
              </div>
              <div className="stat-card">
                <h3>Total Messages</h3>
                <div className="stat-value">{dashboardData.total_messages}</div>
              </div>
              <div className="stat-card">
                <h3>Feedback Count</h3>
                <div className="stat-value">
                  {dashboardData.feedback_stats.total_feedback_count}
                </div>
              </div>
            </div>

            <div className="summary-section">
              <h3>System Summary</h3>
              <p>
                The chat system currently has {dashboardData.total_users}{" "}
                registered users who have created a total of{" "}
                {dashboardData.total_conversations} conversations. These
                conversations contain {dashboardData.total_messages} messages in
                total.
              </p>
              <p>
                Users have provided feedback on{" "}
                {dashboardData.feedback_stats.total_feedback_count} messages.
              </p>
            </div>
          </div>
        )}

        {activeTab === "users" && (
          <div className="users-tab">
            <h2>User Statistics</h2>
            <table className="users-table">
              <thead>
                <tr>
                  <th>Username</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Conversations</th>
                  <th>Messages</th>
                </tr>
              </thead>
              <tbody>
                {dashboardData.user_stats.map((user: UserStats) => (
                  <tr key={user.id}>
                    <td>{user.username}</td>
                    <td>{user.email}</td>
                    <td>
                      <span className={`role-badge ${user.role}`}>
                        {user.role}
                      </span>
                    </td>
                    <td>{user.conversation_count}</td>
                    <td>{user.message_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === "feedback" && (
          <div className="feedback-tab">
            <h2>Feedback Statistics</h2>

            <div className="feedback-summary">
              <div className="feedback-stat">
                <h3>Total Feedback</h3>
                <div className="stat-value">
                  {dashboardData.feedback_stats.total_feedback_count}
                </div>
              </div>
              
              <div className="feedback-stat">
                <h3>Quality: Yes</h3>
                <div className="stat-value">
                  {dashboardData.feedback_stats.quality_stats.yes_percentage}%
                </div>
              </div>
              
              <div className="feedback-stat">
                <h3>Quality: No</h3>
                <div className="stat-value">
                  {dashboardData.feedback_stats.quality_stats.no_percentage}%
                </div>
              </div>
              
              <div className="feedback-stat">
                <h3>Structure: Yes</h3>
                <div className="stat-value">
                  {dashboardData.feedback_stats.structure_stats.yes_percentage}%
                </div>
              </div>
              
              <div className="feedback-stat">
                <h3>Structure: No</h3>
                <div className="stat-value">
                  {dashboardData.feedback_stats.structure_stats.no_percentage}%
                </div>
              </div>
            </div>

            <h3>Rating Distribution</h3>
            <div className="feedback-charts">
              <div className="chart-container">
                <h4>Quality Rating</h4>
                <div className="bar-chart">
                  <div className="bar-container">
                    <div className="bar-label">Yes</div>
                    <div className="bar-wrapper">
                      <div 
                        className="bar yes" 
                        style={{ width: `${dashboardData.feedback_stats.quality_stats.yes_percentage}%` }}
                      >
                        <span className="bar-value">{dashboardData.feedback_stats.quality_stats.yes_percentage}%</span>
                      </div>
                    </div>
                  </div>
                  <div className="bar-container">
                    <div className="bar-label">No</div>
                    <div className="bar-wrapper">
                      <div 
                        className="bar no" 
                        style={{ width: `${dashboardData.feedback_stats.quality_stats.no_percentage}%` }}
                      >
                        <span className="bar-value">{dashboardData.feedback_stats.quality_stats.no_percentage}%</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="chart-container">
                <h4>Structure Rating</h4>
                <div className="bar-chart">
                  <div className="bar-container">
                    <div className="bar-label">Yes</div>
                    <div className="bar-wrapper">
                      <div 
                        className="bar yes" 
                        style={{ width: `${dashboardData.feedback_stats.structure_stats.yes_percentage}%` }}
                      >
                        <span className="bar-value">{dashboardData.feedback_stats.structure_stats.yes_percentage}%</span>
                      </div>
                    </div>
                  </div>
                  <div className="bar-container">
                    <div className="bar-label">No</div>
                    <div className="bar-wrapper">
                      <div 
                        className="bar no" 
                        style={{ width: `${dashboardData.feedback_stats.structure_stats.no_percentage}%` }}
                      >
                        <span className="bar-value">{dashboardData.feedback_stats.structure_stats.no_percentage}%</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "questions" && (
          <div className="questions-tab">
            <h2>Questions and Feedback</h2>
            <p className="questions-info">
              Showing {questions.length} question-response pairs. Click "Show More" to expand content.
            </p>
            
            {questions.length === 0 ? (
              <div className="no-questions">
                <p>No questions or feedback found.</p>
              </div>
            ) : (
              <div className="responsive-table-container">
                <table className="questions-table">
                  <thead>
                    <tr>
                      <th>Question</th>
                      <th>Response</th>
                      <th>Quality</th>
                      <th>Structure</th>
                      <th>Quality Feedback</th>
                      <th>Structure Feedback</th>
                      <th>Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {questions.map((q) => (
                      <tr key={q.id} className={q.has_feedback ? "has-feedback" : ""}>
                        <td className="question-cell">
                          <TruncatedCell text={q.question} threshold={100} maxHeight="80px" />
                        </td>
                        <td className="response-cell">
                          <TruncatedCell text={q.response} threshold={150} maxHeight="80px" />
                        </td>
                        <td className="rating-cell">
                          <RatingIndicator value={q.quality_rating} />
                        </td>
                        <td className="rating-cell">
                          <RatingIndicator value={q.structure_rating} />
                        </td>
                        <td className="feedback-cell">
                          <TruncatedCell text={q.quality_comment} threshold={80} maxHeight="80px" />
                        </td>
                        <td className="feedback-cell">
                          <TruncatedCell text={q.structure_comment} threshold={80} maxHeight="80px" />
                        </td>
                        <td className="date-cell">
                          {new Date(q.asked_at).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
