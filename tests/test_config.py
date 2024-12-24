import pytest
from pathlib import Path
import os
from src import config

class TestConfig:
    def test_setup_environment(self, workspace, monkeypatch):
        """
        setup_environment()の基本機能のテスト
        """
        os.chdir(workspace)
        
        # 設定を一時的に変更
        monkeypatch.setattr('src.config.CONTEST_DIR', str(workspace / "contest"))
        monkeypatch.setattr('src.config.TEMPLATE_DIR', str(workspace / "contest/template"))
        monkeypatch.setattr('src.config.LIB_DIR', str(workspace / "contest/lib"))
        
        # 環境のセットアップを実行
        config.setup_environment()
        
        # 必要なディレクトリが作成されていることを確認
        assert (workspace / "contest").exists(), "Contest directory should be created"
        assert (workspace / "contest/template").exists(), "Template directory should be created"
        assert (workspace / "contest/lib").exists(), "Library directory should be created"
        
        # ディレクトリの権限を確認
        assert os.access(workspace / "contest", os.W_OK), "Contest directory should be writable"
        assert os.access(workspace / "contest/template", os.W_OK), "Template directory should be writable"
        assert os.access(workspace / "contest/lib", os.W_OK), "Library directory should be writable"

    def test_setup_environment_existing_dirs(self, workspace, monkeypatch):
        """
        既存のディレクトリがある場合のsetup_environment()のテスト
        """
        os.chdir(workspace)
        
        # 設定を一時的に変更
        monkeypatch.setattr('src.config.CONTEST_DIR', str(workspace / "contest"))
        monkeypatch.setattr('src.config.TEMPLATE_DIR', str(workspace / "contest/template"))
        monkeypatch.setattr('src.config.LIB_DIR', str(workspace / "contest/lib"))
        
        # 事前にディレクトリを作成
        (workspace / "contest").mkdir(exist_ok=True)
        (workspace / "contest/template").mkdir(parents=True, exist_ok=True)
        
        # テストファイルを作成して、ディレクトリの内容が保持されることを確認
        test_file = workspace / "contest/template/test.txt"
        test_file.write_text("test content")
        
        # 環境のセットアップを実行（エラーが発生しないことを確認）
        config.setup_environment()
        
        # すべてのディレクトリが存在することを確認
        assert (workspace / "contest").exists(), "Contest directory should exist"
        assert (workspace / "contest/template").exists(), "Template directory should exist"
        assert (workspace / "contest/lib").exists(), "Library directory should exist"
        
        # テストファイルが保持されていることを確認
        assert test_file.exists(), "Test file should be preserved"
        assert test_file.read_text() == "test content", "Test file content should be preserved" 