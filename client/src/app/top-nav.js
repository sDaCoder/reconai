"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const tabs = [
  { href: "/", label: "Dashboard" },
  { href: "/cases", label: "Cases" },
];

export default function TopNav() {
  const pathname = usePathname();

  return (
    <header className="pt-6 sm:pt-8">
      <nav className="glass-nav mx-auto flex max-w-5xl items-center justify-between gap-6 rounded-md py-3 pr-3 pl-6 sm:pl-7">
        <Link href="/" className="leading-tight">
          <span className="font-display block text-[1.05rem] font-bold tracking-tight">
            ReconAI
          </span>
          <span className="block text-[0.7rem] font-medium tracking-[0.08em] text-muted-foreground uppercase">
            Finance Reconciliation
          </span>
        </Link>
        <div className="glass-soft flex items-center rounded-md p-1">
          {tabs.map((tab) => {
            const active = pathname === tab.href;
            return (
              <Link
                key={tab.href}
                href={tab.href}
                className={cn(
                  "rounded-md px-4 py-1.5 text-sm font-medium transition-all",
                  active
                    ? "bg-white/80 text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {tab.label}
              </Link>
            );
          })}
        </div>
      </nav>
    </header>
  );
}
