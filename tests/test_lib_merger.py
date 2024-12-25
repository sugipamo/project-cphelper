import pytest
from pathlib import Path
import os
from src.lib_merger import merge_libraries, merge_code

class TestLibMerger:
    def test_merge_single_file(self, tmp_path):
        # シンプルなPythonファイルを作成
        source_content = """def add(a, b):
    return a + b

def main():
    print(add(1, 2))
"""
        source_file = tmp_path / "main.py"
        source_file.write_text(source_content)

        # マージを実行
        result = merge_libraries(source_file)

        # 結果を検証
        assert "def add(a, b):" in result
        assert "def main():" in result
        assert "print(add(1, 2))" in result

    def test_merge_with_imports(self, tmp_path):
        # ライブラリファイルを作成
        lib_dir = tmp_path / "lib"
        lib_dir.mkdir()
        lib_content = """def multiply(a, b):
    return a * b
"""
        lib_file = lib_dir / "math_utils.py"
        lib_file.write_text(lib_content)

        # メインファイルを作成
        main_content = """from lib.math_utils import multiply

def main():
    print(multiply(2, 3))
"""
        main_file = tmp_path / "main.py"
        main_file.write_text(main_content)

        # マージを実行
        result = merge_libraries(main_file)

        # 結果を検証
        assert "def multiply(a, b):" in result
        assert "def main():" in result
        assert "print(multiply(2, 3))" in result
        assert "from lib.math_utils import multiply" not in result

    def test_merge_with_relative_imports(self, tmp_path):
        # ディレクトリ構造を作成
        contest_dir = tmp_path / "contest"
        contest_dir.mkdir()
        lib_dir = contest_dir / "lib"
        lib_dir.mkdir()
        
        # ライブラリファイルを作成
        lib_content = """def divide(a, b):
    return a / b
"""
        lib_file = lib_dir / "math_utils.py"
        lib_file.write_text(lib_content)

        # 問題ディレクトリを作成
        problem_dir = contest_dir / "abc123" / "a"
        problem_dir.mkdir(parents=True)

        # メインファイルを作成（相対インポート使用）
        main_content = """from ...lib.math_utils import divide

def main():
    print(divide(6, 2))
"""
        main_file = problem_dir / "main.py"
        main_file.write_text(main_content)

        # マージを実行
        result = merge_libraries(main_file)

        # 結果を検証
        assert "def divide(a, b):" in result
        assert "def main():" in result
        assert "print(divide(6, 2))" in result
        assert "from ...lib.math_utils import divide" not in result

    def test_merge_with_specific_imports(self, tmp_path):
        # ライブラリファイルを作成（複数の関数を含む）
        lib_dir = tmp_path / "lib"
        lib_dir.mkdir()
        lib_content = """def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b
"""
        lib_file = lib_dir / "math_utils.py"
        lib_file.write_text(lib_content)

        # メインファイルを作成（特定の関数のみをインポート）
        main_content = """from lib.math_utils import add, multiply

def main():
    print(add(1, 2))
    print(multiply(3, 4))
"""
        main_file = tmp_path / "main.py"
        main_file.write_text(main_content)

        # マージを実行
        result = merge_libraries(main_file)

        # 結果を検証
        assert "def add(a, b):" in result
        assert "def multiply(a, b):" in result
        assert "def subtract(a, b):" not in result
        assert "def main():" in result
        assert "print(add(1, 2))" in result
        assert "print(multiply(3, 4))" in result

    def test_merge_with_missing_file(self, tmp_path):
        # 存在しないファイルをインポートするメインファイルを作成
        main_content = """from lib.missing_file import some_function

def main():
    print(some_function())
"""
        main_file = tmp_path / "main.py"
        main_file.write_text(main_content)

        # マージを実行（FileNotFoundErrorが発生することを確認）
        with pytest.raises(FileNotFoundError):
            merge_libraries(main_file)

    def test_merge_with_syntax_error(self, tmp_path):
        # 構文エラーを含むファイルを作成
        main_content = """def invalid_function(
    print("This is invalid syntax")
"""
        main_file = tmp_path / "main.py"
        main_file.write_text(main_content)

        # マージを実行（SyntaxErrorが発生することを確認）
        with pytest.raises(SyntaxError):
            merge_libraries(main_file)

    def test_merge_with_circular_imports(self, tmp_path):
        # 循環参照を含むファイルを作成
        lib_dir = tmp_path / "lib"
        lib_dir.mkdir()

        file_a_content = """from .b import function_b

def function_a():
    return function_b()
"""
        file_a = lib_dir / "a.py"
        file_a.write_text(file_a_content)

        file_b_content = """from .a import function_a

def function_b():
    return function_a()
"""
        file_b = lib_dir / "b.py"
        file_b.write_text(file_b_content)

        # メインファイルを作成
        main_content = """from lib.a import function_a

def main():
    print(function_a())
"""
        main_file = tmp_path / "main.py"
        main_file.write_text(main_content)

        # マージを実行（循環参照が適切に処理されることを確認）
        result = merge_libraries(main_file)
        assert "def function_a" in result
        assert "def function_b" in result
        assert "def main" in result