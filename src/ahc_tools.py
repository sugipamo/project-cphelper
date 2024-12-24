"""
AHC関連の機能の実装
"""

import subprocess
import os
from pathlib import Path
from . import config

def setup_tools(contest_id: str):
    """
    AHCのツール類をセットアップ
    """
    contest_dir = Path(config.CONTEST_DIR) / contest_id
    tools_dir = contest_dir / "tools"
    
    # ツールのダウンロードとセットアップ
    if not tools_dir.exists():
        # Gitの初期化
        if not (contest_dir / ".git").exists():
            subprocess.run("git init", shell=True, cwd=contest_dir)
            subprocess.run("git branch -m main", shell=True, cwd=contest_dir)
        
        # ツールのダウンロード
        url = f"https://atcoder.jp/contests/{contest_id}"
        subprocess.run(f"cargo new tools", shell=True, cwd=contest_dir)
        
        # TODO: コンテスト固有のツールダウンロード処理
        
        # Webvisualizerのセットアップ
        webvis_dir = contest_dir / "webvis"
        if not webvis_dir.exists():
            # TODO: Webvisualizer用の設定
            pass

def run_test_cases(contest_id: str, n_cases: int):
    """
    AHCのテストケース実行
    """
    contest_dir = Path(config.CONTEST_DIR) / contest_id
    tools_dir = contest_dir / "tools"
    
    # 入出力ディレクトリの作成
    for dir_name in ["in", "out", "other"]:
        (tools_dir / dir_name).mkdir(parents=True, exist_ok=True)
    
    # シード値の設定
    seeds_file = tools_dir / "seeds.txt"
    seeds_file.write_text("\n".join(str(i) for i in range(n_cases)))
    
    # テストケースの生成
    subprocess.run(
        "cargo run --manifest-path tools/Cargo.toml --bin gen seeds.txt",
        shell=True,
        cwd=contest_dir
    )
    
    # ビジュアライザのビルド
    subprocess.run(
        "cargo build --manifest-path tools/Cargo.toml --release --bin vis",
        shell=True,
        cwd=contest_dir
    )
    
    # TODO: テストケースの並列実行
    # TODO: スコア集計 