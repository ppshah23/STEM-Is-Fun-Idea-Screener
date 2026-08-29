"use client";

import Image from "next/image";
import { useState } from "react";

type CheckDimension =
  | "grade_level_fit"
  | "materials_feasibility"
  | "instructor_capability"
  | "ai_assistance_value"
  | "time_scope_fit"
  | "safety"
  | "pedagogical_alignment";

const CHECK_LABELS: Record<CheckDimension, string> = {
  grade_level_fit: "Grade-level fit",
  materials_feasibility: "Materials feasibility",
  instructor_capability: "Instructor capability",
  ai_assistance_value: "AI assistance value",
  time_scope_fit: "Time / scope fit",
  safety: "Safety",
  pedagogical_alignment: "Pedagogical alignment",
};

type Assessment = {
  summary: string;
  verdict: "feasible" | "feasible_with_changes" | "needs_more_info" | "not_feasible";
  overall_score: number;
  safety_override: boolean;
  checks: Record<CheckDimension, { score: number; pass: boolean; notes: string; weight: number | null }>;
  blocking_issues: string[];
  open_questions: string[];
  suggested_changes: string[];
  mock: boolean;
};

type Message =
  | { role: "user"; content: string }
  | { role: "assistant"; status: "thinking" }
  | { role: "assistant"; status: "error"; content: string }
  | { role: "assistant"; status: "done"; assessment: Assessment };

const VERDICT_STYLE: Record<Assessment["verdict"], string> = {
  feasible: "bg-emerald-400/10 text-emerald-300 border-emerald-400/30",
  feasible_with_changes: "bg-amber-400/10 text-amber-300 border-amber-400/30",
  needs_more_info: "bg-sky-400/10 text-sky-300 border-sky-400/30",
  not_feasible: "bg-red-400/10 text-red-300 border-red-400/30",
};

const VERDICT_LABEL: Record<Assessment["verdict"], string> = {
  feasible: "Feasible",
  feasible_with_changes: "Feasible with changes",
  needs_more_info: "Needs more info",
  not_feasible: "Not feasible",
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "";

function scoreColor(score: number): string {
  if (score >= 70) return "text-emerald-400";
  if (score >= 40) return "text-amber-400";
  return "text-red-400";
}

function scoreBarColor(score: number): string {
  if (score >= 70) return "bg-emerald-400";
  if (score >= 40) return "bg-amber-400";
  return "bg-red-400";
}

function ChevronIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 20 20" fill="none" className={className} aria-hidden="true">
      <path d="M5 7.5L10 12.5L15 7.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function WarningIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 20 20" fill="none" className={className} aria-hidden="true">
      <path
        d="M8.68 3.5a1.5 1.5 0 0 1 2.64 0l6.32 11.4A1.5 1.5 0 0 1 16.32 17H3.68a1.5 1.5 0 0 1-1.32-2.1L8.68 3.5Z"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinejoin="round"
      />
      <path d="M10 8v3.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
      <circle cx="10" cy="13.6" r="0.9" fill="currentColor" />
    </svg>
  );
}

function SendIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 20 20" fill="none" className={className} aria-hidden="true">
      <path d="M10 15.5V4.5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
      <path d="M5 9.5L10 4.5L15 9.5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function AssessmentCard({ assessment }: { assessment: Assessment }) {
  return (
    <div className="space-y-5">
      {assessment.mock && (
        <div className="rounded-xl border border-purple-400/30 bg-purple-400/10 px-3 py-2 text-xs font-medium text-purple-200">
          MOCK MODE — this is randomized placeholder data. No API call was
          made and nothing here reflects a real screening.
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <span
          className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium ${VERDICT_STYLE[assessment.verdict]}`}
        >
          <span className="h-1.5 w-1.5 rounded-full bg-current" />
          {VERDICT_LABEL[assessment.verdict]}
        </span>
        <span className={`text-2xl font-bold tabular-nums ${scoreColor(assessment.overall_score)}`}>
          {assessment.overall_score}
          <span className="text-sm font-medium text-white/40">/100</span>
        </span>
      </div>

      {assessment.safety_override && (
        <p className="flex items-start gap-2 rounded-lg border border-red-400/30 bg-red-400/10 px-3 py-2 text-sm font-medium text-red-300">
          <WarningIcon className="mt-0.5 h-4 w-4 shrink-0" />
          Safety scored too low — this overrides every other dimension, regardless of score.
        </p>
      )}

      <p className="text-[15px] leading-relaxed text-white/90">{assessment.summary}</p>

      {assessment.blocking_issues.length > 0 && (
        <Section title="Blocking issues" accent="border-red-400/50">
          <ul className="list-disc space-y-1 pl-5 text-red-300/90">
            {assessment.blocking_issues.map((issue, i) => (
              <li key={i}>{issue}</li>
            ))}
          </ul>
        </Section>
      )}

      {assessment.open_questions.length > 0 && (
        <Section title="Open questions" accent="border-sky-400/50">
          <ul className="list-disc space-y-1 pl-5 text-white/80">
            {assessment.open_questions.map((q, i) => (
              <li key={i}>{q}</li>
            ))}
          </ul>
        </Section>
      )}

      {assessment.suggested_changes.length > 0 && (
        <Section title="Suggested changes" accent="border-emerald-400/50">
          <ul className="list-disc space-y-1 pl-5 text-white/80">
            {assessment.suggested_changes.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </Section>
      )}

      <details className="group rounded-xl border border-white/10 bg-white/[0.03] p-3.5 open:bg-white/[0.05]">
        <summary className="flex cursor-pointer list-none items-center justify-between text-sm font-medium text-white/80 marker:content-none [&::-webkit-details-marker]:hidden">
          Full rubric breakdown (weighted decision matrix)
          <ChevronIcon className="h-4 w-4 shrink-0 text-white/40 transition-transform duration-200 group-open:rotate-180" />
        </summary>
        <div className="mt-4 space-y-4 border-t border-white/10 pt-4">
          {(Object.keys(CHECK_LABELS) as CheckDimension[]).map((dim) => {
            const check = assessment.checks[dim];
            return (
              <div key={dim} className="text-sm">
                <div className="flex items-center justify-between font-medium text-white/80">
                  <span>
                    {CHECK_LABELS[dim]}
                    {check.weight !== null && (
                      <span className="ml-2 text-xs font-normal text-white/35">
                        {check.weight}% weight
                      </span>
                    )}
                    {check.weight === null && (
                      <span className="ml-2 text-xs font-normal text-white/35">
                        hard gate
                      </span>
                    )}
                  </span>
                  <span className={`font-semibold tabular-nums ${scoreColor(check.score)}`}>
                    {check.score}
                  </span>
                </div>
                <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-white/10">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${scoreBarColor(check.score)}`}
                    style={{ width: `${check.score}%` }}
                  />
                </div>
                <p className="mt-1.5 text-xs leading-relaxed text-white/50">{check.notes}</p>
              </div>
            );
          })}
        </div>
      </details>
    </div>
  );
}

function Section({ title, accent, children }: { title: string; accent: string; children: React.ReactNode }) {
  return (
    <div className={`border-l-2 ${accent} pl-3`}>
      <h3 className="text-xs font-semibold uppercase tracking-wider text-white/50">
        {title}
      </h3>
      <div className="mt-1.5 text-sm">{children}</div>
    </div>
  );
}

