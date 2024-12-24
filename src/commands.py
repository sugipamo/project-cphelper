"""
コマンド実行の実装
"""

import subprocess
import webbrowser
import os
from pathlib import Path
from . import config
from . import lib_merger
from . import test_generator
from . import ahc_tools
import shutil

def handle_command(contest_id: str, command: str, args: list):
    """
    コマンドの振り分けと実行
    """
    if command == "o":
        if not args:
            raise IndexError("Problem ID is required")
        open_problem(contest_id, args[0], "--rust" in args or "-rs" in args)
    elif command == "t" and len(args) >= 1:
        test_solution(contest_id, args[0], "--rust" in args or "-rs" in args)
    elif command == "s" and len(args) >= 1:
        submit_solution(contest_id, args[0], "--rust" in args or "-rs" in args)
    elif command == "g" and len(args) >= 1:
        create_or_generate(contest_id, args[0])
    elif command == "ahctest" and len(args) >= 1:
        run_ahc_test(contest_id, int(args[0]))
    else:
        raise ValueError("Invalid command or arguments")

def open_problem(contest_id: str, problem_id: str, use_rust: bool = False):
    """
    問題を開き、テストケースをダウンロード
    """
    # URLを開く
    url = f"https://atcoder.jp/contests/{contest_id}/tasks/{contest_id}_{problem_id}"
    webbrowser.open(url)

    # 問題ディレクトリ作成
    problem_dir = config.get_problem_dir(contest_id, problem_id)
    problem_dir.mkdir(parents=True, exist_ok=True)

    # ソースファイル作成
    ext = "rs" if use_rust else "py"
    source_file = problem_dir / f"{problem_id}.{ext}"
    if not source_file.exists():
        template_file = Path(config.TEMPLATE_DIR) / f"main.{ext}"
        if template_file.exists():
            source_file.write_text(template_file.read_text())
        else:
            source_file.touch()

    # テストケースダウンロード
    test_dir = config.get_test_dir(contest_id, problem_id)
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(f"oj download {url}", shell=True, cwd=test_dir)
    
    # test/testディレクトリが作成された場合は、その中身を移動
    nested_test_dir = test_dir / "test"
    if nested_test_dir.exists():
        for file in nested_test_dir.glob("*"):
            shutil.move(str(file), str(test_dir / file.name))
        shutil.rmtree(nested_test_dir)

    # エディタで開く
    if "code" in os.environ["PATH"]:
        subprocess.run(f"code {source_file}", shell=True)
    else:
        subprocess.run(f"cursor {source_file}", shell=True)

def test_solution(contest_id: str, problem_id: str, use_rust: bool = False):
    """
    解答のテスト実行
    """
    problem_dir = config.get_problem_dir(contest_id, problem_id)
    test_dir = config.get_test_dir(contest_id, problem_id)

    # ソースファイルの存在確認
    ext = "rs" if use_rust else "py"
    source_file = problem_dir / f"{problem_id}.{ext}"
    if not source_file.exists():
        raise FileNotFoundError(f"Source file not found: {source_file}")

    # カスタムテストケースの生成
    generator_file = problem_dir / f"{problem_id}_gen.py"
    if generator_file.exists():
        test_generator.generate_test_cases(contest_id, problem_id, test_dir)

    # テスト実行
    lang = "rust" if use_rust else "pypy"  # デフォルトはpypy
    docker_img = config.DOCKER_IMAGE[lang]
    
    # 問題ディレクトリとテストディレクトリをDockerコンテナにマウント
    docker_cmd = (
        f"docker run --rm -i "
        f"-v {source_file.absolute()}:/app/work/{source_file.name} "
        f"-v {test_dir.absolute()}:/app/work/test "
        f"-w /app/work"
    )
    docker_base = f"{docker_cmd} {docker_img}"

    if use_rust:
        # Rustのビルド
        subprocess.run(f"{docker_base} cargo build --release", shell=True)
        cmd = f"./target/release/{contest_id}_{problem_id}"
    else:
        interpreter = config.INTERPRETER[lang]
        cmd = f"{interpreter} {source_file.name}"

    # ojコマンドをホストで実行し、実行コマンドとしてDockerを使用
    test_cmd = f'{docker_base} {cmd}'
    try:
        subprocess.run(
            f'oj test -c "{test_cmd}" -d test -j {config.PARALLEL}',
            shell=True,
            check=True,
            cwd=problem_dir
        )
        return True
    except subprocess.CalledProcessError:
        return False

