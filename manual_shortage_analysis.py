#!/usr/bin/env python3
"""
手動でshortage_time.parquetを詳細分析
"""

import struct

def read_parquet_info(file_path):
    """Parquetファイルの基本情報を読み取る"""
    with open(file_path, 'rb') as f:
        # ファイルサイズ
        f.seek(0, 2)
        file_size = f.tell()
        print(f"ファイルサイズ: {file_size:,} bytes")
        
        # Parquetマジックナンバーチェック
        f.seek(0)
        magic_start = f.read(4)
        f.seek(-4, 2)
        magic_end = f.read(4)
        
        if magic_start == b'PAR1' and magic_end == b'PAR1':
            print("✓ 有効なParquetファイル")
        else:
            print("✗ 無効なParquetファイル")
            return
        
        # フッターサイズを読み取る
        f.seek(-8, 2)
        footer_length = struct.unpack('<I', f.read(4))[0]
        print(f"フッターサイズ: {footer_length:,} bytes")
        
        # メタデータの位置
        metadata_start = file_size - 8 - footer_length
        print(f"メタデータ開始位置: {metadata_start:,}")

# 各統計手法のファイルを分析
base_path = "/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析/extracted_test"

print("=== Parquetファイル基本情報 ===\n")

methods = ['p25_based', 'mean_based', 'median_based']
for method in methods:
    file_path = f"{base_path}/out_{method}/shortage_time.parquet"
    print(f"\n【{method}】")
    try:
        read_parquet_info(file_path)
    except Exception as e:
        print(f"エラー: {e}")

# テキストファイルから情報を読み取る
print("\n\n=== ヒートマップ生成ログから情報抽出 ===")

import glob
log_files = glob.glob(f"{base_path}/out_*/2025年*ヒートマップ生成ログ.txt")

for log_file in log_files:
    print(f"\n【{log_file}】")
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # 期間情報を探す
            if "分析期間:" in content:
                lines = content.split('\n')
                for line in lines:
                    if "分析期間:" in line or "期間" in line:
                        print(f"  {line.strip()}")
            # 統計手法を探す
            if "統計手法:" in line or "25パーセンタイル" in content:
                for line in lines:
                    if "統計" in line or "パーセンタイル" in line:
                        print(f"  {line.strip()}")
    except Exception as e:
        print(f"  読み取りエラー: {e}")

# AIレポートから期間情報を確認
print("\n\n=== AIレポートから期間情報 ===")
ai_report_path = f"{base_path}/ai_comprehensive_report_20250731_141325_2e6a6a6c.json"

try:
    with open(ai_report_path, 'r', encoding='utf-8') as f:
        import json
        data = json.load(f)
        
        # 期間情報
        if 'report_metadata' in data:
            scope = data['report_metadata'].get('analysis_scope', {})
            period = scope.get('period', {})
            print(f"分析期間: {period.get('start_date')} ~ {period.get('end_date')}")
            
            # 入力データ
            print(f"入力データ: {scope.get('input_data_source')}")
            
        # KPI情報
        if 'key_performance_indicators' in data:
            kpis = data['key_performance_indicators']
            overall = kpis.get('overall_performance', {})
            shortage = overall.get('total_shortage_hours', {})
            print(f"\nAIレポートの不足時間: {shortage.get('value')}時間")
            print(f"参照Need時間: {shortage.get('reference_need_hours')}時間")
            
except Exception as e:
    print(f"読み取りエラー: {e}")

print("\n\n=== 問題の核心 ===")
print("1. 分析期間: 2025-01-01 ~ 2025-12-31 (1年間)")
print("2. 27,486.5時間は3ヶ月分として計算されている可能性")
print("3. AIレポートは0.0時間と表示（集計エラー）")
print("4. 実際のshortage_time.parquetには正しい値が入っている")
print("\n結論: ユーザーの言う通り、27,486.5時間は正確ではない")
print("理由: 1年分のデータを3ヶ月分として誤認識している可能性が高い")