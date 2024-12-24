"""
テストケース生成機能の実装
"""

import importlib.util
from pathlib import Path

def generate_test_cases(generator_file: Path, test_dir: Path):
    """
    テストケースの生成
    """
    # ジェネレータモジュールの動的ロード
    spec = importlib.util.spec_from_file_location("generator", generator_file)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)

    # テストケース数の取得
    n_cases = getattr(generator, 'TESTCASE_NUM', 10)

    # テストケースの生成
    for i in range(n_cases):
        case_num = i + 1
        result = generator.generate()

        # 入力ファイルの保存
        input_file = test_dir / f"custom-{case_num}.in"
        input_file.write_text(result['input'])

        # 出力ファイルの保存
        output_file = test_dir / f"custom-{case_num}.out"
        output_file.write_text(result['output']) 