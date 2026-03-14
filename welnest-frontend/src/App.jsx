import { useState, useEffect } from "react";
import "./App.css";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Bar } from "react-chartjs-2";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const BACKEND_URL = "http://127.0.0.1:8000";

const NAV_ITEMS = [
  { key: "dashboard", label: "Dashboard", icon: "🏠" },
  { key: "mood", label: "Mood Tracker", icon: "😊" },
  { key: "chat", label: "AI Journal", icon: "🤖" },
  { key: "analytics", label: "Analytics", icon: "📈" },
  { key: "reports", label: "Reports", icon: "📄" },
  { key: "settings", label: "Settings", icon: "⚙️" },
];

/* ================= AUTH FETCH ================= */

const authFetch = async (url, options = {}) => {
  const token = localStorage.getItem("token");

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(url, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    window.location.reload();
  }

  return res;
};

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isRegister, setIsRegister] = useState(false);
  const [page, setPage] = useState("dashboard");

  const [darkMode, setDarkMode] = useState(
    localStorage.getItem("theme") === "dark"
  );

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [summary, setSummary] = useState(null);
  const [streak, setStreak] = useState(null);
  const [weeklyInsight, setWeeklyInsight] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [reportStatus, setReportStatus] = useState({
    has_journal_data: false,
    journal_entries: 0,
    mood_entries: 0,
  });
  const [reportStatusLoading, setReportStatusLoading] = useState(false);
  const [reportStatusLoaded, setReportStatusLoaded] = useState(false);
  const [reportStatusError, setReportStatusError] = useState("");
  const [providerEmail, setProviderEmail] = useState("");
  const [privacyActionLoading, setPrivacyActionLoading] = useState(false);
  const [privacyMessage, setPrivacyMessage] = useState("");

  const [mood, setMood] = useState("");
  const [journal, setJournal] = useState("");
  const [response, setResponse] = useState("");

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  };

  /* ================= AUTO LOGIN ================= */

  useEffect(() => {
    const token = localStorage.getItem("token");
    const savedUser = localStorage.getItem("username");

    if (savedUser) setUsername(savedUser);

    if (token) {
      setIsLoggedIn(true);
      loadDashboard();
    }
  }, []);

  /* ================= SAVE THEME ================= */

  useEffect(() => {
    localStorage.setItem("theme", darkMode ? "dark" : "light");
  }, [darkMode]);

  const loadDashboard = () => {
    fetchSummary();
    fetchStreak();
    fetchWeeklyInsight();
    fetchAnalytics();
    fetchReportStatus();
  };

  /* ================= LOGIN ================= */

  const login = async () => {
    if (!username || !password) return alert("Enter username and password");

    try {
      const res = await fetch(`${BACKEND_URL}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
          username,
          password,
        }),
      });

      let data = {};
      try {
        data = await res.json();
      } catch {
        // Ignore JSON parse errors and use fallback message below.
      }

      if (!res.ok) return alert(data.detail || "Login failed");

      if (!data?.access_token) {
        return alert("Login failed: missing access token from server");
      }

      localStorage.setItem("token", data.access_token);
      localStorage.setItem("username", username);

      setIsLoggedIn(true);
      loadDashboard();
    } catch (err) {
      console.error("Login error:", err);
      alert("Unable to connect to server. Please check backend is running on port 8000.");
    }
  };

  /* ================= REGISTER ================= */

  const register = async () => {
    if (!username || !password) return alert("Enter username and password");

    try {
      const res = await fetch(`${BACKEND_URL}/auth/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username,
          password,
        }),
      });

      let data = {};
      try {
        data = await res.json();
      } catch {
        // Ignore JSON parse errors and use fallback message below.
      }

      if (!res.ok) return alert(data.detail || "Registration failed");

      alert("Account created successfully");
      setIsRegister(false);
    } catch (err) {
      console.error("Register error:", err);
      alert("Unable to connect to server. Please check backend is running on port 8000.");
    }
  };

  /* ================= LOGOUT ================= */

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    window.location.reload();
  };

  /* ================= MOOD ================= */

  const submitMood = async () => {
    const moodValue = Number(mood);

    if (isNaN(moodValue) || moodValue < 1 || moodValue > 10) {
      return alert("Mood must be between 1-10");
    }

    const res = await authFetch(`${BACKEND_URL}/mood`, {
      method: "POST",
      body: JSON.stringify({
        mood_score: moodValue,
      }),
    });

    if (!res.ok) return alert("Mood submission failed");

    setMood("");
    loadDashboard();
  };

  /* ================= JOURNAL ================= */

  const submitJournal = async () => {
    if (!journal.trim()) return alert("Journal cannot be empty");

    setResponse("Thinking... 🤖");

    const res = await authFetch(`${BACKEND_URL}/journal`, {
      method: "POST",
      body: JSON.stringify({
        content: journal,
      }),
    });

    const data = await res.json();

    if (!res.ok) {
      setResponse("AI error");
      return;
    }

    setResponse(data.ai_summary);
    setJournal("");
    loadDashboard();
  };

  /* ================= REPORT DOWNLOAD ================= */

  const downloadReport = async (type) => {
    const token = localStorage.getItem("token");

    const res = await fetch(`${BACKEND_URL}/api/report/${type}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      let message = "Report download failed";
      try {
        const err = await res.json();
        if (err?.detail) message = err.detail;
      } catch {
        // ignore json parse failure
      }
      alert(message);
      return;
    }
    const blob = await res.blob();

    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");

    a.href = url;
    a.download = `wellnest_report.${type}`;
    a.click();
  };

  const fetchReportStatus = async () => {
    try {
      setReportStatusLoading(true);
      setReportStatusError("");
      const res = await authFetch(`${BACKEND_URL}/api/report/status`);
      const data = await res.json();
      if (res.ok) {
        setReportStatus(data);
        setReportStatusLoaded(true);
      } else {
        setReportStatusError("Unable to fetch report status.");
      }
    } catch (err) {
      console.error(err);
      setReportStatusError("Unable to fetch report status.");
    } finally {
      setReportStatusLoading(false);
    }
  };

  const shouldDisableReports =
    reportStatusLoading || (reportStatusLoaded && !reportStatus.has_journal_data);

  /* ================= PRIVACY CONTROLS ================= */

  const shareReportWithProvider = async () => {
    if (!providerEmail.trim()) {
      return alert("Please enter provider email");
    }

    setPrivacyActionLoading(true);
    setPrivacyMessage("");

    try {
      const res = await authFetch(`${BACKEND_URL}/api/report/share`, {
        method: "POST",
        body: JSON.stringify({
          provider_email: providerEmail.trim(),
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setPrivacyMessage(data?.detail || "Failed to share report");
        return;
      }

      setPrivacyMessage(data?.message || "Report shared successfully");
      setProviderEmail("");
    } catch (err) {
      console.error(err);
      setPrivacyMessage("Failed to share report");
    } finally {
      setPrivacyActionLoading(false);
    }
  };

  const deleteAllMyData = async () => {
    const isConfirmed = window.confirm(
      "Are you sure you want to delete all your personal data?"
    );

    if (!isConfirmed) return;

    setPrivacyActionLoading(true);
    setPrivacyMessage("");

    try {
      const res = await authFetch(`${BACKEND_URL}/api/user/delete-data`, {
        method: "DELETE",
      });

      const data = await res.json();

      if (!res.ok) {
        setPrivacyMessage(data?.detail || "Failed to delete your data");
        return;
      }

      setPrivacyMessage(data?.message || "All personal data deleted successfully");
      setResponse("");
      setChartData([]);
      setSummary(null);
      setStreak(0);
      setWeeklyInsight(null);
      fetchReportStatus();
    } catch (err) {
      console.error(err);
      setPrivacyMessage("Failed to delete your data");
    } finally {
      setPrivacyActionLoading(false);
    }
  };

  const deleteMyAccount = async () => {
    const isConfirmed = window.confirm("This action cannot be undone.");
    if (!isConfirmed) return;

    setPrivacyActionLoading(true);
    setPrivacyMessage("");

    try {
      const res = await authFetch(`${BACKEND_URL}/api/user/delete-account`, {
        method: "DELETE",
      });

      const data = await res.json();

      if (!res.ok) {
        setPrivacyMessage(data?.detail || "Failed to delete account");
        return;
      }

      alert(data?.message || "Account deleted successfully");
      logout();
    } catch (err) {
      console.error(err);
      setPrivacyMessage("Failed to delete account");
    } finally {
      setPrivacyActionLoading(false);
    }
  };

  /* ================= ANALYTICS ================= */

  const fetchSummary = async () => {
    try {
      const res = await authFetch(`${BACKEND_URL}/analytics/summary`);
      const data = await res.json();
      if (res.ok) setSummary(data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchStreak = async () => {
    try {
      const res = await authFetch(`${BACKEND_URL}/analytics/streak`);
      const data = await res.json();
      if (res.ok) setStreak(data.streak);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchWeeklyInsight = async () => {
    try {
      const res = await authFetch(`${BACKEND_URL}/analytics/weekly-ai-insight`);
      const data = await res.json();
      if (res.ok) setWeeklyInsight(data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const res = await authFetch(`${BACKEND_URL}/analytics/mood-trends`);
      const data = await res.json();

      if (!data?.labels) return;

      const formatted = data.labels.map((label, i) => ({
        date: label,
        mood: data.values[i],
      }));

      setChartData(formatted);
    } catch (err) {
      console.error(err);
    }
  };

  /* ================= UI ================= */

  return (
    <div className={darkMode ? "dashboard dark" : "dashboard"}>
      {!isLoggedIn ? (
        <div className="auth-screen">
          <div className="login-box">
            <p className="brand-pill">WellNest AI</p>
            <h2>{isRegister ? "Create your account" : "Welcome back"}</h2>
            <p className="auth-subtitle">
              Track your mood, reflect with AI, and build better daily wellness habits.
            </p>

            <input
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />

            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            {isRegister ? (
              <>
                <button onClick={register}>Register</button>
                <p className="auth-switch" onClick={() => setIsRegister(false)}>
                  Already have an account? Login
                </p>
              </>
            ) : (
              <>
                <button onClick={login}>Login</button>
                <p className="auth-switch" onClick={() => setIsRegister(true)}>
                  Create new account
                </p>
              </>
            )}
          </div>
        </div>
      ) : (
        <>
          {/* SIDEBAR */}

          <div className="sidebar">
            <h2>WellNest</h2>
            <p className="sidebar-user">@{username}</p>

            {NAV_ITEMS.map((item) => (
              <button
                key={item.key}
                className={page === item.key ? "active" : ""}
                onClick={() => setPage(item.key)}
              >
                <span>{item.icon}</span> {item.label}
              </button>
            ))}
          </div>

          {/* MAIN */}

          <div className="main-content">
            {page === "dashboard" && (
              <>
                <div className="hero">
                  <p className="hero-subtitle">Your daily wellness space</p>
                  <h1>{getGreeting()} 👋</h1>
                  <p className="hero-description">
                    Small reflections each day can create meaningful long-term change.
                  </p>
                </div>

                <div className="hero-stats">
                  <div className="hero-card">
                    <p>🔥 Streak</p>
                    <h3>{streak || 0} days</h3>
                  </div>
                  <div className="hero-card">
                    <p>📊 Avg mood</p>
                    <h3>{summary?.average || 0}/10</h3>
                  </div>
                  <div className="hero-card">
                    <p>📘 Journal entries</p>
                    <h3>{summary?.total_entries || 0}</h3>
                  </div>
                </div>

                {weeklyInsight && (
                  <div className="insight-modern">
                    <h3>🧠 Weekly Insight</h3>
                    <p>{weeklyInsight.insight}</p>
                  </div>
                )}
              </>
            )}

            {page === "mood" && (
              <div className="action-card">
                <h2>Log Mood</h2>
                <p>How are you feeling today on a scale of 1 to 10?</p>

                <input
                  type="number"
                  value={mood}
                  onChange={(e) => setMood(e.target.value)}
                  placeholder="1-10"
                />

                <button onClick={submitMood}>Submit</button>
              </div>
            )}

            {page === "chat" && (
              <div className="action-card">
                <h2>AI Journal</h2>
                <p>Write your thoughts and get a calm, helpful summary from AI.</p>

                <textarea
                  rows="6"
                  value={journal}
                  onChange={(e) => setJournal(e.target.value)}
                  placeholder="What happened today? How did it make you feel?"
                />

                <button onClick={submitJournal}>Ask AI</button>

                {response && <div className="ai-response">{response}</div>}
              </div>
            )}

            {page === "analytics" && (
              <div className="chart-box">
                <h2>Mood Trends</h2>
                <p className="chart-subtitle">Your recent mood history at a glance.</p>

                {chartData.length > 0 ? (
                  <div style={{ height: 320 }}>
                    <Bar
                      data={{
                        labels: chartData.map((item) => item.date),
                        datasets: [
                          {
                            label: "Mood",
                            data: chartData.map((item) => item.mood),
                            backgroundColor: "rgba(124, 58, 237, 0.85)",
                            borderRadius: 8,
                          },
                        ],
                      }}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          legend: { position: "top" },
                          title: { display: false },
                        },
                        scales: {
                          y: {
                            min: 0,
                            max: 10,
                            ticks: {
                              stepSize: 1,
                            },
                          },
                        },
                      }}
                    />
                  </div>
                ) : (
                  <div className="empty-state">
                    No mood data yet. Add your first mood entry to see analytics.
                  </div>
                )}
              </div>
            )}

            {page === "reports" && (
              <div className="action-card">
                <h2>Download Wellness Report</h2>
                <p>Export your progress in PDF or CSV format.</p>

                {reportStatusError && (
                  <p className="chart-subtitle">Status check failed. You can still try downloading.</p>
                )}

                {reportStatusLoaded && !reportStatus.has_journal_data && !reportStatusLoading && (
                  <p className="chart-subtitle">
                    Add at least one journal entry to enable report downloads.
                  </p>
                )}

                <button
                  className="download-btn"
                  onClick={() => downloadReport("pdf")}
                  disabled={shouldDisableReports}
                >
                  Download Wellness Report (PDF)
                </button>

                <button
                  className="download-btn"
                  onClick={() => downloadReport("csv")}
                  disabled={shouldDisableReports}
                >
                  Export Data (CSV)
                </button>
              </div>
            )}

            {page === "settings" && (
              <div className="settings-card">
                <h2>Settings</h2>

                <p>Username: {username}</p>

                <button onClick={() => setDarkMode(!darkMode)}>
                  {darkMode
                    ? "Switch to Light Mode ☀️"
                    : "Switch to Dark Mode 🌙"}
                </button>

                <button className="logout-modern" onClick={logout}>
                  Logout
                </button>

                <div className="privacy-controls">
                  <h3>Privacy Controls</h3>

                  <div className="privacy-group">
                    <h4>Share Report With Provider</h4>
                    <input
                      type="email"
                      placeholder="Provider email"
                      value={providerEmail}
                      onChange={(e) => setProviderEmail(e.target.value)}
                    />
                    <button
                      className="share-report-btn"
                      onClick={shareReportWithProvider}
                      disabled={privacyActionLoading}
                    >
                      Share Report
                    </button>
                  </div>

                  <div className="privacy-group">
                    <h4>Delete My Data</h4>
                    <button
                      className="delete-data-btn"
                      onClick={deleteAllMyData}
                      disabled={privacyActionLoading}
                    >
                      Delete All My Data
                    </button>
                  </div>

                  <div className="privacy-group">
                    <h4>Delete My Account</h4>
                    <button
                      className="delete-account-btn"
                      onClick={deleteMyAccount}
                      disabled={privacyActionLoading}
                    >
                      Delete My Account
                    </button>
                  </div>

                  {privacyMessage && <p className="privacy-message">{privacyMessage}</p>}
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default App;