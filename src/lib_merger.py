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
        lib_code = resolve_imports(lib_code, processed_files)
        
        # 必要な関数のみを抽出
        if imports == '*':
            return lib_code
        
        # 指定された関数のみを抽出
        funcs = [f.strip() for f in imports.split(',')]
        extracted_code = extract_functions(lib_code, funcs)
        
        return extracted_code

    # import文の置換
    merged_code = re.sub(pattern, replace_import, source_code)
    
    return merged_code

def extract_functions(code: str, function_names: list) -> str:
    """
    指定された関数のコードを抽出
    """
    result = []
    current_func = None
    func_lines = []
    
    for line in code.split('\n'):
        # 関数定義の開始を検出
        if line.startswith('def '):
            if current_func:
                # 前の関数が対象だった場合は保存
                if current_func in function_names:
                    result.extend(func_lines)
            # 新しい関数の開始
            current_func = line[4:line.find('(')]
            func_lines = [line]
        elif current_func:
            # 関数の続き
            func_lines.append(line)
        elif not line.strip().startswith(('import ', 'from ')):
            # グローバルスコープのコード（import文以外）
            result.append(line)
    
    # 最後の関数の処理
    if current_func and current_func in function_names:
        result.extend(func_lines)
    
    return '\n'.join(result) 