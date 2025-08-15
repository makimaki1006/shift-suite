#!/usr/bin/env python3
"""
ZIPファイルの内容を簡易分析
"""

import zipfile
import json
from pathlib import Path

def analyze_zip():
    zip_path = "analysis_results (55).zip"
    
    print(f"📦 ZIPファイル分析: {zip_path}")
    print(f"ファイルサイズ: {Path(zip_path).stat().st_size / 1024 / 1024:.1f} MB")
    print("=" * 80)
    
    with zipfile.ZipFile(zip_path, 'r') as zf:
        file_list = zf.namelist()
        print(f"総ファイル数: {len(file_list)}")
        
        # ファイルタイプ別集計
        file_types = {}
        for fname in file_list:
            ext = Path(fname).suffix.lower()
            file_types[ext] = file_types.get(ext, 0) + 1
        
        print("\n📊 ファイルタイプ別:")
        for ext, count in sorted(file_types.items()):
            print(f"  {ext}: {count}ファイル")
        
        # 重要ファイルの抽出
        print("\n🔍 重要ファイル:")
        
        # 1. 不足分析ファイル
        shortage_files = [f for f in file_list if 'shortage' in f.lower()]
        print(f"\n不足分析関連: {len(shortage_files)}ファイル")
        for f in shortage_files[:3]:
            info = zf.getinfo(f)
            print(f"  - {f} ({info.file_size:,} bytes)")
        
        # 2. JSON出力（AI包括レポート）
        json_files = [f for f in file_list if f.endswith('.json')]
        comprehensive_json = [f for f in json_files if 'comprehensive' in f]
        
        print(f"\nJSON出力: {len(json_files)}ファイル")
        print(f"  うちAI包括レポート: {len(comprehensive_json)}ファイル")
        
        # AI包括レポートの内容確認
        if comprehensive_json:
            json_file = comprehensive_json[0]
            print(f"\n📄 {json_file} の内容確認:")
            
            try:
                with zf.open(json_file) as f:
                    data = json.load(f)
                
                # トップレベルキーの確認
                print("  トップレベルキー:")
                for key in sorted(data.keys()):
                    print(f"    - {key}")
                
                # 主要データの確認
                if 'shortage_analysis' in data:
                    shortage = data['shortage_analysis']
                    print("\n  【不足分析データ】")
                    for k, v in shortage.items():
                        if isinstance(v, (int, float, str)):
                            print(f"    {k}: {v}")
                
                if 'fatigue_analysis' in data:
                    fatigue = data['fatigue_analysis']
                    print("\n  【疲労分析データ】")
                    for k, v in fatigue.items():
                        if isinstance(v, (int, float, str)):
                            print(f"    {k}: {v}")
                
                if 'fairness_analysis' in data:
                    fairness = data['fairness_analysis']
                    print("\n  【公平性分析データ】")
                    for k, v in fairness.items():
                        if isinstance(v, (int, float, str)):
                            print(f"    {k}: {v}")
                
                # データ整合性の確認
                if 'data_integrity_summary' in data:
                    integrity = data['data_integrity_summary']
                    print("\n  【データ整合性】")
                    for k, v in integrity.items():
                        print(f"    {k}: {v}")
                        
            except json.JSONDecodeError as e:
                print(f"  ❌ JSON解析エラー: {e}")
            except Exception as e:
                print(f"  ❌ エラー: {e}")
        
        # 3. 設定ファイル
        config_files = [f for f in file_list if 'config' in f and f.endswith('.json')]
        if config_files:
            print(f"\n⚙️ 設定ファイル: {config_files[0]}")
            try:
                with zf.open(config_files[0]) as f:
                    config = json.load(f)
                    if 'slot_minutes' in config:
                        print(f"  スロット間隔: {config['slot_minutes']}分")
                    if 'analysis_start_date' in config:
                        print(f"  分析開始日: {config['analysis_start_date']}")
                    if 'analysis_end_date' in config:
                        print(f"  分析終了日: {config['analysis_end_date']}")
            except Exception as e:
                print(f"  設定読み込みエラー: {e}")

if __name__ == "__main__":
    analyze_zip()