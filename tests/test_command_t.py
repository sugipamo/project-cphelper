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