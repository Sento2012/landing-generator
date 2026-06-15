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

// ─── API helpers ─────────────────────────────────────────────────────────────
async function createGeneration(prompt: string): Promise<{ id: number }> {
  const r = await fetch("/api/generations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  if (!r.ok) throw new Error(`Create failed: ${r.status}`);
  return r.json();
}

async function loadHistory(): Promise<HistoryItem[]> {
  const r = await fetch("/api/generations");
  if (!r.ok) return [];
  return r.json();
}

async function loadGeneration(id: number): Promise<GenResult | null> {
  const r = await fetch(`/api/generations/${id}`);
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

// ─── Main ────────────────────────────────────────────────────────────────────
const TOOL_LABELS: Record<Step, string> = {
  html: "Структура (HTML)",
  css: "Стили (CSS)",
  js: "Интерактив (JS)",
};

export default function App() {
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
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    loadHistory().then(setHistory);
    return () => esRef.current?.close();
  }, []);

  function resetState() {
    setResult(null);
    setErrorMsg(null);
    setSteps({ html: "pending", css: "pending", js: "pending" });
  }

  async function handleGenerate() {
    if (!prompt.trim() || generating) return;
    resetState();
    setGenerating(true);

    try {
      const { id } = await createGeneration(prompt.trim());

      const es = new EventSource(`/api/generations/${id}/stream`);
      esRef.current = es;

      es.addEventListener("tool_start", (e) => {
        const data = JSON.parse((e as MessageEvent).data);
        const tool = (data.tool as string).replace("set_", "") as Step;
        setSteps((prev) => ({ ...prev, [tool]: "running" }));
      });

      es.addEventListener("tool_complete", (e) => {
        const data = JSON.parse((e as MessageEvent).data);
        const tool = (data.tool as string).replace("set_", "") as Step;
        setSteps((prev) => ({ ...prev, [tool]: "done" }));
      });

      es.addEventListener("done", (e) => {
        const data = JSON.parse((e as MessageEvent).data);
        setResult(data.result);
        // js может быть пропущен моделью
        setSteps((prev) => ({
          ...prev,
          js: data.result.js ? "done" : "pending",
        }));
        setGenerating(false);
        es.close();
        loadHistory().then(setHistory);
      });

      es.addEventListener("error", (e) => {
        // У EventSource error может быть и для разрыва сети без data;
        // мы шлём с бэка кастомное error-событие с data — обработаем оба.
        const msg = (e as MessageEvent).data
          ? JSON.parse((e as MessageEvent).data).message
          : "Соединение оборвалось";
        setErrorMsg(msg);
        setGenerating(false);
        es.close();
      });
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
      {/* Sidebar — история */}
      <aside className="w-72 border-r bg-white p-4 overflow-y-auto">
        <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">
          История
        </h2>
        {history.length === 0 && (
          <p className="text-sm text-slate-400">Пусто. Сгенерируй первый лендинг.</p>
        )}
        <ul className="space-y-2">
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
      </aside>

      {/* Main */}
      <main className="flex-1 flex flex-col">
        <header className="bg-white border-b px-6 py-4">
          <h1 className="text-xl font-semibold text-slate-800">Landing Generator</h1>
          <p className="text-sm text-slate-500">
            Опиши лендинг — Claude его сгенерирует за пару tool calls
          </p>
        </header>

        <div className="p-6 max-w-5xl w-full mx-auto flex flex-col gap-6 flex-1">
          {/* Prompt */}
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
              <span className="text-xs text-slate-400">
                {prompt.length} / 2000
              </span>
              <button
                onClick={handleGenerate}
                disabled={generating || !prompt.trim()}
                className="px-4 py-2 rounded-lg bg-indigo-600 text-white font-medium disabled:opacity-40 hover:bg-indigo-700 transition"
              >
                {generating ? "Генерирую..." : "Сгенерировать"}
              </button>
            </div>
          </div>

          {/* Loader / error / preview */}
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
        <span className="font-medium text-slate-800">Claude генерирует лендинг…</span>
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
        // sandbox без allow-same-origin — JS изолирован от родителя
        sandbox="allow-scripts allow-forms"
        className="w-full flex-1 border-0 bg-white"
      />
    </div>
  );
}
