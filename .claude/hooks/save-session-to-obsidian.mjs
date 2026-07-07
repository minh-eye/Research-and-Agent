#!/usr/bin/env node
import { readFileSync, existsSync, mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";

function readStdin() {
  try {
    return readFileSync(0, "utf-8");
  } catch {
    return "";
  }
}

function extractText(content) {
  if (typeof content === "string") return content;
  if (!Array.isArray(content)) return "";
  return content
    .filter((block) => block && block.type === "text" && typeof block.text === "string")
    .map((block) => block.text)
    .join("\n");
}

function main() {
  const vaultPath = process.env.OBSIDIAN_VAULT_PATH;
  if (!vaultPath) {
    console.error("[obsidian-sync] OBSIDIAN_VAULT_PATH is not set, skipping save.");
    return;
  }

  let input;
  try {
    input = JSON.parse(readStdin());
  } catch {
    return;
  }

  const transcriptPath = input.transcript_path;
  if (!transcriptPath || !existsSync(transcriptPath)) return;

  const lines = readFileSync(transcriptPath, "utf-8").split("\n").filter(Boolean);
  const turns = [];

  for (const line of lines) {
    let entry;
    try {
      entry = JSON.parse(line);
    } catch {
      continue;
    }
    const role = entry?.message?.role ?? entry?.type;
    if (role !== "user" && role !== "assistant") continue;
    const text = extractText(entry?.message?.content ?? entry?.content).trim();
    if (!text) continue;
    turns.push({ role, text });
  }

  if (turns.length === 0) return;

  const now = new Date();
  const stamp = now.toISOString().replace(/[:.]/g, "-").slice(0, 19);
  const cwdName = path.basename(input.cwd || process.cwd());
  const fileName = `${stamp}-${cwdName}.md`;

  const outDir = path.join(vaultPath, "Claude Conversations");
  mkdirSync(outDir, { recursive: true });

  const header = [
    `# Claude Code session - ${cwdName}`,
    "",
    `- Date: ${now.toLocaleString()}`,
    `- Session ID: ${input.session_id ?? "unknown"}`,
    `- Ended: ${input.reason ?? "unknown"}`,
    "",
    "---",
    "",
  ].join("\n");

  const body = turns
    .map((t) => `**${t.role === "user" ? "User" : "Claude"}:**\n\n${t.text}`)
    .join("\n\n---\n\n");

  writeFileSync(path.join(outDir, fileName), header + body, "utf-8");
  console.error(`[obsidian-sync] Saved session note to ${path.join(outDir, fileName)}`);
}

main();
