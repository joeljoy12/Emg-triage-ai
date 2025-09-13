import React, { useEffect, useMemo, useState } from "react";
import tailwindcss from 'tailwindcss';
import env from  'dotenv/config'
// ──────────────────────────────────────────────────────────────
// Config
// ──────────────────────────────────────────────────────────────
const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";


// Tailwind badge colors by triage level
const TRIAGE_COLORS: Record<string, string> = {
  Immediate: "bg-red-600 text-white",
  Delayed: "bg-yellow-500 text-black",
  Minor: "bg-green-600 text-white",
  Expectant: "bg-gray-800 text-white",
};

// Small helper
function cx(...classes: (string | false | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}

// Types for API contract
type TriageIn = {
  description: string;
  vitals?: {
    resp_rate?: number | null;
    pulse?: string | null;
    cap_refill?: string | number | null;
  } | null;
};

type TriageOut = {
  triage_level: "Immediate" | "Delayed" | "Minor" | "Expectant";
  actions: string[];
  reasoning: string;
  disclaimer: string;
};

export default function App() {
  // Form state
  const [description, setDescription] = useState(
    localStorage.getItem("triage_desc") || "40M, heavy forearm bleeding, pale, dizzy, responsive to voice"
  );
  const [respRate, setRespRate] = useState<string>("");
  const [pulse, setPulse] = useState<string>("");
  const [capRefill, setCapRefill] = useState<string>("");

  // Runtime state
  const [health, setHealth] = useState<{ ok: boolean; offline: boolean } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TriageOut | null>(null);

  // Health check once
  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${API_BASE}/health`);
        const j = await r.json();
        setHealth(j);
      } catch (e) {
        setHealth({ ok: false, offline: false });
      }
    })();
  }, []);

  useEffect(() => {
    localStorage.setItem("triage_desc", description);
  }, [description]);

  // Build the POST payload from current form
  const payload: TriageIn = useMemo(() => {
    const v: TriageIn["vitals"] = {};
    if (respRate !== "") v!.resp_rate = Number(respRate);
    if (pulse) v!.pulse = pulse;
    if (capRefill !== "") v!.cap_refill = capRefill; // allow "<2" or numeric or ">2"

    return {
      description: description.trim(),
      vitals: Object.keys(v!).length ? v : undefined,
    };
  }, [description, respRate, pulse, capRefill]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    setResult(null);

    try {
      const r = await fetch(`${API_BASE}/triage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const j: TriageOut = await r.json();
      setResult(j);
    } catch (err: any) {
      setError(err?.message || "Request failed");
    } finally {
      setLoading(false);
    }
  }

  function fillExample(desc: string, rr?: number, pulse?: string, cap?: string) {
    setDescription(desc);
    setRespRate(rr !== undefined ? String(rr) : "");
    setPulse(pulse ?? "");
    setCapRefill(cap ?? "");
    setResult(null);
    setError(null);
  }

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100">
      <header className="sticky top-0 z-10 border-b border-neutral-800 bg-neutral-950/80 backdrop-blur">
        <div className="mx-auto max-w-5xl px-4 py-4 flex items-center gap-3">
          <div className="text-xl font-bold">🚑 Emergency Triage (Offline)</div>
          {health && (
            <span
              className={cx(
                "ml-auto rounded-full px-3 py-1 text-sm",
                health.ok ? "bg-emerald-600 text-white" : "bg-red-600 text-white"
              )}
            >
              {health.ok ? (health.offline ? "API OK • Offline Mode" : "API OK") : "API Unavailable"}
            </span>
          )}
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-6 grid gap-6 md:grid-cols-5">
        {/* Left: form */}
        <section className="md:col-span-3">
          <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-4 shadow">
            <h2 className="mb-3 text-lg font-semibold">Enter Case</h2>
            <form className="space-y-4" onSubmit={onSubmit}>
              <div>
                <label className="mb-1 block text-sm text-neutral-300">Description</label>
                <textarea
                  className="w-full rounded-xl border border-neutral-700 bg-neutral-950 p-3 outline-none focus:ring-2 focus:ring-sky-600"
                  rows={5}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="e.g., 40M, heavy forearm bleeding, pale, dizzy, responsive to voice"
                  required
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="mb-1 block text-sm text-neutral-300">Respiratory Rate (breaths/min)</label>
                  <input
                    type="number"
                    min="0"
                    className="w-full rounded-xl border border-neutral-700 bg-neutral-950 p-2.5 outline-none focus:ring-2 focus:ring-sky-600"
                    value={respRate}
                    onChange={(e) => setRespRate(e.target.value)}
                    placeholder="e.g., 28 or 40"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-neutral-300">Pulse</label>
                  <select
                    className="w-full rounded-xl border border-neutral-700 bg-neutral-950 p-2.5 outline-none focus:ring-2 focus:ring-sky-600"
                    value={pulse}
                    onChange={(e) => setPulse(e.target.value)}
                  >
                    <option value="">— optional —</option>
                    <option>strong</option>
                    <option>normal</option>
                    <option>weak</option>
                    <option>none</option>
                    <option>absent</option>
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-sm text-neutral-300">Capillary Refill</label>
                  {/* Use a select so special characters are safely escaped in JSX */}
                  <select
                    className="w-full rounded-xl border border-neutral-700 bg-neutral-950 p-2.5 outline-none focus:ring-2 focus:ring-sky-600"
                    value={capRefill}
                    onChange={(e) => setCapRefill(e.target.value)}
                  >
                    <option value="">— optional —</option>
                    <option value="<2">&lt;2</option>
                    <option value="2">2</option>
                    <option value=">2">&gt;2</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <button
                  type="submit"
                  disabled={loading}
                  className={cx(
                    "rounded-xl px-4 py-2 font-medium",
                    loading ? "bg-sky-900 text-neutral-300" : "bg-sky-600 hover:bg-sky-500 text-white"
                  )}
                >
                  {loading ? "Triaging…" : "Run Triage"}
                </button>
                {error && <div className="text-red-400 text-sm">{error}</div>}
              </div>
            </form>
          </div>

          {/* Examples */}
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <button
              onClick={() => fillExample("No breathing, no pulse", 0, "none", ">2")}
              className="rounded-xl border border-neutral-800 bg-neutral-900 p-3 text-left hover:bg-neutral-800"
            >
              🔴 Expectant – no breathing + no pulse
            </button>
            <button
              onClick={() => fillExample("Respiratory rate 40/min, speaking in short phrases", 40, "strong", "<2")}
              className="rounded-xl border border-neutral-800 bg-neutral-900 p-3 text-left hover:bg-neutral-800"
            >
              🔴 Immediate – RR &gt; 30
            </button>
            <button
              onClick={() => fillExample("Walking with small cuts, talking clearly", 18, "strong", "<2")}
              className="rounded-xl border border-neutral-800 bg-neutral-900 p-3 text-left hover:bg-neutral-800"
            >
              🟢 Minor – ambulatory
            </button>
          </div>
        </section>

        {/* Right: result */}
        <section className="md:col-span-2">
          <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-4 shadow min-h-[220px]">
            <h2 className="mb-3 text-lg font-semibold">Result</h2>
            {!result ? (
              <div className="text-neutral-400">Submit a case to see the triage result.</div>
            ) : (
              <ResultCard result={result} />
            )}
          </div>
        </section>
      </main>

      <footer className="mx-auto max-w-5xl px-4 pb-8 text-xs text-neutral-400">
        Built for the OpenAI Open Model Hackathon • Offline-first • Demo only
      </footer>
    </div>
  );
}

