import pytest
import os
from pathlib import Path
from src.commands import handle_command
import builtins
from unittest.mock import patch

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

        # テストケースディレクトリを作成
        test_dir = mock_config.get_test_dir('abc123', 'a')
        test_dir.mkdir(parents=True)
        with open(test_dir / "sample-1.in", "w") as f:
            f.write("test input")
        with open(test_dir / "sample-1.out", "w") as f:
            f.write("test output")

        # input()をモック化
        with patch('builtins.input', return_value='y'):
            handle_command('abc123', 's', ['a'])

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

        # テストケースディレクトリを作成
        test_dir = mock_config.get_test_dir('abc123', 'a')
        test_dir.mkdir(parents=True)
        with open(test_dir / "sample-1.in", "w") as f:
            f.write("test input")
        with open(test_dir / "sample-1.out", "w") as f:
            f.write("test output")

        # input()をモック化
        with patch('builtins.input', return_value='y'):
            handle_command('abc123', 's', ['a', '--rust'])

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

        # テストケースディレクトリを作成
        test_dir = mock_config.get_test_dir('abc123', 'a')
        test_dir.mkdir(parents=True)
        with open(test_dir / "sample-1.in", "w") as f:
            f.write("test input")
        with open(test_dir / "sample-1.out", "w") as f:
            f.write("test output")

        # input()をモック化
        with patch('builtins.input', return_value='y'):
            handle_command('abc123', 's', ['a'])

@pytest.fixture
def mock_lib_merger(monkeypatch):
    """lib_mergerのモック"""
    def mock_merge_libraries(source_file):
        with open(source_file) as f:
            content = f.read()
        return "def gcd(a, b):\n    return b if a % b == 0 else gcd(b, a % b)\n\n" + content
    
    monkeypatch.setattr('src.commands.lib_merger.merge_libraries', mock_merge_libraries) 