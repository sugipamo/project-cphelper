import pytest
import os
from pathlib import Path
from src.commands import handle_command

class TestCommandS:
    def test_basic_submit(self, workspace, mock_subprocess, mock_config):
        """
        基本的な提出のテスト
        """
        os.chdir(workspace)
        # テスト対象のファイルを作成
        problem_dir = workspace / "contest" / "abc123" / "a"
        problem_dir.mkdir(parents=True)
        with open(problem_dir / "a.py", "w") as f:
            f.write("# Test solution")
        
        handle_command('abc123', 's', ['a'])
        
        # ojコマンドが実行されたことを確認
        expected_url = "https://atcoder.jp/contests/abc123/tasks/abc123_a"
        expected_lang = mock_config.LANGUAGE_CODE["pypy"]
        assert any(f"oj submit --yes {expected_url}" in cmd for cmd in mock_subprocess.commands), "Submit command should be executed"
        assert any(f"-l {expected_lang}" in cmd for cmd in mock_subprocess.commands), "Language ID should be specified"

    def test_rust_submit(self, workspace, mock_subprocess, mock_config):
        """
        Rustの提出のテスト
        """
        os.chdir(workspace)
        # テスト対象のファイルを作成
        problem_dir = workspace / "contest" / "abc123" / "a"
        problem_dir.mkdir(parents=True)
        with open(problem_dir / "a.rs", "w") as f:
            f.write("// Test solution")
        
        handle_command('abc123', 's', ['a', '--rust'])
        
        # ojコマンドが実行されたことを確認
        expected_url = "https://atcoder.jp/contests/abc123/tasks/abc123_a"
        expected_lang = mock_config.LANGUAGE_CODE["rust"]
        assert any(f"oj submit --yes {expected_url}" in cmd for cmd in mock_subprocess.commands), "Submit command should be executed"
        assert any(f"-l {expected_lang}" in cmd for cmd in mock_subprocess.commands), "Language ID should be specified"

    def test_missing_source_file(self, workspace, mock_subprocess, mock_config):
        """
        ソースファイルが存在しない場合のテスト
        """
        os.chdir(workspace)
        problem_dir = workspace / "contest" / "abc123" / "a"
        problem_dir.mkdir(parents=True)
        with pytest.raises(FileNotFoundError):
            handle_command('abc123', 's', ['a'])

    def test_python_library_merge(self, workspace, mock_subprocess, mock_config, mock_lib_merger):
        """
        Pythonのライブラリマージのテスト
        """
        os.chdir(workspace)
        # テスト対象のファイルとライブラリを作成
        problem_dir = workspace / "contest" / "abc123" / "a"
        problem_dir.mkdir(parents=True)
        with open(problem_dir / "a.py", "w") as f:
            f.write("from lib.math import gcd\n\n# Test solution")
        
        handle_command('abc123', 's', ['a'])
        
        # マージされたファイルが作成されたことを確認
        temp_file = workspace / ".temp" / "a.py"
        assert temp_file.exists(), "Merged file should be created"
        
        # マージされたファイルの内容を確認
        with open(temp_file) as f:
            content = f.read()
            assert "def gcd" in content, "Library function should be merged"
            assert "Test solution" in content, "Original code should be preserved"

@pytest.fixture
def mock_lib_merger(monkeypatch):
    """lib_mergerのモック"""
    def mock_merge_libraries(source_file):
        with open(source_file) as f:
            content = f.read()
        return "def gcd(a, b):\n    return b if a % b == 0 else gcd(b, a % b)\n\n" + content
    
    monkeypatch.setattr('src.commands.lib_merger.merge_libraries', mock_merge_libraries) 