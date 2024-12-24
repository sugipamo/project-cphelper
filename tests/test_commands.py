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

class TestCommandO:
    def test_basic_python(self, workspace, mock_subprocess):
        """
        基本的なPythonファイル作成のテスト
        """
        os.chdir(workspace)
        handle_command('abc123', 'o', ['a'])
        
        # 各階層のディレクトリ存在確認
        contest_base = workspace / "contest"
        assert contest_base.exists(), "Contest base directory should exist"
        assert "abc123" in os.listdir(contest_base), "Contest directory should be created"
        
        contest_abc = contest_base / "abc123"
        assert contest_abc.exists(), "Contest ABC directory should exist"
        assert "a" in os.listdir(contest_abc), "Problem directory should be created"
        
        contest_dir = contest_abc / "a"
        assert contest_dir.exists(), "Problem directory should exist"
        assert "a.py" in os.listdir(contest_dir), "Python file should be created"
        
        # ファイルの内容確認
        target_file = contest_dir / "a.py"
        assert target_file.exists(), "Target file should exist"
        with open(target_file) as f:
            content = f.read()
            assert content.strip() == "# Test template", "File should contain template content"
        
        # コマンド実行確認
        expected_commands = [
            'oj download https://atcoder.jp/contests/abc123/tasks/abc123_a',
            'cursor contest/abc123/a/a.py'
        ]
        assert mock_subprocess.commands == expected_commands, "Commands should match expected sequence"

    def test_rust_option(self, workspace, mock_subprocess):
        """
        Rustオプション指定のテスト
        """
        os.chdir(workspace)
        handle_command('abc123', 'o', ['a', '--rust'])
        
        # ディレクトリとファイルの確認
        contest_dir = workspace / "contest" / "abc123" / "a"
        assert contest_dir.exists()
        assert (contest_dir / "a.rs").exists()
        
        # テンプレートの内容確認
        with open(contest_dir / "a.rs") as f:
            content = f.read()
        assert content.strip() == "// Test template"

    def test_missing_problem_id(self, workspace):
        """
        問題IDが指定されていない場合のテスト
        """
        os.chdir(workspace)
        with pytest.raises(IndexError, match="Problem ID is required"):
            handle_command('abc123', 'o', [])

    def test_missing_template(self, workspace, mock_subprocess):
        """
        テンプレートファイルが存在しない場合のテスト
        """
        os.chdir(workspace)
        os.remove(workspace / "template" / "main.py")
        handle_command('abc123', 'o', ['a'])
        
        # ディレクトリは作成されるが、ファイルは作成されない
        contest_dir = workspace / "contest" / "abc123"
        assert contest_dir.exists()
        assert not (contest_dir / "a.py").exists()

    def test_existing_contest_dir(self, workspace, mock_subprocess):
        """
        コンテストディレクトリが既に存在する場合のテスト
        """
        os.chdir(workspace)
        # 問題のディレクトリまで作成
        contest_dir = workspace / "contest" / "abc123" / "a"
        contest_dir.mkdir(parents=True)
        
        handle_command('abc123', 'o', ['a'])
        assert (contest_dir / "a.py").exists()
        
        # テンプレートの内容確認
        with open(contest_dir / "a.py") as f:
            content = f.read()
        assert content.strip() == "# Test template" 