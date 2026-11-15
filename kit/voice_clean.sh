#!/usr/bin/env bash
# Trata a locução gravada no celular: tira ruído, desabafa, dá presença e nivela.
# Uso: bash kit/voice_clean.sh entrada.(m4a|mp3|wav|ogg) saida.wav
set -euo pipefail
IN="$1"; OUT="$2"
ffmpeg -y -hide_banner -loglevel error -i "$IN" -ac 1 -ar 48000 -af "\
highpass=f=85,\
afftdn=nr=14:nf=-42:tn=1,\
agate=threshold=0.012:ratio=2:attack=5:release=180,\
equalizer=f=220:t=q:w=1.2:g=-3,\
equalizer=f=450:t=q:w=1.4:g=-4,\
equalizer=f=3200:t=q:w=1.0:g=4,\
equalizer=f=6000:t=q:w=1.5:g=2,\
highshelf=f=10000:g=2,\
deesser=i=0.4,\
acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=4,\
loudnorm=I=-16:TP=-1.5:LRA=9" "$OUT"
echo "ok -> $OUT"
