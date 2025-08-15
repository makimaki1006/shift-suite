#!/usr/bin/env python3
"""
直接Excel読み込みシステム - 外部ライブラリなしでExcelファイルの内容を取得
本来の目的（シフト作成者の意図発見）のため、技術的困難に立ち向かう
"""

import sys
import json
import logging
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import re

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

class DirectExcelReader:
    """直接Excel読み込み器 - .xlsxファイルをZIPとして解析"""
    
    def __init__(self):
        self.reader_name = "直接Excel読み込み器"
        self.version = "1.0.0"
    
    def read_xlsx_as_zip(self, file_path: str) -> Optional[List[List[Any]]]:
        """xlsxファイルをZIPとして読み込み、シートデータを抽出"""
        print(f"\n=== {file_path} の直接読み込み ===")
        
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                # ファイル構造を確認
                file_list = zip_file.namelist()
                print(f"ZIPファイル内のファイル数: {len(file_list)}")
                
                # シートデータの取得
                sheet_data = None
                shared_strings = None
                
                # 共有文字列の取得
                if 'xl/sharedStrings.xml' in file_list:
                    with zip_file.open('xl/sharedStrings.xml') as f:
                        shared_strings = self._parse_shared_strings(f.read())
                    print(f"共有文字列数: {len(shared_strings)}")
                
                # シート1のデータ取得
                if 'xl/worksheets/sheet1.xml' in file_list:
                    with zip_file.open('xl/worksheets/sheet1.xml') as f:
                        sheet_data = self._parse_sheet_data(f.read(), shared_strings)
                    print(f"シートデータ取得: {len(sheet_data)}行")
                
                return sheet_data
                
        except Exception as e:
            print(f"✗ ZIP読み込みエラー: {e}")
            return None
    
    def _parse_shared_strings(self, xml_data: bytes) -> List[str]:
        """共有文字列XMLを解析"""
        strings = []
        try:
            root = ET.fromstring(xml_data)
            # 名前空間の処理
            ns = {'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            
            for si in root.findall('.//x:si', ns):
                text = ''
                for t in si.findall('.//x:t', ns):
                    if t.text:
                        text += t.text
                strings.append(text)
        except Exception as e:
            print(f"共有文字列解析エラー: {e}")
        
        return strings
    
    def _parse_sheet_data(self, xml_data: bytes, shared_strings: Optional[List[str]]) -> List[List[Any]]:
        """シートデータXMLを解析"""
        rows = {}
        try:
            root = ET.fromstring(xml_data)
            ns = {'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            
            # 各セルを処理
            for cell in root.findall('.//x:c', ns):
                cell_ref = cell.get('r', '')
                cell_type = cell.get('t', '')
                
                # セル位置を解析（例: A1 -> (0, 0)）
                match = re.match(r'([A-Z]+)(\d+)', cell_ref)
                if not match:
                    continue
                
                col_str, row_str = match.groups()
                row_idx = int(row_str) - 1
                col_idx = self._col_letter_to_index(col_str)
                
                # セル値を取得
                value = None
                v_elem = cell.find('x:v', ns)
                if v_elem is not None and v_elem.text:
                    if cell_type == 's' and shared_strings:
                        # 共有文字列参照
                        idx = int(v_elem.text)
                        if 0 <= idx < len(shared_strings):
                            value = shared_strings[idx]
                    else:
                        # 数値またはその他
                        try:
                            value = float(v_elem.text)
                            if value.is_integer():
                                value = int(value)
                        except:
                            value = v_elem.text
                
                # 行データに追加
                if row_idx not in rows:
                    rows[row_idx] = {}
                rows[row_idx][col_idx] = value
            
            # 行データをリストに変換
            if rows:
                max_row = max(rows.keys())
                max_col = max(max(row.keys()) if row else -1 for row in rows.values())
                
                data = []
                for r in range(max_row + 1):
                    row = []
                    for c in range(max_col + 1):
                        value = rows.get(r, {}).get(c, None)
                        row.append(value)
                    data.append(row)
                
                return data
                
        except Exception as e:
            print(f"シートデータ解析エラー: {e}")
        
        return []
    
    def _col_letter_to_index(self, col_str: str) -> int:
        """列文字を数値インデックスに変換（A->0, B->1, ..., Z->25, AA->26）"""
        result = 0
        for char in col_str:
            result = result * 26 + (ord(char) - ord('A') + 1)
        return result - 1

class ShiftPatternAnalyzer:
    """シフトパターン分析器 - 作成者の意図を発見"""
    
    def __init__(self):
        self.analyzer_name = "シフトパターン分析器"
    
    def analyze_raw_data(self, data: List[List[Any]]) -> Dict[str, Any]:
        """生データからシフトパターンを分析"""
        print("\n=== シフトパターン分析 ===")
        
        if not data or len(data) < 2:
            print("分析に十分なデータがありません")
            return {}
        
        # データ構造の理解
        print(f"データサイズ: {len(data)}行 × {len(data[0]) if data[0] else 0}列")
        
        # ヘッダー行の特定
        header_row_idx = self._find_header_row(data)
        if header_row_idx is None:
            print("ヘッダー行を特定できませんでした")
            return {}
        
        print(f"ヘッダー行: {header_row_idx + 1}行目")
        headers = data[header_row_idx]
        
        # スタッフ列の特定
        staff_col_idx = self._find_staff_column(headers)
        print(f"スタッフ列: {staff_col_idx + 1}列目")
        
        # パターン分析
        patterns = {
            "staff_shifts": {},
            "shift_codes": set(),
            "implicit_rules": [],
            "anomalies": []
        }
        
        # 各スタッフのシフトを収集
        for row_idx in range(header_row_idx + 1, len(data)):
            row = data[row_idx]
            if not row or len(row) <= staff_col_idx:
                continue
            
            staff_name = row[staff_col_idx]
            if not staff_name:
                continue
            
            staff_name = str(staff_name).strip()
            if staff_name not in patterns["staff_shifts"]:
                patterns["staff_shifts"][staff_name] = {
                    "shifts": [],
                    "shift_count": {},
                    "consecutive_patterns": [],
                    "weekly_patterns": {}
                }
            
            # 各日のシフトを記録
            for col_idx in range(staff_col_idx + 1, len(row)):
                if col_idx < len(headers) and row[col_idx]:
                    date_header = headers[col_idx] if col_idx < len(headers) else f"Day{col_idx}"
                    shift_code = str(row[col_idx]).strip()
                    
                    if shift_code and shift_code not in ['', 'None', 'nan']:
                        patterns["shift_codes"].add(shift_code)
                        patterns["staff_shifts"][staff_name]["shifts"].append({
                            "date": str(date_header),
                            "shift": shift_code,
                            "col_index": col_idx
                        })
                        
                        # シフトコードカウント
                        if shift_code not in patterns["staff_shifts"][staff_name]["shift_count"]:
                            patterns["staff_shifts"][staff_name]["shift_count"][shift_code] = 0
                        patterns["staff_shifts"][staff_name]["shift_count"][shift_code] += 1
        
        # パターン分析
        self._analyze_patterns(patterns)
        
        return patterns
    
    def _find_header_row(self, data: List[List[Any]]) -> Optional[int]:
        """ヘッダー行を特定"""
        keywords = ['氏名', '名前', 'スタッフ', '職員', 'name', '月', '火', '水', '木', '金', '土', '日']
        
        for i, row in enumerate(data[:10]):  # 最初の10行をチェック
            if row:
                row_str = ' '.join(str(cell) for cell in row if cell)
                if any(keyword in row_str for keyword in keywords):
                    return i
        
        # キーワードが見つからない場合、最初の非空行を使用
        for i, row in enumerate(data[:5]):
            if row and any(cell for cell in row if cell):
                return i
        
        return 0
    
    def _find_staff_column(self, headers: List[Any]) -> int:
        """スタッフ名の列を特定"""
        staff_keywords = ['氏名', '名前', 'スタッフ', '職員', 'name', 'staff']
        
        for i, header in enumerate(headers):
            if header:
                header_str = str(header).lower()
                if any(keyword in header_str for keyword in staff_keywords):
                    return i
        
        # 見つからない場合は最初の列
        return 0
    
    def _analyze_patterns(self, patterns: Dict) -> None:
        """収集したデータからパターンを分析"""
        print(f"\n分析対象スタッフ数: {len(patterns['staff_shifts'])}")
        print(f"発見されたシフトコード: {patterns['shift_codes']}")
        
        # 各スタッフのパターンを分析
        for staff_name, staff_data in patterns["staff_shifts"].items():
            total_shifts = sum(staff_data["shift_count"].values())
            
            if total_shifts == 0:
                continue
            
            # シフト偏向性の分析
            for shift_code, count in staff_data["shift_count"].items():
                ratio = count / total_shifts
                if ratio > 0.6:  # 60%以上
                    rule = {
                        "type": "shift_preference",
                        "staff": staff_name,
                        "shift": shift_code,
                        "ratio": ratio,
                        "description": f"{staff_name}は{shift_code}シフトに{ratio:.0%}集中",
                        "intention": f"{staff_name}を{shift_code}シフト専門として配置している可能性"
                    }
                    patterns["implicit_rules"].append(rule)
            
            # 連続勤務パターンの分析
            shifts = staff_data["shifts"]
            if len(shifts) >= 3:
                for i in range(len(shifts) - 2):
                    if (shifts[i]["col_index"] + 1 == shifts[i+1]["col_index"] and 
                        shifts[i+1]["col_index"] + 1 == shifts[i+2]["col_index"]):
                        # 3連続勤務
                        if shifts[i]["shift"] == shifts[i+1]["shift"] == shifts[i+2]["shift"]:
                            rule = {
                                "type": "consecutive_same_shift",
                                "staff": staff_name,
                                "shift": shifts[i]["shift"],
                                "days": 3,
                                "description": f"{staff_name}は{shifts[i]['shift']}シフトを3日連続",
                                "intention": f"集中的な業務対応または専門性の活用"
                            }
                            if rule not in patterns["implicit_rules"]:
                                patterns["implicit_rules"].append(rule)
        
        # 全体的なパターン分析
        all_shifts_count = {}
        total_staff_shifts = 0
        
        for staff_data in patterns["staff_shifts"].values():
            for shift_code, count in staff_data["shift_count"].items():
                if shift_code not in all_shifts_count:
                    all_shifts_count[shift_code] = 0
                all_shifts_count[shift_code] += count
                total_staff_shifts += count
        
        # シフトコードの使用頻度から組織の特性を推測
        for shift_code, total_count in all_shifts_count.items():
            ratio = total_count / total_staff_shifts if total_staff_shifts > 0 else 0
            if ratio > 0.3:  # 30%以上
                rule = {
                    "type": "organizational_pattern",
                    "shift": shift_code,
                    "ratio": ratio,
                    "description": f"組織全体で{shift_code}シフトが{ratio:.0%}を占める",
                    "intention": f"{shift_code}シフトが主要業務時間帯である可能性"
                }
                patterns["implicit_rules"].append(rule)
        
        print(f"発見された暗黙ルール: {len(patterns['implicit_rules'])}個")
    
    def discover_creator_intentions(self, patterns: Dict) -> List[Dict[str, Any]]:
        """パターンから作成者の意図を推測"""
        print("\n=== シフト作成者の意図推測 ===")
        
        intentions = []
        
        # 暗黙ルールから意図を導出
        for rule in patterns.get("implicit_rules", []):
            if rule["type"] == "shift_preference":
                intentions.append({
                    "finding": rule["description"],
                    "intention": rule["intention"],
                    "evidence": f"{rule['shift']}シフト率{rule['ratio']:.0%}",
                    "confidence": min(0.9, rule['ratio'] + 0.2),
                    "actionable": f"{rule['staff']}の{rule['shift']}シフト専門性を考慮した配置継続を推奨"
                })
            
            elif rule["type"] == "consecutive_same_shift":
                intentions.append({
                    "finding": rule["description"],
                    "intention": "業務の継続性または専門性重視の配置",
                    "evidence": f"{rule['days']}日連続同一シフト",
                    "confidence": 0.7,
                    "actionable": "連続勤務による疲労度を監視しつつ、専門性を活かす"
                })
            
            elif rule["type"] == "organizational_pattern":
                intentions.append({
                    "finding": rule["description"],
                    "intention": f"{rule['shift']}シフトを中心とした運営体制",
                    "evidence": f"全体の{rule['ratio']:.0%}",
                    "confidence": 0.8,
                    "actionable": f"{rule['shift']}シフトの人員を重点的に確保"
                })
        
        # 意図を確信度順にソート
        intentions.sort(key=lambda x: x['confidence'], reverse=True)
        
        print(f"推測された意図: {len(intentions)}個")
        
        return intentions

def main():
    """メイン実行関数"""
    print("=" * 80)
    print("複合Excel分析 - 複数ファイルから作成者の意図を発見")
    print("=" * 80)
    
    # Excelファイルの検索
    excel_files = list(Path('.').glob('*.xlsx'))
    if not excel_files:
        print("\nExcelファイルが見つかりません")
        return 1
    
    print(f"\n見つかったExcelファイル: {len(excel_files)}個")
    for i, f in enumerate(excel_files, 1):
        print(f"  {i}. {f.name} ({f.stat().st_size:,}バイト)")
    
    # 複合分析のため複数ファイルを分析
    all_patterns = {}
    all_intentions = []
    combined_shift_codes = set()
    combined_staff_count = 0
    
    reader = DirectExcelReader()
    analyzer = ShiftPatternAnalyzer()
    
    # 各ファイルを個別に分析
    for target_file in excel_files:
        print(f"\n{'='*60}")
        print(f"分析中: {target_file.name}")
        print(f"{'='*60}")
        
        # Excel読み込み
        data = reader.read_xlsx_as_zip(str(target_file))
        
        if not data:
            print(f"[SKIP] {target_file.name} - データを読み込めませんでした")
            continue
        
        # パターン分析
        patterns = analyzer.analyze_raw_data(data)
        
        if not patterns.get("staff_shifts"):
            print(f"[SKIP] {target_file.name} - スタッフデータが見つかりませんでした")
            continue
        
        # 作成者の意図発見
        intentions = analyzer.discover_creator_intentions(patterns)
        
        # 結果を蓄積
        all_patterns[str(target_file)] = patterns
        all_intentions.extend(intentions)
        combined_shift_codes.update(patterns.get("shift_codes", set()))
        combined_staff_count += len(patterns.get("staff_shifts", {}))
        
        print(f"[OK] {target_file.name} - {len(patterns.get('staff_shifts', {}))}名のスタッフ、{len(patterns.get('implicit_rules', []))}個の暗黙ルール発見")
    
    if not all_patterns:
        print("\n[ERROR] 分析可能なファイルがありませんでした")
        return 1
    
    # 複合分析の実行
    print(f"\n{'='*80}")
    print("複合分析 - 複数ファイルからの共通パターン発見")
    print(f"{'='*80}")
    
    # スタッフ名の重複パターン分析
    staff_across_files = {}
    for file_path, patterns in all_patterns.items():
        for staff_name in patterns.get("staff_shifts", {}):
            if staff_name not in staff_across_files:
                staff_across_files[staff_name] = []
            staff_across_files[staff_name].append(file_path)
    
    # 重複スタッフの分析
    recurring_staff = {name: files for name, files in staff_across_files.items() if len(files) > 1}
    
    if recurring_staff:
        print(f"\n◆ 複数ファイルに登場するスタッフ ({len(recurring_staff)}名)")
        for staff, files in list(recurring_staff.items())[:5]:
            print(f"  - {staff}: {len(files)}ファイルに登場")
    
    # シフトコードの共通性分析
    shift_code_frequency = {}
    for patterns in all_patterns.values():
        for code in patterns.get("shift_codes", set()):
            shift_code_frequency[code] = shift_code_frequency.get(code, 0) + 1
    
    common_shift_codes = {code: freq for code, freq in shift_code_frequency.items() if freq > 1}
    
    if common_shift_codes:
        print(f"\n◆ 複数ファイルで使用されるシフトコード ({len(common_shift_codes)}種類)")
        sorted_codes = sorted(common_shift_codes.items(), key=lambda x: x[1], reverse=True)
        for code, freq in sorted_codes[:10]:
            print(f"  - '{code}': {freq}ファイルで使用")
    
    # 結果表示
    print("\n" + "=" * 80)
    print("【全体的な発見された真実】")
    print("=" * 80)
    
    print(f"\n◆ 分析サマリー")
    print(f"  - 分析ファイル数: {len(all_patterns)}")
    print(f"  - 総スタッフ数: {combined_staff_count}")
    print(f"  - 発見されたシフトコード: {len(combined_shift_codes)}種類")
    print(f"  - 総暗黙ルール数: {sum(len(p.get('implicit_rules', [])) for p in all_patterns.values())}")
    print(f"  - 総推測意図数: {len(all_intentions)}")
    
    # 上位の意図を確信度順で表示
    if all_intentions:
        all_intentions.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        print("\n◆ 最も確信度の高いシフト作成者の意図 (全ファイル統合)")
        for i, intent in enumerate(all_intentions[:15], 1):  # 上位15個
            print(f"\n{i}. {intent['finding']}")
            print(f"   意図: {intent['intention']}")
            print(f"   根拠: {intent['evidence']}")
            print(f"   確信度: {intent.get('confidence', 0):.0%}")
            print(f"   提案: {intent['actionable']}")
    
    # 複合レポート保存
    report = {
        "analysis_metadata": {
            "timestamp": datetime.now().isoformat(),
            "analyzed_files": list(all_patterns.keys()),
            "method": "compound_direct_xlsx_parsing"
        },
        "compound_discovery": {
            "total_files_analyzed": len(all_patterns),
            "total_staff_count": combined_staff_count,
            "total_shift_codes": len(combined_shift_codes),
            "recurring_staff_count": len(recurring_staff),
            "common_shift_codes_count": len(common_shift_codes)
        },
        "discovered_patterns": {
            "all_shift_codes": list(combined_shift_codes),
            "recurring_staff": dict(list(recurring_staff.items())[:10]),
            "common_shift_codes": dict(sorted(common_shift_codes.items(), key=lambda x: x[1], reverse=True)[:10]),
            "total_implicit_rules": sum(len(p.get('implicit_rules', [])) for p in all_patterns.values()),
            "total_intentions": len(all_intentions)
        },
        "key_findings": {
            "top_creator_intentions": all_intentions[:15],
            "file_specific_patterns": {str(k): {"implicit_rules": v.get("implicit_rules", [])[:5], "staff_count": len(v.get("staff_shifts", {}))} for k, v in all_patterns.items()}
        }
    }
    
    try:
        with open("compound_shift_analysis_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n[OK] 複合分析レポート保存: compound_shift_analysis_report.json")
    except Exception as e:
        print(f"[WARNING] レポート保存エラー: {e}")
    
    print("\n[COMPLETE] 複合シフト分析完了 - 複数ファイルから作成者の真の意図をあぶりだしました")
    print(f"[ACHIEVEMENT] 本来の目的達成 - シフト作成者の意図発見: {len(all_intentions)}個")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())