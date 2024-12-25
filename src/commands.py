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
from colorama import init, Fore, Style

# coloramaの初期化
init()

def handle_command(contest_id: str, command: str, args: list):
    """
    コマンドの処理
    """
    # オプションの解析
    use_rust = "--rust" in args or "-rs" in args
    
    if not args:
        raise IndexError("Problem ID is required")
    
    problem_id = args[0]
    
    if command == "o":
        return open_problem(contest_id, problem_id, use_rust)
    elif command == "s":
        return submit_solution(contest_id, problem_id, use_rust)
    elif command == "t":
        return test_solution(contest_id, problem_id, use_rust)
    elif command == "g":
        return generate_testcases(contest_id, problem_id)
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

def merge_and_copy_to_temp(source_file: Path, use_rust: bool) -> Path:
    """
    ソースコードをマージして.tempにコピーする
    Args:
        source_file (Path): ソースファイルのパス
        use_rust (bool): Rustを使用するかどうか
    Returns:
        Path: .temp内のファイルパス
    """
    temp_dir = Path(".temp")
    temp_dir.mkdir(parents=True, exist_ok=True)

    if use_rust:
        # Cargo.tomlの生成（存在しない場合のみ）
        cargo_toml_path = temp_dir / "Cargo.toml"
        if not cargo_toml_path.exists():
            cargo_toml = f"""
[package]
name = "competitive"
version = "0.1.0"
edition = "2021"

[dependencies]
proconio = "0.4.5"
"""
            cargo_toml_path.write_text(cargo_toml)
        
        # srcディレクトリの作成とソースファイルのコピー
        src_dir = temp_dir / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        
        # ソースファイルをmain.rsとしてコピー
        main_file = src_dir / "main.rs"
        try:
            content = source_file.read_text()
            main_file.write_text(content)
            print(f"Copied source file to {main_file}")
        except Exception as e:
            print(f"Error copying source file: {e}")
            raise
        return main_file
    else:
        # Pythonの場合、ライブラリのマージ
        merged_code = lib_merger.merge_libraries(source_file)
        main_file = temp_dir / "main.py"
        main_file.write_text(merged_code)
        print(f"Copied source file to {main_file}")
        return main_file

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
    
    # ソースコードのマージとコピー
    temp_dir = Path(".temp")
    main_file = merge_and_copy_to_temp(source_file, use_rust)
    
    # テスト実行
    lang = "rust" if use_rust else "pypy"  # デフォルトはpypy
    docker_img = config.DOCKER_IMAGE[lang]
    
    # Dockerコマンドの設定
    docker_cmd = (
        f"docker run --rm -i "
        f"-v {temp_dir.absolute()}:/app/work "
        f"-v {test_dir.absolute()}:/app/work/test "
        f"-w /app/work"
    )
    docker_base = f"{docker_cmd} {docker_img}"
    
    if use_rust:
        # Rustのビルド
        print("Building Rust project...")
        subprocess.run(f"{docker_base} cargo build --release", shell=True, check=True)
        cmd = "/app/work/target/release/competitive"  # 固定の実行ファイル名を使用
    else:
        interpreter = config.INTERPRETER[lang]
        cmd = f"{interpreter} main.py"

    # ojコマンドをホストで実行し、実行コマンドとしてDockerを使用
    test_cmd = f'{docker_base} {config.TIMEOUT} {cmd}'
    try:
        # テストケースファイルの収集
        test_files = list(Path(test_dir).glob("*.in"))
        if not test_files:
            print("テストケースが見つかりません")
            return False

        # テストケースファイルをソート
        test_files.sort()

        print(f"Running {len(test_files)} test cases...")

        # 各テストケースを非同期で実行
        import asyncio
        
        async def run_test(test_file: Path):
            in_file = test_file
            out_file = test_file.with_suffix(".out")
            
            # 同期的にファイルを読み込み
            with open(in_file, "r") as f:
                input_data = f.read()
            with open(out_file, "r") as f:
                expected = f.read()
            
            # テスト実行
            proc = await asyncio.create_subprocess_shell(
                test_cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate(input_data.encode())
            actual = stdout.decode().strip()
            error = stderr.decode().strip()
            
            if error:
                print(f"\n{Fore.RED}Error in test {test_file.name}:{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Input file (.in):{Style.RESET_ALL}")
                print("-" * 40)
                print(input_data.strip())
                print("-" * 40)
                print(f"{Fore.CYAN}Expected output (.out):{Style.RESET_ALL}")
                print("-" * 40)
                print(expected.strip())
                print("-" * 40)
                print(f"{Fore.RED}Error message:{Style.RESET_ALL}")
                print(error)
                return False
            
            if actual.strip() != expected.strip():
                print(f"\n{Fore.RED}Failed test: {test_file.name}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Input file (.in):{Style.RESET_ALL}")
                print("-" * 40)
                print(input_data.strip())
                print("-" * 40)
                print(f"{Fore.CYAN}Expected output (.out):{Style.RESET_ALL}")
                print("-" * 40)
                print(expected.strip())
                print("-" * 40)
                print(f"{Fore.YELLOW}Your output:{Style.RESET_ALL}")
                print("-" * 40)
                print(actual)
                print("-" * 40)
                return False
            return True

        # 並列実行
        async def run_all_tests():
            # テストケースを非同期で実行
            tasks = [run_test(tf) for tf in test_files]
            results = await asyncio.gather(*tasks)
            
            # 結果を順番に表示
            for i, (test_file, result) in enumerate(zip(test_files, results)):
                if result:
                    print(f"{Fore.GREEN}Passed test: {test_file.name}{Style.RESET_ALL}")
                # エラーメッセージは既にrun_test内で表示されている
            
            return all(results)
            
        success = asyncio.run(run_all_tests())
        if success:
            print(f"\n{Fore.GREEN}All tests passed!{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}Some tests failed.{Style.RESET_ALL}")
        return success

    except Exception as e:
        print(f"Error running tests: {e}")
        return False

def generate_testcases(contest_id: str, problem_id: str):
    """
    カスタムテストケースの生成
    """
    problem_dir = config.get_problem_dir(contest_id, problem_id)
    test_dir = config.get_test_dir(contest_id, problem_id)
    
    # ジェネレータファイルの存在確認と作成
    generator_file = problem_dir / f"{problem_id}_gen.py"
    if not generator_file.exists():
        problem_dir.mkdir(parents=True, exist_ok=True)
        template_file = Path(config.TEMPLATE_DIR) / "generator.py"
        if template_file.exists():
            generator_file.write_text(template_file.read_text())
        else:
            template = '''import random

TESTCASE_NUM = 10

def check_constraints(input_data: str) -> bool:
    """
    入力データが制約を満たしているかチェックする
    Args:
        input_data (str): 入力データ
    Returns:
        bool: 制約を満たしている場合True
    """
    return True

def generate():
    """
    テストケースを生成する
    Returns:
        dict: 入力と出力のデータ
    """
    return {
        'input': '',
        'output': ''
    }
'''
            generator_file.write_text(template)
        print(f"{Fore.GREEN}Created generator file: {generator_file}{Style.RESET_ALL}")
        return True
    
    # テストケースの生成
    print(f"{Fore.CYAN}Generating test cases...{Style.RESET_ALL}")
    num_generated = test_generator.generate_test_cases(contest_id, problem_id, test_dir)
    print(f"{Fore.GREEN}Successfully generated {num_generated} test cases!{Style.RESET_ALL}")
    return True

def submit_solution(contest_id: str, problem_id: str, use_rust: bool = False):
    """
    解答の提出
    """
    # ソースファイルの存在確認
    ext = "rs" if use_rust else "py"
    source_file = config.get_problem_dir(contest_id, problem_id) / f"{problem_id}.{ext}"
    if not source_file.exists():
        raise FileNotFoundError(f"Source file not found: {source_file}")

    # ソースコードのマージとコピー
    main_file = merge_and_copy_to_temp(source_file, use_rust)

    # 言語IDの取得
    lang_id = config.LANGUAGE_CODE["rust" if use_rust else "pypy"]

    # 提出
    url = f"https://atcoder.jp/contests/{contest_id}/tasks/{contest_id}_{problem_id}"
    subprocess.run(f"oj submit --yes {url} {main_file} -l {lang_id}", shell=True, check=True)

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