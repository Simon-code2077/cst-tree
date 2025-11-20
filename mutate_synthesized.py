#!/usr/bin/env python3
"""
mutate_synthesized.py

Usage:
    python3 mutate_synthesized.py [--mutations N] [--seed SEED] [--output-dir DIR]
"""

import argparse
import sys
import subprocess
from pathlib import Path
from typing import List, Optional
import json
from datetime import datetime

# 项目根目录
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
CST_TREE_DIR = ROOT / "cst-tree"
SPLICE_RUST = CST_TREE_DIR / "splice_rust.py"
DEFAULT_OUTPUT_DIR = ROOT / "data" / "mutated_synthesized"


def find_synthesized_files(data_dir: Path = DATA_DIR) -> List[Path]:
    files = []
    for rs_file in data_dir.rglob("synthesized*.rs"):
        files.append(rs_file)
    
    files.sort()  
    return files


def ensure_splice_rust_exists():

    if not SPLICE_RUST.exists():
        print(f"❌ splice_rust.py not found at {SPLICE_RUST}")
        sys.exit(1)
    print(f"✅ Found splice_rust.py at {SPLICE_RUST}")


def mutate_file(input_file: Path, output_file: Path, num_mutations: int = 1, 
                seed: int = 42) -> bool:

    try:
        cmd = [
            "python3", str(SPLICE_RUST),
            str(input_file),
            "--mutations", str(num_mutations),
            "--seed", str(seed),
            "--output", str(output_file)
        ]
        
        print(f"  🔨 Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"  ❌ Failed to mutate {input_file.name}")
            if result.stderr:
                print(f"     Error: {result.stderr[:200]}")
            return False
        
        print(f"  ✅ Mutated {input_file.name} -> {output_file.name}")
        return True
        
    except subprocess.TimeoutExpired:
        print(f"  ⏱️  Timeout while mutating {input_file.name}")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def process_synthesized_files(data_dir: Path = DATA_DIR,
                             output_dir: Path = DEFAULT_OUTPUT_DIR,
                             num_mutations: int = 1,
                             seed: int = 42,
                             max_files: Optional[int] = None) -> dict:

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f" Output directory: {output_dir}")
    print()
    
    # 找到所有 synthesized 文件
    files = find_synthesized_files(data_dir)
    
    if not files:
        print(" No synthesized*.rs files found!")
        return {"total": 0, "success": 0, "failed": 0}
    
    print(f" Found {len(files)} synthesized*.rs files")
    if max_files:
        files = files[:max_files]
        print(f"  Processing first {max_files} files")
    print()
    
    
    stats = {
        "total": len(files),
        "success": 0,
        "failed": 0,
        "files": []
    }
    
   
    for i, input_file in enumerate(files, 1):
        rel_path = input_file.relative_to(data_dir)
        print(f"[{i}/{len(files)}] Processing: {rel_path}")
        
       
        output_file = output_dir / f"{input_file.stem}_mutated.rs"
        
        
        success = mutate_file(
            input_file,
            output_file,
            num_mutations=num_mutations,
            seed=seed + i  
        )
        
        if success:
            stats["success"] += 1
            stats["files"].append({
                "input": str(rel_path),
                "output": f"{output_file.stem}.rs",
                "status": "success"
            })
        else:
            stats["failed"] += 1
            stats["files"].append({
                "input": str(rel_path),
                "output": None,
                "status": "failed"
            })
        
        print()
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="自动变异所有 synthesized*.rs 文件"
    )
    parser.add_argument(
        "--mutations", "-m",
        type=int,
        default=5,
        help="每个文件的变异次数 (default: 5)"
    )
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=42,
        help="随机种子 (default: 42)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"输出目录 (default: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=None,
        help="最多处理的文件数 (default: all)"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DATA_DIR,
        help=f"数据目录 (default: {DATA_DIR})"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🔄 LegoFuzz-Rustlantis Synthesized File Mutator")
    print("=" * 70)
    print()
    
    # 检查 splice_rust.py
    ensure_splice_rust_exists()
    print()
    
    # 处理文件
    print(f"⚙️  Configuration:")
    print(f"   Mutations per file: {args.mutations}")
    print(f"   Base seed: {args.seed}")
    print(f"   Output directory: {args.output_dir}")
    print(f"   Max files: {args.max_files if args.max_files else 'all'}")
    print()
    
    start_time = datetime.now()
    stats = process_synthesized_files(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        num_mutations=args.mutations,
        seed=args.seed,
        max_files=args.max_files
    )
    end_time = datetime.now()
    
    # 打印统计信息
    print("=" * 70)
    print("📈 Summary")
    print("=" * 70)
    print(f"Total files: {stats['total']}")
    print(f"✅ Success: {stats['success']}")
    print(f"❌ Failed: {stats['failed']}")
    print(f"⏱️  Time elapsed: {end_time - start_time}")
    print()
    
    # 保存统计信息
    report_file = args.output_dir / "mutation_report.json"
    stats["timestamp"] = start_time.isoformat()
    stats["duration_seconds"] = (end_time - start_time).total_seconds()
    
    with open(report_file, "w") as f:
        json.dump(stats, f, indent=2)
    
    print(f"📊 Report saved to: {report_file}")
    
    # 返回成功代码
    return 0 if stats["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
