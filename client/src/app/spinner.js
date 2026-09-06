export function Spinner({ className = "h-6 w-6" }) {
  return (
    <span
      role="status"
      aria-label="Loading"
      className={`inline-block animate-spin rounded-full border-2 border-foreground/20 border-t-foreground/70 ${className}`}
    />
  );
}

export function PageLoading() {
  return (
    <main className="flex min-h-[50vh] flex-col items-center justify-center gap-3 pt-10 sm:pt-14">
      <Spinner className="h-8 w-8" />
      <p className="text-sm text-muted-foreground">Loading</p>
    </main>
  );
}
