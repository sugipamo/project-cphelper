"""
設定値の管理モジュール
"""

import os
from pathlib import Path

# ディレクトリ設定
CONTEST_DIR = "contest"
TEMPLATE_DIR = os.path.join(CONTEST_DIR, "template")
LIB_DIR = os.path.join(CONTEST_DIR, "lib")

# 言語設定
INTERPRETER = {
    "python": "python",
    "pypy": "pypy",
    "rust": "rust",
    "py": "pypy",  # デフォルト
    "rs": "rust",
}

EXTENSIONS = {
    "python": "py",
    "pypy": "py",
    "rust": "rs",
}

LANGUAGE_CODE = {
    "python": "5082",
    "pypy": "5078",  # デフォルト
    "rust": "5054",
}

# Docker設定
DOCKER_IMAGE = {
    "python": "python:3.10-slim",
    "pypy": "pypy:3.10-slim",
    "rust": "rust:1.70"
}

DOCKER_CMD = "docker run --rm -v $(pwd):/workspace -w /workspace"
DOCKER_RESOURCES = {
    "cpu": "2",
    "memory": "1024M",
}

# テスト実行設定
PARALLEL = 10
TIMEOUT = "timeout 5s"

def setup_environment():
    """
    必要なディレクトリ構造を作成
    """
    dirs = [
        CONTEST_DIR,
        TEMPLATE_DIR,
        LIB_DIR,
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

def get_problem_dir(contest_id: str, problem_id: str) -> Path:
    """
    問題ディレクトリのパスを取得
    """
    return Path(CONTEST_DIR) / contest_id / problem_id

def get_test_dir(contest_id: str, problem_id: str) -> Path:
    """
    テストケースディレクトリのパスを取得
    """
    return get_problem_dir(contest_id, problem_id) / "test" 