import pytest
import os
from pathlib import Path
from src.commands import handle_command

class TestCommandT:
    def test_basic_test(self, workspace, mock_subprocess, mock_config):
        """
        基本的なテスト実行のテスト
        """
        os.chdir(workspace)
        # テスト対象のファイルを作成
        problem_dir = workspace / "contest" / "abc123" / "a"
        problem_dir.mkdir(parents=True)
        with open(problem_dir / "a.py", "w") as f:
            f.write("print('test output')")

        # テストケースディレクトリを作成
        test_dir = mock_config.get_test_dir('abc123', 'a')
        test_dir.mkdir(parents=True)
        with open(test_dir / "sample-1.in", "w") as f:
            f.write("test input")
        with open(test_dir / "sample-1.out", "w") as f:
            f.write("test output")

        handle_command('abc123', 't', ['a'])

        # Dockerコマンドが実行されたことを確認
        docker_cmd = "docker run"
        assert any(docker_cmd in cmd for cmd in mock_subprocess.commands), "Docker command should be executed"

    def test_rust_test(self, workspace, mock_subprocess, mock_config):
        """
        Rustのテスト実行のテスト
        """
        os.chdir(workspace)
        # テスト対象のファイルを作成
        problem_dir = workspace / "contest" / "abc123" / "a"
        problem_dir.mkdir(parents=True)
        with open(problem_dir / "a.rs", "w") as f:
            f.write("// Test solution")

        # テストケースディレクトリを作成
        test_dir = mock_config.get_test_dir('abc123', 'a')
        test_dir.mkdir(parents=True)
        with open(test_dir / "sample-1.in", "w") as f:
            f.write("test input")
        with open(test_dir / "sample-1.out", "w") as f:
            f.write("test output")

        handle_command('abc123', 't', ['a', '--rust'])

        # cargoコマンドとDockerコマンドが実行されたことを確認
        assert any("cargo build" in cmd for cmd in mock_subprocess.commands), "Cargo build should be executed"
        docker_cmd = "docker run"
        assert any(docker_cmd in cmd for cmd in mock_subprocess.commands), "Docker command should be executed"

    def test_missing_source_file(self, workspace, mock_subprocess, mock_config):
        """
        ソースファイルが存在しない場合のテスト
        """
        os.chdir(workspace)
        with pytest.raises(FileNotFoundError):
            handle_command('abc123', 't', ['a'])

    def test_custom_testcase_generation(self, workspace, mock_subprocess, mock_config):
        """
        カスタムテストケース生成のテスト
        """
        os.chdir(workspace)
        problem_dir = workspace / "contest" / "abc123" / "a"
        problem_dir.mkdir(parents=True)

        # ソースファイルを作成
        with open(problem_dir / "a.py", "w") as f:
            f.write("# Test solution")

        # テストケースジェネレータを作成
        with open(problem_dir / "a_gen.py", "w") as f:
            f.write("""
TESTCASE_NUM = 3

def generate():
    return {
        'input': '3 4\\n',
        'output': '7\\n'
    }
""")

        # テストケースを生成
        handle_command('abc123', 'g', ['a'])

        # テストケースが生成されたことを確認
        test_dir = mock_config.get_test_dir('abc123', 'a')
        test_files = list(test_dir.glob("custom-*.in"))
        assert len(test_files) == 3, "Should have exactly 3 test cases"

    def test_custom_testcase_invalid_generator(self, workspace, mock_subprocess, mock_config):
        """
        無効なテストケースジェネレータのテスト
        """
        os.chdir(workspace)
        problem_dir = workspace / "contest" / "abc123" / "a"
        problem_dir.mkdir(parents=True)

        # ソースファイルを作成
        with open(problem_dir / "a.py", "w") as f:
            f.write("# Test solution")

        # 無効なジェネレータを作成（generate関数がない）
        with open(problem_dir / "a_gen.py", "w") as f:
            f.write("# Invalid generator")

        with pytest.raises(AttributeError):
            handle_command('abc123', 'g', ['a'])

    def test_custom_testcase_invalid_return(self, workspace, mock_subprocess, mock_config):
        """
        不正な戻り値を返すジェネレータのテスト
        """
        os.chdir(workspace)
        problem_dir = workspace / "contest" / "abc123" / "a"
        problem_dir.mkdir(parents=True)

        # ソースファイルを作成
        with open(problem_dir / "a.py", "w") as f:
            f.write("# Test solution")

        # 不正な戻り値を返すジェネレータを作成
        with open(problem_dir / "a_gen.py", "w") as f:
            f.write("""
def generate():
    return "invalid"
""")

        with pytest.raises(TypeError):
            handle_command('abc123', 'g', ['a'])

    def test_custom_testcase_with_constraints(self, workspace, mock_subprocess, mock_config):
        """
        制約チェック機能付きのテストケース生成のテスト
        """
        os.chdir(workspace)
        problem_dir = workspace / "contest" / "abc123" / "a"
        problem_dir.mkdir(parents=True)

        # ソースファイルを作成
        with open(problem_dir / "a.py", "w") as f:
            f.write("# Test solution")

        # 制約チェック付きジェネレータを作成
        with open(problem_dir / "a_gen.py", "w") as f:
            f.write("""
TESTCASE_NUM = 2

def check_constraints(input_data):
    H, W = map(int, input_data.strip().split())
    return 1 <= H <= 100 and 1 <= W <= 100

def generate():
    return {
        'input': '50 60\\n',
        'output': '110\\n'
    }
""")

        # テストケースを生成
        handle_command('abc123', 'g', ['a'])

        # テストケースが生成されたことを確認
        test_dir = mock_config.get_test_dir('abc123', 'a')
        test_files = list(test_dir.glob("custom-*.in"))
        assert len(test_files) == 2, "Should have exactly 2 test cases"

    def test_custom_testcase_multiple_generations(self, workspace, mock_subprocess, mock_config):
        """
        複数回のテストケース生成のテスト
        """
        os.chdir(workspace)
        problem_dir = workspace / "contest" / "abc123" / "a"
        problem_dir.mkdir(parents=True)

        # ソースファイルを作成
        with open(problem_dir / "a.py", "w") as f:
            f.write("# Test solution")

        # カウンタ付きジェネレータを作成
        with open(problem_dir / "a_gen.py", "w") as f:
            f.write("""
TESTCASE_NUM = 2

def generate():
    return {
        'input': '1 2\\n',
        'output': '3\\n'
    }
""")

        # 最初のテストケースを生成
        handle_command('abc123', 'g', ['a'])

        # 最初のテストケースを確認
        test_dir = mock_config.get_test_dir('abc123', 'a')
        test_files = list(test_dir.glob("custom-*.in"))
        test_files.sort()
        assert len(test_files) == 2, "Should have exactly 2 test cases in first run"

        # 2回目のテストケースを生成
        handle_command('abc123', 'g', ['a'])

        # 2回目のテストケースを確認
        test_files = list(test_dir.glob("custom-*.in"))
        test_files.sort()
        assert len(test_files) == 4, "Should have exactly 4 test cases after second run"

    def test_custom_testcase_persistence(self, workspace, mock_subprocess, mock_config):
        """
        テストケースの永続化のテスト（追加方式）
        """
        os.chdir(workspace)
        problem_dir = workspace / "contest" / "abc123" / "a"
        problem_dir.mkdir(parents=True)

        # ソースファイルを作成
        with open(problem_dir / "a.py", "w") as f:
            f.write("# Test solution")

        # 初期ジェネレータを作成
        with open(problem_dir / "a_gen.py", "w") as f:
            f.write("""
TESTCASE_NUM = 2

def generate():
    return {
        'input': '1 2\\n',
        'output': '3\\n'
    }
""")

        # 最初のテストケースを生成
        handle_command('abc123', 'g', ['a'])

        # 最初のテストケースを確認
        test_dir = mock_config.get_test_dir('abc123', 'a')
        test_files = list(test_dir.glob("custom-*.in"))
        test_files.sort()
        assert len(test_files) == 2, "Should have exactly 2 test cases in first run"

        # ジェネレータを更新
        with open(problem_dir / "a_gen.py", "w") as f:
            f.write("""
TESTCASE_NUM = 3

def generate():
    return {
        'input': '5 6\\n',
        'output': '11\\n'
    }
""")

        # 新しいテストケースを生成
        handle_command('abc123', 'g', ['a'])

        # 全てのテストケースを確認
        test_files = list(test_dir.glob("custom-*.in"))
        test_files.sort()
        assert len(test_files) == 5, "Should have exactly 5 test cases after second run"

    def test_custom_testcase_file_format(self, workspace, mock_subprocess, mock_config):
        """
        テストケースのファイル名形式のテスト
        """
        os.chdir(workspace)
        problem_dir = workspace / "contest" / "abc123" / "a"
        problem_dir.mkdir(parents=True)

        # ソースファイルを作成
        with open(problem_dir / "a.py", "w") as f:
            f.write("# Test solution")

        # ジェネレータを作成
        with open(problem_dir / "a_gen.py", "w") as f:
            f.write("""
TESTCASE_NUM = 1

def generate():
    return {
        'input': '1 2\\n',
        'output': '3\\n'
    }
""")

        # テストケースを生成
        handle_command('abc123', 'g', ['a'])

        # ファイル名の形式を確認
        test_dir = mock_config.get_test_dir('abc123', 'a')
        test_files = list(test_dir.glob("custom-*.in"))
        assert len(test_files) == 1, "Should have exactly 1 test case"

        # ファイル名の形式を確認
        test_file = test_files[0]
        assert test_file.name.startswith("custom-"), "File name should start with 'custom-'"
        assert test_file.name.endswith(".in"), "Input file should end with '.in'"
        
        # 対応する出力ファイルの存在を確認
        output_file = test_dir / test_file.name.replace(".in", ".out")
        assert output_file.exists(), "Output file should exist"

    def test_runtime_error(self, workspace, mock_subprocess, mock_config):
        """
        実行時エラーが発生するケースのテスト
        """
        os.chdir(workspace)
        # テスト対象のファイルを作成
        problem_dir = workspace / "contest" / "abc123" / "a"
        problem_dir.mkdir(parents=True)
        with open(problem_dir / "a.py", "w") as f:
            f.write("""def main():
    N = int(input())
    if N == 1:
        raise Exception("Not implemented")
    print(N)

if __name__ == "__main__":
    main()""")

        # テストケースディレクトリを作成
        test_dir = mock_config.get_test_dir('abc123', 'a')
        test_dir.mkdir(parents=True)
        with open(test_dir / "sample-1.in", "w") as f:
            f.write("1")
        with open(test_dir / "sample-1.out", "w") as f:
            f.write("1")

        # テスト実行（エラーが発生することを期待）
        result = handle_command('abc123', 't', ['a'])
        assert result == False, "Runtime error should cause test to fail"

    def test_wrong_output_format(self, workspace, mock_subprocess, mock_config):
        """
        出力形式が間違っているケースのテスト
        """
        os.chdir(workspace)
        # テスト対象のファイルを作成
        problem_dir = workspace / "contest" / "abc123" / "a"
        problem_dir.mkdir(parents=True)
        with open(problem_dir / "a.py", "w") as f:
            f.write("""def main():
    N = int(input())
    # 数値を文字列として出力（期待される出力は数値）
    print(f"The answer is: {N}")

if __name__ == "__main__":
    main()""")

        # テストケースディレクトリを作成
        test_dir = mock_config.get_test_dir('abc123', 'a')
        test_dir.mkdir(parents=True)
        with open(test_dir / "sample-1.in", "w") as f:
            f.write("42")
        with open(test_dir / "sample-1.out", "w") as f:
            f.write("42")

        # テスト実行（出力形式の違いでテストが失敗することを期待）
        result = handle_command('abc123', 't', ['a'])
        assert result == False, "Wrong output format should cause test to fail"

    def test_syntax_error(self, workspace, mock_subprocess, mock_config):
        """
        構文エラーがあるケースのテスト
        """
        os.chdir(workspace)
        # テスト対象のファイルを作成（構文エラーを含む）
        problem_dir = workspace / "contest" / "abc123" / "a"
        problem_dir.mkdir(parents=True)
        with open(problem_dir / "a.py", "w") as f:
            f.write("""def main()
    # コロンが抜けている（構文エラー）
    print("Hello")

if __name__ == "__main__":
    main()""")

        # テストケースディレクトリを作成
        test_dir = mock_config.get_test_dir('abc123', 'a')
        test_dir.mkdir(parents=True)
        with open(test_dir / "sample-1.in", "w") as f:
            f.write("test")
        with open(test_dir / "sample-1.out", "w") as f:
            f.write("Hello")

        # テスト実行（構文エラーでテストが失敗することを期待）
        result = handle_command('abc123', 't', ['a'])
        assert result == False, "Syntax error should cause test to fail"