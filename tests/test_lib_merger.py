import pytest
from pathlib import Path
import os
from src.lib_merger import merge_libraries

class TestLibMerger:
    def test_basic_import(self, workspace):
        """
        基本的なライブラリインポートのテスト
        """
        os.chdir(workspace)
        
        # テスト用のディレクトリを作成
        source_dir = workspace / "contest/abc123/a"
        source_dir.mkdir(parents=True)
        
        lib_dir = workspace / "contest/lib"
        lib_dir.mkdir(parents=True)
        
        # テスト用のライブラリファイルを作成
        with open(lib_dir / "basic.py", "w") as f:
            f.write("""
def gcd(a: int, b: int) -> int:
    return b if a % b == 0 else gcd(b, a % b)
""")
        
        # テスト用のソースファイルを作成
        source_file = source_dir / "a.py"
        source_file.write_text("""
from ..lib.basic import gcd

def solve():
    print(gcd(10, 5))
""")
        
        # マージを実行
        merged_code = merge_libraries(source_file)
        
        # マージ結果を確認
        assert 'def gcd' in merged_code, "Should contain imported function"
        assert 'from ..lib.basic import gcd' not in merged_code, "Should remove import statement"
        assert 'def solve' in merged_code, "Should preserve original code"

    def test_multiple_imports(self, workspace):
        """
        複数の関数をインポートするテスト
        """
        os.chdir(workspace)
        
        # テスト用のディレクトリを作成
        source_dir = workspace / "contest/abc123/a"
        source_dir.mkdir(parents=True)
        
        lib_dir = workspace / "contest/lib"
        lib_dir.mkdir(parents=True)
        
        # テスト用のライブラリファイルを作成
        with open(lib_dir / "basic.py", "w") as f:
            f.write("""
def gcd(a: int, b: int) -> int:
    return b if a % b == 0 else gcd(b, a % b)

def lcm(a: int, b: int) -> int:
    return a * b // gcd(a, b)
""")
        
        # テスト用のソースファイルを作成
        source_file = source_dir / "a.py"
        source_file.write_text("""
from ..lib.basic import gcd, lcm

def solve():
    print(gcd(10, 5))
    print(lcm(10, 5))
""")
        
        # マージを実行
        merged_code = merge_libraries(source_file)
        
        # マージ結果を確認
        assert 'def gcd' in merged_code, "Should contain first imported function"
        assert 'def lcm' in merged_code, "Should contain second imported function"
        assert 'from ..lib.basic import' not in merged_code, "Should remove import statement"

    def test_recursive_imports(self, workspace):
        """
        再帰的なインポートのテスト
        """
        os.chdir(workspace)
        
        # テスト用のディレクトリを作成
        source_dir = workspace / "contest/abc123/a"
        source_dir.mkdir(parents=True)
        
        lib_dir = workspace / "contest/lib"
        lib_dir.mkdir(parents=True)
        
        # テスト用のライブラリファイルを作成
        with open(lib_dir / "basic.py", "w") as f:
            f.write("""
def gcd(a: int, b: int) -> int:
    return b if a % b == 0 else gcd(b, a % b)
""")

        with open(lib_dir / "advanced.py", "w") as f:
            f.write("""
from .basic import gcd

def lcm(a: int, b: int) -> int:
    return a * b // gcd(a, b)
""")
        
        # テスト用のソースファイルを作成
        source_file = source_dir / "a.py"
        source_file.write_text("""
from ..lib.advanced import lcm

def solve():
    print(lcm(10, 5))
""")
        
        # マージを実行
        merged_code = merge_libraries(source_file)
        
        # マージ結果を確認
        assert 'def gcd' in merged_code, "Should contain base function"
        assert 'def lcm' in merged_code, "Should contain imported function"
        assert 'from .basic import gcd' not in merged_code, "Should remove all import statements"
        assert 'from ..lib.advanced import lcm' not in merged_code, "Should remove all import statements"

    def test_missing_library(self, workspace):
        """
        存在しないライブラリをインポートした場合のテスト
        """
        os.chdir(workspace)
        
        # テスト用のディレクトリを作成
        source_dir = workspace / "contest/abc123/a"
        source_dir.mkdir(parents=True)
        
        # テスト用のソースファイルを作成（存在しないライブラリを参照）
        source_file = source_dir / "a.py"
        source_file.write_text("""
from ..lib.missing import function

def solve():
    print(function(10))
""")
        
        # マージを実行（エラーが発生することを確認）
        with pytest.raises(FileNotFoundError, match=r".*インポートされたファイルが見つかりません.*"):
            merge_libraries(source_file)

    def test_syntax_error(self, workspace):
        """
        構文エラーがあるケースのテスト
        """
        os.chdir(workspace)
        
        # テスト用のディレクトリを作成
        source_dir = workspace / "contest/abc123/a"
        source_dir.mkdir(parents=True)
        
        # テスト用のソースファイルを作成（構文エラーを含む）
        source_file = source_dir / "test_syntax_error.py"
        source_file.write_text("""
def main()  # コロンが抜けている
    print("Hello")

if __name__ == "__main__":
    main()
""")
        
        # マージを実行（元のコードが返されることを確認）
        merged_code = merge_libraries(source_file)
        assert 'def main()' in merged_code, "Should preserve original code with syntax error" 