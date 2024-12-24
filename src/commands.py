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
    if not test_dir.exists():
        subprocess.run(f"oj download {url}", shell=True, cwd=test_dir.parent)

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

    # テストケースのダウンロード
    test_dir.mkdir(parents=True, exist_ok=True)
    url = f"https://atcoder.jp/contests/{contest_id}/tasks/{contest_id}_{problem_id}"
    subprocess.run(f"oj download {url}", shell=True, cwd=test_dir)

    # カスタムテストケースの生成
    gen_file = problem_dir / f"{problem_id}_gen.py"
    if gen_file.exists():
        test_generator.generate_test_cases(gen_file, test_dir)

    # テスト実行
    lang = "rust" if use_rust else "pypy"  # デフォルトはpypy
    docker_img = config.DOCKER_IMAGE[lang]
    
    # 問題ディレクトリとテストディレクトリをDockerコンテナにマウント
    docker_cmd = (
        f"docker run --rm -i "
        f"-v {problem_dir.absolute()}:/app/work "
        f"-w /app/work"
    )
    docker_base = f"{docker_cmd} {docker_img}"

    if use_rust:
        # Rustのビルド
        subprocess.run(f"{docker_base} cargo build --release", shell=True)
        cmd = f"./target/release/{contest_id}_{problem_id}"
    else:
        interpreter = config.INTERPRETER[lang]
        cmd = f"{interpreter} {problem_id}.{ext}"

    # ojコマンドをホストで実行し、実行コマンドとしてDockerを使用
    test_cmd = f'{docker_base} {cmd}'
    subprocess.run(
        f'oj test -c "{test_cmd}" -d {test_dir.absolute()} -j {config.PARALLEL}',
        shell=True
    )

def submit_solution(contest_id: str, problem_id: str, use_rust: bool = False):
    """
    解答の提出
    """
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
    subprocess.run(f"oj submit {url} {source_file} -l {lang_id}", shell=True)

def run_ahc_test(contest_id: str, n_cases: int):
    """
    AHCのテスト実行
    """
    ahc_tools.setup_tools(contest_id)
    ahc_tools.run_test_cases(contest_id, n_cases) 