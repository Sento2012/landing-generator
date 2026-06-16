import { useEffect, useRef, useState } from "react";

// ─── Types ───────────────────────────────────────────────────────────────────
type Step = "html" | "css" | "js";
type StepStatus = "pending" | "running" | "done";

type GenResult = { html: string; css: string; js: string };

type HistoryItem = {
  id: number;
  prompt: string;
  status: string;
  created_at: string;
};

type User = { id: number; email: string };

type WsGenEvent = {
  gen_id: number;
  type: "tool_start" | "tool_complete" | "tool_delta" | "done" | "error" | "status";
  tool?: string;
  result?: GenResult;
  message?: string;
  status?: "pending" | "running" | "completed" | "failed";
};

// ─── Token storage ───────────────────────────────────────────────────────────
const TOKEN_KEY = "auth_token";
const getToken = () => localStorage.getItem(TOKEN_KEY);
const setToken = (t: string | null) => {
  if (t) localStorage.setItem(TOKEN_KEY, t);
  else localStorage.removeItem(TOKEN_KEY);
};

function authHeaders(): Record<string, string> {
  const t = getToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

// ─── API ─────────────────────────────────────────────────────────────────────
async function apiMe(): Promise<User | null> {
  const r = await fetch("/api/auth/me", { headers: authHeaders() });
  if (!r.ok) return null;
  return r.json();
}

async function apiRegister(email: string, password: string): Promise<void> {
  const r = await fetch("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!r.ok) {
    const detail = await r.json().catch(() => ({ detail: r.statusText }));
    throw new Error(detail.detail ?? "Ошибка регистрации");
  }
}

async function apiLogin(email: string, password: string): Promise<string> {
  const r = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!r.ok) {
    const detail = await r.json().catch(() => ({ detail: r.statusText }));
    throw new Error(detail.detail ?? "Ошибка входа");
  }
  const data = await r.json();
  return data.access_token;
}

async function createGeneration(prompt: string): Promise<{ id: number }> {
  const r = await fetch("/api/generations", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ prompt }),
  });
  if (!r.ok) throw new Error(`Create failed: ${r.status}`);
  return r.json();
}

async function loadHistory(): Promise<HistoryItem[]> {
  const r = await fetch("/api/generations", { headers: authHeaders() });
  if (!r.ok) return [];
  const data = await r.json();
  return Array.isArray(data) ? data : (data.items ?? []);
}

async function loadGeneration(id: number): Promise<GenResult | null> {
  const r = await fetch(`/api/generations/${id}`, { headers: authHeaders() });
  if (!r.ok) return null;
  const data = await r.json();
  if (data.status !== "completed") return null;
  return { html: data.html, css: data.css, js: data.js };
}

