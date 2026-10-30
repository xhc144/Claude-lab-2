#!/bin/bash
# 渲染全部场景（1080p60，4 个并行）。每个场景用单独的 media 目录，避免并行编译 LaTeX 时互相覆盖。
# 用法：./render_all.sh [画质参数，默认 -qh] [场景...]   场景名如 E1A、E6C，写在 ep<集号>.py 里
cd "$(dirname "$0")"
Q=${1:--qh}
shift
LIST=${*:-$(python -c "from outline import SCENES; print(' '.join(s['id'] for s in SCENES))")}
mkdir -p logs
for s in $LIST; do echo "$s ep${s:1:1}"; done | xargs -P 4 -n 2 sh -c \
  'manim '"$Q"' --disable_caching --media_dir media/$0 $1.py $0 > logs/$0.log 2>&1 && echo "$0 完成" || echo "$0 失败"'
