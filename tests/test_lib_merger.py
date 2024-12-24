import pytest
from pathlib import Path
import os
from src.lib_merger import merge_libraries, resolve_imports, extract_functions

class TestLibMerger:
    def test_basic_import(self, workspace, monkeypatch):
        """
        基本的なライブラリインポートのテスト
        """
        os.chdir(workspace)
        
        # ライブラリディレクトリの設定
        lib_dir = workspace / "contest/lib"
        lib_dir.mkdir(parents=True)
        monkeypatch.setattr('src.config.LIB_DIR', str(lib_dir))
        
        # テスト用のライブラリファイルを作成
        math_dir = lib_dir / "math"
        math_dir.mkdir()
        with open(math_dir / "__init__.py", "w") as f:
            f.write("")
        with open(math_dir / "basic.py", "w") as f:
            f.write("""
def gcd(a: int, b: int) -> int:
    return b if a % b == 0 else gcd(b, a % b)
""")
        
        # テスト用のソースファイルを作成
        source_dir = workspace / "contest/abc123/a"
        source_dir.mkdir(parents=True)
        source_file = source_dir / "a.py"
        source_file.write_text("""
from lib.math.basic import gcd

def solve():
    print(gcd(10, 5))
""")
        
        # マージを実行
        merged_code = merge_libraries(source_file)
        
        # マージ結果を確認
        assert 'def gcd' in merged_code, "Should contain imported function"
        assert 'from lib.math.basic import gcd' not in merged_code, "Should remove import statement"
        assert 'def solve' in merged_code, "Should preserve original code"

    def test_multiple_imports(self, workspace, monkeypatch):
        """
        複数の関数をインポートするテスト
        """
        os.chdir(workspace)
        
        # ライブラリディレクトリの設定
        lib_dir = workspace / "contest/lib"
        lib_dir.mkdir(parents=True)
        monkeypatch.setattr('src.config.LIB_DIR', str(lib_dir))
        
        # テスト用のライブラリファイルを作成
        math_dir = lib_dir / "math"
        math_dir.mkdir()
        with open(math_dir / "__init__.py", "w") as f:
            f.write("")
        with open(math_dir / "basic.py", "w") as f:
            f.write("""
def gcd(a: int, b: int) -> int:
    return b if a % b == 0 else gcd(b, a % b)

def lcm(a: int, b: int) -> int:
    return a * b // gcd(a, b)
""")
        
        # テスト用のソースファイルを作成
        source_dir = workspace / "contest/abc123/a"
        source_dir.mkdir(parents=True)
        source_file = source_dir / "a.py"
        source_file.write_text("""
from lib.math.basic import gcd, lcm

def solve():
    print(gcd(10, 5))
    print(lcm(10, 5))
""")
        
        # マージを実行
        merged_code = merge_libraries(source_file)
        
        # マージ結果を確認
        assert 'def gcd' in merged_code, "Should contain first imported function"
        assert 'def lcm' in merged_code, "Should contain second imported function"
        assert 'from lib.math.basic import' not in merged_code, "Should remove import statement"

    def test_recursive_imports(self, workspace, monkeypatch):
        """
        再帰的なインポートのテスト
        """
        os.chdir(workspace)
        
        # ライブラリディレクトリの設定
        lib_dir = workspace / "contest/lib"
        lib_dir.mkdir(parents=True)
        monkeypatch.setattr('src.config.LIB_DIR', str(lib_dir))
        
        # テスト用のライブラリファイルを作成
        math_dir = lib_dir / "math"
        math_dir.mkdir()
        with open(math_dir / "__init__.py", "w") as f:
            f.write("")
        with open(math_dir / "advanced.py", "w") as f:
            f.write("""
from lib.math.basic import gcd

def lcm(a: int, b: int) -> int:
    return a * b // gcd(a, b)
""")
        with open(math_dir / "basic.py", "w") as f:
            f.write("""
def gcd(a: int, b: int) -> int:
    return b if a % b == 0 else gcd(b, a % b)
""")
        
        # テスト用のソースファイルを作成
        source_dir = workspace / "contest/abc123/a"
        source_dir.mkdir(parents=True)
        source_file = source_dir / "a.py"
        source_file.write_text("""
from lib.math.advanced import lcm

def solve():
    print(lcm(10, 5))
""")
        
        # マージを実行
        merged_code = merge_libraries(source_file)
        
        # マージ結果を確認
        assert 'def gcd' in merged_code, "Should contain base function"
        assert 'def lcm' in merged_code, "Should contain imported function"
        assert 'from lib.math' not in merged_code, "Should remove all import statements"

    def test_missing_library(self, workspace, monkeypatch):
        """
        存在しないライブラリをインポートした場合のテスト
        """
        os.chdir(workspace)
        
        # ライブラリディレクトリの設定
        lib_dir = workspace / "contest/lib"
        lib_dir.mkdir(parents=True)
        monkeypatch.setattr('src.config.LIB_DIR', str(lib_dir))
        
        # テスト用のソースファイルを作成（存在しないライブラリを参照）
        source_dir = workspace / "contest/abc123/a"
        source_dir.mkdir(parents=True)
        source_file = source_dir / "a.py"
        source_file.write_text("""
from lib.math.missing import function

def solve():
    print(function(10))
""")
        
        # マージを実行（警告は出るが、元のコードは保持される）
        merged_code = merge_libraries(source_file)
        
        # マージ結果を確認
        assert 'from lib.math.missing import function' in merged_code, "Should preserve import of missing library"
        assert 'def solve' in merged_code, "Should preserve original code" 