import { Source_Serif_4, Fraunces } from "next/font/google";
import { NuqsAdapter } from "nuqs/adapters/next/app";
import "./globals.css";
import TopNav from "./top-nav";
import ChatBubble from "./chat-bubble";

const sourceSerif = Source_Serif_4({
  variable: "--font-sans",
  subsets: ["latin"],
});

const fraunces = Fraunces({
  variable: "--font-display",
  subsets: ["latin"],
});

export const metadata = {
  title: "ReconAI — Finance Reconciliation",
  description:
    "Reconcile payments, settlements and bank transactions with AI-assisted exception investigation.",
};

export default function RootLayout({ children }) {
  return (
    <html
      lang="en"
      className={`${sourceSerif.variable} ${fraunces.variable}`}
    >
      <body>
        <NuqsAdapter>
          <div
            aria-hidden="true"
            className="fixed inset-0 -z-10 overflow-hidden bg-background"
          >
            <div
              className="blob"
              style={{
                width: "44rem",
                height: "44rem",
                top: "-14rem",
                left: "-10rem",
                background: "var(--blob-a)",
              }}
            />
            <div
              className="blob"
              style={{
                width: "36rem",
                height: "36rem",
                top: "30%",
                right: "-12rem",
                background: "var(--blob-b)",
                animationDelay: "-9s",
              }}
            />
            <div
              className="blob"
              style={{
                width: "32rem",
                height: "32rem",
                bottom: "-12rem",
                left: "28%",
                background: "var(--blob-c)",
                animationDelay: "-17s",
              }}
            />
          </div>

          <div className="mx-auto max-w-5xl px-4 pb-20 sm:px-6">
            <TopNav />
            {children}
          </div>

          <ChatBubble />
        </NuqsAdapter>
      </body>
    </html>
  );
}
