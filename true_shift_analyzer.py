#!/usr/bin/env python3
"""
真のシフト分析システム - シフト作成者の意図をあぶりだす
目的逸脱を反省し、本来の目的に取り組む
"""

import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import subprocess

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

class TrueShiftAnalyzer:
    """真のシフト分析器 - 作成者の意図を発見"""
    
    def __init__(self):
        self.analyzer_name = "真のシフト分析システム"
        self.version = "1.0.0"
        self.has_pandas = self._check_pandas()
        self.has_openpyxl = self._check_openpyxl()
    
    def _check_pandas(self) -> bool:
        """pandasの利用可能性チェック"""
        try:
            import pandas
            return True
        except ImportError:
            return False
    
    def _check_openpyxl(self) -> bool:
        """openpyxlの利用可能性チェック"""
        try:
            import openpyxl
            return True
        except ImportError:
            return False
    
    def install_dependencies(self) -> bool:
        """必要な依存関係のインストール試行"""
        print("=== 依存関係のインストール ===")
        
        if not self.has_pandas:
            print("pandasがありません。インストールを試みます...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas"])
                self.has_pandas = True
                print("✓ pandasのインストール成功")
            except Exception as e:
                print(f"✗ pandasのインストール失敗: {e}")
                
        if not self.has_openpyxl:
            print("openpyxlがありません。インストールを試みます...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
                self.has_openpyxl = True
                print("✓ openpyxlのインストール成功")
            except Exception as e:
                print(f"✗ openpyxlのインストール失敗: {e}")
        
        return self.has_pandas or self.has_openpyxl
    
    def read_excel_basic(self, file_path: str) -> Optional[List[List[Any]]]:
        """基本的なExcel読み込み（openpyxl使用）"""
        if not self.has_openpyxl:
            return None
            
        try:
            import openpyxl
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            ws = wb.active
            
            data = []
            for row in ws.iter_rows(values_only=True):
                data.append(list(row))
            
            wb.close()
            print(f"✓ openpyxlで{len(data)}行のデータを読み込みました")
            return data
            
        except Exception as e:
            print(f"✗ openpyxl読み込みエラー: {e}")
            return None
    
    def read_excel_pandas(self, file_path: str) -> Optional[Any]:
        """pandas使用のExcel読み込み"""
        if not self.has_pandas:
            return None
            
        try:
            import pandas as pd
            # 全シートを読み込む
            all_sheets = pd.read_excel(file_path, sheet_name=None)
            print(f"✓ pandasで{len(all_sheets)}個のシートを読み込みました")
            
            # 最初のシートをメインとして扱う
            first_sheet_name = list(all_sheets.keys())[0]
            df = all_sheets[first_sheet_name]
            
            print(f"   メインシート: {first_sheet_name}")
            print(f"   データサイズ: {len(df)}行 × {len(df.columns)}列")
            
            return df
            
        except Exception as e:
            print(f"✗ pandas読み込みエラー: {e}")
            return None
    
    def analyze_shift_patterns(self, data: Any) -> Dict[str, Any]:
        """シフトパターンの分析"""
        print("\n=== シフトパターン分析 ===")
        
        patterns = {
            "staff_patterns": {},  # スタッフ別パターン
            "time_patterns": {},   # 時間帯別パターン
            "combination_patterns": {},  # スタッフ組み合わせ
            "implicit_rules": []   # 発見された暗黙ルール
        }
        
        # データ形式に応じた分析
        if isinstance(data, list):  # openpyxlデータ
            self._analyze_list_data(data, patterns)
        else:  # pandasデータ
            self._analyze_pandas_data(data, patterns)
        
        return patterns
    
    def _analyze_list_data(self, data: List[List[Any]], patterns: Dict) -> None:
        """リスト形式データの分析"""
        if len(data) < 2:
            print("データが少なすぎます")
            return
        
        # ヘッダー行の特定
        header_row = None
        for i, row in enumerate(data[:5]):  # 最初の5行をチェック
            if row and any(cell for cell in row if cell):
                # 日付や曜日を含む可能性のあるヘッダーを探す
                row_str = str(row)
                if any(keyword in row_str for keyword in ['月', '火', '水', '木', '金', '土', '日', '氏名', '名前', 'スタッフ']):
                    header_row = i
                    break
        
        if header_row is None:
            print("ヘッダー行が特定できませんでした")
            return
        
        print(f"ヘッダー行: {header_row + 1}行目")
        headers = data[header_row]
        
        # スタッフ名の列を特定
        staff_col = None
        for i, header in enumerate(headers):
            if header and any(keyword in str(header) for keyword in ['氏名', '名前', 'スタッフ', '職員']):
                staff_col = i
                break
        
        if staff_col is None:
            print("スタッフ列が特定できませんでした")
            # 最初の列をスタッフ列と仮定
            staff_col = 0
        
        print(f"スタッフ列: {staff_col + 1}列目")
        
        # シフトデータの分析
        for row_idx in range(header_row + 1, len(data)):
            row = data[row_idx]
            if not row or not row[staff_col]:
                continue
            
            staff_name = str(row[staff_col])
            if staff_name not in patterns["staff_patterns"]:
                patterns["staff_patterns"][staff_name] = {
                    "shifts": [],
                    "days_worked": 0,
                    "shift_types": {}
                }
            
            # 各日のシフトを分析
            for col_idx in range(staff_col + 1, len(row)):
                if col_idx < len(headers) and row[col_idx]:
                    date_header = headers[col_idx]
                    shift_code = str(row[col_idx])
                    
                    patterns["staff_patterns"][staff_name]["shifts"].append({
                        "date": str(date_header),
                        "shift": shift_code
                    })
                    
                    if shift_code not in patterns["staff_patterns"][staff_name]["shift_types"]:
                        patterns["staff_patterns"][staff_name]["shift_types"][shift_code] = 0
                    patterns["staff_patterns"][staff_name]["shift_types"][shift_code] += 1
                    patterns["staff_patterns"][staff_name]["days_worked"] += 1
        
        # 暗黙ルールの発見
        self._discover_implicit_rules(patterns)
    
    def _analyze_pandas_data(self, df: Any, patterns: Dict) -> None:
        """pandasデータフレームの分析"""
        import pandas as pd
        
        print(f"データフレーム形状: {df.shape}")
        print(f"列名: {list(df.columns)[:10]}...")  # 最初の10列
        
        # スタッフ列の特定
        staff_columns = [col for col in df.columns if any(keyword in str(col) for keyword in ['氏名', '名前', 'スタッフ', '職員'])]
        
        if not staff_columns:
            # 最初の列をスタッフ列と仮定
            staff_col = df.columns[0]
        else:
            staff_col = staff_columns[0]
        
        print(f"スタッフ列として識別: {staff_col}")
        
        # 各スタッフのシフトパターンを分析
        for _, row in df.iterrows():
            staff_name = str(row[staff_col])
            if pd.isna(staff_name) or staff_name == 'nan':
                continue
            
            if staff_name not in patterns["staff_patterns"]:
                patterns["staff_patterns"][staff_name] = {
                    "shifts": [],
                    "days_worked": 0,
                    "shift_types": {},
                    "consecutive_days": []
                }
            
            # 各列（日付）のシフトを分析
            for col in df.columns:
                if col == staff_col:
                    continue
                
                shift_value = row[col]
                if pd.notna(shift_value) and shift_value:
                    patterns["staff_patterns"][staff_name]["shifts"].append({
                        "date": str(col),
                        "shift": str(shift_value)
                    })
                    
                    shift_code = str(shift_value)
                    if shift_code not in patterns["staff_patterns"][staff_name]["shift_types"]:
                        patterns["staff_patterns"][staff_name]["shift_types"][shift_code] = 0
                    patterns["staff_patterns"][staff_name]["shift_types"][shift_code] += 1
                    patterns["staff_patterns"][staff_name]["days_worked"] += 1
        
        # 暗黙ルールの発見
        self._discover_implicit_rules(patterns)
    
    def _discover_implicit_rules(self, patterns: Dict) -> None:
        """暗黙のルールを発見"""
        print("\n暗黙ルールの発見中...")
        
        # 1. 特定シフトへの偏り
        for staff, data in patterns["staff_patterns"].items():
            if data["shift_types"]:
                total_shifts = sum(data["shift_types"].values())
                for shift_type, count in data["shift_types"].items():
                    ratio = count / total_shifts
                    if ratio > 0.7:  # 70%以上
                        rule = f"{staff}は{shift_type}シフトに{ratio:.0%}集中（暗黙の専門性？）"
                        patterns["implicit_rules"].append({
                            "type": "shift_specialization",
                            "staff": staff,
                            "shift": shift_type,
                            "ratio": ratio,
                            "rule": rule
                        })
        
        # 2. 勤務日数の偏り
        all_days_worked = [data["days_worked"] for data in patterns["staff_patterns"].values()]
        if all_days_worked:
            avg_days = sum(all_days_worked) / len(all_days_worked)
            for staff, data in patterns["staff_patterns"].items():
                if data["days_worked"] > avg_days * 1.3:
                    rule = f"{staff}は平均より多く勤務（{data['days_worked']}日 vs 平均{avg_days:.1f}日）"
                    patterns["implicit_rules"].append({
                        "type": "workload_imbalance",
                        "staff": staff,
                        "days": data["days_worked"],
                        "average": avg_days,
                        "rule": rule
                    })
                elif data["days_worked"] < avg_days * 0.7:
                    rule = f"{staff}は平均より少なく勤務（{data['days_worked']}日 vs 平均{avg_days:.1f}日）"
                    patterns["implicit_rules"].append({
                        "type": "workload_imbalance", 
                        "staff": staff,
                        "days": data["days_worked"],
                        "average": avg_days,
                        "rule": rule
                    })
        
        print(f"発見された暗黙ルール: {len(patterns['implicit_rules'])}個")
    
    def find_creator_intentions(self, patterns: Dict) -> List[Dict[str, Any]]:
        """シフト作成者の意図を推測"""
        print("\n=== シフト作成者の意図推測 ===")
        
        intentions = []
        
        # 暗黙ルールから意図を推測
        for rule in patterns.get("implicit_rules", []):
            if rule["type"] == "shift_specialization":
                intentions.append({
                    "observation": rule["rule"],
                    "possible_intention": f"{rule['staff']}は{rule['shift']}シフトのスペシャリストとして配置",
                    "confidence": rule["ratio"],
                    "evidence": f"{rule['shift']}シフト率{rule['ratio']:.0%}"
                })
            elif rule["type"] == "workload_imbalance":
                if rule["days"] > rule["average"]:
                    intentions.append({
                        "observation": rule["rule"],
                        "possible_intention": f"{rule['staff']}は信頼できる中核スタッフ",
                        "confidence": 0.7,
                        "evidence": f"平均より{(rule['days']/rule['average']-1)*100:.0f}%多い勤務"
                    })
                else:
                    intentions.append({
                        "observation": rule["rule"],
                        "possible_intention": f"{rule['staff']}は補助的役割または勤務制限あり",
                        "confidence": 0.6,
                        "evidence": f"平均より{(1-rule['days']/rule['average'])*100:.0f}%少ない勤務"
                    })
        
        print(f"推測された意図: {len(intentions)}個")
        
        return intentions
    
    def generate_truth_report(self, file_path: str, patterns: Dict, intentions: List[Dict]) -> Dict[str, Any]:
        """真実のレポート生成"""
        report = {
            "analysis_metadata": {
                "timestamp": datetime.now().isoformat(),
                "file": file_path,
                "analyzer": self.analyzer_name,
                "version": self.version
            },
            "discovered_patterns": {
                "staff_count": len(patterns.get("staff_patterns", {})),
                "implicit_rules": len(patterns.get("implicit_rules", [])),
                "creator_intentions": len(intentions)
            },
            "key_findings": {
                "implicit_rules": patterns.get("implicit_rules", [])[:5],  # 上位5つ
                "creator_intentions": intentions[:5]  # 上位5つ
            },
            "full_analysis": {
                "patterns": patterns,
                "intentions": intentions
            }
        }
        
        return report

def main():
    """メイン実行関数"""
    print("=" * 80)
    print("真のシフト分析システム - シフト作成者の意図をあぶりだす")
    print("=" * 80)
    
    analyzer = TrueShiftAnalyzer()
    
    # 依存関係チェック
    print(f"pandas利用可能: {analyzer.has_pandas}")
    print(f"openpyxl利用可能: {analyzer.has_openpyxl}")
    
    if not analyzer.has_pandas and not analyzer.has_openpyxl:
        print("\nExcel読み込みライブラリが不足しています。")
        if not analyzer.install_dependencies():
            print("必要なライブラリをインストールできませんでした。")
            print("手動でインストールしてください: pip install pandas openpyxl")
            return 1
    
    # 分析対象ファイルの選択
    excel_files = list(Path('.').glob('*.xlsx'))
    if not excel_files:
        print("\n分析対象のExcelファイルが見つかりません")
        return 1
    
    print(f"\n見つかったExcelファイル: {len(excel_files)}個")
    
    # デイ関連ファイルを優先
    target_file = None
    for f in excel_files:
        if 'デイ' in f.name and 'テスト' in f.name:
            target_file = f
            break
    
    if not target_file:
        target_file = excel_files[0]
    
    print(f"\n分析対象: {target_file}")
    
    # Excel読み込み
    data = None
    if analyzer.has_pandas:
        data = analyzer.read_excel_pandas(str(target_file))
    
    if data is None and analyzer.has_openpyxl:
        data = analyzer.read_excel_basic(str(target_file))
    
    if data is None:
        print("\nExcelファイルを読み込めませんでした")
        return 1
    
    # シフトパターン分析
    patterns = analyzer.analyze_shift_patterns(data)
    
    # 作成者の意図推測
    intentions = analyzer.find_creator_intentions(patterns)
    
    # 結果表示
    print("\n" + "=" * 80)
    print("発見された真実")
    print("=" * 80)
    
    print(f"\n分析されたスタッフ数: {len(patterns.get('staff_patterns', {}))}")
    print(f"発見された暗黙ルール: {len(patterns.get('implicit_rules', []))}")
    print(f"推測された作成者の意図: {len(intentions)}")
    
    if patterns.get("implicit_rules"):
        print("\n【主要な暗黙ルール】")
        for i, rule in enumerate(patterns["implicit_rules"][:5], 1):
            print(f"{i}. {rule['rule']}")
    
    if intentions:
        print("\n【推測される作成者の意図】")
        for i, intent in enumerate(intentions[:5], 1):
            print(f"{i}. {intent['possible_intention']}")
            print(f"   根拠: {intent['evidence']}")
            print(f"   確信度: {intent['confidence']:.0%}")
    
    # レポート生成
    report = analyzer.generate_truth_report(str(target_file), patterns, intentions)
    
    try:
        with open("true_shift_analysis_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n[OK] 真のシフト分析レポート保存完了: true_shift_analysis_report.json")
    except Exception as e:
        print(f"[WARNING] レポート保存エラー: {e}")
    
    print("\n[COMPLETE] 真のシフト分析完了")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())