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

type SuggestedPart = { name: string; url: string; note: string };

type Assessment = {
  summary: string;
  verdict: "feasible" | "feasible_with_changes" | "needs_more_info" | "not_feasible";
  overall_score: number;
  safety_override: boolean;
  checks: Record<CheckDimension, { score: number; pass: boolean; notes: string; weight: number | null }>;
  blocking_issues: string[];
  open_questions: string[];
  suggested_changes: string[];
  suggested_parts: SuggestedPart[];
  mock: boolean;
};

type Message =
  | { role: "user"; content: string }
  | { role: "assistant"; status: "classifying" }
  | { role: "assistant"; status: "classified"; classification: LevelClassification }
  | { role: "assistant"; status: "review-prompt"; curriculumText: string }
  | { role: "assistant"; status: "thinking" }
  | { role: "assistant"; status: "error"; content: string }
  | { role: "assistant"; status: "done"; assessment: Assessment; level: Level }
  | { role: "assistant"; status: "review-done"; review: CurriculumReview };

type InterviewTurn = { role: "ai" | "prompter"; message: string };

type RoadmapDay = {
  day: number;
  title: string;
  summary: string;
  key_activities: string[];
  materials: string[];
};

type Roadmap = {
  title: string;
  total_sessions: number;
  session_length_minutes: number;
  duration_summary: string;
  days: RoadmapDay[];
  open_questions: string[];
  shopping_list: SuggestedPart[];
};

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

type Level = "level_1" | "level_2" | "level_3";

type LevelSignalDimension =
  | "existing_artifact"
  | "relevant_experience"
  | "goal_clarity"
  | "decision_ownership"
  | "guidance_request";

type PughCriterion = { score: number; relative: -1 | 0 | 1; weight: number; weighted: number };
type PughCandidate = { criteria: Record<string, PughCriterion>; net_score: number };

type LevelClassification = {
  summary: string;
  level: Level;
  level_label: string;
  existing_artifact_override: boolean;
  matrix: { level_2: PughCandidate; level_3: PughCandidate };
  signals: Record<LevelSignalDimension, { score: number; notes: string }>;
  mock: boolean;
};

type ReviewItem = { item: string; reason: string };

type RestructuredSlideLayout =
  | "TITLE_AND_BODY"
  | "Statement"
  | "Section"
  | "Frame Only"
  | "Title Only"
  | "Agenda Numbered"
  | "Title & Bullets";

type RestructuredSlideType =
  | "title"
  | "hook"
  | "review_question"
  | "concept"
  | "challenge"
  | "activity_bridge"
  | "section_break"
  | "recap";

type RestructuredSlide = {
  order: number;
  layout: RestructuredSlideLayout;
  type: RestructuredSlideType;
  title: string;
  content: string;
  speaker_notes: string;
  source_reference: string;
};

type RestructuredDay = {
  day: number;
  title: string;
  slides: RestructuredSlide[];
};

type CurriculumReview = {
  summary: string;
  strengths: string[];
  cut_candidates: ReviewItem[];
  add_candidates: ReviewItem[];
  adjust_candidates: ReviewItem[];
  open_questions: string[];
  restructured_outline: RestructuredDay[];
};

const SLIDE_LAYOUT_STYLE: Record<RestructuredSlideLayout, string> = {
  TITLE_AND_BODY: "bg-indigo-400/10 text-indigo-300 border-indigo-400/30",
  Statement: "bg-sky-400/10 text-sky-300 border-sky-400/30",
  Section: "bg-amber-400/10 text-amber-300 border-amber-400/30",
  "Frame Only": "bg-white/10 text-white/60 border-white/20",
  "Title Only": "bg-white/10 text-white/60 border-white/20",
  "Agenda Numbered": "bg-emerald-400/10 text-emerald-300 border-emerald-400/30",
  "Title & Bullets": "bg-white/10 text-white/60 border-white/20",
};

