import { Suspense } from "react";
import Link from "next/link";
import { Check, AlertTriangle, Info, ChevronRight, ChevronLeft } from "lucide-react";
import { inr } from "@/lib/format";
import { getReconciliationCasesPage, classifyStatus, formatCaseCode } from "@/lib/api";
import { Spinner } from "../spinner";

export const metadata = {
  title: "Reconciliation Cases — ReconAI",
  description:
    "Browse reconciliation cases with per-case results: reconciled, exceptions and explained variances.",
};

const PAGE_SIZE = 10;

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

function CasesTableLoading() {
  return (
    <div className="glass rise-in mt-8 flex min-h-[520px] flex-col items-center justify-center gap-3 rounded-md">
      <Spinner className="h-8 w-8" />
      <p className="text-sm text-muted-foreground">Loading</p>
    </div>
  );
}

async function CasesTable({ page: requestedPage }) {
  const {
    items: pageCases,
    page,
    total,
    total_pages: totalPages,
  } = await getReconciliationCasesPage(requestedPage, PAGE_SIZE);

  return (
    <>
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

        {pageCases.map((c) => {
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

      <div
        className="rise-in mt-4 flex flex-col items-start justify-between gap-3 sm:flex-row sm:items-center"
        style={{ animationDelay: "160ms" }}
      >
        <p className="text-xs text-muted-foreground">
          Showing {pageCases.length ? (page - 1) * PAGE_SIZE + 1 : 0}
          –{(page - 1) * PAGE_SIZE + pageCases.length} of {total} cases.
        </p>

        {totalPages > 1 && (
          <nav
            aria-label="Cases pagination"
            className="flex items-center gap-1"
          >
            <Link
              href={`/cases?page=${page - 1}`}
              aria-disabled={page === 1}
              className={`flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground transition-colors ${
                page === 1
                  ? "pointer-events-none opacity-40"
                  : "hover:bg-white/50 hover:text-foreground"
              }`}
            >
              <ChevronLeft className="h-4 w-4" strokeWidth={2.4} />
            </Link>

            {Array.from({ length: totalPages }, (_, i) => i + 1).map((n) => (
              <Link
                key={n}
                href={`/cases?page=${n}`}
                aria-current={n === page ? "page" : undefined}
                className={`flex h-8 w-8 items-center justify-center rounded-md text-xs font-semibold tabular-nums transition-colors ${
                  n === page
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-white/50 hover:text-foreground"
                }`}
              >
                {n}
              </Link>
            ))}

            <Link
              href={`/cases?page=${page + 1}`}
              aria-disabled={page === totalPages}
              className={`flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground transition-colors ${
                page === totalPages
                  ? "pointer-events-none opacity-40"
                  : "hover:bg-white/50 hover:text-foreground"
              }`}
            >
              <ChevronRight className="h-4 w-4" strokeWidth={2.4} />
            </Link>
          </nav>
        )}
      </div>
    </>
  );
}

export default async function CasesPage({ searchParams }) {
  const { page: pageParam } = await searchParams;
  const requestedPage = Math.max(1, Number(pageParam) || 1);

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

      <Suspense key={requestedPage} fallback={<CasesTableLoading />}>
        <CasesTable page={requestedPage} />
      </Suspense>
    </main>
  );
}