// ─── Iframe srcDoc ───────────────────────────────────────────────────────────
function composeDocument(r: GenResult): string {
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Generated Landing</title>
  <style>${r.css || ""}</style>
</head>
<body>
${r.html || ""}
<script>${r.js || ""}</script>
</body>
</html>`;
}

// ─── Root: auth gate ─────────────────────────────────────────────────────────
export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      setLoading(false);
      return;
    }
    apiMe()
      .then((u) => {
        if (!u) setToken(null);
        setUser(u);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center bg-slate-100 text-slate-500">
        Загрузка…
      </div>
    );
  }

  if (!user) {
    return <AuthScreen onAuth={setUser} />;
  }

  return <GeneratorApp user={user} onLogout={() => { setToken(null); setUser(null); }} />;
}

// ─── Auth screen ─────────────────────────────────────────────────────────────
function AuthScreen({ onAuth }: { onAuth: (u: User) => void }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      if (mode === "register") {
        await apiRegister(email, password);
      }
      const token = await apiLogin(email, password);
      setToken(token);
      const me = await apiMe();
      if (me) onAuth(me);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="h-full flex items-center justify-center bg-slate-100">
      <div className="bg-white rounded-2xl shadow-md border w-full max-w-sm p-8">
        <h1 className="text-xl font-semibold text-slate-800 mb-1">
          Landing Generator
        </h1>
        <p className="text-sm text-slate-500 mb-6">
          {mode === "login" ? "Войти в аккаунт" : "Создать аккаунт"}
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs text-slate-500 uppercase tracking-wide">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={busy}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 outline-none focus:border-indigo-400"
            />
          </div>
          <div>
            <label className="text-xs text-slate-500 uppercase tracking-wide">Пароль</label>
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={busy}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 outline-none focus:border-indigo-400"
            />
            <p className="text-xs text-slate-400 mt-1">Минимум 8 символов</p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-3 text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={busy}
            className="w-full px-4 py-2 rounded-lg bg-indigo-600 text-white font-medium disabled:opacity-40 hover:bg-indigo-700 transition"
          >
            {busy ? "..." : mode === "login" ? "Войти" : "Зарегистрироваться"}
          </button>
        </form>

        <div className="mt-4 text-sm text-center text-slate-500">
          {mode === "login" ? "Нет аккаунта? " : "Уже есть аккаунт? "}
          <button
            type="button"
            onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(null); }}
            className="text-indigo-600 hover:underline font-medium"
          >
            {mode === "login" ? "Зарегистрироваться" : "Войти"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── WebSocket hook ──────────────────────────────────────────────────────────
const PING_INTERVAL_MS = 25_000;
const RECONNECT_DELAY_MS = 2_000;

function useGenerationSocket(
  onEvent: (event: WsGenEvent) => void,
  connectionStatusChanged: (connected: boolean) => void,
) {
  const wsRef = useRef<WebSocket | null>(null);
  const pingTimerRef = useRef<number | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);
  const closedManuallyRef = useRef(false);
  const onEventRef = useRef(onEvent);
  const onStatusRef = useRef(connectionStatusChanged);
  onEventRef.current = onEvent;
  onStatusRef.current = connectionStatusChanged;

  useEffect(() => {
    closedManuallyRef.current = false;

    function connect() {
      const token = encodeURIComponent(getToken() ?? "");
      const scheme = window.location.protocol === "https:" ? "wss" : "ws";
      const ws = new WebSocket(`${scheme}://${window.location.host}/ws?token=${token}`);
      wsRef.current = ws;

      ws.onopen = () => {
        onStatusRef.current(true);
        pingTimerRef.current = window.setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "ping" }));
          }
        }, PING_INTERVAL_MS);
      };

      ws.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        if (msg?.type === "pong") return;
        onEventRef.current(msg as WsGenEvent);
      };

      ws.onclose = () => {
        onStatusRef.current(false);
        if (pingTimerRef.current) window.clearInterval(pingTimerRef.current);
        pingTimerRef.current = null;
        if (!closedManuallyRef.current) {
          reconnectTimerRef.current = window.setTimeout(connect, RECONNECT_DELAY_MS);
        }
      };

      ws.onerror = () => {
        // onclose будет вызван следом — переподключаемся там.
      };
    }

    connect();
    return () => {
      closedManuallyRef.current = true;
      if (pingTimerRef.current) window.clearInterval(pingTimerRef.current);
      if (reconnectTimerRef.current) window.clearTimeout(reconnectTimerRef.current);
      wsRef.current?.close();
    };
  }, []);
}

// ─── Main app (after auth) ───────────────────────────────────────────────────
const TOOL_LABELS: Record<Step, string> = {
  html: "Структура (HTML)",
  css: "Стили (CSS)",
  js: "Интерактив (JS)",
};

