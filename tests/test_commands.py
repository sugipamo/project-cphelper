import pytest
from pathlib import Path
import os
import shutil
from src.commands import handle_command

@pytest.fixture
def workspace(tmp_path):
    """一時的な作業ディレクトリを提供する"""
    # 必要なディレクトリ構造を作成
    (tmp_path / "template").mkdir()
    (tmp_path / "contest").mkdir()
    
    # テンプレートファイルを作成
    with open(tmp_path / "template" / "main.py", "w") as f:
        f.write("# Test template")
    with open(tmp_path / "template" / "main.rs", "w") as f:
        f.write("// Test template")
    
    return tmp_path

@pytest.fixture
def mock_subprocess(monkeypatch):
    """subprocessのモック"""
    class MockSubprocess:
        def __init__(self):
            self.commands = []
        
        def run(self, command, *args, **kwargs):
            if isinstance(command, str):
                self.commands.append(command)
            else:
                self.commands.append(' '.join(command))
            return type('obj', (object,), {'returncode': 0})()
    
    mock = MockSubprocess()
    monkeypatch.setattr('subprocess.run', mock.run)
    return mock

def test_workspace_setup(workspace):
    """
    テスト環境のセットアップが正しく機能しているか確認
    """
    print(f"\n=== Workspace Setup Test ===")
    print(f"Workspace path: {workspace}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Template directory exists: {(workspace / 'template').exists()}")
    print(f"Contest directory exists: {(workspace / 'contest').exists()}")
    print(f"Template files:")
    if (workspace / 'template').exists():
        print(f"  Contents: {os.listdir(workspace / 'template')}")
        if (workspace / 'template' / 'main.py').exists():
            with open(workspace / 'template' / 'main.py') as f:
                print(f"  main.py content: {f.read()}")
    
    # 基本的な検証
    assert (workspace / "template").exists()
    assert (workspace / "contest").exists()
    assert (workspace / "template" / "main.py").exists()
    assert (workspace / "template" / "main.rs").exists()

def test_handle_command_debug(workspace, mock_subprocess):
    """
    handle_commandの動作を詳細に確認
    """
    print(f"\n=== Handle Command Debug ===")
    os.chdir(workspace)
    print(f"Current directory before command: {os.getcwd()}")
    print(f"Directory contents before command: {os.listdir()}")
    
    handle_command('abc123', 'o', ['a'])
    
    print(f"Directory contents after command: {os.listdir()}")
    contest_dir = workspace / "contest" / "abc123"
    if contest_dir.exists():
        print(f"Contest directory contents: {os.listdir(contest_dir)}")
    
    # モックされたコマンドの確認
    print(f"Mocked subprocess commands: {mock_subprocess.commands}")

@pytest.fixture
def mock_config(monkeypatch, workspace):
    """configのモック"""
    class MockConfig:
        TEMPLATE_DIR = workspace / "template"
        def get_problem_dir(self, contest_id, problem_id):
            return workspace / "contest" / contest_id / problem_id
        def get_test_dir(self, contest_id, problem_id):
            return workspace / "test" / contest_id / problem_id
    
    mock = MockConfig()
    monkeypatch.setattr('src.commands.config.TEMPLATE_DIR', mock.TEMPLATE_DIR)
    monkeypatch.setattr('src.commands.config.get_problem_dir', mock.get_problem_dir)
    monkeypatch.setattr('src.commands.config.get_test_dir', mock.get_test_dir)
    return mock

@pytest.fixture
def mock_webbrowser(monkeypatch):
    """webbrowserのモック"""
    def mock_open(url):
        pass
    monkeypatch.setattr('webbrowser.open', mock_open)

