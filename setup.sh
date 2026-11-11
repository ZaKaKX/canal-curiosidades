#!/bin/bash
# One-time setup for a fresh Linux workspace (~3-5 min). Run from the repo root: bash setup.sh
set -e
cd "$(dirname "$0")"
pip install --break-system-packages -q kokoro-onnx soundfile skia-python numpy uv
uv python install 3.11 >/dev/null
[ -d .venv-bl ] || uv venv -q -p 3.11 .venv-bl
uv pip install -q -p .venv-bl/bin/python bpy
mkdir -p models
[ -f models/kokoro-v1.0.onnx ] || curl -sSL -o models/kokoro-v1.0.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
[ -f models/voices-v1.0.bin ] || curl -sSL -o models/voices-v1.0.bin https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
.venv-bl/bin/python -c "import bpy; print('blender', bpy.app.version_string)"
python3 -c "import skia, kokoro_onnx; print('skia+kokoro ok')"
