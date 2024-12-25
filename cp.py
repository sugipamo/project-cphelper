#!/usr/bin/env python3

import sys
import os
from src.commands import handle_command
from src.config import setup_environment

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 cp.py <contest_id> <command> [problem_id] [options]")
        print("Commands:")
        print("  o <problem_id>     : Open problem and download tests")
        print("  t <problem_id>     : Test solution")
        print("  s <problem_id>     : Submit solution")
        print("  ahctest <n_cases>  : Run AHC test cases")
        print("Options:")
        print("  --rust, -rs        : Use Rust instead of Python")
        sys.exit(1)

    contest_id = sys.argv[1]
    command = sys.argv[2]
    args = sys.argv[3:]

    # 作業ディレクトリをスクリプトのある場所に変更
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 環境設定
    setup_environment()
    
    # 元のコマンド処理を実行
    handle_command(contest_id, command, args)

if __name__ == "__main__":
    main()
