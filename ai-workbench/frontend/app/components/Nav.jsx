"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/chat", label: "Chat" },
  { href: "/", label: "RAG Assistant" },
  { href: "/lab/chunking", label: "Chunking Lab" },
  { href: "/lab/embeddings", label: "Embeddings Visualizer" },
  { href: "/evaluation", label: "RAG Evaluation" },
  { href: "/app", label: "Workflows" },
];

export default function Nav() {
  const pathname = usePathname();

  return (
    <nav className="nav">
      {LINKS.map((link) => (
        <Link
          key={link.href}
          href={link.href}
          className={
            pathname === link.href ? "nav-link active" : "nav-link"
          }
        >
          {link.label}
        </Link>
      ))}
    </nav>
  );
}
