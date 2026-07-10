"""llama.cpp server client + lifecycle. Local CPU inference, $0 spend (D11)."""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path

import requests


class LlamaServer:
    def __init__(self, server_exe: str, model_path: str, ctx: int = 12288,
                 port: int = 8080, threads: int = 8, n_gpu_layers: int = 0):
        self.base = f"http://127.0.0.1:{port}"
        self.proc: subprocess.Popen | None = None
        self.server_exe, self.model_path, self.ctx, self.port, self.threads = (
            server_exe, model_path, ctx, port, threads)
        # n_gpu_layers > 0 offloads that many transformer layers to the GPU (needs a CUDA/Metal
        # llama.cpp build; the CPU-only build ignores it). Use 99 to offload the whole 7B to an
        # 11GB+ card (fits Q4 + 16K KV) for a large speedup. Default 0 = CPU-only (unchanged).
        self.n_gpu_layers = n_gpu_layers

    def healthy(self) -> bool:
        try:
            return requests.get(f"{self.base}/health", timeout=3).status_code == 200
        except requests.RequestException:
            return False

    def ensure_running(self, wait_s: int = 300) -> None:
        if self.healthy():
            return
        exe = Path(self.server_exe)
        if not exe.exists():
            raise FileNotFoundError(exe)
        cmd = [str(exe), "-m", self.model_path, "-c", str(self.ctx),
               "-t", str(self.threads), "--port", str(self.port),
               "--no-warmup", "--log-disable"]
        if self.n_gpu_layers:
            cmd += ["-ngl", str(self.n_gpu_layers)]
        self.proc = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        t0 = time.time()
        while time.time() - t0 < wait_s:
            if self.healthy():
                return
            if self.proc.poll() is not None:
                raise RuntimeError(f"llama-server exited with {self.proc.returncode}")
            time.sleep(3)
        raise TimeoutError("llama-server did not become healthy")

    def chat(self, system: str, user: str, max_tokens: int = 700,
             temperature: float = 0.0, seed: int = 42) -> dict:
        t0 = time.time()
        r = requests.post(
            f"{self.base}/v1/chat/completions",
            json={
                "messages": [{"role": "system", "content": system},
                             {"role": "user", "content": user}],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "seed": seed,
            },
            timeout=5400,
        )
        r.raise_for_status()
        data = r.json()
        return {
            "text": data["choices"][0]["message"]["content"],
            "usage": data.get("usage", {}),
            "wall_s": round(time.time() - t0, 1),
        }

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()


class ClaudePClient:
    """TEACHER backend for E2′ data generation: Claude Haiku 4.5 via a deterministic
    `claude -p --model haiku` one-shot per pass (the D29/D30 lineage — same OAuth path as the
    production compressor, no API key, no agent improvisation). The system prompt is embedded
    into the stdin prompt (one-shot has no separate system role we control deterministically).
    Named limitation, recorded per trajectory: `claude -p` exposes no temperature/seed control,
    so teacher decoding parameters are the CLI defaults — acceptable for a teacher (the student
    distills the behaviour, not the sampler), impossible for a clean comparison arm. Same
    interface as the other clients so runners use it unchanged."""

    def __init__(self, model: str = "haiku", exe: str | None = None,
                 timeout: int = 300, **_ignored):
        import os
        from shutil import which

        self.model = model
        self.exe = exe or os.environ.get("PCA_CLAUDE_EXE") or which("claude") or "claude"
        self.timeout = timeout

    def healthy(self) -> bool:
        return True

    def ensure_running(self, wait_s: int = 0) -> None:
        return  # external CLI; nothing to launch

    def chat(self, system: str, user: str, max_tokens: int = 700,
             temperature: float = 0.0, seed: int = 42) -> dict:
        prompt = (system or "") + "\n\n========\n\n" + (user or "")
        prov = f"claude-p:{self.model}|temp/seed=cli-defaults"
        t0 = time.time()
        try:
            p = subprocess.run([self.exe, "-p", "--model", self.model],
                               input=prompt, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=self.timeout)
        except subprocess.TimeoutExpired:
            return {"text": "", "usage": {}, "provider": prov,
                    "wall_s": round(time.time() - t0, 1)}
        if p.returncode != 0:
            raise RuntimeError(f"claude -p exit {p.returncode}: {(p.stderr or '')[:200]}")
        return {"text": (p.stdout or "").strip(), "usage": {},
                "provider": prov, "wall_s": round(time.time() - t0, 1)}

    def stop(self) -> None:
        return


