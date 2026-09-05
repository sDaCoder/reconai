import { CheckCircle2, AlertTriangle, ShieldCheck } from "lucide-react";
import { getReconciliationCases, classifyStatus } from "@/lib/api";

async function getStats() {
  const cases = await getReconciliationCases();

  const processed = cases.length;
  const exceptions = cases.filter(
    (c) => classifyStatus(c.status) === "exception",
  ).length;
  const autoResolved = processed - exceptions;
  const accuracy = processed ? (autoResolved / processed) * 100 : 0;
  const avgConfidence = processed
    ? (cases.reduce((sum, c) => sum + c.confidence, 0) / processed) * 100
    : 0;

  return { processed, autoResolved, exceptions, accuracy, avgConfidence };
}

function StatCard({ label, value, detail, icon, delay }) {
  return (
    <div
      className="glass rise-in rounded-md p-6 transition-transform duration-300 hover:-translate-y-0.5"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm font-medium text-muted-foreground">{label}</p>
        {icon}
      </div>
      <p className="font-display mt-4 text-4xl font-bold tracking-tight tabular-nums">
        {value}
      </p>
      {detail && (
        <p className="mt-1.5 text-[0.8rem] text-muted-foreground">{detail}</p>
      )}
    </div>
  );
}

function BreakdownChart({ stats, delay }) {
  const total = stats.processed;
  const segments = [
    {
      label: "Auto-resolved",
      value: stats.autoResolved,
      color: "oklch(0.52 0 0)",
    },
    {
      label: "Exceptions",
      value: stats.exceptions,
      color: "oklch(0.78 0 0)",
    },
  ];

  // Donut geometry — small gap between segments for definition
  const r = 66;
  const c = 2 * Math.PI * r;
  const gap = 3; // degrees of visual gap per segment boundary
  let offset = 0;
  const arcs = segments.map((s) => {
    const sweep = (s.value / total) * c;
    const arc = { ...s, dash: Math.max(sweep - (gap / 360) * c, 1), offset };
    offset += sweep;
    return arc;
  });
  const pct = (stats.autoResolved / total) * 100;

  return (
    <section
      className="glass rise-in mt-4 rounded-md p-8 sm:p-12"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex flex-col items-center gap-8 sm:flex-row sm:gap-12">
        <div
          className="relative shrink-0"
          aria-label="Reconciliation breakdown donut chart"
        >
          <svg
            width="184"
            height="184"
            viewBox="0 0 184 184"
            role="img"
            className="-rotate-90"
          >
            <circle
              cx="92"
              cy="92"
              r={r}
              fill="none"
              stroke="oklch(1 0 0 / 45%)"
              strokeWidth="16"
            />
            {arcs.map((a) => (
              <circle
                key={a.label}
                cx="92"
                cy="92"
                r={r}
                fill="none"
                stroke={a.color}
                strokeWidth="16"
                strokeDasharray={`${a.dash} ${c - a.dash}`}
                strokeDashoffset={-a.offset}
                strokeLinecap="round"
              />
            ))}
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="font-display text-3xl font-bold tabular-nums">
              {pct.toFixed(0)}%
            </span>
            <span className="text-xs text-muted-foreground">
              auto-resolved
            </span>
          </div>
        </div>

        <div className="flex-1">
          <h2 className="font-display text-lg font-semibold tracking-tight">
            Reconciliation breakdown
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Latest run · {total.toLocaleString("en-IN")} records
          </p>
          <ul className="mt-5 space-y-3">
            {segments.map((s) => (
              <li key={s.label} className="flex items-center gap-3">
                <span
                  aria-hidden
                  className="h-3 w-3 shrink-0 rounded-full"
                  style={{ background: s.color }}
                />
                <span className="text-sm">{s.label}</span>
                <span className="ml-auto text-sm font-medium tabular-nums text-muted-foreground">
                  {s.value.toLocaleString("en-IN")} ·{" "}
                  {((s.value / total) * 100).toFixed(0)}%
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}

export default async function Dashboard() {
  const stats = await getStats();
  const autoResolvedPct = stats.processed
    ? (stats.autoResolved / stats.processed) * 100
    : 0;

  return (
    <main className="pt-10 sm:pt-14">
      <div className="rise-in">
        <h1 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">
          Reconciliation overview
        </h1>
        <p className="mt-2 text-muted-foreground">
          Latest run · {stats.processed.toLocaleString("en-IN")} records
        </p>
      </div>

      <section className="mt-8 grid gap-4 sm:grid-cols-3">
        <StatCard
          label="Records processed"
          value={stats.processed.toLocaleString("en-IN")}
          detail="Across all channels"
          icon={<CheckCircle2 className="h-5 w-5 text-info" strokeWidth={2.2} />}
          delay={0}
        />
        <StatCard
          label="Auto-resolved"
          value={stats.autoResolved.toLocaleString("en-IN")}
          detail={`${autoResolvedPct.toFixed(0)}% of all records`}
          icon={<ShieldCheck className="h-5 w-5 text-success" strokeWidth={2.2} />}
          delay={70}
        />
        <StatCard
          label="Exceptions"
          value={stats.exceptions.toLocaleString("en-IN")}
          detail="Queued for review"
          icon={
            <AlertTriangle className="h-5 w-5 text-warning" strokeWidth={2.2} />
          }
          delay={140}
        />
      </section>

      <section className="mt-4 grid gap-4 sm:grid-cols-2">
        <StatCard
          label="Accuracy"
          value={`${stats.accuracy.toFixed(1)}%`}
          detail="Auto-resolved share of all reconciled legs"
          delay={210}
        />
        <StatCard
          label="Avg. confidence"
          value={`${stats.avgConfidence.toFixed(1)}%`}
          detail="Model confidence across all cases"
          delay={280}
        />
      </section>

      <BreakdownChart stats={stats} delay={350} />
    </main>
  );
}