const LEVEL_LABEL: Record<Level, string> = {
  level_1: "Guided",
  level_2: "Driven",
  level_3: "Review",
};

const LEVEL_STYLE: Record<Level, string> = {
  level_1: "bg-cyan-400/10 text-cyan-300 border-cyan-400/30",
  level_2: "bg-violet-400/10 text-violet-300 border-violet-400/30",
  level_3: "bg-pink-400/10 text-pink-300 border-pink-400/30",
};

const SIGNAL_LABEL: Record<LevelSignalDimension, string> = {
  existing_artifact: "Existing artifact",
  relevant_experience: "Relevant experience",
  goal_clarity: "Goal clarity",
  decision_ownership: "Decision ownership",
  guidance_request: "Guidance request",
};

function LevelBadge({ level }: { level: Level }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium ${LEVEL_STYLE[level]}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {LEVEL_LABEL[level]}
    </span>
  );
}

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

function CartIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 20 20" fill="none" className={className} aria-hidden="true">
      <path
        d="M3 3h1.5l1.6 8.6a1.5 1.5 0 0 0 1.48 1.23h6.1a1.5 1.5 0 0 0 1.47-1.19L16.5 6.5H5.1"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="8" cy="16.5" r="1.15" fill="currentColor" />
      <circle cx="14" cy="16.5" r="1.15" fill="currentColor" />
    </svg>
  );
}

function ExternalLinkIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 20 20" fill="none" className={className} aria-hidden="true">
      <path d="M8.5 5H5.5a1 1 0 0 0-1 1v8.5a1 1 0 0 0 1 1H14a1 1 0 0 0 1-1v-3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M11.5 3.5H16v4.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M16 3.5L9.5 10" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function CloseIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 20 20" fill="none" className={className} aria-hidden="true">
      <path d="M5 5l10 10M15 5L5 15" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