class TestCommandO:
    def test_basic_python(self, workspace, mock_subprocess, mock_config, mock_webbrowser):
        """
        基本的なPythonファイル作成のテスト
        """
        os.chdir(workspace)
        handle_command('abc123', 'o', ['a'])
        
        # 各階層のディレクトリ存在確認
        problem_dir = workspace / "contest" / "abc123" / "a"
        assert problem_dir.exists(), "Problem directory should exist"
        assert (problem_dir / "a.py").exists(), "Python file should be created"
        
        # ファイルの内容確認
        with open(problem_dir / "a.py") as f:
            content = f.read()
            assert content.strip() == "# Test template", "File should contain template content"
        
        # コマンド実行確認
        expected_url = "https://atcoder.jp/contests/abc123/tasks/abc123_a"
        assert any(expected_url in cmd for cmd in mock_subprocess.commands), "URL should be in commands"

    def test_missing_problem_id(self, workspace):
        """
        問題IDが指定されていない場合のテスト
        """
        os.chdir(workspace)
        with pytest.raises(IndexError, match="Problem ID is required"):
            handle_command('abc123', 'o', [])

    def test_invalid_command(self, workspace):
        """
        無効なコマンドのテスト
        """
        os.chdir(workspace)
        with pytest.raises(ValueError, match="Invalid command or arguments"):
            handle_command('abc123', 'invalid', ['a']) 

    def test_rust_option(self, workspace, mock_subprocess, mock_config, mock_webbrowser):
        """
        Rustオプション指定のテスト
        """
        os.chdir(workspace)
        handle_command('abc123', 'o', ['a', '--rust'])
        
        # 各階層のディレクトリ存在確認
        problem_dir = workspace / "contest" / "abc123" / "a"
        assert problem_dir.exists(), "Problem directory should exist"
        assert (problem_dir / "a.rs").exists(), "Rust file should be created"
        
        # ファイルの内容確認
        with open(problem_dir / "a.rs") as f:
            content = f.read()
            assert content.strip() == "// Test template", "File should contain Rust template content"
        
        # コマンド実行確認
        expected_url = "https://atcoder.jp/contests/abc123/tasks/abc123_a"
        assert any(expected_url in cmd for cmd in mock_subprocess.commands), "URL should be in commands"

    def test_rust_short_option(self, workspace, mock_subprocess, mock_config, mock_webbrowser):
        """
        Rustの短縮オプション(-rs)のテスト
        """
        os.chdir(workspace)
        handle_command('abc123', 'o', ['a', '-rs'])
        
        # 各階層のディレクトリ存在確認
        problem_dir = workspace / "contest" / "abc123" / "a"
        assert problem_dir.exists(), "Problem directory should exist"
        assert (problem_dir / "a.rs").exists(), "Rust file should be created"
        
        # ファイルの内容確認
        with open(problem_dir / "a.rs") as f:
            content = f.read()
            assert content.strip() == "// Test template", "File should contain Rust template content"
        
        # コマンド実行確認
        expected_url = "https://atcoder.jp/contests/abc123/tasks/abc123_a"
        assert any(expected_url in cmd for cmd in mock_subprocess.commands), "URL should be in commands" 

    def test_missing_template(self, workspace, mock_subprocess, mock_config, mock_webbrowser):
        """
        テンプレートファイルが存在しない場合のテスト
        """
        os.chdir(workspace)
        # テンプレートファイルを削除
        os.remove(workspace / "template" / "main.py")
        handle_command('abc123', 'o', ['a'])
        
        # ディレクトリは作成されるが、空のファイルが作成されることを確認
        problem_dir = workspace / "contest" / "abc123" / "a"
        assert problem_dir.exists(), "Problem directory should exist"
        assert (problem_dir / "a.py").exists(), "Empty Python file should be created"
        
        # ファイルが空であることを確認
        with open(problem_dir / "a.py") as f:
            content = f.read()
            assert content.strip() == "", "File should be empty when template is missing"
        
        # コマンド実行確認
        expected_url = "https://atcoder.jp/contests/abc123/tasks/abc123_a"
        assert any(expected_url in cmd for cmd in mock_subprocess.commands), "URL should be in commands"

    def test_missing_rust_template(self, workspace, mock_subprocess, mock_config, mock_webbrowser):
        """
        Rustのテンプレートファイルが存在しない場合のテスト
        """
        os.chdir(workspace)
        # Rustのテンプレートファイルを削除
        os.remove(workspace / "template" / "main.rs")
        handle_command('abc123', 'o', ['a', '--rust'])
        
        # ディレクトリは作成されるが、空のファイルが作成されることを確認
        problem_dir = workspace / "contest" / "abc123" / "a"
        assert problem_dir.exists(), "Problem directory should exist"
        assert (problem_dir / "a.rs").exists(), "Empty Rust file should be created"
        
        # ファイルが空であることを確認
        with open(problem_dir / "a.rs") as f:
            content = f.read()
            assert content.strip() == "", "File should be empty when template is missing"
        
        # コマンド実行確認
        expected_url = "https://atcoder.jp/contests/abc123/tasks/abc123_a"
        assert any(expected_url in cmd for cmd in mock_subprocess.commands), "URL should be in commands" 