"""
テストケース生成機能の実装
"""

import importlib.util
import importlib
import sys
import os
from datetime import datetime
from pathlib import Path

def generate_test_cases(contest_id: str, problem_id: str, test_dir: Path):
    """
    テストケースを生成して保存する

    Args:
        contest_id (str): コンテストID
        problem_id (str): 問題ID
        test_dir (Path): テストケースを保存するディレクトリ
    """
    # ジェネレータファイルのパスを構築
    generator_path = Path("contest") / contest_id / problem_id / f"{problem_id}_gen.py"
    
    if not generator_path.exists():
        return
    
    # モジュール名を生成（一意になるようにパスを含める）
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    module_name = f"generator_{contest_id}_{problem_id}_{timestamp}"
    
    # 既存のモジュールを削除
    for key in list(sys.modules.keys()):
        if key.startswith(f"generator_{contest_id}_{problem_id}"):
            del sys.modules[key]
    
    # ジェネレータモジュールを動的にロード
    with open(generator_path) as f:
        code = compile(f.read(), str(generator_path.absolute()), 'exec')
    
    # 新しいモジュールを作成
    generator = type(importlib.util.module_from_spec(importlib.util.spec_from_loader(module_name, None)))(module_name)
    sys.modules[module_name] = generator
    
    # コードを実行
    exec(code, generator.__dict__)
    
    # テストケース数を取得（デフォルト10）
    num_cases = getattr(generator, "TESTCASE_NUM", 10)
    
    # テストディレクトリを作成
    os.makedirs(test_dir, exist_ok=True)
    
    # 既存のテストケースの数を取得
    existing_files = sorted(test_dir.glob("custom-*.in"))
    next_index = len(existing_files) + 1
    
    # テストケースを生成して保存
    for i in range(num_cases):
        # テストケースを生成
        test_case = generator.generate()
        
        if not isinstance(test_case, dict) or 'input' not in test_case or 'output' not in test_case:
            raise TypeError("Generator must return a dict with 'input' and 'output' keys")
            
        # 制約チェックがある場合は実行
        if hasattr(generator, 'check_constraints'):
            if not generator.check_constraints(test_case['input']):
                raise ValueError(f"Test case {i+1} violates constraints")
        
        # ファイル名を生成
        input_file = test_dir / f"custom-{timestamp}-{next_index + i}.in"
        output_file = test_dir / f"custom-{timestamp}-{next_index + i}.out"
        
        # テストケースを保存
        with open(input_file, 'w') as f:
            input_data = test_case['input']
            if not input_data.endswith('\n'):
                input_data += '\n'
            f.write(input_data)
        with open(output_file, 'w') as f:
            output_data = test_case['output'] 
            if not output_data.endswith('\n'):
                output_data += '\n'
            f.write(output_data)
            
    # 古いテストケースを保持するために、ファイルの一覧を取得
    all_test_files = []
    for test_file in test_dir.glob("custom-*.in"):
        all_test_files.append(test_file)
        
    # テストケースが多すぎる場合は古いものから削除
    max_test_cases = 100  # 最大保持数
    if len(all_test_files) > max_test_cases:
        all_test_files.sort()  # タイムスタンプ順にソート
        for test_file in all_test_files[:-max_test_cases]:
            os.remove(test_file)
            output_file = test_file.parent / test_file.name.replace(".in", ".out")
            if output_file.exists():
                os.remove(output_file) 