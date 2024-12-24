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
            f.write("# Test solution")
        
        handle_command('abc123', 't', ['a'])
        
        # ojコマンドが実行されたことを確認
        expected_cmd = "oj test"
        assert any(expected_cmd in cmd for cmd in mock_subprocess.commands), "Test command should be executed"

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
        
        handle_command('abc123', 't', ['a', '--rust'])
        
        # cargoコマンドとojコマンドが実行されたことを確認
        assert any("cargo build" in cmd for cmd in mock_subprocess.commands), "Cargo build should be executed"
        assert any("oj test" in cmd for cmd in mock_subprocess.commands), "Test command should be executed"

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
        
        handle_command('abc123', 't', ['a'])
        
        # テストケースが生成されたことを確認
        test_dir = mock_config.get_test_dir('abc123', 'a')
        test_files = list(test_dir.glob("custom-*.in"))
        assert len(test_files) == 3, "Should have exactly 3 test cases"
        
        # ファイル名のパターンをチェック
        import re
        pattern = re.compile(r'custom-\d{14}-\d+\.in')
        for test_file in test_files:
            assert pattern.match(test_file.name), f"File name {test_file.name} should match the pattern"
            
        # テストケースの内容を確認
        for test_file in test_files:
            with open(test_file) as f:
                assert f.read() == "3 4\n", "Custom test input content should match"
            output_file = test_file.parent / test_file.name.replace(".in", ".out")
            with open(output_file) as f:
                assert f.read() == "7\n", "Custom test output content should match"

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
            handle_command('abc123', 't', ['a'])

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
            handle_command('abc123', 't', ['a']) 

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
        
        handle_command('abc123', 't', ['a'])
        
        # テストケースが生成されたことを確認
        test_dir = mock_config.get_test_dir('abc123', 'a')
        test_files = list(test_dir.glob("custom-*.in"))
        assert len(test_files) == 2, "Should have exactly 2 test cases"
        
        # ファイル名のパターンをチェック
        import re
        pattern = re.compile(r'custom-\d{14}-\d+\.in')
        for test_file in test_files:
            assert pattern.match(test_file.name), f"File name {test_file.name} should match the pattern"

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
        
        # 最初のテスト実行
        handle_command('abc123', 't', ['a'])
        
        # 最初のテストケースを確認
        test_dir = mock_config.get_test_dir('abc123', 'a')
        test_files = list(test_dir.glob("custom-*.in"))
        test_files.sort()
        
        assert len(test_files) == 2, "Should have exactly 2 test cases in first run"
        for test_file in test_files:
            with open(test_file) as f:
                content = f.read()
                assert content == "1 2\n", "First test cases should match"
        
        # ジェネレータを変更
        with open(problem_dir / "a_gen.py", "w") as f:
            f.write("""
TESTCASE_NUM = 2

def generate():
    return {
        'input': '3 4\\n',
        'output': '7\\n'
    }
""")
        
        # 2回目のテスト実行
        handle_command('abc123', 't', ['a'])
        
        # 新しいテストケースを確認
        test_files = list(test_dir.glob("custom-*.in"))
        test_files.sort()
        
        assert len(test_files) == 2, "Should have exactly 2 test cases in second run"
        for test_file in test_files:
            with open(test_file) as f:
                content = f.read()
                assert content == "3 4\n", "Second test cases should match"

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
        handle_command('abc123', 't', ['a'])
        
        # 最初のテストケースを確認
        test_dir = mock_config.get_test_dir('abc123', 'a')
        test_files = list(test_dir.glob("custom-*.in"))
        test_files.sort()
        
        assert len(test_files) == 2, "Should have exactly 2 test cases in first run"
        for test_file in test_files:
            with open(test_file) as f:
                content = f.read()
                assert content == "1 2\n", "First test cases should match"
        
        # ジェネレータを変更
        with open(problem_dir / "a_gen.py", "w") as f:
            f.write("""
TESTCASE_NUM = 2

def generate():
    return {
        'input': '10 20\\n',
        'output': '30\\n'
    }
""")
        
        # 再度テストを実行
        handle_command('abc123', 't', ['a'])
        
        # 新しいテストケースを確認
        test_files = list(test_dir.glob("custom-*.in"))
        test_files.sort()
        
        assert len(test_files) == 2, "Should have exactly 2 test cases in second run"
        for test_file in test_files:
            with open(test_file) as f:
                content = f.read()
                assert content == "10 20\n", "Second test cases should match"

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
        handle_command('abc123', 't', ['a'])
        
        # ファイル名の形式を確認
        test_dir = mock_config.get_test_dir('abc123', 'a')
        test_files = list(test_dir.glob("custom-*.in"))
        
        # テストケースが生成されていることを確認
        assert len(test_files) == 1, "Should have exactly 1 test case"
        
        # ファイル名のパターンをチェック
        import re
        pattern = re.compile(r'custom-\d{14}-\d+\.in')
        test_file = test_files[0]
        assert pattern.match(test_file.name), f"File name {test_file.name} should match the pattern"
        
        # 対応する.outファイルが存在することを確認
        output_file = test_file.parent / test_file.name.replace(".in", ".out")
        assert output_file.exists(), "Output file should exist"
        
        # ファイルの内容を確認
        with open(test_file) as f:
            assert f.read() == "1 2\n", "Input file content should match"
        with open(output_file) as f:
            assert f.read() == "3\n", "Output file content should match"