export default function Page() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const idea = input.trim();
    if (!idea || busy) return;

    setInput("");
    setBusy(true);
    setMessages((prev) => [
      ...prev,
      { role: "user", content: idea },
      { role: "assistant", status: "thinking" },
    ]);

    try {
      const res = await fetch(`${API_BASE}/api/screen-idea`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idea }),
      });
      if (!res.ok) {
        throw new Error(`Server returned ${res.status}`);
      }
      const assessment: Assessment = await res.json();
      setMessages((prev) => [
        ...prev.slice(0, -1),
        { role: "assistant", status: "done", assessment },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev.slice(0, -1),
        {
          role: "assistant",
          status: "error",
          content: err instanceof Error ? err.message : "Something went wrong.",
        },
      ]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="relative isolate flex flex-1 flex-col overflow-hidden">
      <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute -top-24 -left-16 h-72 w-72 rounded-full bg-rose-400/15 blur-3xl" />
        <div className="absolute -top-32 right-0 h-80 w-80 rounded-full bg-sky-400/20 blur-3xl" />
        <div className="absolute bottom-10 left-0 h-64 w-64 rounded-full bg-emerald-400/15 blur-3xl" />
        <div className="absolute bottom-0 right-10 h-72 w-72 rounded-full bg-amber-400/15 blur-3xl" />
      </div>

      <div className="relative z-10 mx-auto flex w-full max-w-3xl flex-1 flex-col px-4 py-6 md:py-10">
        <header className="flex items-center gap-4 pb-6">
          <div className="shrink-0 rounded-2xl bg-white p-2 shadow-lg shadow-black/20">
            <Image
              src="/stem-is-fun-logo.png"
              alt="STEM is Fun"
              width={360}
              height={172}
              priority
              className="h-10 w-auto"
            />
          </div>
          <div>
            <h1 className="text-xl font-semibold tracking-tight text-white">
              Idea Screener
            </h1>
            <p className="mt-0.5 text-sm text-white/60">
              Screened for grade fit, materials, instructor capability, AI value, scope &amp; safety.
            </p>
          </div>
        </header>

        <div className="flex-1 space-y-4 overflow-y-auto py-2">
          {messages.length === 0 && (
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-5 py-4 text-sm text-white/50">
              <p className="mb-1 font-medium text-white/70">Try an idea:</p>
              <p>&ldquo;Build a robotic arm that sorts LEGO bricks by color, for our summer coding camp.&rdquo;</p>
            </div>
          )}
          {messages.map((m, i) => {
            if (m.role === "user") {
              return (
                <div
                  key={i}
                  className="animate-fade-in ml-auto max-w-[80%] rounded-2xl rounded-br-md bg-gradient-to-br from-sky-500 to-indigo-500 px-4 py-2.5 text-sm text-white shadow-lg shadow-sky-500/10"
                >
                  {m.content}
                </div>
              );
            }
            return (
              <div
                key={i}
                className="animate-fade-in max-w-full rounded-2xl rounded-bl-md border border-white/10 bg-white/[0.04] px-5 py-4 shadow-xl shadow-black/20 backdrop-blur-sm"
              >
                {m.status === "thinking" && (
                  <div className="flex items-center gap-2 text-sm text-white/50">
                    <span className="flex gap-1">
                      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-sky-400 [animation-delay:-0.3s]" />
                      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-sky-400 [animation-delay:-0.15s]" />
                      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-sky-400" />
                    </span>
                    Screening idea…
                  </div>
                )}
                {m.status === "error" && (
                  <div className="flex items-center gap-2 text-sm text-red-300">
                    <WarningIcon className="h-4 w-4 shrink-0" />
                    {m.content}
                  </div>
                )}
                {m.status === "done" && <AssessmentCard assessment={m.assessment} />}
              </div>
            );
          })}
        </div>

        <form
          onSubmit={handleSubmit}
          className="mt-4 flex items-center gap-2 rounded-full border border-white/10 bg-white/5 p-1.5 pl-5 shadow-lg shadow-black/20 transition-colors focus-within:border-white/25"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Describe a STEM project idea…"
            className="flex-1 bg-transparent py-2 text-sm text-white placeholder:text-white/35 outline-none"
            disabled={busy}
          />
          <button
            type="submit"
            disabled={busy || !input.trim()}
            aria-label="Send"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-sky-400 to-indigo-500 text-white shadow-md shadow-sky-500/20 transition-transform enabled:hover:scale-105 disabled:opacity-30"
          >
            <SendIcon className="h-4 w-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
