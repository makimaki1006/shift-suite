#!/usr/bin/env python3
"""
技術的負債の定量評価
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Tuple
import subprocess

class TechnicalDebtAnalyzer:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.debt_scores = {}
    
    def analyze_code_complexity(self, file_path: Path) -> Dict[str, float]:
        """コード複雑度分析"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            complexity_metrics = {
                'cyclomatic_complexity': self._calculate_cyclomatic_complexity(tree),
                'nesting_depth': self._calculate_nesting_depth(tree),
                'function_count': len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
                'class_count': len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
                'line_count': len(content.split('\n')),
            }
            
            return complexity_metrics
        except Exception as e:
            return {'error': str(e)}
    
    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """循環的複雑度計算"""
        complexity = 1  # ベース
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
        
        return complexity
    
    def _calculate_nesting_depth(self, tree: ast.AST) -> int:
        """ネストの深さ計算"""
        max_depth = 0
        
        def traverse(node, depth):
            nonlocal max_depth
            max_depth = max(max_depth, depth)
            
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.With)):
                depth += 1
            
            for child in ast.iter_child_nodes(node):
                traverse(child, depth)
        
        traverse(tree, 0)
        return max_depth
    
    def calculate_debt_score(self, file_path: Path) -> float:
        """技術的負債スコア計算 (0-100, 100が最悪)"""
        metrics = self.analyze_code_complexity(file_path)
        
        if 'error' in metrics:
            return 0.0
        
        # 重み付けスコア計算
        score = 0.0
        
        # ファイルサイズペナルティ
        line_count = metrics['line_count']
        if line_count > 5000:
            score += 40  # 巨大ファイル
        elif line_count > 2000:
            score += 25  # 大きなファイル
        elif line_count > 1000:
            score += 10  # やや大きなファイル
        
        # 複雑度ペナルティ
        complexity = metrics['cyclomatic_complexity']
        if complexity > 50:
            score += 30
        elif complexity > 25:
            score += 15
        elif complexity > 10:
            score += 5
        
        # ネスト深度ペナルティ
        nesting = metrics['nesting_depth']
        if nesting > 10:
            score += 20
        elif nesting > 6:
            score += 10
        elif nesting > 4:
            score += 5
        
        # 関数数ペナルティ（モノリシック構造）
        func_count = metrics['function_count']
        if func_count > 200:
            score += 15
        elif func_count > 100:
            score += 8
        elif func_count > 50:
            score += 3
        
        return min(score, 100.0)
    
    def analyze_project(self) -> Dict[str, float]:
        """プロジェクト全体の分析"""
        results = {}
        
        for py_file in self.root_path.rglob('*.py'):
            if any(exclude in str(py_file) for exclude in ['.git', '__pycache__', 'venv', 'test_']):
                continue
            
            debt_score = self.calculate_debt_score(py_file)
            relative_path = py_file.relative_to(self.root_path)
            results[str(relative_path)] = debt_score
        
        return results
    
    def generate_priority_report(self) -> List[Tuple[str, float, str]]:
        """優先度付きレポート生成"""
        debt_scores = self.analyze_project()
        
        # スコア順でソート
        sorted_files = sorted(debt_scores.items(), key=lambda x: x[1], reverse=True)
        
        priority_report = []
        for file_path, score in sorted_files[:20]:  # Top 20
            if score > 50:
                priority = "[緊急]"
            elif score > 30:
                priority = "[重要]"  
            elif score > 15:
                priority = "[通常]"
            else:
                priority = "[低]"
            
            priority_report.append((file_path, score, priority))
        
        return priority_report

def main():
    analyzer = TechnicalDebtAnalyzer("C:/ShiftAnalysis")
    
    print("=== 技術的負債分析レポート ===")
    print()
    
    priority_report = analyzer.generate_priority_report()
    
    print("優先度順 Top 20:")
    print("-" * 80)
    print(f"{'ファイル名':<50} {'スコア':<10} {'優先度'}")
    print("-" * 80)
    
    for file_path, score, priority in priority_report:
        print(f"{file_path:<50} {score:<10.1f} {priority}")
    
    print()
    print("=== 推奨改善順序 ===")
    
    high_priority = [item for item in priority_report if item[1] > 50]
    medium_priority = [item for item in priority_report if 30 <= item[1] <= 50]
    low_priority = [item for item in priority_report if item[1] < 30]
    
    print(f"[緊急対応] ({len(high_priority)}ファイル):")
    for file_path, score, _ in high_priority[:5]:
        print(f"  - {file_path} (スコア: {score:.1f})")
    
    print(f"\n[重要対応] ({len(medium_priority)}ファイル):")
    for file_path, score, _ in medium_priority[:5]:
        print(f"  - {file_path} (スコア: {score:.1f})")

if __name__ == "__main__":
    main()