# AtCoder CLI ツール 追加機能アイデア

## 1. テストケース生成機能

### 概要
問題ごとのジェネレータファイルによるテストケース自動生成

### 詳細
- 問題ディレクトリに`a_gen.py`形式でジェネレータを配置
  ```python
  # abc300/a_gen.py
  def generate():
      # 入力生成
      n = random.randint(1, 100)
      a = [random.randint(1, 1000) for _ in range(n)]
      
      # 入力形式
      input_data = f"{n}\\n" + " ".join(map(str, a))
      
      # 解答計算
      ans = solve(n, a)  # 解答を計算
      
      return {
          "input": input_data,
          "output": str(ans)
      }

  # テストケース数を指定して生成
  TESTCASE_NUM = 10
  ```
- 生成されたテストケースは`test/custom/`ディレクトリに保存
- 通常のテストケースと同様に実行可能

### 使用例
```
python3 manage.py <contest_id> t <problem_id> --custom  # カスタムテストケースでテスト
```

## 2. ログ管理機能

### 概要
提出履歴、テスト実行結果、パフォーマンス情報の管理

### 詳細
- 提出情報の記録
  - 提出日時
  - 結果（AC/WA/TLE等）
  - 実行時間・メモリ使用量
  - 使用言語
  - コードのバージョン

- テスト実行ログ
  - テストケースごとの結果
  - 失敗したケースの入出力
  - 実行時間の統計

- パフォーマンス分析
  - 問題種別ごとの正答率
  - 言語ごとの実行時間比較
  - 改善点の提案

### 使用例
```
python3 manage.py log list  # ログ一覧
python3 manage.py log show <submission_id>  # 詳細表示
python3 manage.py log stats  # 統計情報
```

## 実装優先度
1. ログ管理機能
2. テストケース生成機能 