class RateLimitStop(RuntimeError):
    """Raised on 402 (credits/quota) or a persistent 429 (RPM/RPD cap). NOT an HTTPError, so
    run.py's truncation handler does not catch it -- it propagates and stops the run cleanly,
    leaving the in-progress seed incomplete (and therefore re-run on resume), never corrupt."""


class OpenRouterClient:
    """OpenAI-compatible client for OpenRouter (or any compatible endpoint). Same interface as
    LlamaServer so run.py / the gates can use it interchangeably. Key(s) from an env var (one, or a
    comma-separated list -> rotation). Optional `provider_order` pins OpenRouter upstream routing
    (with `allow_fallbacks`) so every call lands on ONE provider -> consistent weights/quant across
    seeds (the multi-upstream fan-out corrupted the first 72B run).

    Error policy (learned the hard way): a GENUINE context-overflow 4xx -- body says 'maximum context
    length' / 'reduce the length' -- raises HTTPError so run.py truncates the arm gracefully. ANY
    OTHER failure (a spurious 4xx/5xx, a network error, or a 200 carrying an EMPTY choices array) is
    TRANSIENT -> rotate key + backoff + retry, NEVER silently truncated (mis-truncating spurious 400s
    as overflow is exactly what produced state=6tok 'truncations' before). Only after `max_attempts`
    transient failures does it raise RateLimitStop (clean stop -> seed left incomplete -> re-run on
    resume, never corrupt)."""

    URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_model: str, ctx: int = 32768, max_tokens: int = 900,
                 base_url: str | None = None, api_key_env: str = "OPENROUTER_API_KEY",
                 provider_order: list | None = None, allow_fallbacks: bool = True,
                 max_attempts: int = 10, **_ignored):
        self.api_model, self.ctx, self.max_tokens = api_model, ctx, max_tokens
        self.base_url = base_url or self.URL
        raw = os.environ.get(api_key_env, "")
        self.keys = [k.strip() for k in raw.split(",") if k.strip()]  # comma-separated -> rotation
        if not self.keys:
            raise RuntimeError(f"{api_key_env} not set in environment")
        self.idx = 0
        self.max_attempts = max_attempts
        self.provider = ({"order": list(provider_order), "allow_fallbacks": bool(allow_fallbacks)}
                         if provider_order else None)
        self.extra = {"HTTP-Referer": "https://localhost", "X-Title": "p7-split-unit"}

    def healthy(self) -> bool:
        return True

    def ensure_running(self, wait_s: int = 0) -> None:
        return  # remote API; nothing to launch

    @staticmethod
    def _is_ctx_overflow(text: str) -> bool:
        t = (text or "").lower()
        return ("maximum context length" in t or "context length" in t
                or "context_length_exceeded" in t or "reduce the length" in t)

    def chat(self, system: str, user: str, max_tokens: int = 700,
             temperature: float = 0.0, seed: int = 42) -> dict:
        payload = {"model": self.api_model,
                   "messages": [{"role": "system", "content": system},
                                {"role": "user", "content": user}],
                   "max_tokens": max_tokens, "temperature": temperature, "seed": seed}
        if self.provider:
            payload["provider"] = self.provider
        t0 = time.time()
        n = len(self.keys)
        last = None
        for attempt in range(self.max_attempts):
            hdr = {"Authorization": f"Bearer {self.keys[self.idx]}", **self.extra}
            try:
                r = requests.post(self.base_url, headers=hdr, json=payload, timeout=600)
            except requests.RequestException as e:
                last = f"net:{str(e)[:100]}"
            else:
                if r.status_code == 200:
                    data = r.json()
                    if data.get("choices"):
                        return {"text": (data["choices"][0].get("message") or {}).get("content") or "",
                                "usage": data.get("usage", {}),
                                "provider": data.get("provider"),
                                "wall_s": round(time.time() - t0, 1)}
                    last = f"200 empty-choices: {json.dumps(data)[:120]}"   # transient -> retry
                elif self._is_ctx_overflow(r.text):
                    r.raise_for_status()      # GENUINE overflow -> HTTPError -> run.py truncates arm
                else:
                    last = f"{r.status_code}: {r.text[:120]}"               # spurious -> retry
            self.idx = (self.idx + 1) % n
            if attempt < self.max_attempts - 1:
                time.sleep(min(2 + 2 * attempt, 20))
        raise RateLimitStop(f"{self.max_attempts} transient attempts exhausted: {last}")

    def stop(self) -> None:
        return


