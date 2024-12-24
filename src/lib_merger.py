"""
ライブラリマージ機能の実装
複数のPythonファイルを1つのファイルにマージします。
"""

import ast
import re
import os
from pathlib import Path
from typing import Set, Dict, List

class ImportResolver:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.processed_files: Set[Path] = set()
        self.imported_contents: Dict[str, str] = {}
        self.workspace_root = self._find_workspace_root(base_dir)

    def _find_workspace_root(self, start_path: Path) -> Path:
        """ワークスペースのルートディレクトリを探索"""
        current = start_path.absolute()
        while current != current.parent:
            if (current / "contest").exists():
                return current
            current = current.parent
        return start_path.absolute()

    def resolve_file(self, file_path: Path) -> str:
        """ファイルの内容を解決し、依存関係を含めた完全なコードを返します"""
        if file_path in self.processed_files:
            return ""
        
        if not file_path.exists():
            raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")

        self.processed_files.add(file_path)
        content = file_path.read_text(encoding='utf-8')
        
        # ASTを使用してimport文を解析
        tree = ast.parse(content)
        imports = self._find_imports(tree)
        
        # 各importを解決
        resolved_contents = []
        for imp in imports:
            import_path = self._resolve_import_path(file_path, imp)
            if import_path and import_path.exists() and import_path not in self.processed_files:
                resolved_contents.append(self.resolve_file(import_path))

        # import文を除去
        cleaned_content = self._remove_imports(content)
        resolved_contents.append(cleaned_content)
        
        return '\n'.join(resolved_contents)

    def _find_imports(self, tree: ast.AST) -> List[str]:
        """ASTからすべてのインポートパスを抽出"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.append(name.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_path = f"{'.' * node.level}{node.module}"
                    imports.append(module_path)
        return imports

    def _resolve_import_path(self, current_file: Path, import_name: str) -> Path:
        """インポートパスを解決"""
        if import_name.startswith('.'):
            # 相対インポート
            return self._resolve_relative_import(current_file, import_name.lstrip('.'))
        else:
            # 絶対インポート
            parts = import_name.split('.')
            if parts[0] == 'contest':
                # contestからの絶対インポート
                return self.workspace_root / Path(*parts).with_suffix('.py')
            else:
                # その他の絶対インポート
                return self.base_dir / Path(import_name.replace('.', '/')).with_suffix('.py')

    def _resolve_relative_import(self, current_file: Path, relative_path: str) -> Path:
        """相対インポートのパスを解決"""
        return (current_file.parent / relative_path.replace('.', '/')).with_suffix('.py')

    def _remove_imports(self, content: str) -> str:
        """import文を除去"""
        lines = content.split('\n')
        cleaned_lines = []
        skip_next = False
        
        for line in lines:
            if skip_next:
                if line.strip().startswith(('import ', 'from ')):
                    continue
                skip_next = False
            
            if line.strip().startswith(('import ', 'from ')):
                skip_next = True
                continue
                
            cleaned_lines.append(line)
            
        return '\n'.join(cleaned_lines)

def merge_code(source_file: Path) -> str:
    """
    メインのマージ関数
    source_file: マージ対象のメインファイルのパス
    """
    resolver = ImportResolver(source_file.parent)
    merged_code = resolver.resolve_file(source_file)
    
    # 重複する空行を削除
    merged_code = re.sub(r'\n\s*\n', '\n\n', merged_code)
    return merged_code.strip() + '\n'

def save_merged_code(source_file: Path, output_file: Path = None) -> None:
    """
    マージしたコードを保存
    source_file: マージ対象のメインファイルのパス
    output_file: 出力先のファイルパス（Noneの場合は.tempファイルを作成）
    """
    if output_file is None:
        output_file = source_file.with_suffix('.temp')
    
    merged_code = merge_code(source_file)
    output_file.write_text(merged_code, encoding='utf-8')
    print(f"マージされたコードを保存しました: {output_file}") 

def merge_libraries(source_file: Path) -> str:
    """
    後方互換性のために残している関数
    merge_code関数を呼び出します
    """
    return merge_code(source_file) 