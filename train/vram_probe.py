"""One fwd/bwd at an exact sequence length through the run-2 training config.
Prints peak VRAM. Usage: vram_probe.py <seq_len>"""
import sys

import torch
try:  # WSL-without-a-C-compiler workaround only; no-op where gcc/clang exists (D34 amendment)
    from torch._native.registry import deregister_op_overrides
    deregister_op_overrides(disable_dsl_names=["triton"])
except ImportError:
    pass
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM

seq = int(sys.argv[1])
dtype = torch.float16 if (len(sys.argv) > 2 and sys.argv[2] == "fp16") else torch.float32
attn = "sdpa"
if len(sys.argv) > 3 and sys.argv[3] == "chunked":
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
    from chunked_attn import register
    attn = register()
DEV = "cpu" if (len(sys.argv) > 4 and sys.argv[4] == "cpu") else "cuda"
if DEV == "cpu":
    torch.set_num_threads(24)
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct",
                                             torch_dtype=dtype, device_map=DEV,
                                             attn_implementation=attn)
model.config.use_cache = False
model = get_peft_model(model, LoraConfig(
    r=16, lora_alpha=32, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]))
model.gradient_checkpointing_enable()
model.enable_input_require_grads()
opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-4)

import time

ids = torch.randint(1000, 5000, (1, seq), device="cuda")
labels = ids.clone()
for step in range(3):
    t0 = time.time()
    out = model(input_ids=ids, labels=labels)
    out.loss.backward()
    opt.step(); opt.zero_grad(set_to_none=True)
    torch.cuda.synchronize()
    print(f"step {step}: {time.time()-t0:.1f}s | loss {out.loss.item():.3f} | "
          f"peak {torch.cuda.max_memory_allocated()/2**30:.2f} GiB "
          f"| reserved {torch.cuda.max_memory_reserved()/2**30:.2f} GiB")
print("PROBE-OK", seq, dtype)