class KiroClient:
    """Drives `kiro-cli chat --no-interactive` as a HEAVILY CONFOUNDED completion backend for the P7
    YOLO probe ONLY -- never the clean cross-family table. kiro-cli wraps every call in its own agent
    harness (Kiro's system prompt + tools) and exposes NO temperature/seed/max_tokens control, so its
    results are not comparable to the clean API rungs and can't reproduce the temp-0/temp-0.7 draws.
    The P7 system prompt is embedded into the single prompt (kiro has no system role); the prompt is
    fed on STDIN (avoids the Windows argv length limit); Kiro's UI chrome (warning, 'Credits: ...',
    cursor codes) goes to stderr, so stdout -- after stripping ANSI and the leading '> ' marker -- is
    the model's raw response. Same interface as the other clients so run.py/gates use it unchanged."""

    _ANSI = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07]*\x07|\x1b[=>]")

    def __init__(self, kiro_model: str, exe: str | None = None, ctx: int = 200000,
                 max_tokens: int = 900, agent: str | None = None,
                 effort: str | None = None, **_ignored):
        import os
        from shutil import which

        self.kiro_model = kiro_model
        # PATH/env-resolved, never a hardcoded per-user path (machine-portable, scrub-safe)
        self.exe = exe or os.environ.get("PCA_KIRO_EXE") or which("kiro-cli") or "kiro-cli"
        self.ctx, self.max_tokens = ctx, max_tokens
        self.agent, self.effort = agent, effort

    def healthy(self) -> bool:
        return True

    def ensure_running(self, wait_s: int = 0) -> None:
        return  # external CLI; nothing to launch

    def chat(self, system: str, user: str, max_tokens: int = 700,
             temperature: float = 0.0, seed: int = 42) -> dict:
        prompt = (system or "") + "\n\n========\n\n" + (user or "")
        prov = f"kiro:{self.kiro_model}|agent={self.agent or 'default'}|effort={self.effort or 'default'}"
        t0 = time.time()
        argv = [self.exe, "chat", "--no-interactive", "--model", self.kiro_model, "--trust-tools="]
        if self.agent:
            argv += ["--agent", self.agent]
        if self.effort:
            argv += ["--effort", self.effort]
        try:
            p = subprocess.run(argv, input=prompt, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=600)
        except subprocess.TimeoutExpired:
            return {"text": "", "usage": {}, "provider": prov,
                    "wall_s": round(time.time() - t0, 1)}
        out = self._ANSI.sub("", p.stdout or "")
        lines = [(ln[2:] if ln.startswith("> ") else ln) for ln in out.splitlines()]
        return {"text": "\n".join(lines).strip(), "usage": {},
                "provider": prov, "wall_s": round(time.time() - t0, 1)}

    def stop(self) -> None:
        return
