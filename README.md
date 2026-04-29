# Voice Prompt Agent

A local desktop app that turns rough spoken ideas into clean, structured AI prompts. Speak into your microphone, hit Stop, then Improve — the app transcribes your speech and rewrites it as a formatted Markdown prompt using a local LLM.

Runs entirely offline. No API keys. No cloud.

---

## How It Works

1. **Record** — press Record, speak, press Stop
2. **Improve** — sends your transcription to a local Qwen 2.5 3B model
3. **Copy** — paste the structured Markdown prompt into Claude Code, ChatGPT, etc.

Multiple recordings accumulate in the text box before you improve — useful for building up context across several thoughts.

---

## Requirements

| Dependency | Version |
|---|---|
| Python | 3.12+ |
| ROCm | 7.x (AMD GPU) |
| PyTorch | 2.11.0+rocm7.2 |
| xclip | any (for clipboard support) |

**Hardware:** AMD GPU with ROCm support and ≥4 GB VRAM (tested on RX 7800 XT with 16 GB).

---

## Setup

```bash
# 1. Clone
git clone https://github.com/jamess005/voice-prompt-agent.git
cd voice-prompt-agent

# 2. Install system deps
sudo apt install python3-tk xclip

# 3. Create venv
python3 -m venv .venv

# 4. Install ROCm PyTorch
.venv/bin/pip install torch --index-url https://download.pytorch.org/whl/rocm7.2

# 5. Install remaining deps
.venv/bin/pip install -r requirements.txt

# 6. Configure
cp .env.example .env
# Edit .env — set MODEL_PATH to your local Qwen 2.5 3B instruct model directory
```

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `MODEL_PATH` | `/home/james/ml-proj/models/qwen2.5-3b-instruct` | Path to local Qwen 2.5 3B instruct model |
| `WHISPER_MODEL` | `small` | Whisper model size (`tiny`, `base`, `small`, `medium`) |

---

## Running

```bash
# From terminal
./run.sh

# Or directly
.venv/bin/python3 main.py
```

To add it to your application menu (Linux Mint / GNOME):

```bash
cp voiceagent.desktop ~/.local/share/applications/
```

---

## Docker (GPU + display required)

```bash
docker build -t voice-prompt-agent .

docker run --device=/dev/kfd --device=/dev/dri \
  --device=/dev/snd \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v /path/to/models:/models \
  -e DISPLAY=$DISPLAY \
  voice-prompt-agent
```

---

## Project Structure

```
voice-prompt-agent/
├── main.py          # Desktop UI (customtkinter)
├── recorder.py      # Microphone capture (sounddevice)
├── transcriber.py   # Speech-to-text (faster-whisper, CPU)
├── improver.py      # Prompt improvement (Qwen 2.5 3B, ROCm GPU)
├── logger.py        # Session logging to logs/YYYY-MM-DD.jsonl
├── run.sh           # Launch script
├── voiceagent.desktop  # Linux desktop entry
├── Dockerfile
├── requirements.txt
└── .env             # Local config (gitignored)
```

---

## Roles

Select a persona before hitting Improve to tailor the output style:

- Software Engineer
- Senior Developer
- DevOps Engineer
- ML / Data Scientist
- Full Stack Developer
- Security Engineer

---

## Logs

Each session is logged to `logs/YYYY-MM-DD.jsonl` (gitignored). Each entry contains the raw transcription and the improved output with a timestamp.

---

## Licence

MIT — see [LICENSE](LICENSE).
