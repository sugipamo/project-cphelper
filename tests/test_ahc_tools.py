import pytest
from pathlib import Path
import os
from src.ahc_tools import setup_tools, run_test_cases

class TestAHCTools:
    def test_setup_tools(self, workspace, monkeypatch):
        """
        AHCツールのセットアップをテスト
        """
        os.chdir(workspace)
        
        # コンテストディレクトリの設定
        contest_dir = workspace / "contest/ahc001"
        contest_dir.mkdir(parents=True)
        
        # ツールのセットアップを実行
        setup_tools("ahc001")
        
        # 必要なファイルとディレクトリが作成されていることを確認
        assert (contest_dir / "tools").exists(), "Tools directory should be created"
        assert (contest_dir / "tools/in").exists(), "Input directory should be created"
        assert (contest_dir / "tools/out").exists(), "Output directory should be created"

    def test_run_test_cases(self, workspace, monkeypatch):
        """
        テストケースの実行をテスト
        """
        os.chdir(workspace)
        
        # コンテストディレクトリの設定
        contest_dir = workspace / "contest/ahc001"
        contest_dir.mkdir(parents=True)
        tools_dir = contest_dir / "tools"
        tools_dir.mkdir()
        in_dir = tools_dir / "in"
        out_dir = tools_dir / "out"
        in_dir.mkdir()
        out_dir.mkdir()
        
        # テスト用の入力ファイルを作成
        (in_dir / "0000.txt").write_text("test input")
        
        # テスト用のソースファイルを作成
        source_file = contest_dir / "main.py"
        source_file.write_text("""
def solve():
    print("test output")
""")
        
        # テストケースを実行
        scores = run_test_cases("ahc001", source_file)
        
        # 結果を確認
        assert len(scores) > 0, "Should return scores"
        assert (out_dir / "0000.txt").exists(), "Should create output file"

    def test_setup_tools_existing_dir(self, workspace, monkeypatch):
        """
        既存のディレクトリがある場合のセットアップテスト
        """
        os.chdir(workspace)
        
        # 事前にディレクトリを作成
        contest_dir = workspace / "contest/ahc001"
        contest_dir.mkdir(parents=True)
        tools_dir = contest_dir / "tools"
        tools_dir.mkdir()
        
        # テストファイルを作成
        test_file = tools_dir / "test.txt"
        test_file.write_text("test content")
        
        # ツールのセットアップを実行
        setup_tools("ahc001")
        
        # ディレクトリ構造が正しいことを確認
        assert (contest_dir / "tools").exists(), "Tools directory should exist"
        assert (contest_dir / "tools/in").exists(), "Input directory should be created"
        assert (contest_dir / "tools/out").exists(), "Output directory should be created"
        
        # 既存のファイルが保持されていることを確認
        assert test_file.exists(), "Existing files should be preserved"
        assert test_file.read_text() == "test content", "File content should be preserved"

    def test_run_test_cases_multiple(self, workspace, monkeypatch):
        """
        複数のテストケースの実行をテスト
        """
        os.chdir(workspace)
        
        # コンテストディレクトリの設定
        contest_dir = workspace / "contest/ahc001"
        contest_dir.mkdir(parents=True)
        tools_dir = contest_dir / "tools"
        tools_dir.mkdir()
        in_dir = tools_dir / "in"
        out_dir = tools_dir / "out"
        in_dir.mkdir()
        out_dir.mkdir()
        
        # 複数のテスト用入力ファイルを作成
        for i in range(3):
            (in_dir / f"{i:04d}.txt").write_text(f"test input {i}")
        
        # テスト用のソースファイルを作成
        source_file = contest_dir / "main.py"
        source_file.write_text("""
def solve():
    print("test output")
""")
        
        # テストケースを実行
        scores = run_test_cases("ahc001", source_file)
        
        # 結果を確認
        assert len(scores) == 3, "Should return scores for all test cases"
        for i in range(3):
            assert (out_dir / f"{i:04d}.txt").exists(), f"Should create output file for test case {i}" 