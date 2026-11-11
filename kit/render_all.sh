#!/bin/bash
# usage: kit/render_all.sh <workdir> <plates_script.py> plate1 plate2 ...
# renders each 3D plate (beauty + line passes) with Blender and inks it -> <workdir>/plates/<name>_ink.png
REPO="$(cd "$(dirname "$0")/.." && pwd)"
WD="$1"; PS="$2"; shift 2
mkdir -p "$WD/plates"
for p in "$@"; do
  if [ -f "$WD/plates/${p}_ink.png" ]; then continue; fi
  BL_PCT=${BL_PCT:-75} BL_SAMPLES=${BL_SAMPLES:-36} "$REPO/.venv-bl/bin/python" "$PS" "$p" "$WD/plates" 2>&1 | grep -E "PLATE|rror" >> "$WD/plates/log.txt"
  python3 -I -c "import sys; sys.path.insert(0,'$REPO/kit'); import ink; d='$WD/plates/$p'; ink.ink_composite(d+'.png', d+'_nrm.png', d+'_id.png', d+'_ink.png', width=2)" 2>>"$WD/plates/log.txt"
  echo "INK $p" >> "$WD/plates/log.txt"
done
echo ALLDONE >> "$WD/plates/log.txt"
