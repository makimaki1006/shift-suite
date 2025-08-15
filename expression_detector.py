# -*- coding: utf-8 -*-
"""
表現品質自動検出スクリプト
誇張表現・不適切表現の自動検出と評価スコア算出
"""

import sys
sys.path.append('.')

import re
import json
import argparse
from pathlib import Path
from datetime import datetime
import logging

class ExpressionDetector:
    """表現品質検出エンジン"""
    
    def __init__(self, config_file="quality_management_process_design.json"):
        """検出ルール設定の初期化"""
        # ログ設定
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        self.logger = logging.getLogger(__name__)
        
        self.config = self._load_config(config_file)
        self.detection_patterns = self._compile_patterns()
        self.severity_weights = {"高": 3, "中": 2, "低": 1}
    
    def _load_config(self, config_file):
        """設定ファイル読み込み"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"設定ファイルが見つかりません: {config_file}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"設定ファイルの解析エラー: {e}")
            return None
    
    def _compile_patterns(self):
        """正規表現パターンのコンパイル"""
        if not self.config:
            return {}
        
        patterns = {}
        checklist = self.config.get("expression_checklist", {})
        check_categories = checklist.get("check_categories", {})
        
        for category, details in check_categories.items():
            category_patterns = []
            severity = details.get("severity", "低")
            
            # 各チェックポイントのパターンをコンパイル
            for check_point in details.get("check_points", []):
                regex_pattern = check_point.get("regex_pattern", "")
                if regex_pattern:
                    try:
                        compiled_pattern = re.compile(regex_pattern, re.IGNORECASE)
                        category_patterns.append({
                            "pattern": compiled_pattern,
                            "description": check_point.get("item", ""),
                            "correct_example": check_point.get("correct_example", ""),
                            "original_regex": regex_pattern
                        })
                    except re.error as e:
                        self.logger.warning(f"正規表現コンパイルエラー: {regex_pattern} - {e}")
            
            patterns[category] = {
                "name": details.get("name", category),
                "severity": severity,
                "patterns": category_patterns
            }
        
        self.logger.info(f"検出パターン読み込み完了: {len(patterns)}カテゴリ")
        return patterns
    
    def detect_issues_in_text(self, text, file_path=""):
        """テキスト内の問題表現検出"""
        if not self.detection_patterns:
            self.logger.error("検出パターンが未設定です")
            return {}
        
        detection_results = {
            "file_path": file_path,
            "analysis_timestamp": datetime.now().isoformat(),
            "total_issues": 0,
            "severity_summary": {"高": 0, "中": 0, "低": 0},
            "categories": {},
            "detailed_findings": []
        }
        
        # カテゴリ別検出実行
        for category, category_info in self.detection_patterns.items():
            category_issues = []
            severity = category_info["severity"]
            
            for pattern_info in category_info["patterns"]:
                pattern = pattern_info["pattern"]
                matches = pattern.finditer(text)
                
                for match in matches:
                    issue = {
                        "category": category,
                        "severity": severity,
                        "description": pattern_info["description"],
                        "found_text": match.group(),
                        "correct_example": pattern_info["correct_example"],
                        "position": {
                            "start": match.start(),
                            "end": match.end(),
                            "line": self._get_line_number(text, match.start())
                        },
                        "context": self._get_context(text, match.start(), match.end())
                    }
                    category_issues.append(issue)
                    detection_results["detailed_findings"].append(issue)
            
            detection_results["categories"][category] = {
                "name": category_info["name"],
                "severity": severity,
                "issue_count": len(category_issues),
                "issues": category_issues
            }
            
            # 重要度別集計
            detection_results["severity_summary"][severity] += len(category_issues)
            detection_results["total_issues"] += len(category_issues)
        
        return detection_results
    
    def _get_line_number(self, text, position):
        """文字位置から行番号を取得"""
        return text[:position].count('\n') + 1
    
    def _get_context(self, text, start, end, context_length=50):
        """マッチした表現の前後コンテキストを取得"""
        context_start = max(0, start - context_length)
        context_end = min(len(text), end + context_length)
        
        context = text[context_start:context_end]
        # マッチ部分をハイライト
        match_relative_start = start - context_start
        match_relative_end = end - context_start
        
        return {
            "text": context,
            "highlight_start": match_relative_start,
            "highlight_end": match_relative_end
        }
    
    def calculate_quality_score(self, detection_results):
        """品質スコア算出"""
        if not self.config:
            return {"error": "設定未読み込み"}
        
        # 客観性評価基準を取得
        objectivity_criteria = self.config.get("objectivity_criteria", {})
        evaluation_dimensions = objectivity_criteria.get("evaluation_dimensions", {})
        
        # 表現適切性の評価（重み25%）
        expression_score = self._calculate_expression_score(detection_results)
        
        # 基本スコア（他の次元は簡易評価）
        base_scores = {
            "factual_accuracy": 3.0,  # デフォルト良好
            "expression_appropriateness": expression_score,
            "scope_clarity": 3.0,     # デフォルト良好
            "verification_coverage": 2.5,  # デフォルト許容
            "consistency": 3.0        # デフォルト良好
        }
        
        # 重み付き総合スコア計算
        weights = {
            "factual_accuracy": 0.35,
            "expression_appropriateness": 0.25,
            "scope_clarity": 0.20,
            "verification_coverage": 0.15,
            "consistency": 0.05
        }
        
        weighted_score = sum(base_scores[dim] * weights[dim] for dim in weights.keys())
        
        # グレード判定
        grade_thresholds = objectivity_criteria.get("grade_thresholds", {
            "A": 3.5, "B+": 3.0, "B": 2.5, "B-": 2.0, "C+": 1.5, "C": 1.0
        })
        
        grade = "C"
        for grade_name, threshold in sorted(grade_thresholds.items(), key=lambda x: x[1], reverse=True):
            if weighted_score >= threshold:
                grade = grade_name
                break
        
        return {
            "weighted_score": round(weighted_score, 3),
            "grade": grade,
            "dimension_scores": base_scores,
            "weights": weights,
            "pass_fail": "PASS" if weighted_score >= 2.5 else "FAIL",
            "improvement_needed": weighted_score < 3.0
        }
    
    def _calculate_expression_score(self, detection_results):
        """表現適切性スコアの計算"""
        total_issues = detection_results["total_issues"]
        high_issues = detection_results["severity_summary"]["高"]
        medium_issues = detection_results["severity_summary"]["中"]
        low_issues = detection_results["severity_summary"]["低"]
        
        # 重要度別ペナルティ
        penalty_score = (high_issues * 1.0) + (medium_issues * 0.5) + (low_issues * 0.2)
        
        # スコア算出（4点満点から減点）
        if penalty_score == 0:
            return 4.0  # 優秀
        elif penalty_score <= 1.0:
            return 3.0  # 良好
        elif penalty_score <= 2.0:
            return 2.0  # 許容
        else:
            return 1.0  # 不良
    
    def detect_file(self, file_path):
        """ファイルの表現品質検出"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='cp932') as f:
                    content = f.read()
            except Exception as e:
                self.logger.error(f"ファイル読み込みエラー: {file_path} - {e}")
                return None
        except Exception as e:
            self.logger.error(f"ファイル読み込みエラー: {file_path} - {e}")
            return None
        
        detection_results = self.detect_issues_in_text(content, str(file_path))
        quality_score = self.calculate_quality_score(detection_results)
        
        return {
            "detection_results": detection_results,
            "quality_assessment": quality_score,
            "recommendations": self._generate_recommendations(detection_results)
        }
    
    def _generate_recommendations(self, detection_results):
        """改善推奨事項生成"""
        recommendations = []
        
        for category, category_info in detection_results["categories"].items():
            if category_info["issue_count"] > 0:
                severity = category_info["severity"]
                count = category_info["issue_count"]
                
                if severity == "高":
                    priority = "緊急"
                    action = "即座修正"
                elif severity == "中":
                    priority = "高"
                    action = "優先修正"
                else:
                    priority = "中"
                    action = "計画修正"
                
                recommendations.append({
                    "priority": priority,
                    "category": category_info["name"],
                    "issue_count": count,
                    "action": action,
                    "description": f"{category_info['name']}の{count}件の問題を{action}してください"
                })
        
        # 優先度順でソート
        priority_order = {"緊急": 1, "高": 2, "中": 3, "低": 4}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 5))
        
        return recommendations
    
    def generate_report(self, analysis_result, output_format="json"):
        """検出レポート生成"""
        if not analysis_result:
            return "分析結果がありません"
        
        if output_format == "json":
            return json.dumps(analysis_result, indent=2, ensure_ascii=False, default=str)
        
        elif output_format == "text":
            return self._generate_text_report(analysis_result)
        
        else:
            return "サポートされていない出力形式です"
    
    def _generate_text_report(self, analysis_result):
        """テキストレポート生成"""
        detection = analysis_result["detection_results"]
        quality = analysis_result["quality_assessment"]
        recommendations = analysis_result["recommendations"]
        
        report_lines = [
            "=== 表現品質検出レポート ===",
            f"ファイル: {detection['file_path']}",
            f"分析日時: {detection['analysis_timestamp']}",
            "",
            "【検出サマリー】",
            f"総問題数: {detection['total_issues']}件",
            f"高重要度: {detection['severity_summary']['高']}件",
            f"中重要度: {detection['severity_summary']['中']}件",
            f"低重要度: {detection['severity_summary']['低']}件",
            "",
            "【品質評価】",
            f"総合スコア: {quality['weighted_score']}/4.0",
            f"グレード: {quality['grade']}",
            f"判定: {quality['pass_fail']}",
            ""
        ]
        
        if detection['total_issues'] > 0:
            report_lines.extend([
                "【検出詳細】",
                ""
            ])
            
            for finding in detection['detailed_findings'][:10]:  # 上位10件まで
                report_lines.extend([
                    f"[{finding['severity']}] {finding['description']}",
                    f"  発見箇所: \"{finding['found_text']}\" (行{finding['position']['line']})",
                    f"  推奨表現: \"{finding['correct_example']}\"",
                    ""
                ])
        
        if recommendations:
            report_lines.extend([
                "【改善推奨】",
                ""
            ])
            
            for rec in recommendations:
                report_lines.append(f"[{rec['priority']}] {rec['description']}")
        
        return "\n".join(report_lines)

def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description='表現品質自動検出ツール')
    parser.add_argument('--file', '-f', required=True, help='分析対象ファイル')
    parser.add_argument('--output', '-o', help='出力ファイル名')
    parser.add_argument('--format', choices=['json', 'text'], default='text', help='出力形式')
    parser.add_argument('--config', help='設定ファイル', default='quality_management_process_design.json')
    
    args = parser.parse_args()
    
    # 検出器初期化
    detector = ExpressionDetector(args.config)
    
    # ファイル分析実行
    result = detector.detect_file(args.file)
    
    if not result:
        print("分析に失敗しました")
        return 1
    
    # レポート生成
    report = detector.generate_report(result, args.format)
    
    # 出力
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"レポート出力: {args.output}")
    else:
        print(report)
    
    # 終了ステータス
    quality_score = result["quality_assessment"]["weighted_score"]
    return 0 if quality_score >= 2.5 else 1

if __name__ == '__main__':
    sys.exit(main())