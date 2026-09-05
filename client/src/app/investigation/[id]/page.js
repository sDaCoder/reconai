import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, Check, AlertTriangle, Info } from "lucide-react";
import { inr } from "@/lib/format";
import {
  getReconciliationCases,
  classifyStatus,
  formatCaseCode,
  formatStatusLabel,
} from "@/lib/api";

async function findCase(id) {
  const cases = await getReconciliationCases();
  return cases.find((c) => String(c.case_id) === id);
}

export async function generateMetadata({ params }) {
  const { id } = await params;
  const c = await findCase(id);
  if (!c) {
    return { title: "Case not found — ReconAI", robots: { index: false } };
  }
  return { title: `Case ${formatCaseCode(c.case_id)} — ReconAI`, robots: { index: false } };
}

const decisionStyle = {
  reconciled: {
    badge: "text-success bg-success-soft",
    label: "Reconciled",
    icon: <Check className="h-3.5 w-3.5" strokeWidth={3} />,
  },
  exception: {
    badge: "text-warning bg-warning-soft",
    label: "Exception",
    icon: <AlertTriangle className="h-3.5 w-3.5" strokeWidth={2.6} />,
  },
  explained: {
    badge: "text-info bg-info-soft",
    label: "Explained",
    icon: <Info className="h-3.5 w-3.5" strokeWidth={2.6} />,
  },
};

function Field({ label, children }) {
  return (
    <div>
      <p className="text-[0.7rem] font-semibold tracking-[0.1em] text-muted-foreground uppercase">
        {label}
      </p>
      <div className="mt-1.5 text-[0.95rem] leading-relaxed">{children}</div>
    </div>
  );
}

export default async function InvestigationPage({ params }) {
  const { id } = await params;
  const c = await findCase(id);
  if (!c) notFound();

  const result = classifyStatus(c.status);
  const meta = decisionStyle[result];
  const expectedAmount = Number(c.expected_amount);
  const actualAmount = Number(c.actual_amount);
  const difference = Number(c.difference_amount);
  const diff = difference === 0 ? inr(0) : `− ${inr(Math.abs(difference))}`;

  return (
    <main className="pt-10 sm:pt-14">
      <div className="rise-in flex flex-wrap items-end justify-between gap-4">
        <div>
          <Link
            href="/cases"
            className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" strokeWidth={2.2} />
            All cases
          </Link>
          <h1 className="font-display mt-3 flex items-center gap-3 text-3xl font-bold tracking-tight sm:text-4xl">
            {formatCaseCode(c.case_id)}
          </h1>
        </div>
        <span
          className={`glass-soft inline-flex items-center gap-1.5 rounded-md px-4 py-1.5 text-sm font-semibold ${meta.badge}`}
        >
          {meta.icon}
          {meta.label}
        </span>
      </div>

      <section
        className="glass rise-in mt-8 grid gap-8 rounded-md p-7 sm:grid-cols-3 sm:p-8"
        style={{ animationDelay: "80ms" }}
      >
        <Field label="Payment">Payment #{c.payment_id}</Field>
        <Field label="Settlement">
          {c.settlement_id ? `Settlement #${c.settlement_id}` : "No settlement matched"}
        </Field>
        <Field label="Bank transaction">
          {c.bank_transaction_id
            ? `Bank transaction #${c.bank_transaction_id}`
            : "No bank transaction matched"}
        </Field>
        <Field label="Expected amount">
          <span className="font-display font-semibold tabular-nums">
            {inr(expectedAmount)}
          </span>
        </Field>
        <Field label="Actual amount">
          <span className="font-display font-semibold tabular-nums">
            {inr(actualAmount)}
          </span>
        </Field>
        <Field label="Difference">
          <span
            className={`font-display font-semibold tabular-nums ${
              difference === 0 ? "text-success" : "text-warning"
            }`}
          >
            {diff}
          </span>
        </Field>
      </section>

      <section
        className="glass rise-in mt-4 rounded-md p-7 sm:p-8"
        style={{ animationDelay: "160ms" }}
      >
        <h2 className="font-display text-lg font-semibold tracking-tight">
          Investigation record
        </h2>
        <div className="mt-6 grid gap-8 lg:grid-cols-2">
          <Field label="Explanation">{c.explanation}</Field>
          <Field label="Confidence">
            <span className="font-medium">{(c.confidence * 100).toFixed(0)}%</span>
          </Field>
          <Field label="Status">
            <span className="font-medium">{formatStatusLabel(c.status)}</span>
          </Field>
        </div>
      </section>
    </main>
  );
}
