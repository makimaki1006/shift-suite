#!/usr/bin/env python3
"""
KPI計算のテスト
実際のKPI収集関数をテストして値を確認
"""

import sys
from pathlib import Path

# モジュールパスを追加
sys.path.insert(0, str(Path.cwd()))

try:
    # dash_app.pyの関数をインポート
    from dash_app import collect_dashboard_overview_kpis, get_dynamic_slot_hours
    
    print("🔍 === KPI計算テスト ===\n")
    
    # シナリオディレクトリを探す
    scenario_dirs = [
        Path("./temp_analysis_check/out_median_based"),
        Path("./median_based"),
        Path("./mean_based"),
        Path("./p25_based")
    ]
    
    for scenario_dir in scenario_dirs:
        if scenario_dir.exists():
            print(f"\n📁 シナリオ: {scenario_dir}")
            
            # KPIを計算
            kpis = collect_dashboard_overview_kpis(scenario_dir)
            
            print(f"  総不足時間: {kpis.get('total_shortage_hours', 0):.2f}時間")
            print(f"  総過剰時間: {kpis.get('total_excess_hours', 0):.2f}時間")
            
            # 値の妥当性チェック
            shortage = kpis.get('total_shortage_hours', 0)
            if shortage > 10000:
                print(f"  ⚠️ 警告: 不足時間 {shortage:.0f}時間は異常に大きいです！")
                
                # スロット数として扱われている可能性を検証
                print(f"\n  【推定計算】")
                for slot_minutes in [15, 30, 60]:
                    estimated_hours = shortage * (slot_minutes / 60.0)
                    print(f"  - もし{shortage:.0f}がスロット数なら:")
                    print(f"    {slot_minutes}分/スロット → {estimated_hours:.2f}時間")
                
                # 逆算も試す
                print(f"\n  【逆算】")
                for slot_minutes in [15, 30, 60]:
                    estimated_slots = shortage / (slot_minutes / 60.0)
                    print(f"  - {slot_minutes}分/スロットとすると:")
                    print(f"    {shortage:.0f}時間 = {estimated_slots:.0f}スロット")
    
    # 動的スロット時間も確認
    print(f"\n【動的スロット時間】")
    slot_hours = get_dynamic_slot_hours()
    print(f"  現在の設定: {slot_hours:.2f}時間/スロット ({slot_hours * 60:.0f}分/スロット)")
    
except Exception as e:
    print(f"❌ エラー: {e}")
    import traceback
    traceback.print_exc()