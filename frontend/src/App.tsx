import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Database,
  FileUp,
  KeyRound,
  LayoutDashboard,
  Link2,
  Play,
  PlugZap,
  RefreshCw,
  Server,
  Square,
  Upload,
} from "lucide-react";
import { ChangeEvent, FormEvent, useEffect, useMemo, useRef, useState } from "react";
import {
  ActiveSession,
  ClientConfig,
  ConnectionState,
  DashboardPayload,
  Profile,
  TaskRequest,
  createApiClient,
  inferTaskType,
  parseCsv,
} from "./api";

const STORAGE_KEY = "ytgrid.desktop.config";

type Notice = {
  tone: "success" | "error" | "info";
  message: string;
};

const defaultConfig: ClientConfig = {
  apiBaseUrl: "http://127.0.0.1:8000",
  apiKey: "",
};

function loadConfig(): ClientConfig {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? { ...defaultConfig, ...JSON.parse(saved) } : defaultConfig;
  } catch {
    return defaultConfig;
  }
}

function saveConfig(config: ClientConfig) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
}

function formatMetric(value: string | number | undefined) {
  if (value === undefined || value === "N/A") return "N/A";
  return `${value}%`;
}

function App() {
  const [config, setConfig] = useState<ClientConfig>(loadConfig);
  const [draftConfig, setDraftConfig] = useState<ClientConfig>(config);
  const [connection, setConnection] = useState<ConnectionState>("checking");
  const [sessions, setSessions] = useState<ActiveSession[]>([]);
  const [health, setHealth] = useState<DashboardPayload["system_health"]>({});
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [csvTasks, setCsvTasks] = useState<TaskRequest[]>([]);
  const [selectedProfile, setSelectedProfile] = useState("");
  const [newProfileName, setNewProfileName] = useState("");
  const [newProfileDescription, setNewProfileDescription] = useState("");
  const [task, setTask] = useState<TaskRequest>({
    url: "",
    speed: 1,
    loop_count: 1,
    task_type: "video",
  });
  const streamRef = useRef<EventSource | null>(null);

  const api = useMemo(() => createApiClient(config), [config]);

  async function refreshData() {
    try {
      const [tasks, profileList] = await Promise.all([api.tasks(), api.profiles().catch(() => [])]);
      setSessions(tasks.active_sessions || []);
      setProfiles(profileList);
      setConnection("online");
    } catch (error) {
      setConnection("offline");
      setNotice({ tone: "error", message: error instanceof Error ? error.message : "API is offline" });
    }
  }

  async function checkHealth() {
    setConnection("checking");
    try {
      await api.health();
      setConnection("online");
      await refreshData();
      setNotice({ tone: "success", message: "Connected to YTGrid API" });
    } catch (error) {
      setConnection("offline");
      setNotice({ tone: "error", message: error instanceof Error ? error.message : "Could not connect" });
    }
  }

  useEffect(() => {
    saveConfig(config);
    setDraftConfig(config);
    void checkHealth();

    streamRef.current?.close();
    const stream = new EventSource(api.dashboardStreamUrl());
    streamRef.current = stream;

    stream.onmessage = (event) => {
      const data = JSON.parse(event.data) as DashboardPayload;
      setSessions(data.active_sessions || []);
      setHealth(data.system_health || {});
      setConnection("online");
    };
    stream.onerror = () => {
      setConnection("offline");
    };

    return () => stream.close();
  }, [api, config]);

  async function submitConnection(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setConfig(draftConfig);
  }

  async function submitTask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const payload = {
        ...task,
        task_type: task.task_type || inferTaskType(task.url),
      };
      const response = await api.startTask(payload);
      setNotice({ tone: "success", message: response.message });
      setTask({ url: "", speed: 1, loop_count: 1, task_type: "video" });
      await refreshData();
    } catch (error) {
      setNotice({ tone: "error", message: error instanceof Error ? error.message : "Task launch failed" });
    }
  }

  async function stopTask(sessionId: string) {
    try {
      const response = await api.stopTask(sessionId);
      setNotice({ tone: "success", message: response.message });
      await refreshData();
    } catch (error) {
      setNotice({ tone: "error", message: error instanceof Error ? error.message : "Stop failed" });
    }
  }

  async function onCsvFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      const parsed = parseCsv(text).map((row) => ({
        ...row,
        loop_count: row.loop_count || 1,
        speed: row.speed || 1,
      }));
      setCsvTasks(parsed);
      setNotice({ tone: "info", message: `Loaded ${parsed.length} CSV tasks` });
    } catch (error) {
      setNotice({ tone: "error", message: error instanceof Error ? error.message : "Could not read CSV" });
    }
  }

  async function launchCsvTasks() {
    let started = 0;
    try {
      for (const csvTask of csvTasks) {
        await api.startTask(csvTask);
        started += 1;
      }
      setNotice({ tone: "success", message: `Started ${started} CSV tasks` });
      setCsvTasks([]);
      await refreshData();
    } catch (error) {
      setNotice({
        tone: "error",
        message: `Started ${started}; then failed: ${error instanceof Error ? error.message : "unknown error"}`,
      });
    }
  }

  async function createProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      await api.createProfile(newProfileName, newProfileDescription);
      setNewProfileName("");
      setNewProfileDescription("");
      setNotice({ tone: "success", message: "Profile created" });
      await refreshData();
    } catch (error) {
      setNotice({ tone: "error", message: error instanceof Error ? error.message : "Profile creation failed" });
    }
  }

  async function runProfile() {
    if (!selectedProfile) return;
    try {
      const response = await api.runProfile(selectedProfile);
      setNotice({ tone: "success", message: `Profile started: ${response.sessions.join(", ")}` });
      await refreshData();
    } catch (error) {
      setNotice({ tone: "error", message: error instanceof Error ? error.message : "Profile run failed" });
    }
  }

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">YT</div>
          <div>
            <strong>YTGrid</strong>
            <span>Desktop Controller</span>
          </div>
        </div>

        <nav className="nav">
          <a href="#overview">
            <LayoutDashboard size={18} /> Overview
          </a>
          <a href="#launch">
            <Play size={18} /> Launch
          </a>
          <a href="#batch">
            <FileUp size={18} /> Batch
          </a>
          <a href="#profiles">
            <Database size={18} /> Profiles
          </a>
        </nav>

        <form className="connection-card" onSubmit={submitConnection}>
          <label>
            <span>API URL</span>
            <div className="input-icon">
              <Server size={16} />
              <input
                value={draftConfig.apiBaseUrl}
                onChange={(event) => setDraftConfig({ ...draftConfig, apiBaseUrl: event.target.value })}
              />
            </div>
          </label>
          <label>
            <span>API Key</span>
            <div className="input-icon">
              <KeyRound size={16} />
              <input
                type="password"
                value={draftConfig.apiKey}
                onChange={(event) => setDraftConfig({ ...draftConfig, apiKey: event.target.value })}
              />
            </div>
          </label>
          <button className="primary" type="submit">
            <PlugZap size={16} /> Connect
          </button>
        </form>
      </aside>

      <section className="content">
        <header className="topbar">
          <div>
            <h1>YTGrid v3.2 Desktop Foundation</h1>
            <p>Local controller for the v3.1 automation API.</p>
          </div>
          <div className={`status-pill ${connection}`}>
            {connection === "online" ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
            {connection}
          </div>
        </header>

        {notice && (
          <div className={`notice ${notice.tone}`}>
            <span>{notice.message}</span>
            <button onClick={() => setNotice(null)}>Dismiss</button>
          </div>
        )}

        <section className="metrics" id="overview">
          <div className="metric">
            <Activity size={20} />
            <span>Active Sessions</span>
            <strong>{sessions.length}</strong>
          </div>
          <div className="metric">
            <Server size={20} />
            <span>CPU</span>
            <strong>{formatMetric(health?.cpu)}</strong>
          </div>
          <div className="metric">
            <Database size={20} />
            <span>RAM</span>
            <strong>{formatMetric(health?.ram)}</strong>
          </div>
          <button className="ghost metric-action" onClick={refreshData}>
            <RefreshCw size={18} /> Refresh
          </button>
        </section>

        <section className="panel">
          <div className="panel-heading">
            <h2>Running Sessions</h2>
          </div>
          <div className="session-table">
            {sessions.length === 0 ? (
              <div className="empty">No active sessions</div>
            ) : (
              sessions.map((session) => (
                <div className="session-row" key={session.id}>
                  <code>{session.id}</code>
                  <span>{session.loop ? `Loop ${session.loop}` : session.status || "running"}</span>
                  <button className="danger" onClick={() => void stopTask(session.id)}>
                    <Square size={15} /> Stop
                  </button>
                </div>
              ))
            )}
          </div>
        </section>

        <section className="two-column">
          <form className="panel" id="launch" onSubmit={submitTask}>
            <div className="panel-heading">
              <h2>Launch Task</h2>
            </div>
            <label>
              <span>YouTube URL</span>
              <div className="input-icon">
                <Link2 size={16} />
                <input
                  required
                  value={task.url}
                  placeholder="https://www.youtube.com/watch?v=..."
                  onChange={(event) =>
                    setTask({ ...task, url: event.target.value, task_type: inferTaskType(event.target.value) })
                  }
                />
              </div>
            </label>
            <div className="compact-grid">
              <label>
                <span>Speed</span>
                <input
                  type="number"
                  step="0.25"
                  min="0.25"
                  max="16"
                  value={task.speed}
                  onChange={(event) => setTask({ ...task, speed: Number(event.target.value) })}
                />
              </label>
              <label>
                <span>Loops</span>
                <input
                  type="number"
                  min="1"
                  max="1000"
                  value={task.loop_count}
                  onChange={(event) => setTask({ ...task, loop_count: Number(event.target.value) })}
                />
              </label>
              <label>
                <span>Type</span>
                <select
                  value={task.task_type}
                  onChange={(event) => setTask({ ...task, task_type: event.target.value as TaskRequest["task_type"] })}
                >
                  <option value="video">Video</option>
                  <option value="playlist">Playlist</option>
                  <option value="channel">Channel</option>
                </select>
              </label>
            </div>
            <button className="primary" type="submit">
              <Play size={16} /> Start Task
            </button>
          </form>

          <section className="panel" id="batch">
            <div className="panel-heading">
              <h2>CSV Batch</h2>
            </div>
            <label className="file-target">
              <Upload size={20} />
              <span>Choose CSV</span>
              <input type="file" accept=".csv,text/csv" onChange={onCsvFile} />
            </label>
            <div className="batch-summary">
              <strong>{csvTasks.length}</strong>
              <span>tasks loaded</span>
            </div>
            <button className="primary" disabled={csvTasks.length === 0} onClick={() => void launchCsvTasks()}>
              <Play size={16} /> Launch Batch
            </button>
          </section>
        </section>

        <section className="panel" id="profiles">
          <div className="panel-heading">
            <h2>Profiles</h2>
          </div>
          <div className="profile-grid">
            <form className="profile-form" onSubmit={createProfile}>
              <input
                placeholder="Profile name"
                value={newProfileName}
                onChange={(event) => setNewProfileName(event.target.value)}
                required
              />
              <input
                placeholder="Description"
                value={newProfileDescription}
                onChange={(event) => setNewProfileDescription(event.target.value)}
              />
              <button className="ghost" type="submit">
                Create
              </button>
            </form>
            <div className="profile-runner">
              <select value={selectedProfile} onChange={(event) => setSelectedProfile(event.target.value)}>
                <option value="">Select profile</option>
                {profiles.map((profile) => (
                  <option key={profile.id ?? profile.name} value={profile.name}>
                    {profile.name}
                  </option>
                ))}
              </select>
              <button className="primary" disabled={!selectedProfile} onClick={() => void runProfile()}>
                <Play size={16} /> Run Profile
              </button>
            </div>
          </div>
        </section>
      </section>
    </main>
  );
}

export default App;
