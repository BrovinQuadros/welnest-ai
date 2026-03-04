import { useState, useEffect } from "react";
import "./App.css";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

const BACKEND_URL = "http://127.0.0.1:8000";

/* ================= AUTH FETCH ================= */
const authFetch = async (url, options = {}) => {
  const token = localStorage.getItem("token");

  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  if (res.status === 401) {
    localStorage.removeItem("token");
    window.location.reload();
  }

  return res;
};

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [summary, setSummary] = useState(null);
  const [streak, setStreak] = useState(null);
  const [weeklyInsight, setWeeklyInsight] = useState(null);
  const [chartData, setChartData] = useState([]);

  const [mood, setMood] = useState("");
  const [journal, setJournal] = useState("");
  const [response, setResponse] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      setIsLoggedIn(true);
      loadDashboard();
    }
  }, []);

  const loadDashboard = async () => {
    fetchSummary();
    fetchStreak();
    fetchWeeklyInsight();
    fetchAnalytics();
  };

  /* ================= AUTH ================= */

  const login = async () => {
    const res = await fetch(`${BACKEND_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ username, password }),
    });

    const data = await res.json();
    if (!res.ok) return alert("Login failed");

    localStorage.setItem("token", data.access_token);
    setIsLoggedIn(true);
    loadDashboard();
  };

  const logout = () => {
    localStorage.removeItem("token");
    window.location.reload();
  };

  /* ================= MOOD ================= */

  const submitMood = async () => {
    const moodValue = Number(mood);
    if (isNaN(moodValue) || moodValue < 1 || moodValue > 10)
      return alert("Mood must be between 1 and 10");

    const res = await authFetch(`${BACKEND_URL}/mood`, {
      method: "POST",
      body: JSON.stringify({ mood_score: moodValue }),
    });

    if (!res.ok) return alert("Mood failed");

    setMood("");
    loadDashboard();
  };

  /* ================= JOURNAL ================= */

  const submitJournal = async () => {
    if (!journal.trim()) return alert("Journal empty");

    setResponse("Thinking... 🤖");

    const res = await authFetch(`${BACKEND_URL}/journal`, {
      method: "POST",
      body: JSON.stringify({ content: journal }),
    });

    const data = await res.json();
    if (!res.ok) return setResponse("Error");

    setResponse(data.ai_summary);
    setJournal("");
  };

  /* ================= ANALYTICS ================= */

  const fetchSummary = async () => {
    const res = await authFetch(`${BACKEND_URL}/analytics/summary`);
    const data = await res.json();
    if (res.ok) setSummary(data);
  };

  const fetchStreak = async () => {
    const res = await authFetch(`${BACKEND_URL}/analytics/streak`);
    const data = await res.json();
    if (res.ok) setStreak(data.streak);
  };

  const fetchWeeklyInsight = async () => {
    const res = await authFetch(`${BACKEND_URL}/analytics/weekly-ai-insight`);
    const data = await res.json();
    if (res.ok) setWeeklyInsight(data);
  };

  const fetchAnalytics = async () => {
    const res = await authFetch(`${BACKEND_URL}/analytics/mood-trends`);
    const data = await res.json();
    if (!res.ok) return;

    const formatted = data.labels.map((label, i) => ({
      date: label,
      mood: data.values[i],
    }));

    setChartData(formatted);
  };

  /* ================= UI ================= */

  return (
    <div className="app">
      {!isLoggedIn ? (
        <div className="login-box">
          <h2>Welcome to WellNest AI</h2>
          <input placeholder="Username" onChange={(e) => setUsername(e.target.value)} />
          <input type="password" placeholder="Password" onChange={(e) => setPassword(e.target.value)} />
          <button onClick={login}>Login</button>
        </div>
      ) : (
        <>
          {/* HERO SECTION */}
          <div className="hero">
            <h1>Good Afternoon 👋</h1>
            <p>Ready to continue your wellness journey?</p>

            <div className="hero-stats">
              <div className="hero-card">
                <span>🔥</span>
                <p>{streak || 0} days</p>
              </div>
              <div className="hero-card">
                <span>📊</span>
                <p>{summary?.average || 0} Avg Mood</p>
              </div>
              <div className="hero-card">
                <span>📘</span>
                <p>{summary?.total_entries || 0} Entries</p>
              </div>
            </div>
          </div>

          {/* DASHBOARD CARDS */}
          {summary && (
            <div className="dashboard-grid">
              <div className="card">Average <strong>{summary.average}</strong></div>
              <div className="card">Minimum <strong>{summary.minimum}</strong></div>
              <div className="card">Maximum <strong>{summary.maximum}</strong></div>
              <div className="card">Total Entries <strong>{summary.total_entries}</strong></div>
            </div>
          )}

          {/* INSIGHT */}
          {weeklyInsight && (
            <div className="insight-modern">
              <h3>Weekly Insight</h3>
              <p>{weeklyInsight.insight}</p>
            </div>
          )}

          {/* MOOD + JOURNAL */}
          <div className="actions">
            <div className="action-card">
              <h3>Log Mood</h3>
              <input
                type="number"
                min="1"
                max="10"
                placeholder="Mood 1-10"
                value={mood}
                onChange={(e) => setMood(e.target.value)}
              />
              <button onClick={submitMood}>Submit</button>
            </div>

            <div className="action-card">
              <h3>Journal</h3>
              <textarea
                rows="3"
                value={journal}
                onChange={(e) => setJournal(e.target.value)}
              />
              <button onClick={submitJournal}>Submit</button>
              <p>{response}</p>
            </div>
          </div>

          {/* CHART */}
          {chartData.length > 0 && (
            <div className="chart-box">
              <BarChart width={800} height={300} data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="mood" fill="#7c3aed" />
              </BarChart>
            </div>
          )}

          <button className="logout-modern" onClick={logout}>
            Logout
          </button>
        </>
      )}
    </div>
  );
}

export default App;
