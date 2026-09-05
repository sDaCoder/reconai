import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function CaseNotFound() {
  return (
    <main className="flex min-h-[60vh] flex-col items-center justify-center">
      <div className="glass rise-in max-w-md rounded-md p-10 text-center">
        <h1 className="font-display text-xl font-semibold">Case not found</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          No reconciliation case exists at this address.
        </p>
        <Link
          href="/cases"
          className="mt-6 inline-flex items-center gap-2 rounded-md bg-primary px-5 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
        >
          <ArrowLeft className="h-4 w-4" strokeWidth={2.4} />
          Back to cases
        </Link>
      </div>
    </main>
  );
}