function AssessmentCard({
  assessment,
  level,
  onShowParts,
}: {
  assessment: Assessment;
  level?: Level;
  onShowParts: (parts: SuggestedPart[]) => void;
}) {
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
        {level && <LevelBadge level={level} />}
        <span className={`text-2xl font-bold tabular-nums ${scoreColor(assessment.overall_score)}`}>
          {assessment.overall_score}
          <span className="text-sm font-medium text-white/40">/100</span>
        </span>
        {(assessment.suggested_parts ?? []).length > 0 && (
          <button
            type="button"
            onClick={() => onShowParts(assessment.suggested_parts)}
            className="ml-auto inline-flex items-center gap-1.5 rounded-full border border-amber-400/30 bg-amber-400/10 px-3 py-1 text-xs font-medium text-amber-300 transition-colors hover:bg-amber-400/20"
          >
            <CartIcon className="h-3.5 w-3.5" />
            Suggested parts ({assessment.suggested_parts.length})
          </button>
        )}
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

function ClassificationCard({ classification }: { classification: LevelClassification }) {
  const { level, summary, matrix, mock } = classification;
  return (
    <div className="space-y-4">
      {mock && (
        <div className="rounded-xl border border-purple-400/30 bg-purple-400/10 px-3 py-2 text-xs font-medium text-purple-200">
          MOCK MODE — this is randomized placeholder data. No API call was
          made and nothing here reflects a real classification.
        </div>
      )}
      <div className="flex flex-wrap items-center gap-3">
        <LevelBadge level={level} />
      </div>
      <p className="text-[15px] leading-relaxed text-white/90">{summary}</p>
      <details className="group rounded-xl border border-white/10 bg-white/[0.03] p-3.5 open:bg-white/[0.05]">
        <summary className="flex cursor-pointer list-none items-center justify-between text-sm font-medium text-white/80 marker:content-none [&::-webkit-details-marker]:hidden">
          Pugh matrix (how this was decided)
          <ChevronIcon className="h-4 w-4 shrink-0 text-white/40 transition-transform duration-200 group-open:rotate-180" />
        </summary>
        <div className="mt-4 space-y-5 border-t border-white/10 pt-4">
          {(["level_2", "level_3"] as const).map((candidate) => (
            <div key={candidate} className="text-sm">
              <div className="flex items-center justify-between font-medium text-white/80">
                <span>{LEVEL_LABEL[candidate]} vs. Guided (datum)</span>
                <span
                  className={`font-semibold tabular-nums ${
                    matrix[candidate].net_score > 0 ? "text-emerald-400" : "text-white/40"
                  }`}
                >
                  net {matrix[candidate].net_score > 0 ? "+" : ""}
                  {matrix[candidate].net_score}
                </span>
              </div>
              <div className="mt-2 space-y-1">
                {Object.entries(matrix[candidate].criteria).map(([dim, c]) => (
                  <div key={dim} className="flex items-center justify-between text-xs text-white/60">
                    <span>{SIGNAL_LABEL[dim as LevelSignalDimension]}</span>
                    <span className="flex items-center gap-2 tabular-nums">
                      <span>{c.score}</span>
                      <span
                        className={
                          c.relative > 0 ? "text-emerald-400" : c.relative < 0 ? "text-red-400" : "text-white/30"
                        }
                      >
                        {c.relative > 0 ? "▲" : c.relative < 0 ? "▼" : "–"}
                      </span>
                      <span className="text-white/30">×{c.weight}</span>
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </details>
    </div>
  );
}

function ReviewItemList({ items }: { items: ReviewItem[] }) {
  return (
    <ul className="space-y-2">
      {items.map((entry, i) => (
        <li key={i} className="text-white/80">
          <span className="font-medium text-white/90">{entry.item}</span> — {entry.reason}
        </li>
      ))}
    </ul>
  );
}

function RestructuredOutlineView({ days }: { days: RestructuredDay[] }) {
  if (days.length === 0) return null;
  return (
    <Section title="Restructured into the house format" accent="border-indigo-400/50">
      <p className="mb-3 text-xs text-white/50">
        Same content, reorganized onto the STEM is FUN day-arc and slide-layout skeleton — every
        slide traces back to something already in the original submission.
      </p>
      <div className="space-y-3">
        {days.map((day) => (
          <details
            key={day.day}
            className="group rounded-xl border border-white/10 bg-white/[0.03] p-3.5 open:bg-white/[0.05]"
          >
            <summary className="flex cursor-pointer list-none items-center justify-between text-sm font-medium text-white/80 marker:content-none [&::-webkit-details-marker]:hidden">
              <span className="flex items-center gap-2">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-400 to-sky-500 text-xs font-bold text-[#0a1f44]">
                  {day.day}
                </span>
                {day.title}
              </span>
              <span className="flex items-center gap-2 text-xs font-normal text-white/40">
                {day.slides.length} slides
                <ChevronIcon className="h-4 w-4 shrink-0 transition-transform duration-200 group-open:rotate-180" />
              </span>
            </summary>
            <div className="mt-3 space-y-2 border-t border-white/10 pt-3">
              {day.slides.map((slide) => (
                <div
                  key={slide.order}
                  className="rounded-lg border border-white/10 bg-white/[0.02] p-3 text-sm"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-semibold text-white/40">#{slide.order}</span>
                    <span
                      className={`rounded-full border px-2 py-0.5 text-[11px] font-medium ${SLIDE_LAYOUT_STYLE[slide.layout]}`}
                    >
                      {slide.layout}
                    </span>
                    <span className="text-[11px] uppercase tracking-wider text-white/30">
                      {slide.type.replace("_", " ")}
                    </span>
                  </div>
                  <p className="mt-1.5 font-medium text-white/90">{slide.title}</p>
                  <p className="mt-1 whitespace-pre-wrap text-white/70">{slide.content}</p>
                  {slide.speaker_notes && (
                    <p className="mt-1.5 text-xs italic text-white/45">{slide.speaker_notes}</p>
                  )}
                  <p className="mt-1.5 text-[11px] text-white/35">
                    Source: {slide.source_reference}
                  </p>
                </div>
              ))}
            </div>
          </details>
        ))}
      </div>
    </Section>
  );
}

function ReviewCard({ review }: { review: CurriculumReview }) {
  return (
    <div className="space-y-5">
      <p className="flex items-start gap-2 rounded-lg border border-sky-400/30 bg-sky-400/10 px-3 py-2 text-sm font-medium text-sky-300">
        These are observations, not a rewrite — you decide what to act on.
      </p>
      <p className="text-[15px] leading-relaxed text-white/90">{review.summary}</p>
      {review.strengths.length > 0 && (
        <Section title="Strengths" accent="border-emerald-400/50">
          <ul className="list-disc space-y-1 pl-5 text-white/80">
            {review.strengths.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </Section>
      )}
      {review.cut_candidates.length > 0 && (
        <Section title="Consider cutting" accent="border-red-400/50">
          <ReviewItemList items={review.cut_candidates} />
        </Section>
      )}
      {review.add_candidates.length > 0 && (
        <Section title="Consider adding" accent="border-emerald-400/50">
          <ReviewItemList items={review.add_candidates} />
        </Section>
      )}
      {review.adjust_candidates.length > 0 && (
        <Section title="Consider adjusting" accent="border-amber-400/50">
          <ReviewItemList items={review.adjust_candidates} />
        </Section>
      )}
      {review.open_questions.length > 0 && (
        <Section title="Open questions" accent="border-sky-400/50">
          <ul className="list-disc space-y-1 pl-5 text-white/80">
            {review.open_questions.map((q, i) => (
              <li key={i}>{q}</li>
            ))}
          </ul>
        </Section>
      )}
      <RestructuredOutlineView days={review.restructured_outline} />
    </div>
  );
}

function ReviewPromptForm({
  busy,
  onSubmit,
}: {
  busy: boolean;
  onSubmit: (constraints: string) => void;
}) {
  const [constraints, setConstraints] = useState("");
  return (
    <div className="space-y-3">
      <p className="text-sm text-white/70">
        This looks like an already-completed project or curriculum. Any constraints for the
        review? (time limit, different age group, materials change — optional)
      </p>
      <div className="flex items-center gap-2">
        <input
          value={constraints}
          onChange={(e) => setConstraints(e.target.value)}
          placeholder="e.g. need to cut to 3 sessions"
          className="flex-1 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-white placeholder:text-white/35 outline-none focus:border-white/25"
          disabled={busy}
        />
        <button
          type="button"
          onClick={() => onSubmit(constraints.trim())}
          disabled={busy}
          className="shrink-0 rounded-full bg-gradient-to-br from-sky-400 to-indigo-500 px-4 py-2 text-sm font-medium text-white shadow-md shadow-sky-500/20 transition-transform enabled:hover:scale-105 disabled:opacity-30"
        >
          Get feedback
        </button>
      </div>
    </div>
  );
}

function RoadmapView({
  roadmap,
  level,
  onShowParts,
}: {
  roadmap: Roadmap;
  level?: Level;
  onShowParts: (parts: SuggestedPart[]) => void;
}) {
  return (
    <div className="space-y-5">
      <div>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold text-white">{roadmap.title}</h3>
            {level && <LevelBadge level={level} />}
          </div>
          {(roadmap.shopping_list ?? []).length > 0 && (
            <button
              type="button"
              onClick={() => onShowParts(roadmap.shopping_list)}
              className="inline-flex items-center gap-1.5 rounded-full border border-amber-400/30 bg-amber-400/10 px-3 py-1 text-xs font-medium text-amber-300 transition-colors hover:bg-amber-400/20"
            >
              <CartIcon className="h-3.5 w-3.5" />
              Shopping list ({roadmap.shopping_list.length})
            </button>
          )}
        </div>
        <p className="mt-1 text-sm text-white/60">
          <span className="font-medium text-white/80">
            {roadmap.total_sessions} sessions x {roadmap.session_length_minutes} min
          </span>{" "}
          — {roadmap.duration_summary}
        </p>
      </div>

      <div className="space-y-3">
        {roadmap.days.map((day) => (
          <div key={day.day} className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
            <div className="flex items-center gap-2">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-sky-400 to-indigo-500 text-xs font-bold text-[#0a1f44]">
                {day.day}
              </span>
              <p className="text-sm font-medium text-white">{day.title}</p>
            </div>
            <p className="mt-2 text-sm text-white/70">{day.summary}</p>
            {day.key_activities.length > 0 && (
              <div className="mt-2">
                <p className="text-xs font-semibold uppercase tracking-wider text-white/40">Activities</p>
                <ul className="mt-1 list-disc space-y-0.5 pl-5 text-sm text-white/70">
                  {day.key_activities.map((a, i) => (
                    <li key={i}>{a}</li>
                  ))}
                </ul>
              </div>
            )}
            {day.materials.length > 0 && (
              <div className="mt-2">
                <p className="text-xs font-semibold uppercase tracking-wider text-white/40">Materials</p>
                <ul className="mt-1 list-disc space-y-0.5 pl-5 text-sm text-white/70">
                  {day.materials.map((m, i) => (
                    <li key={i}>{m}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>

      {roadmap.open_questions.length > 0 && (
        <Section title="Open questions" accent="border-sky-400/50">
          <ul className="list-disc space-y-1 pl-5 text-white/80">
            {roadmap.open_questions.map((q, i) => (
              <li key={i}>{q}</li>
            ))}
          </ul>
        </Section>
      )}
    </div>
  );
}

export default function Page() {
  const [mode, setMode] = useState<"screen" | "interview">("screen");

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [partsPanelOpen, setPartsPanelOpen] = useState(false);
  const [partsPanelItems, setPartsPanelItems] = useState<SuggestedPart[]>([]);
  const [sessionLevel, setSessionLevel] = useState<Level | null>(null);

  const [interviewIdea, setInterviewIdea] = useState<string | null>(null);
  const [transcript, setTranscript] = useState<InterviewTurn[]>([]);
  const [interviewStatus, setInterviewStatus] = useState<"asking" | "ready">("asking");
  const [interviewInput, setInterviewInput] = useState("");
  const [interviewBusy, setInterviewBusy] = useState(false);
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [roadmapBusy, setRoadmapBusy] = useState(false);
  const [roadmapError, setRoadmapError] = useState<string | null>(null);

  function openPartsPanel(parts: SuggestedPart[]) {
    setPartsPanelItems(parts);
    setPartsPanelOpen(true);
  }

  function resetInterview() {
    setInterviewIdea(null);
    setTranscript([]);
    setInterviewStatus("asking");
    setRoadmap(null);
    setRoadmapError(null);
    setSessionLevel(null);
  }

  async function handleInterviewSubmit(e: React.FormEvent) {
    e.preventDefault();
    const text = interviewInput.trim();
    if (!text || interviewBusy) return;
    setInterviewInput("");
    setInterviewBusy(true);

    const isFirstMessage = interviewIdea === null;
    const idea = interviewIdea ?? text;
    const nextTranscript = isFirstMessage ? transcript : [...transcript, { role: "prompter" as const, message: text }];
    if (isFirstMessage) {
      setInterviewIdea(text);
    } else {
      setTranscript(nextTranscript);
    }

    let level = sessionLevel;
    if (isFirstMessage && level === null) {
      try {
        const classifyRes = await fetch(`${API_BASE}/api/classify-level`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ idea: text }),
        });
        if (classifyRes.ok) {
          const classification: LevelClassification = await classifyRes.json();
          level = classification.level;
          setSessionLevel(classification.level);
        }
      } catch {
        // Classification is enrichment here, not a hard gate -- fall through
        // to the interview even if it fails.
      }
    }

    try {
      const res = await fetch(`${API_BASE}/api/interview-turn`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          idea,
          transcript: nextTranscript,
          level: level === "level_1" || level === "level_2" ? level : null,
        }),
      });
      if (!res.ok) {
        throw new Error(`Server returned ${res.status}`);
      }
      const turn: { status: "asking" | "ready"; message: string } = await res.json();
      setTranscript((prev) => [...prev, { role: "ai", message: turn.message }]);
      setInterviewStatus(turn.status);
    } catch (err) {
      setTranscript((prev) => [
        ...prev,
        { role: "ai", message: err instanceof Error ? err.message : "Something went wrong." },
      ]);
    } finally {
      setInterviewBusy(false);
    }
  }

  async function handleGenerateRoadmap() {
    if (!interviewIdea || roadmapBusy) return;
    setRoadmapBusy(true);
    setRoadmapError(null);
    try {
      const res = await fetch(`${API_BASE}/api/generate-roadmap`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          idea: interviewIdea,
          transcript,
          level: sessionLevel === "level_1" || sessionLevel === "level_2" ? sessionLevel : null,
        }),
      });
      if (!res.ok) {
        throw new Error(`Server returned ${res.status}`);
      }
      const result: Roadmap = await res.json();
      setRoadmap(result);
    } catch (err) {
      setRoadmapError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setRoadmapBusy(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const idea = input.trim();
    if (!idea || busy) return;

    setInput("");
    setBusy(true);
    setMessages((prev) => [
      ...prev,
      { role: "user", content: idea },
      { role: "assistant", status: "classifying" },
    ]);

    let level: Level | null = null;
    try {
      const classifyRes = await fetch(`${API_BASE}/api/classify-level`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idea }),
      });
      if (!classifyRes.ok) {
        throw new Error(`Server returned ${classifyRes.status}`);
      }
      const classification: LevelClassification = await classifyRes.json();
      level = classification.level;
      setSessionLevel(classification.level);
      setMessages((prev) => [
        ...prev.slice(0, -1),
        { role: "assistant", status: "classified", classification },
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
      setBusy(false);
      return;
    }

    if (level === "level_3") {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", status: "review-prompt", curriculumText: idea },
      ]);
      setBusy(false);
      return;
    }

    setMessages((prev) => [...prev, { role: "assistant", status: "thinking" }]);
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
        { role: "assistant", status: "done", assessment, level: level as Level },
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

  async function handleReviewSubmit(curriculumText: string, constraints: string) {
    setBusy(true);
    setMessages((prev) => [...prev, { role: "assistant", status: "thinking" }]);
    try {
      const res = await fetch(`${API_BASE}/api/review-curriculum`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ curriculum_text: curriculumText, constraints: constraints || null }),
      });
      if (!res.ok) {
        throw new Error(`Server returned ${res.status}`);
      }
      const review: CurriculumReview = await res.json();
      setMessages((prev) => [
        ...prev.slice(0, -1),
        { role: "assistant", status: "review-done", review },
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

        <div className="mb-4 flex gap-1 rounded-full border border-white/10 bg-white/5 p-1">
          <button
            type="button"
            onClick={() => setMode("screen")}
            className={`flex-1 rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
              mode === "screen" ? "bg-white/10 text-white" : "text-white/50 hover:text-white/80"
            }`}
          >
            Screen an idea
          </button>
          <button
            type="button"
            onClick={() => setMode("interview")}
            disabled={sessionLevel === "level_3"}
            title={
              sessionLevel === "level_3"
                ? "This session is a curriculum review -- there's no roadmap to build."
                : undefined
            }
            className={`flex-1 rounded-full px-3 py-1.5 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-30 ${
              mode === "interview" ? "bg-white/10 text-white" : "text-white/50 hover:text-white/80"
            }`}
          >
            Build a roadmap
          </button>
        </div>

        {mode === "screen" && (
        <>
        <div className="flex-1 space-y-4 overflow-y-auto py-2">
          {messages.length === 0 && (
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-5 py-4 text-sm text-white/50">
              <p className="mb-1 font-medium text-white/70">Try an idea:</p>
              <p>&ldquo;Build a robotic arm that sorts LEGO bricks by color, for our summer coding camp.&rdquo;</p>
              <p className="mt-2 text-white/40">
                Already have a finished project or curriculum? Paste it here instead for feedback.
              </p>
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
                {m.status === "classifying" && (
                  <div className="flex items-center gap-2 text-sm text-white/50">
                    <span className="flex gap-1">
                      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-sky-400 [animation-delay:-0.3s]" />
                      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-sky-400 [animation-delay:-0.15s]" />
                      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-sky-400" />
                    </span>
                    Figuring out how much guidance you need…
                  </div>
                )}
                {m.status === "classified" && (
                  <ClassificationCard classification={m.classification} />
                )}
                {m.status === "review-prompt" && (
                  <ReviewPromptForm
                    busy={busy}
                    onSubmit={(constraints) => handleReviewSubmit(m.curriculumText, constraints)}
                  />
                )}
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
                {m.status === "done" && (
                  <AssessmentCard assessment={m.assessment} level={m.level} onShowParts={openPartsPanel} />
                )}
                {m.status === "review-done" && <ReviewCard review={m.review} />}
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
        </>
        )}

        {mode === "interview" && (
        <>
        <div className="flex-1 space-y-4 overflow-y-auto py-2">
          {interviewIdea === null && (
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-5 py-4 text-sm text-white/50">
              <p className="mb-1 font-medium text-white/70">Start with your idea:</p>
              <p>
                Claude will ask one follow-up question at a time, drilling toward specifics
                (audience, timeline, materials, goals) until you say you&rsquo;re ready to
                generate a day-by-day roadmap.
              </p>
            </div>
          )}
          {interviewIdea !== null && (
            <div className="animate-fade-in ml-auto max-w-[80%] rounded-2xl rounded-br-md bg-gradient-to-br from-sky-500 to-indigo-500 px-4 py-2.5 text-sm text-white shadow-lg shadow-sky-500/10">
              {interviewIdea}
            </div>
          )}
          {interviewIdea !== null && sessionLevel && (
            <div className="flex justify-end">
              <LevelBadge level={sessionLevel} />
            </div>
          )}
          {transcript.map((turn, i) =>
            turn.role === "prompter" ? (
              <div
                key={i}
                className="animate-fade-in ml-auto max-w-[80%] rounded-2xl rounded-br-md bg-gradient-to-br from-sky-500 to-indigo-500 px-4 py-2.5 text-sm text-white shadow-lg shadow-sky-500/10"
              >
                {turn.message}
              </div>
            ) : (
              <div
                key={i}
                className="animate-fade-in max-w-full rounded-2xl rounded-bl-md border border-white/10 bg-white/[0.04] px-5 py-4 text-sm text-white/90 shadow-xl shadow-black/20 backdrop-blur-sm"
              >
                {turn.message}
              </div>
            )
          )}
          {interviewBusy && (
            <div className="animate-fade-in max-w-full rounded-2xl rounded-bl-md border border-white/10 bg-white/[0.04] px-5 py-4 shadow-xl shadow-black/20 backdrop-blur-sm">
              <div className="flex items-center gap-2 text-sm text-white/50">
                <span className="flex gap-1">
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-sky-400 [animation-delay:-0.3s]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-sky-400 [animation-delay:-0.15s]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-sky-400" />
                </span>
                Thinking…
              </div>
            </div>
          )}
          {interviewStatus === "ready" && interviewIdea !== null && !interviewBusy && !roadmap && (
            <div className="animate-fade-in flex justify-center">
              <button
                type="button"
                onClick={handleGenerateRoadmap}
                disabled={roadmapBusy}
                className="inline-flex items-center gap-2 rounded-full bg-gradient-to-br from-emerald-400 to-sky-500 px-4 py-2 text-sm font-medium text-[#0a1f44] shadow-lg shadow-emerald-500/20 transition-transform enabled:hover:scale-105 disabled:opacity-40"
              >
                {roadmapBusy ? "Generating roadmap…" : "Generate curriculum roadmap"}
              </button>
            </div>
          )}
          {roadmapError && (
            <div className="animate-fade-in flex items-center gap-2 rounded-xl border border-red-400/30 bg-red-400/10 px-4 py-3 text-sm text-red-300">
              <WarningIcon className="h-4 w-4 shrink-0" />
              {roadmapError}
            </div>
          )}
          {roadmap && (
            <div className="animate-fade-in max-w-full rounded-2xl border border-white/10 bg-white/[0.04] px-5 py-4 shadow-xl shadow-black/20 backdrop-blur-sm">
              <RoadmapView roadmap={roadmap} level={sessionLevel ?? undefined} onShowParts={openPartsPanel} />
            </div>
          )}
        </div>

        <form
          onSubmit={handleInterviewSubmit}
          className="mt-4 flex items-center gap-2 rounded-full border border-white/10 bg-white/5 p-1.5 pl-5 shadow-lg shadow-black/20 transition-colors focus-within:border-white/25"
        >
          <input
            value={interviewInput}
            onChange={(e) => setInterviewInput(e.target.value)}
            placeholder={interviewIdea === null ? "Describe your idea…" : "Your answer…"}
            className="flex-1 bg-transparent py-2 text-sm text-white placeholder:text-white/35 outline-none"
            disabled={interviewBusy}
          />
          {interviewIdea !== null && (
            <button
              type="button"
              onClick={resetInterview}
              className="shrink-0 text-xs font-medium text-white/40 transition-colors hover:text-white/70"
            >
              Start over
            </button>
          )}
          <button
            type="submit"
            disabled={interviewBusy || !interviewInput.trim()}
            aria-label="Send"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-sky-400 to-indigo-500 text-white shadow-md shadow-sky-500/20 transition-transform enabled:hover:scale-105 disabled:opacity-30"
          >
            <SendIcon className="h-4 w-4" />
          </button>
        </form>
        </>
        )}
      </div>

      {partsPanelOpen && (
        <div
          onClick={() => setPartsPanelOpen(false)}
          className="animate-fade-in fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
        />
      )}
      <aside
        className={`fixed right-0 top-0 z-50 flex h-full w-full max-w-sm flex-col border-l border-white/10 bg-[#0d234d]/95 shadow-2xl shadow-black/40 backdrop-blur-xl transition-transform duration-300 ease-out ${
          partsPanelOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
          <div className="flex items-center gap-2">
            <CartIcon className="h-4 w-4 text-amber-300" />
            <h2 className="text-sm font-semibold text-white">Suggested parts</h2>
          </div>
          <button
            type="button"
            onClick={() => setPartsPanelOpen(false)}
            aria-label="Close"
            className="flex h-7 w-7 items-center justify-center rounded-full text-white/50 transition-colors hover:bg-white/10 hover:text-white"
          >
            <CloseIcon className="h-4 w-4" />
          </button>
        </div>
        <div className="flex-1 space-y-3 overflow-y-auto px-5 py-4">
          {partsPanelItems.map((part, i) => (
            <div key={i} className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
              <p className="text-sm font-medium text-white">{part.name}</p>
              <p className="mt-1 text-xs leading-relaxed text-white/60">{part.note}</p>
              <a
                href={part.url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-sky-300 transition-colors hover:text-sky-200"
              >
                View listing
                <ExternalLinkIcon className="h-3.5 w-3.5" />
              </a>
            </div>
          ))}
        </div>
      </aside>
    </div>
  );
}