function GeneratorApp({ user, onLogout }: { user: User; onLogout: () => void }) {
  const [prompt, setPrompt] = useState("");
  const [generating, setGenerating] = useState(false);
  const [steps, setSteps] = useState<Record<Step, StepStatus>>({
    html: "pending",
    css: "pending",
    js: "pending",
  });
  const [result, setResult] = useState<GenResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [wsConnected, setWsConnected] = useState(false);
  const activeGenIdRef = useRef<number | null>(null);

  useEffect(() => {
    loadHistory().then(setHistory);
  }, []);

  function resetState() {
    setResult(null);
    setErrorMsg(null);
    setSteps({ html: "pending", css: "pending", js: "pending" });
  }

  function handleWsEvent(event: WsGenEvent) {
    // Любое финальное событие → обновить историю (даже если это другой клиент / вкладка).
    if (event.type === "done" || event.type === "error" || event.status === "completed" || event.status === "failed") {
      loadHistory().then(setHistory);
    }
    // UI-шаги обновляем только для активной генерации.
    if (activeGenIdRef.current !== event.gen_id) return;

    if (event.type === "tool_start" && event.tool) {
      const tool = event.tool.replace("set_", "") as Step;
      if (tool === "html" || tool === "css" || tool === "js") {
        setSteps((prev) => ({ ...prev, [tool]: "running" }));
      }
    } else if (event.type === "tool_complete" && event.tool) {
      const tool = event.tool.replace("set_", "") as Step;
      if (tool === "html" || tool === "css" || tool === "js") {
        setSteps((prev) => ({ ...prev, [tool]: "done" }));
      }
    } else if (event.type === "done") {
      setResult(event.result ?? null);
      setSteps((prev) => ({ ...prev, js: event.result?.js ? "done" : "pending" }));
      setGenerating(false);
      activeGenIdRef.current = null;
    } else if (event.type === "error") {
      setErrorMsg(event.message ?? "Ошибка генерации");
      setGenerating(false);
      activeGenIdRef.current = null;
    }
  }

  useGenerationSocket(handleWsEvent, setWsConnected);

  async function handleGenerate() {
    if (!prompt.trim() || generating) return;
    resetState();
    setGenerating(true);
    try {
      const { id } = await createGeneration(prompt.trim());
      activeGenIdRef.current = id;
    } catch (err) {
      setErrorMsg((err as Error).message);
      setGenerating(false);
    }
  }

  async function handleHistoryClick(item: HistoryItem) {
    if (generating) return;
    setPrompt(item.prompt);
    resetState();
    if (item.status === "completed") {
      const data = await loadGeneration(item.id);
      if (data) {
        setResult(data);
        setSteps({
          html: "done",
          css: "done",
          js: data.js ? "done" : "pending",
        });
      }
    }
  }

  return (
    <div className="h-full flex bg-slate-100">
      <aside className="w-72 border-r bg-white p-4 overflow-y-auto flex flex-col">
        <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">
          История
        </h2>
        {history.length === 0 && (
          <p className="text-sm text-slate-400">Пусто. Сгенерируй первый лендинг.</p>
        )}
        <ul className="space-y-2 flex-1">
          {history.map((it) => (
            <li
              key={it.id}
              onClick={() => handleHistoryClick(it)}
              className="cursor-pointer rounded-lg p-2 hover:bg-slate-50 border border-slate-100"
              title={it.prompt}
            >
              <div className="text-sm text-slate-800 line-clamp-2">{it.prompt}</div>
              <div className="text-xs text-slate-400 mt-1">
                {new Date(it.created_at).toLocaleString()} · {it.status}
              </div>
            </li>
          ))}
        </ul>

        <div className="mt-4 pt-4 border-t text-xs text-slate-500">
          <div className="flex items-center gap-2 mb-2">
            <span
              className={`w-2 h-2 rounded-full ${wsConnected ? "bg-green-500" : "bg-slate-300"}`}
              title={wsConnected ? "WebSocket connected" : "Reconnecting..."}
            />
            <span className="font-medium text-slate-700 truncate" title={user.email}>
              {user.email}
            </span>
          </div>
          <button onClick={onLogout} className="text-indigo-600 hover:underline">
            Выйти
          </button>
        </div>
      </aside>

      <main className="flex-1 flex flex-col">
        <header className="bg-white border-b px-6 py-4">
          <h1 className="text-xl font-semibold text-slate-800">Landing Generator</h1>
          <p className="text-sm text-slate-500">
            Опиши лендинг — модель сгенерирует его за пару tool calls
          </p>
        </header>

        <div className="p-6 max-w-5xl w-full mx-auto flex flex-col gap-6 flex-1">
          <div className="bg-white rounded-xl shadow-sm border p-4">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              disabled={generating}
              rows={3}
              placeholder="Например: лендинг для SaaS, отслеживающего привычки. Фиолетовая палитра, секции hero / features / pricing / CTA"
              className="w-full resize-none rounded-lg border border-slate-200 px-3 py-2 outline-none focus:border-indigo-400"
            />
            <div className="flex justify-between items-center mt-3">
              <span className="text-xs text-slate-400">{prompt.length} / 2000</span>
              <button
                onClick={handleGenerate}
                disabled={generating || !prompt.trim()}
                className="px-4 py-2 rounded-lg bg-indigo-600 text-white font-medium disabled:opacity-40 hover:bg-indigo-700 transition"
              >
                {generating ? "Генерирую..." : "Сгенерировать"}
              </button>
            </div>
          </div>

          {generating && <StepsLoader steps={steps} />}
          {errorMsg && (
            <div className="bg-red-50 border border-red-200 text-red-800 rounded-xl p-4">
              <strong>Ошибка:</strong> {errorMsg}
            </div>
          )}
          {result && !generating && <Preview result={result} />}
        </div>
      </main>
    </div>
  );
}

