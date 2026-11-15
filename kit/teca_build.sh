#!/bin/bash
# Episódio do Teca a partir dos áudios do Pedro.
# uso: teca_build.sh <work> <ep_dir> <audio_p1> [audio_p2]   (ep_dir com falas_pN.txt, render.py, sfx.py)
set -e
W=$1; E=$2; shift 2; K=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$W"; cd "$W"; p=0
for A in "$@"; do p=$((p+1))
  ffmpeg -y -v error -i "$A" -ac 1 -ar 48000 -c:a pcm_s16le dfin_p$p.wav
  mkdir -p dfout && /home/claude/dfn/deep-filter -D -a 35 -o dfout dfin_p$p.wav >/dev/null 2>&1
  ffmpeg -y -v error -i dfout/dfin_p$p.wav -af "highpass=f=75,equalizer=f=320:t=q:w=1.2:g=-2.5,equalizer=f=3000:t=q:w=1.2:g=3,highshelf=f=9000:g=1.5,acompressor=threshold=-22dB:ratio=2.5:attack=10:release=150:makeup=3,loudnorm=I=-16:TP=-1.5:LRA=9" -ar 48000 v_p$p.wav
  python3 /home/claude/asr/tx.py v_p$p.wav asr$p.json > /dev/null
  python3 -I $K/align.py $E/falas_p$p.txt asr$p.json v_p$p.wav timings_p$p.json mouth_p$p.json
  python3 $E/sfx.py timings_p$p.json sfx_p$p.wav
  ffmpeg -y -v error -i v_p$p.wav -i sfx_p$p.wav -filter_complex "[0:a]apad=pad_dur=1.3[v];[1:a]volume=0.5[s];[v][s]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,loudnorm=I=-14:TP=-1.5:LRA=11" -ar 48000 mix_p$p.wav
  NF=$(python3 -c "import json;print(int((json.load(open('timings_p$p.json'))['duration']+1.3)*30))"); H=$((NF/2))
  python3 $E/render.py timings_p$p.json 0 $H a_p$p.mp4 $K plates 2>/dev/null &
  python3 $E/render.py timings_p$p.json $H $NF b_p$p.mp4 $K plates 2>/dev/null &
  wait
  printf "file 'a_p$p.mp4'\nfile 'b_p$p.mp4'\n" > l$p.txt
  ffmpeg -y -v error -f concat -safe 0 -i l$p.txt -i mix_p$p.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart final_p$p.mp4
  echo "DONE $p"
done