function ResultCard({ result }: { result: TriageOut }) {
  const color = TRIAGE_COLORS[result.triage_level] ?? "bg-neutral-700";
  const [checked, setChecked] = useState<boolean[]>(() => new Array(result.actions.length).fill(false));

  useEffect(() => {
    setChecked(new Array(result.actions.length).fill(false));
  }, [result.actions.length]);

  function copyJSON() {
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
    navigator.clipboard.writeText(JSON.stringify(result, null, 2));
    // also offer a download
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `triage_${result.triage_level.toLowerCase()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <span className={cx("rounded-full px-3 py-1 text-sm font-semibold", color)}>
          {result.triage_level}
        </span>
        <button
          onClick={copyJSON}
          className="ml-auto rounded-lg border border-neutral-700 px-3 py-1 text-sm hover:bg-neutral-800"
        >
          Copy / Download JSON
        </button>
      </div>

      <div>
        <div className="mb-2 text-sm uppercase tracking-wide text-neutral-400">Actions</div>
        <ul className="space-y-2">
          {result.actions.map((a, i) => (
            <li key={i} className="flex items-start gap-2">
              <input
                type="checkbox"
                className="mt-1 h-4 w-4 rounded border-neutral-600 bg-neutral-950"
                checked={checked[i]}
                onChange={(e) => setChecked((prev) => prev.map((v, j) => (j === i ? e.target.checked : v)))}
              />
              <span className={checked[i] ? "line-through text-neutral-400" : ""}>{a}</span>
            </li>)
          )}
        </ul>
      </div>

      <div>
        <div className="mb-1 text-sm uppercase tracking-wide text-neutral-400">Reasoning</div>
        <p className="rounded-xl border border-neutral-800 bg-neutral-950 p-3 text-neutral-200">
          {result.reasoning}
        </p>
      </div>

      <div className="text-xs text-neutral-400">{result.disclaimer}</div>
    </div>
  );
}
