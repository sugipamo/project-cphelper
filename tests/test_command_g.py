import pytest
import os
from pathlib import Path
from src.commands import handle_command

class TestCommandG:
    def test_create_generator(self, workspace, mock_subprocess, mock_config):
        """
        ジェネレータファイルの新規作成のテスト
        """
        os.chdir(workspace)
        
        # ジェネレータファイルを作成
        handle_command('abc123', 'g', ['a'])
        
        # ファイルが作成されていることを確認
        generator_file = workspace / "contest/abc123/a/a_gen.py"
        assert generator_file.exists(), "Generator file should be created"
        
        # ファイルの内容を確認
        content = generator_file.read_text()
        assert 'TESTCASE_NUM = 10' in content, "Should contain default test case number"
        assert 'def generate():' in content, "Should contain generate function"
        assert 'def check_constraints(' in content, "Should contain check_constraints function"
        
        # テンプレートの基本的な構造を確認
        assert '"""' in content, "Should contain docstring"
        assert 'import random' in content, "Should import random module"
        assert "return {" in content, "Should contain return statement"
        assert "'input':" in content, "Should contain input key"
        assert "'output':" in content, "Should contain output key"

    def test_create_generator_existing_dir(self, workspace, mock_subprocess, mock_config):
        """
        既存のディレクトリにジェネレータファイルを作成するテスト
        """
        os.chdir(workspace)
        
        # 事前にディレクトリを作成
        problem_dir = workspace / "contest/abc123/a"
        problem_dir.mkdir(parents=True)
        
        # ジェネレータファイルを作成
        handle_command('abc123', 'g', ['a'])
        
        # ファイルが作成されていることを確認
        generator_file = problem_dir / "a_gen.py"
        assert generator_file.exists(), "Generator file should be created"
        
        # ファイルの内容を確認
        content = generator_file.read_text()
        assert 'def generate():' in content, "Should contain generate function"

    def test_create_generator_existing_file(self, workspace, mock_subprocess, mock_config):
        """
        既存のジェネレータファイルがある場合のテスト
        """
        os.chdir(workspace)
        
        # 事前にディレクトリとファイルを作成
        problem_dir = workspace / "contest/abc123/a"
        problem_dir.mkdir(parents=True)
        generator_file = problem_dir / "a_gen.py"
        
        # 有効なジェネレータコードを作成
        generator_code = '''
TESTCASE_NUM = 1

def generate():
    return {
        'input': '1 2\\n',
        'output': '3\\n'
    }
'''
        generator_file.write_text(generator_code)
        
        # ジェネレータコマンドを実行
        handle_command('abc123', 'g', ['a'])
        
        # テストケースが生成されることを確認
        test_dir = mock_config.get_test_dir('abc123', 'a')
        assert test_dir.exists(), "Test directory should be created"
        
        # テストケースファイルが生成されていることを確認
        test_files = list(test_dir.glob("custom-*.in"))
        assert len(test_files) > 0, "Should generate at least one test case"
        
        # テストケースの内容を確認
        test_file = test_files[0]
        assert test_file.read_text() == "1 2\n", "Test case input should match"
        output_file = test_file.parent / test_file.name.replace(".in", ".out")
        assert output_file.exists(), "Output file should exist"
        assert output_file.read_text() == "3\n", "Test case output should match" 