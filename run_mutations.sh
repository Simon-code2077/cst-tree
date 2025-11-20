#!/bin/bash
# run_mutations.sh - 便捷脚本来运行 mutate_synthesized.py

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MUTATIONS=${1:-5}      # 第一个参数：变异次数，默认 5
MAX_FILES=${2:-}       # 第二个参数：最多文件数，默认全部

cd "$SCRIPT_DIR"

echo "🚀 Starting mutation process..."
echo "  Mutations per file: $MUTATIONS"
if [ -n "$MAX_FILES" ]; then
    echo "  Max files: $MAX_FILES"
    python3 mutate_synthesized.py --mutations "$MUTATIONS" --max-files "$MAX_FILES"
else
    echo "  Max files: all"
    python3 mutate_synthesized.py --mutations "$MUTATIONS"
fi

echo ""
echo "✅ Done! Check data/mutated_synthesized/ for results."
