"""llama.cpp server client + lifecycle. Local CPU inference, $0 spend (D11)."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

import requests


class LlamaServer:
    def __init__(self, server_exe: str, model_path: str, ctx: int = 12288,
                 port: int = 8080, threads: int = 8):
        self.base = f"http://127.0.0.1:{port}"
        self.proc: subprocess.Popen | None = None
        self.server_exe, self.model_path, self.ctx, self.port, self.threads = (
            server_exe, model_path, ctx, port, threads)

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
        self.proc = subprocess.Popen(
            [str(exe), "-m", self.model_path, "-c", str(self.ctx),
             "-t", str(self.threads), "--port", str(self.port),
             "--no-warmup", "--log-disable"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
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
            timeout=1800,
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
