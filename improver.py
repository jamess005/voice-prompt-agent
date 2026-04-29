import os
from dotenv import load_dotenv

load_dotenv()
# Restrict to the dedicated GPU only — prevents accelerate spreading model onto iGPU
os.environ.setdefault("HIP_VISIBLE_DEVICES", "0")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")

from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

MODEL_PATH = os.getenv("MODEL_PATH", "/home/james/ml-proj/models/qwen2.5-3b-instruct")

SYSTEM_PROMPT = """\
You are an experienced software engineer with a strong background in AI, machine learning, and full-stack development.
The user has dictated a rough idea for a coding or AI task. Rewrite it as a clean, structured prompt in Markdown.

Always use exactly this format — no preamble, no explanation, nothing outside it:

- **Goal:** One concise sentence describing the objective.
- **Requirements:**
  - Bullet point per specific task, fix, or feature.
- **Context:**
  - Bullet point per relevant background detail, constraint, or current state.

Rules:
- Use only information present in the user's input. Do not invent details.
- Keep each bullet tight — one idea per line.
- Always output valid Markdown. No plain prose blocks.\
"""


class Improver:
    def __init__(self):
        self._model = None
        self._tokenizer = None

    def load(self):
        self._tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
        self._model = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH,
            dtype=torch.float16,
            device_map={"": "cuda:0"},
        )
        self._model.eval()

    def improve(self, raw_text: str) -> str:
        if self._model is None:
            raise RuntimeError("Model not loaded")
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": raw_text},
        ]
        text = self._tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self._tokenizer([text], return_tensors="pt").to("cuda")
        with torch.no_grad():
            output_ids = self._model.generate(
                **inputs,
                max_new_tokens=512,
                do_sample=False,
            )
        generated = output_ids[0][inputs["input_ids"].shape[1]:]
        return self._tokenizer.decode(generated, skip_special_tokens=True).strip()
