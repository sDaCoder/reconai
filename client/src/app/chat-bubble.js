"use client";

import { useState } from "react";
import { useQueryState, parseAsBoolean } from "nuqs";
import { MessageCircle, Maximize2, Minimize2, Send, Loader2, X } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { cn } from "@/lib/utils";
import { reconcileQueryStream } from "@/lib/api";

const markdownComponents = {
  p: (props) => <p className="mb-2 last:mb-0" {...props} />,
  strong: (props) => <strong className="font-semibold" {...props} />,
  ul: (props) => <ul className="mb-2 list-disc space-y-1 pl-4 last:mb-0" {...props} />,
  ol: (props) => <ol className="mb-2 list-decimal space-y-1 pl-4 last:mb-0" {...props} />,
  code: (props) => (
    <code className="rounded bg-black/10 px-1 py-0.5 text-[0.85em]" {...props} />
  ),
  a: (props) => (
    <a className="underline underline-offset-2 hover:text-foreground" {...props} />
  ),
  table: (props) => (
    <div className="mb-2 overflow-x-auto last:mb-0">
      <table className="w-full border-collapse text-xs" {...props} />
    </div>
  ),
  th: (props) => (
    <th
      className="border border-black/10 bg-black/5 px-2 py-1 text-left font-semibold"
      {...props}
    />
  ),
  td: (props) => <td className="border border-black/10 px-2 py-1 align-top" {...props} />,
};

export default function ChatBubble() {
  const [open, setOpen] = useQueryState(
    "chat",
    parseAsBoolean.withDefault(false).withOptions({ history: "replace" }),
  );
  const [expanded, setExpanded] = useQueryState(
    "chatExpanded",
    parseAsBoolean.withDefault(false).withOptions({ history: "replace" }),
  );
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);

  const closeChat = () => {
    setOpen(false);
    setExpanded(false);
  };

  async function handleSubmit(e) {
    e.preventDefault();
    const query = input.trim();
    if (!query || pending) return;

    setMessages((m) => [...m, { role: "user", content: query }, { role: "assistant", content: "" }]);
    setInput("");
    setPending(true);
    try {
      await reconcileQueryStream(query, (token) => {
        setMessages((m) => {
          const next = [...m];
          const last = next[next.length - 1];
          next[next.length - 1] = { ...last, content: last.content + token };
          return next;
        });
      });
    } catch {
      setMessages((m) => {
        const next = [...m];
        next[next.length - 1] = {
          role: "assistant",
          content: "Something went wrong. Please try again.",
        };
        return next;
      });
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="fixed right-5 bottom-5 z-50 sm:right-8 sm:bottom-8">
      {open && (
        <div
          className={cn(
            "glass rise-in mb-3 flex flex-col overflow-hidden rounded-md",
            expanded
              ? "fixed inset-6 mb-0 sm:inset-10"
              : "h-[34rem] max-h-[80vh] w-[22rem] max-w-[calc(100vw-2.5rem)] sm:w-[28rem]",
          )}
        >
          <div className="flex items-center justify-between gap-2 border-b border-white/40 px-4 py-3">
            <p className="font-display text-sm font-semibold tracking-tight">
              ReconAI Assistant
            </p>
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => setExpanded((v) => !v)}
                aria-label={expanded ? "Collapse chat" : "Expand chat"}
                className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-white/50 hover:text-foreground"
              >
                {expanded ? (
                  <Minimize2 className="h-4 w-4" strokeWidth={2.2} />
                ) : (
                  <Maximize2 className="h-4 w-4" strokeWidth={2.2} />
                )}
              </button>
              <button
                type="button"
                onClick={closeChat}
                aria-label="Close chat"
                className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-white/50 hover:text-foreground"
              >
                <X className="h-4 w-4" strokeWidth={2.2} />
              </button>
            </div>
          </div>

          <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
            {messages.length === 0 && (
              <p className="mt-8 text-center text-xs text-muted-foreground">
                Ask about a case, settlement, or exception.
              </p>
            )}
            {messages.map((m, i) => {
              const isPendingPlaceholder =
                m.role === "assistant" &&
                pending &&
                i === messages.length - 1 &&
                m.content === "";
              return (
                <div
                  key={i}
                  className={cn(
                    "max-w-[85%] rounded-md px-3 py-2 text-left text-sm leading-relaxed",
                    m.role === "user"
                      ? "glass-soft ml-auto whitespace-pre-wrap"
                      : "mr-auto bg-black/5",
                  )}
                >
                  {isPendingPlaceholder ? (
                    <span className="flex items-center gap-2 text-muted-foreground">
                      <Loader2 className="h-3.5 w-3.5 animate-spin" strokeWidth={2.4} />
                      Thinking…
                    </span>
                  ) : m.role === "assistant" ? (
                    <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                      {m.content}
                    </ReactMarkdown>
                  ) : (
                    m.content
                  )}
                </div>
              );
            })}
          </div>

          <form
            onSubmit={handleSubmit}
            className="glass-soft m-3 flex items-center gap-2 rounded-md px-3 py-2"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about a reconciliation…"
              className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
            />
            <button
              type="submit"
              disabled={!input.trim() || pending}
              aria-label="Send message"
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground transition-opacity disabled:opacity-40"
            >
              <Send className="h-4 w-4" strokeWidth={2.2} />
            </button>
          </form>
        </div>
      )}
      {!expanded && (
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-label={open ? "Close chat" : "Open chat"}
          aria-expanded={open}
          className="glass ml-auto flex h-14 w-14 items-center justify-center rounded-full text-foreground transition-transform duration-300 hover:-translate-y-0.5"
        >
          {open ? (
            <X className="h-6 w-6" strokeWidth={2.2} />
          ) : (
            <MessageCircle className="h-6 w-6" strokeWidth={2.2} />
          )}
        </button>
      )}
    </div>
  );
}
