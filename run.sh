#!/usr/bin/env bash
# Launch both halves of the demo: Gemma on one GPU, MOSS voice-acting on the other.
#
#   ./run.sh llm     language model only   (GPU $MOSS_LLM_GPU, port 8790)
#   ./run.sh app     voice model + web UI  (GPU $MOSS_TTS_GPU, port 8792)
#   ./run.sh both    both, backgrounded, logs in ./logs
#   ./run.sh stop    stop both
set -euo pipefail
cd "$(dirname "$0")"

VENV=/home/c4r33u19/moss15v2/.venv
LLAMA=/home/c4r33u19/moss15v2/llama.cpp/build/bin/llama-server
GGUF="$(ls ~/.cache/huggingface/hub/models--unsloth--gemma-4-12B-it-qat-GGUF/snapshots/*/gemma-4-12B-it-qat-UD-Q4_K_XL.gguf | head -1)"
# Gemma-4's own audio encoder — this is what does ASR, no Whisper in the stack
MMPROJ="$(ls ~/.cache/huggingface/hub/models--unsloth--gemma-4-12B-it-qat-GGUF/snapshots/*/mmproj-F16.gguf | head -1)"

export MOSS_LLM_GPU="${MOSS_LLM_GPU:-0}"
export MOSS_TTS_GPU="${MOSS_TTS_GPU:-1}"
export MOSS_APP_PORT="${MOSS_APP_PORT:-8792}"
LLM_PORT=8790
mkdir -p logs

start_llm() {
  echo "[llm] gemma-4-12B-it-qat on GPU $MOSS_LLM_GPU, port $LLM_PORT"
  CUDA_VISIBLE_DEVICES="$MOSS_LLM_GPU" "$LLAMA" \
    --model "$GGUF" --mmproj "$MMPROJ" --alias gemma-4-12b-it-qat \
    --host 127.0.0.1 --port "$LLM_PORT" \
    --n-gpu-layers 999 --ctx-size ${MOSS_LLM_CTX:-16384} --batch-size 512 \
    --parallel 1 --flash-attn on --no-warmup \
    --reasoning off --reasoning-budget 0 "$@"
}

start_app() {
  echo "[app] MOSS 4.55B voice-acting on GPU $MOSS_TTS_GPU, web UI on port $MOSS_APP_PORT"
  # CUDA_VISIBLE_DEVICES pins the card; the engine then addresses it as cuda:0.
  # env -u LD_LIBRARY_PATH avoids a leaked cuDNN path from the system CUDA 10.1.
  env -u LD_LIBRARY_PATH CUDA_VISIBLE_DEVICES="$MOSS_TTS_GPU,$MOSS_LLM_GPU" \
    HF_HOME="${HF_HOME:-$HOME/.cache/huggingface}" \
    "$VENV/bin/python" -m uvicorn app:app --host 0.0.0.0 --port "$MOSS_APP_PORT"
}

case "${1:-both}" in
  llm) start_llm ;;
  app) start_app ;;
  both)
    start_llm >logs/llm.log 2>&1 &
    echo "  llm pid $!  -> logs/llm.log"
    start_app >logs/app.log 2>&1 &
    echo "  app pid $!  -> logs/app.log"
    echo "open http://localhost:$MOSS_APP_PORT"
    wait ;;
  stop)
    pkill -f "llama-server.*gemma-4-12b" || true
    pkill -f "uvicorn app:app" || true
    echo "stopped" ;;
  *) echo "usage: $0 {llm|app|both|stop}"; exit 1 ;;
esac
