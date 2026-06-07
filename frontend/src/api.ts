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

function parseCsvLine(line: string): string[] {
  const values: string[] = [];
  let current = "";
  let inQuotes = false;

  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    const next = line[index + 1];

    if (char === '"' && inQuotes && next === '"') {
      current += '"';
      index += 1;
      continue;
    }

    if (char === '"') {
      inQuotes = !inQuotes;
      continue;
    }

    if (char === "," && !inQuotes) {
      values.push(current.trim());
      current = "";
      continue;
    }

    current += char;
  }

  if (inQuotes) {
    throw new Error("CSV contains an unterminated quoted value");
  }

  values.push(current.trim());
  return values;
}

function coercePositiveNumber(value: string, fallback: number, field: string, rowNumber: number) {
  if (!value) return fallback;
  const numberValue = Number(value);
  if (!Number.isFinite(numberValue) || numberValue <= 0) {
    throw new Error(`CSV row ${rowNumber} has invalid ${field}`);
  }
  return numberValue;
}

function normalizeTaskType(value: string, url: string, rowNumber: number): TaskRequest["task_type"] {
  if (!value) return inferTaskType(url);
  if (value === "video" || value === "playlist" || value === "channel") return value;
  throw new Error(`CSV row ${rowNumber} has invalid task_type`);
}

export function parseCsv(text: string): TaskRequest[] {
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  if (lines.length <= 1) return [];

  const headers = parseCsvLine(lines[0]).map((header) => header.trim());
  return lines.slice(1).map((line, index) => {
    const rowNumber = index + 2;
    const values = parseCsvLine(line);
    const row = Object.fromEntries(headers.map((header, i) => [header, values[i] ?? ""]));
    const url = row.url;
    if (!url) {
      throw new Error(`CSV row ${rowNumber} is missing url`);
    }
    return {
      session_id: row.session_id || undefined,
      url,
      speed: coercePositiveNumber(row.speed, 1, "speed", rowNumber),
      loop_count: coercePositiveNumber(row.loop_count || row.loops, 1, "loop_count", rowNumber),
      task_type: normalizeTaskType(row.task_type, url, rowNumber),
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