def submit_solution(contest_id: str, problem_id: str, use_rust: bool = False):
    """
    解答の提出
    """
    # 最初にテストを実行
    if not test_solution(contest_id, problem_id, use_rust):
        print("テストが失敗しました。")
        response = input("それでも提出しますか？(yes/y): ").lower().strip()
        if response not in ['yes', 'y']:
            print("提出を中止します。")
            return

    problem_dir = config.get_problem_dir(contest_id, problem_id)
    
    # ソースファイルの存在確認
    ext = "rs" if use_rust else "py"
    source_file = problem_dir / f"{problem_id}.{ext}"
    if not source_file.exists():
        raise FileNotFoundError(f"Source file not found: {source_file}")

    # Pythonの場合、ライブラリのマージ
    if not use_rust:
        merged_code = lib_merger.merge_libraries(source_file)
        temp_file = Path(".temp") / f"{problem_id}.py"
        temp_file.parent.mkdir(exist_ok=True)
        temp_file.write_text(merged_code)
        source_file = temp_file

    # 言語IDの取得
    lang_id = config.LANGUAGE_CODE["rust" if use_rust else "pypy"]

    # 提出
    url = f"https://atcoder.jp/contests/{contest_id}/tasks/{contest_id}_{problem_id}"
    subprocess.run(f"oj submit --yes {url} {source_file} -l {lang_id}", shell=True, check=True)

def run_ahc_test(contest_id: str, n_cases: int):
    """
    AHCのテスト実行
    """
    ahc_tools.setup_tools(contest_id)
    ahc_tools.run_test_cases(contest_id, n_cases) 

def create_or_generate(contest_id: str, problem_id: str):
    """
    テストケースジェネレータの作成または実行
    
    ジェネレータファイルが存在しない場合は作成し、
    存在する場合はテストケースを生成する
    """
    problem_dir = config.get_problem_dir(contest_id, problem_id)
    generator_file = problem_dir / f"{problem_id}_gen.py"
    
    if not generator_file.exists():
        # テンプレートの内容
        template = '''"""
テストケース生成モジュール
"""

import random

# 生成するテストケース数
TESTCASE_NUM = 10

def generate():
    """
    テストケースを生成する
    
    Returns:
        dict: 入力と期待される出力
            {
                'input': str,  # 入力文字列
                'output': str  # 期待される出力文字列
            }
    """
    # ここにテストケース生成ロジックを実装
    return {
        'input': '1 2\\n',
        'output': '3\\n'
    }

def check_constraints(input_data: str) -> bool:
    """
    制約条件をチェックする（オプション）
    
    Args:
        input_data (str): 生成された入力データ
        
    Returns:
        bool: 制約を満たしていればTrue
    """
    # ここに制約チェックロジックを実装
    return True
'''
        
        # ディレクトリが存在しない場合は作成
        problem_dir.mkdir(parents=True, exist_ok=True)
        
        # テンプレートを書き込む
        generator_file.write_text(template)
        print(f"Created generator file: {generator_file}")
        
        # エディタで開く
        if "code" in os.environ["PATH"]:
            subprocess.run(f"code {generator_file}", shell=True)
        else:
            subprocess.run(f"cursor {generator_file}", shell=True)
    else:
        # ジェネレータが存在する場合はテストケースを生成
        test_dir = config.get_test_dir(contest_id, problem_id)
        test_generator.generate_test_cases(contest_id, problem_id, test_dir)
        print(f"Generated test cases in: {test_dir}") 