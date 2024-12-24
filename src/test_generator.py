"""
テストケース生成機能の実装
"""

import importlib.util
import importlib
import sys
import os
from datetime import datetime
from pathlib import Path
from . import config

def generate_test_cases(contest_id: str, problem_id: str, test_dir: Path) -> int:
    """
    カスタムテストケースを生成する
    Args:
        contest_id (str): コンテストID
        problem_id (str): 問題ID
        test_dir (Path): テストケースの出力先ディレクトリ
    Returns:
        int: 生成したテストケースの数
    """
    # ジェネレータのインポート
    problem_dir = config.get_problem_dir(contest_id, problem_id)
    generator_file = problem_dir / f"{problem_id}_gen.py"
    if not generator_file.exists():
        raise FileNotFoundError(f"Generator file not found: {generator_file}")

    # ジェネレータモジュールの読み込み
    import importlib.util
    spec = importlib.util.spec_from_file_location("generator", generator_file)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)

    # テストケース数の取得（デフォルト値: 10）
    testcase_num = getattr(generator, 'TESTCASE_NUM', 10)

    # 既存のカスタムテストケースの最大番号を取得
    existing_files = list(test_dir.glob("custom-*.in"))
    max_num = 0
    if existing_files:
        max_num = max(int(f.stem.split("-")[1]) for f in existing_files)

    # テストケースの生成
    test_dir.mkdir(parents=True, exist_ok=True)
    num_generated = 0
    for i in range(testcase_num):
        test_case = generator.generate()
        
        # 戻り値の型チェック
        if not isinstance(test_case, dict) or 'input' not in test_case or 'output' not in test_case:
            raise TypeError("Generator must return a dictionary with 'input' and 'output' keys")
            
        input_data = test_case["input"]
        output_data = test_case["output"]

        # 制約チェック（オプション）
        if hasattr(generator, "check_constraints"):
            if not generator.check_constraints(input_data):
                continue

        # ファイル名は連番で生成（既存の番号の続きから）
        case_num = max_num + i + 1
        input_file = test_dir / f"custom-{case_num:03d}.in"
        output_file = test_dir / f"custom-{case_num:03d}.out"

        # ファイルの書き込み
        input_file.write_text(input_data)
        output_file.write_text(output_data)
        num_generated += 1

    return num_generated 