# AtCoder CLI ツール要件定義書

## 1. 概要

AtCoderのコンテスト問題の管理、テスト実行、提出を効率化するCLIツール

## 2. 基本機能要件

### 2.1 通常問題への対応
online-judge-toolsを利用した以下の機能を提供:
```
python3 manage.py <contest_id> <command> <problem_id> [options]
```
- o: 問題ファイルの作成とテストケースの取得
- t: テストケース実行（並列実行、タイムアウト5秒）
  - サンプルケースの実行
  - カスタムケースの自動生成と実行（`a_gen.py`が存在する場合）
    - `custom-1.in`/`custom-1.out`形式で保存
- s: AtCoderへの提出
  - ライブラリの自動マージ（lib/以下のimport文を検知）
  - 依存関係の解決とコード最適化

### 2.2 AHC特有の機能
```
python3 manage.py <contest_id> ahctest <number_of_cases>
```
- ツール類の自動セットアップ（本体、webvisualizer）
- テストケース生成と実行（seed値、in/out/other）
- Git/Cargoによるコード・ビジュアライザー管理

## 3. 実行環境

- Docker環境（CPU 2コア、メモリ1024MB）
  - Python (5082): python:3.10-slim
  - PyPy (5078, デフォルト): pypy:3.10-slim
  - Rust (5054): rust:1.70
  - 言語切替: `--rust`または`-rs`オプション
- 外部ツール: online-judge-tools, Cargo, Git

## 4. プロジェクト構成
```
ojt/
├── src/      # ツール本体
├── contest/  # 問題ファイル
│   ├── template/
│   ├── lib/     # 自動マージ対象のライブラリ
│   └── abc300/  # コンテストディレクトリ例
│       ├── a.py
│       ├── a_gen.py  # テストケースジェネレータ
│       └── test/
│           ├── sample-1.in   # サンプルケース
│           ├── sample-1.out
│           ├── custom-1.in   # 生成したテストケース
│           └── custom-1.out
└── manage.py
```

## 5. 非機能要件
- エラー処理と認証管理
- 言語・ツールの拡張性 