// ─── Steps loader ────────────────────────────────────────────────────────────
function StepsLoader({ steps }: { steps: Record<Step, StepStatus> }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border p-6">
      <div className="flex items-center gap-3 mb-5">
        <div className="w-3 h-3 rounded-full bg-indigo-500 animate-pulse" />
        <span className="font-medium text-slate-800">Идёт генерация…</span>
      </div>
      <ul className="space-y-3">
        {(Object.keys(steps) as Step[]).map((step) => (
          <li key={step} className="flex items-center gap-3">
            <StepIcon status={steps[step]} />
            <span className={
              steps[step] === "done" ? "text-slate-700" :
              steps[step] === "running" ? "text-slate-800 font-medium" :
              "text-slate-400"
            }>
              {TOOL_LABELS[step]}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function StepIcon({ status }: { status: StepStatus }) {
  if (status === "done") {
    return (
      <div className="w-6 h-6 rounded-full bg-green-100 text-green-700 flex items-center justify-center text-xs">✓</div>
    );
  }
  if (status === "running") {
    return (
      <div className="w-6 h-6 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
    );
  }
  return <div className="w-6 h-6 rounded-full bg-slate-100" />;
}

// ─── Preview ─────────────────────────────────────────────────────────────────
function Preview({ result }: { result: GenResult }) {
  const doc = composeDocument(result);
  return (
    <div className="bg-white rounded-xl shadow-sm border overflow-hidden flex-1 flex flex-col min-h-[500px]">
      <div className="px-4 py-2 border-b flex items-center justify-between bg-slate-50">
        <span className="text-sm font-medium text-slate-700">Preview</span>
        <a
          href={`data:text/html;charset=utf-8,${encodeURIComponent(doc)}`}
          target="_blank"
          rel="noreferrer"
          className="text-sm text-indigo-600 hover:underline"
        >
          Открыть в новой вкладке ↗
        </a>
      </div>
      <iframe
        title="Generated landing"
        srcDoc={doc}
        sandbox="allow-scripts allow-forms"
        className="w-full flex-1 border-0 bg-white"
      />
    </div>
  );
}
