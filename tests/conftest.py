import pytest
from pathlib import Path
import os

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