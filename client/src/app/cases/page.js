import Link from "next/link";
import { Check, AlertTriangle, Info, ChevronRight } from "lucide-react";
import { inr } from "@/lib/format";
import { getReconciliationCases, classifyStatus, formatCaseCode } from "@/lib/api";

export const metadata = {
  title: "Reconciliation Cases — ReconAI",
  description:
    "Browse reconciliation cases with per-case results: reconciled, exceptions and explained variances.",
};

const resultMeta = {
  reconciled: {
    label: "Reconciled",
    badge: "text-success bg-success-soft",
    icon: <Check className="h-3.5 w-3.5" strokeWidth={3} />,
  },
  exception: {
    label: "Exception",
    badge: "text-warning bg-warning-soft",
    icon: <AlertTriangle className="h-3.5 w-3.5" strokeWidth={2.6} />,
  },
  explained: {
    label: "Explained",
    badge: "text-info bg-info-soft",
    icon: <Info className="h-3.5 w-3.5" strokeWidth={2.6} />,
  },
};

export default async function CasesPage() {
  const cases = await getReconciliationCases();

  return (
    <main className="pt-10 sm:pt-14">
      <div className="rise-in">
        <h1 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">
          Reconciliation cases
        </h1>
        <p className="mt-2 text-muted-foreground">
          Select a case to open its investigation record.
        </p>
      </div>

      <section
        className="glass rise-in mt-8 overflow-hidden rounded-md"
        style={{ animationDelay: "80ms" }}
      >
        <div className="grid grid-cols-[1fr_auto_auto] items-center gap-4 border-b border-white/60 px-6 py-4 sm:grid-cols-[1.4fr_1fr_1fr]">
          <span className="text-xs font-semibold tracking-[0.08em] text-muted-foreground uppercase">
            Case
          </span>
          <span className="text-right text-xs font-semibold tracking-[0.08em] text-muted-foreground uppercase">
            Amount
          </span>
          <span className="text-right text-xs font-semibold tracking-[0.08em] text-muted-foreground uppercase">
            Result
          </span>
        </div>

        {cases.map((c) => {
          const meta = resultMeta[classifyStatus(c.status)];
          return (
            <Link
              key={c.case_id}
              href={`/investigation/${c.case_id}`}
              className="group grid grid-cols-[1fr_auto_auto] items-center gap-4 border-b border-white/40 px-6 py-5 transition-colors last:border-b-0 hover:bg-white/45 sm:grid-cols-[1.4fr_1fr_1fr]"
            >
              <div className="flex items-center gap-3">
                <span className="font-display text-sm font-semibold tracking-wide">
                  {formatCaseCode(c.case_id)}
                </span>
                <ChevronRight
                  className="h-4 w-4 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100"
                  strokeWidth={2.4}
                />
              </div>
              <span className="text-right font-medium tabular-nums">
                {inr(Number(c.expected_amount))}
              </span>
              <span className="flex justify-end">
                <span
                  className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1 text-xs font-semibold ${meta.badge}`}
                >
                  {meta.icon}
                  {meta.label}
                </span>
              </span>
            </Link>
          );
        })}
      </section>

      <p
        className="rise-in mt-4 text-xs text-muted-foreground"
        style={{ animationDelay: "160ms" }}
      >
        Showing {cases.length} cases from the latest run.
      </p>
    </main>
  );
}
