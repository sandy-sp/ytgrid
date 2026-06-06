export type ConnectionState = "checking" | "online" | "offline";

export type ActiveSession = {
  id: string;
  status?: string;
  loop?: number;
};

export type DashboardPayload = {
  active_sessions?: ActiveSession[];
  session_count?: number;
  system_health?: {
    cpu?: number | string;
    ram?: number | string;
  };
};

export type Profile = {
  id?: number;
  name: string;
  description?: string;
  entries?: ProfileEntry[];
};

export type ProfileEntry = {
  id?: number;
  video_url: string;
  speed: number;
  loop_count: number;
  sequence_order?: number;
};

export type TaskRequest = {
  session_id?: string;
  url: string;
  speed: number;
  loop_count: number;
  task_type: "video" | "playlist" | "channel";
};

export type ClientConfig = {
  apiBaseUrl: string;
  apiKey: string;
};

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function trimSlash(value: string) {
  return value.replace(/\/+$/, "");
}

export function inferTaskType(url: string): TaskRequest["task_type"] {
  if (url.includes("playlist?list=")) return "playlist";
  if (url.includes("/@") || url.includes("/channel/") || url.includes("/c/") || url.includes("/user/")) {
    return "channel";
  }
  return "video";
}

export function parseCsv(text: string): TaskRequest[] {
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  if (lines.length <= 1) return [];

  const headers = lines[0].split(",").map((header) => header.trim());
  return lines.slice(1).map((line, index) => {
    const values = line.split(",").map((value) => value.trim());
    const row = Object.fromEntries(headers.map((header, i) => [header, values[i] ?? ""]));
    const url = row.url;
    if (!url) {
      throw new Error(`CSV row ${index + 2} is missing url`);
    }
    const loopCount = Number(row.loop_count || row.loops || 1);
    const speed = Number(row.speed || 1);
    return {
      session_id: row.session_id || undefined,
      url,
      speed: Number.isFinite(speed) ? speed : 1,
      loop_count: Number.isFinite(loopCount) ? loopCount : 1,
      task_type: (row.task_type as TaskRequest["task_type"]) || inferTaskType(url),
    };
  });
}

export function createApiClient(config: ClientConfig) {
  const baseUrl = trimSlash(config.apiBaseUrl);

  async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers);
    if (config.apiKey) headers.set("X-API-Key", config.apiKey);

    const response = await fetch(`${baseUrl}${path}`, {
      ...init,
      headers,
    });

    if (!response.ok) {
      let message = response.statusText;
      try {
        const payload = await response.json();
        message = typeof payload.detail === "string" ? payload.detail : JSON.stringify(payload.detail ?? payload);
      } catch {
        // Keep status text when the response body is not JSON.
      }
      throw new ApiError(response.status, message);
    }

    if (response.status === 204) return undefined as T;
    return (await response.json()) as T;
  }

  return {
    health: () => request<{ status: string }>("/health"),
    tasks: () => request<{ active_sessions: ActiveSession[] }>("/tasks/"),
    startTask: (task: TaskRequest) =>
      request<{ message: string; session_id: string }>("/tasks/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(task),
      }),
    stopTask: (sessionId: string) =>
      request<{ message: string }>("/tasks/stop", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId }),
      }),
    profiles: () => request<Profile[]>("/profiles/"),
    createProfile: (name: string, description: string) =>
      request<{ status: string; profile_id: number }>("/profiles/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, description }),
      }),
    runProfile: (name: string) =>
      request<{ status: string; sessions: string[] }>(`/profiles/${encodeURIComponent(name)}/run`, {
        method: "POST",
      }),
    dashboardStreamUrl: () => {
      const url = new URL(`${baseUrl}/dashboard/stream`);
      if (config.apiKey) url.searchParams.set("api_key", config.apiKey);
      return url.toString();
    },
  };
}
