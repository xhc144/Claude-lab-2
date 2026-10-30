#!/bin/bash
# Render every chapter at 1080p30, 4 at a time, longest chapters first.
cd "$(dirname "$0")"
mkdir -p logs
mod() { if [ $1 -le 4 ]; then echo scenes_a; elif [ $1 -le 9 ]; then echo scenes_b; elif [ $1 -le 13 ]; then echo scenes_c; else echo scenes_d; fi; }
export -f mod
printf "%s\n" ${@:-01 08 12 03 09 10 02 13 14 07 15 05 16 11 06 04 17 00} | xargs -P 4 -I{} bash -c '
  c={}; m=$(mod $((10#$c)));
  start=$(date +%s)
  /opt/mvenv/bin/manim -r 1920,1080 --fps 30 --disable_caching $m.py Ch$c > logs/hq_ch$c.log 2>&1
  echo "ch$c exit $? $(( $(date +%s) - start ))s"'
