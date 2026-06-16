"""Compression operator C(x, sigma) — pluggable backends.

The production pipeline (per parent README §5) is teacher-LLM summarization.
No inference path for that exists in this workspace at zero cost (Phase-0
inventory), so the default backend is a deterministic extractive compressor
and every result built on it is labelled provisional (GATES.md).

Swapping backends is a config change: `compressor: extractive` vs
`compressor: llm` in the views config.
"""

from __future__ import annotations

import math
import os
import re
from collections import Counter

from .textutils import STOPWORDS, _WORD_RE, n_tokens, split_sentences

# Strip ANSI/VT escape sequences (CSI, OSC) that the Kiro CLI emits on stdout.
_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)")

# The compression prompt is backend-independent (D29): plain abstractive
# summary, key facts preserved, no preamble/formatting.
def _summary_prompt(text: str, target_tokens: int) -> str:
    target_words = max(120, int(target_tokens * 0.7))   # ~512 tok -> ~358 words
    return (
        f"Summarize the following text in about {target_words} words of plain prose. "
        f"Preserve the key facts, figures, dates, named entities, and conclusions. "
        f"Output ONLY the summary — no preamble, no headings, no bullet points.\n\n{text}"
    )


def _check_summary(out: str) -> str:
    """Shared output guard: reject quota/limit responses and too-short stubs."""
    low = out.lower()
    if any(s in low for s in ("session limit", "usage limit", "hit your", "rate limit",
                              "out of credits", "insufficient credit")):
        raise RuntimeError(f"compressor quota/limit response: {out[:120]}")
    if len(out.split()) < 80:
        raise RuntimeError(f"compressor output too short ({len(out.split())} words): {out[:120]}")
    return out


class ExtractiveCompressor:
    """Deterministic salience-based extractive compression.

    Scoring: SumBasic-style content-word probability averaged over the
    sentence, idf-damped within the slice, with a mild lead prior.
    Selection: greedy by score until the token budget is met; output
    preserves original sentence order. No randomness, no metadata emitted.
    """

    name = "extractive-sumbasic-v1"

    def compress(self, text: str, target_tokens: int) -> str:
        if n_tokens(text) <= target_tokens:
            return text.strip()
        sents = split_sentences(text)
        if not sents:
            return text.strip()

        sent_words = [
            [w.lower() for w in _WORD_RE.findall(s) if w.lower() not in STOPWORDS]
            for s in sents
        ]
        tf = Counter(w for ws in sent_words for w in ws)
        df = Counter(w for ws in sent_words for w in set(ws))
        n_s = len(sents)
        total = max(sum(tf.values()), 1)

        def score(i: int) -> float:
            ws = sent_words[i]
            if not ws:
                return 0.0
            sal = sum((tf[w] / total) * math.log(1 + n_s / df[w]) for w in ws) / len(ws)
            lead = 1.0 + 0.15 * (1.0 - i / n_s)  # mild lead prior
            return sal * lead

        ranked = sorted(range(n_s), key=lambda i: (-score(i), i))
        chosen: list[int] = []
        budget = 0
        for i in ranked:
            cost = n_tokens(sents[i])
            if budget + cost > target_tokens and chosen:
                continue
            chosen.append(i)
            budget += cost
            if budget >= target_tokens * 0.95:
                break
        chosen.sort()
        return " ".join(sents[i] for i in chosen)


class LLMCompressor:
    """Production teacher-LLM compressor C = Claude Haiku 4.5 (D29), invoked
    DETERMINISTICALLY via the local `claude -p --model haiku` one-shot under the
    session's OAuth (no API key). One slice in -> one summary out: no autonomous
    agent improvisation and no slice/view misalignment (unlike the subagent path).
    """

    name = "claude-haiku-4-5"

    def __init__(self, model: str = "haiku",
                 claude_exe: str = os.environ.get("CLAUDE_CLI", "claude"),
                 timeout: int = 180, ssh_host: str | None = None,
                 remote_claude: str = os.environ.get("REMOTE_CLAUDE_CLI", "claude")):
        # claude_exe / remote_claude default to `claude` on PATH; set CLAUDE_CLI /
        # REMOTE_CLAUDE_CLI to an absolute path if it is not on PATH (a
        # non-interactive ssh shell often lacks it).
        self.model = model
        self.claude_exe = claude_exe
        self.timeout = timeout
        # When ssh_host is set, the claude -p one-shot runs on the remote box over
        # its own OAuth pool (a second Pro-subscription quota); orchestration and
        # tiktoken counting stay local. Local path is unchanged when ssh_host=None.
        self.ssh_host = ssh_host
        self.remote_claude = remote_claude

    def _cmd(self) -> list[str]:
        if self.ssh_host:
            return ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
                    "-o", "ServerAliveInterval=30", "-o", "ServerAliveCountMax=3",
                    self.ssh_host, self.remote_claude, "-p", "--model", self.model]
        return [self.claude_exe, "-p", "--model", self.model]

    def compress(self, text: str, target_tokens: int) -> str:
        import subprocess

        prompt = _summary_prompt(text, target_tokens)
        r = subprocess.run(self._cmd(),
                           input=prompt, capture_output=True, text=True,
                           encoding="utf-8", timeout=self.timeout)
        out = (r.stdout or "").strip()
        if r.returncode != 0:
            raise RuntimeError(f"claude -p exit {r.returncode}: {(r.stderr or '')[:200]}")
        return _check_summary(out)


class KiroCompressor:
    """Production teacher-LLM compressor via the Kiro CLI headless mode
    (`kiro-cli chat --no-interactive --model claude-haiku-4.5`), authenticated by
    KIRO_API_KEY in the environment. Credit-metered (not the 5h OAuth wall), so a
    single run can finish the whole view set. Same Haiku-4.5 model family as the
    OAuth path (D29); the prompt is identical. Kiro emits the answer on stdout
    behind a `> ` marker and ANSI codes (credits/warnings go to stderr) — both
    stripped here so only the summary text is returned.
    """

    name = "claude-haiku-4-5"   # same model family/label as the OAuth path (D29)

    def __init__(self, model: str = "claude-haiku-4.5",
                 kiro_exe: str = os.environ.get("KIRO_CLI", "kiro-cli"),
                 timeout: int = 180):
        self.model = model
        self.kiro_exe = kiro_exe
        self.timeout = timeout

    def compress(self, text: str, target_tokens: int) -> str:
        import subprocess

        prompt = _summary_prompt(text, target_tokens)
        r = subprocess.run(
            [self.kiro_exe, "chat", "--no-interactive", "--trust-tools=",
             "--model", self.model],
            input=prompt, capture_output=True, text=True,
            encoding="utf-8", timeout=self.timeout)
        if r.returncode != 0:
            raise RuntimeError(f"kiro-cli exit {r.returncode}: {(r.stderr or '')[:200]}")
        out = _ANSI_RE.sub("", r.stdout or "")
        out = re.sub(r"^\s*>\s*", "", out.strip())   # drop the leading response marker
        return _check_summary(out.strip())


def get_compressor(name: str, **kwargs):
    if name == "extractive":
        return ExtractiveCompressor()
    if name == "llm":
        return LLMCompressor(**kwargs)
    if name == "kiro":
        return KiroCompressor(**kwargs)
    raise ValueError(f"unknown compressor: {name}")
