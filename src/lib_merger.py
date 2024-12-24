"""
ライブラリマージ機能の実装
"""

import re
from pathlib import Path
from . import config

def merge_libraries(source_file: Path) -> str:
    """
    ソースコードとライブラリをマージ
    """
    # ソースコードの読み込み
    source_code = source_file.read_text()
    
    # importの検出と解決
    merged_code = resolve_imports(source_code)
    
    return merged_code

def resolve_imports(source_code: str, processed_files: set = None) -> str:
    """
    import文を解決してコードをマージ
    """
    if processed_files is None:
        processed_files = set()

    # from lib.xxx import yyy の形式を検出
    pattern = r'from\s+lib\.([.\w]+)\s+import\s+([^#\n]+)'
    
    def replace_import(match):
        module_path = match.group(1).replace('.', '/')
        imports = match.group(2).strip()
        
        # ライブラリファイルのパス
        lib_file = Path(config.LIB_DIR) / f"{module_path}.py"
        
        # 既に処理済みのファイルはスキップ
        if lib_file in processed_files:
            return ""
        
        if not lib_file.exists():
            print(f"Warning: Library file not found: {lib_file}")
            return match.group(0)
        
        # ライブラリコードの読み込みと再帰的な解決
        processed_files.add(lib_file)
        lib_code = lib_file.read_text()
        resolved_code = resolve_imports(lib_code, processed_files)
        
        # 必要な関数のみを抽出
        if imports == '*':
            return resolved_code
        
        # 指定された関数のみを抽出
        funcs = [f.strip() for f in imports.split(',')]
        extracted_code = extract_functions(resolved_code, funcs)
        
        return extracted_code

    # import文の置換
    merged_code = re.sub(pattern, replace_import, source_code)
    
    return merged_code

def extract_functions(code: str, function_names: list) -> str:
    """
    指定された関数のコードを抽出
    """
    result = []
    
    # 関数定義を探す正規表現
    func_pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
    
    # まず全ての関数定義を見つける
    all_functions = {}
    current_func = None
    current_lines = []
    
    for line in code.split('\n'):
        match = re.match(func_pattern, line)
        if match:
            # 前の関数があれば保存
            if current_func:
                all_functions[current_func] = '\n'.join(current_lines)
            # 新しい関数の開始
            current_func = match.group(1)
            current_lines = [line]
        elif current_func and (line.strip() == '' or line[0] in ' \t'):
            # 関数の続き
            current_lines.append(line)
        elif current_func:
            # 関数の終了
            all_functions[current_func] = '\n'.join(current_lines)
            current_func = None
            current_lines = []
            if not line.strip().startswith(('import ', 'from ')):
                result.append(line)
        elif not line.strip().startswith(('import ', 'from ')):
            # グローバルスコープのコード
            result.append(line)
    
    # 最後の関数があれば保存
    if current_func:
        all_functions[current_func] = '\n'.join(current_lines)
    
    # 関数の依存関係を解決（単純化版）
    processed = set()
    for func_name in function_names:
        if func_name in all_functions and func_name not in processed:
            result.append(all_functions[func_name])
            processed.add(func_name)
            # この関数が使用する他の関数を探す
            func_code = all_functions[func_name]
            for word in re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*\s*\(', func_code):
                called_func = word.strip('(')
                if called_func in all_functions and called_func not in processed:
                    result.append(all_functions[called_func])
                    processed.add(called_func)
    
    return '\n'.join(result) 