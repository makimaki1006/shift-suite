#!/usr/bin/env python3
"""
統合された12軸制約発見システムのテスト
app.pyに組み込まれた制約発見システムが正常に動作することを確認
"""

import sys
import logging
from pathlib import Path

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def test_constraint_discovery_integration():
    """制約発見システムの統合テスト"""
    log.info("12軸制約発見システムの統合テストを開始...")
    
    try:
        # 1. Ultra Dimensional Constraint Discovery Systemをインポート
        from ultra_dimensional_constraint_discovery_system import UltraDimensionalConstraintDiscoverySystem
        log.info("✅ UltraDimensionalConstraintDiscoverySystem のインポート成功")
        
        # 2. システムの初期化
        system = UltraDimensionalConstraintDiscoverySystem()
        log.info("✅ システムの初期化成功")
        
        # 3. テスト用データファイルの確認
        test_file = Path("デイ_テスト用データ_休日精緻.xlsx")
        if test_file.exists():
            log.info(f"✅ テストファイル発見: {test_file}")
            
            # 4. 制約発見の実行
            log.info("制約発見を実行中...")
            result = system.discover_ultra_dimensional_constraints(str(test_file))
            constraints = result.get('constraints', [])
            
            if constraints:
                total_constraints = len(constraints)
                log.info(f"✅ 制約発見成功: {total_constraints}個の制約を発見")
                
                # 軸別の制約数を集計
                axis_counts = {}
                for constraint in constraints:
                    axis = constraint.get('axis', 'Unknown')
                    axis_counts[axis] = axis_counts.get(axis, 0) + 1
                
                log.info("【軸別制約数】:")
                for axis, count in sorted(axis_counts.items()):
                    log.info(f"  {axis}: {count}個")
                
                # 制約の品質チェック
                quality_levels = {}
                for constraint in constraints:
                    level = constraint.get('constraint_level', 'Unknown')
                    quality_levels[level] = quality_levels.get(level, 0) + 1
                
                log.info("【制約深度レベル】:")
                for level, count in sorted(quality_levels.items()):
                    log.info(f"  {level}: {count}個")
                
                if total_constraints >= 300:
                    log.info(f"🎉 目標達成！ {total_constraints}個の制約を発見（目標300+）")
                    return True
                else:
                    log.warning(f"⚠️ 制約数が目標未達: {total_constraints}個 < 300個")
                    return False
                    
            else:
                log.error("❌ 制約発見が空の結果を返しました")
                return False
                
        else:
            log.warning(f"⚠️ テストファイルが見つかりません: {test_file}")
            
            # 代替テストファイルを探す
            alternative_files = [
                "ショート_テスト用データ.xlsx",
                "テストデータ_勤務表　勤務時間_トライアル.xlsx"
            ]
            
            for alt_file in alternative_files:
                alt_path = Path(alt_file)
                if alt_path.exists():
                    log.info(f"✅ 代替テストファイル発見: {alt_path}")
                    result = system.discover_ultra_dimensional_constraints(str(alt_path))
                    constraints = result.get('constraints', [])
                    
                    if constraints:
                        total_constraints = len(constraints)
                        log.info(f"✅ 代替ファイルでの制約発見成功: {total_constraints}個")
                        return True
                    break
            else:
                log.error("❌ 利用可能なテストファイルがありません")
                return False
                
    except ImportError as e:
        log.error(f"❌ インポートエラー: {e}")
        return False
    except Exception as e:
        log.error(f"❌ 予期しないエラー: {e}")
        return False

def test_app_integration():
    """app.pyとの統合テスト"""
    log.info("app.py統合テストを開始...")
    
    try:
        # app.pyから制約発見タブ関数をインポート
        import app
        
        if hasattr(app, 'display_constraint_discovery_tab'):
            log.info("✅ display_constraint_discovery_tab 関数が見つかりました")
            return True
        else:
            log.error("❌ display_constraint_discovery_tab 関数が見つかりません")
            return False
            
    except ImportError as e:
        log.error(f"❌ app.py インポートエラー: {e}")
        return False
    except Exception as e:
        log.error(f"❌ app.py統合テストエラー: {e}")
        return False

def main():
    """メインテスト実行"""
    log.info("=" * 60)
    log.info("12軸制約発見システム統合テスト開始")
    log.info("=" * 60)
    
    # テスト1: 制約発見システム単体テスト
    test1_success = test_constraint_discovery_integration()
    
    # テスト2: app.py統合テスト
    test2_success = test_app_integration()
    
    # 結果サマリー
    log.info("=" * 60)
    log.info("テスト結果サマリー")
    log.info("=" * 60)
    log.info(f"制約発見システム単体: {'✅ 成功' if test1_success else '❌ 失敗'}")
    log.info(f"app.py統合テスト: {'✅ 成功' if test2_success else '❌ 失敗'}")
    
    if test1_success and test2_success:
        log.info("🎉 全てのテストが成功しました！")
        log.info("12軸制約発見システムがStreamlitアプリに正常に統合されています。")
        return True
    else:
        log.error("❌ 一部のテストが失敗しました。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)