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
    
    # コンテストディレクトリの作成
    contest_dir.mkdir(parents=True, exist_ok=True)
    
    # ツールのダウンロードとセットアップ
    if not tools_dir.exists():
        # Gitの初期化
        if not (contest_dir / ".git").exists():
            subprocess.run("git init", shell=True, cwd=contest_dir)
            subprocess.run("git branch -m main", shell=True, cwd=contest_dir)
        
        # ツールのダウンロード
        url = f"https://atcoder.jp/contests/{contest_id}"
        subprocess.run(f"cargo new tools", shell=True, cwd=contest_dir)
    
    # 必要なディレクトリの作成
    for dir_name in ["in", "out", "other"]:
        (tools_dir / dir_name).mkdir(parents=True, exist_ok=True)
        
    # Webvisualizerのセットアップ
    webvis_dir = contest_dir / "webvis"
    if not webvis_dir.exists():
        webvis_dir.mkdir(parents=True)

def run_test_cases(contest_id: str, source_file: Path):
    """
    AHCのテストケース実行
    
    Args:
        contest_id (str): コンテストID
        source_file (Path): 実行するソースファイル
        
    Returns:
        list: 各テストケースのスコア
    """
    contest_dir = Path(config.CONTEST_DIR) / contest_id
    tools_dir = contest_dir / "tools"
    in_dir = tools_dir / "in"
    out_dir = tools_dir / "out"
    
    # 入出力ディレクトリの作成
    for dir_name in ["in", "out", "other"]:
        (tools_dir / dir_name).mkdir(parents=True, exist_ok=True)
    
    # 入力ファイルの一覧を取得
    input_files = sorted(in_dir.glob("*.txt"))
    n_cases = len(input_files)
    
    if n_cases == 0:
        return []
    
    # シード値の設定
    seeds_file = tools_dir / "seeds.txt"
    seeds_file.write_text("\n".join(str(i) for i in range(n_cases)))
    
    # テストケースの実行
    scores = []
    for i, input_file in enumerate(input_files):
        output_file = out_dir / input_file.name
        
        # プログラムを実行
        with open(input_file) as fin, open(output_file, "w") as fout:
            subprocess.run(
                ["python3", str(source_file)],
                stdin=fin,
                stdout=fout,
                check=True
            )
        
        # TODO: スコアの計算
        scores.append(100)  # ダミースコア
    
    return scores 