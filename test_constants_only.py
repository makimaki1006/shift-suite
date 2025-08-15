"""
定数とコアロジックの基本テスト

依存関係を最小限にした動的対応統一化の検証
"""

import sys
from pathlib import Path
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# テスト対象パスを追加
sys.path.insert(0, str(Path(__file__).parent))


def test_constants_import():
    """定数ファイルのインポートテスト"""
    log.info("定数ファイルのインポートテスト開始...")
    
    try:
        from shift_suite.tasks.constants import (
            DEFAULT_SLOT_MINUTES,
            SLOT_HOURS,
            NIGHT_START_TIME,
            NIGHT_END_TIME, 
            NIGHT_START_HOUR,
            NIGHT_END_HOUR,
            WAGE_RATES,
            COST_PARAMETERS,
            STATISTICAL_THRESHOLDS,
            FATIGUE_PARAMETERS,
            is_night_shift_time
        )
        log.info("✓ 定数インポート成功")
        return True
    except ImportError as e:
        log.error(f"✗ 定数インポート失敗: {e}")
        return False


def test_constants_consistency():
    """定数の一貫性テスト"""
    log.info("定数の一貫性テスト開始...")
    
    try:
        from shift_suite.tasks.constants import (
            DEFAULT_SLOT_MINUTES,
            SLOT_HOURS,
            NIGHT_START_HOUR,
            NIGHT_END_HOUR,
            WAGE_RATES
        )
        
        # SLOT_HOURSとDEFAULT_SLOT_MINUTESの整合性
        expected_slot_hours = DEFAULT_SLOT_MINUTES / 60.0
        if abs(SLOT_HOURS - expected_slot_hours) < 0.001:
            log.info("✓ SLOT_HOURS定数の整合性確認")
        else:
            log.error(f"✗ SLOT_HOURS不整合: {SLOT_HOURS} != {expected_slot_hours}")
            return False
        
        # 夜勤時間の妥当性
        if 0 <= NIGHT_START_HOUR <= 23 and 0 <= NIGHT_END_HOUR <= 23:
            log.info("✓ 夜勤時間定数の妥当性確認")
        else:
            log.error(f"✗ 夜勤時間不正: start={NIGHT_START_HOUR}, end={NIGHT_END_HOUR}")
            return False
        
        # 賃金設定の妥当性
        if (WAGE_RATES["regular_staff"] > 0 and 
            WAGE_RATES["temporary_staff"] > 0 and 
            WAGE_RATES["night_differential"] >= 1.0):
            log.info("✓ 賃金設定定数の妥当性確認")
        else:
            log.error("✗ 賃金設定に不正な値")
            return False
            
        return True
    except Exception as e:
        log.error(f"✗ 定数一貫性テスト失敗: {e}")
        return False


def test_night_shift_function():
    """夜勤判定関数のテスト"""
    log.info("夜勤判定関数テスト開始...")
    
    try:
        from shift_suite.tasks.constants import is_night_shift_time, NIGHT_START_HOUR, NIGHT_END_HOUR
        
        # 深夜時間帯のテスト
        if NIGHT_START_HOUR == 22 and NIGHT_END_HOUR == 6:
            # 22時は夜勤
            assert is_night_shift_time(22) == True
            # 23時は夜勤
            assert is_night_shift_time(23) == True
            # 0時は夜勤
            assert is_night_shift_time(0) == True
            # 5時は夜勤
            assert is_night_shift_time(5) == True
            # 6時は日勤
            assert is_night_shift_time(6) == False
            # 12時は日勤
            assert is_night_shift_time(12) == False
            # 21時は日勤
            assert is_night_shift_time(21) == False
            
            log.info("✓ 夜勤判定関数の動作確認")
            return True
        else:
            log.warning(f"夜勤時間設定が予期と異なる: {NIGHT_START_HOUR}-{NIGHT_END_HOUR}")
            # 基本的なテストのみ
            night_result = is_night_shift_time(NIGHT_START_HOUR)
            day_result = is_night_shift_time(12)  # 正午は確実に日勤
            
            if night_result == True and day_result == False:
                log.info("✓ 夜勤判定関数の基本動作確認")
                return True
            else:
                log.error("✗ 夜勤判定関数の動作不正")
                return False
    except Exception as e:
        log.error(f"✗ 夜勤判定関数テスト失敗: {e}")
        return False


def test_config_structure():
    """設定構造のテスト"""
    log.info("設定構造テスト開始...")
    
    try:
        from shift_suite.tasks.constants import (
            WAGE_RATES,
            COST_PARAMETERS,
            STATISTICAL_THRESHOLDS,
            FATIGUE_PARAMETERS
        )
        
        # 必須キーの存在確認
        required_wage_keys = ["regular_staff", "temporary_staff", "night_differential"]
        for key in required_wage_keys:
            if key not in WAGE_RATES:
                log.error(f"✗ WAGE_RATESに必須キー不足: {key}")
                return False
        
        required_cost_keys = ["recruit_cost_per_hire", "penalty_per_shortage_hour"]
        for key in required_cost_keys:
            if key not in COST_PARAMETERS:
                log.error(f"✗ COST_PARAMETERSに必須キー不足: {key}")
                return False
                
        required_stat_keys = ["confidence_level", "significance_alpha"]
        for key in required_stat_keys:
            if key not in STATISTICAL_THRESHOLDS:
                log.error(f"✗ STATISTICAL_THRESHOLDSに必須キー不足: {key}")
                return False
                
        required_fatigue_keys = ["min_rest_hours", "night_shift_threshold"]
        for key in required_fatigue_keys:
            if key not in FATIGUE_PARAMETERS:
                log.error(f"✗ FATIGUE_PARAMETERSに必須キー不足: {key}")
                return False
        
        log.info("✓ 設定構造の完全性確認")
        return True
        
    except Exception as e:
        log.error(f"✗ 設定構造テスト失敗: {e}")
        return False


def test_file_structure():
    """ファイル構造のテスト"""
    log.info("ファイル構造テスト開始...")
    
    base_path = Path(__file__).parent
    
    # 重要なファイルの存在確認
    important_files = [
        "shift_suite/tasks/constants.py",
        "shift_suite/tasks/config_manager.py", 
        "shift_suite/tasks/config_impact_tracker.py",
        "shift_suite/config/facility_types/general_hospital.json",
        "shift_suite/config/facility_types/nursing_home.json",
        "shift_suite/config/facility_types/clinic.json",
        "shift_suite/config/facility_types/daycare.json",
        "shift_suite/config/facilities/sample_hospital.json"
    ]
    
    missing_files = []
    for file_path in important_files:
        full_path = base_path / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        log.error(f"✗ 重要ファイルが不足: {missing_files}")
        return False
    else:
        log.info("✓ 重要ファイルの存在確認")
        return True


def test_template_files():
    """テンプレートファイルの内容テスト"""
    log.info("テンプレートファイル内容テスト開始...")
    
    import json
    
    base_path = Path(__file__).parent
    
    try:
        # 総合病院テンプレートのテスト
        hospital_template_path = base_path / "shift_suite/config/facility_types/general_hospital.json"
        with hospital_template_path.open('r', encoding='utf-8') as f:
            hospital_config = json.load(f)
        
        # 必須セクションの存在確認
        required_sections = ["time", "wage", "cost", "statistical", "fatigue"]
        for section in required_sections:
            if section not in hospital_config:
                log.error(f"✗ 総合病院テンプレートに{section}セクション不足")
                return False
        
        # 基本値の妥当性確認
        if hospital_config["time"]["slot_minutes"] <= 0:
            log.error("✗ 総合病院テンプレートのslot_minutes不正")
            return False
        
        if hospital_config["wage"]["regular_staff"] <= 0:
            log.error("✗ 総合病院テンプレートのregular_staff不正")
            return False
        
        log.info("✓ 総合病院テンプレートの内容確認")
        
        # サンプル施設設定のテスト
        sample_facility_path = base_path / "shift_suite/config/facilities/sample_hospital.json"
        with sample_facility_path.open('r', encoding='utf-8') as f:
            sample_config = json.load(f)
        
        if sample_config["facility_type"] != "general_hospital":
            log.error("✗ サンプル施設の施設タイプ不正")
            return False
        
        log.info("✓ サンプル施設設定の内容確認")
        return True
        
    except Exception as e:
        log.error(f"✗ テンプレートファイル内容テスト失敗: {e}")
        return False


def run_basic_tests():
    """基本テストを実行"""
    log.info("=== 動的対応統一化 基本テスト開始 ===")
    
    tests = [
        ("定数インポート", test_constants_import),
        ("定数一貫性", test_constants_consistency),
        ("夜勤判定関数", test_night_shift_function),
        ("設定構造", test_config_structure),
        ("ファイル構造", test_file_structure),
        ("テンプレートファイル", test_template_files)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                log.info(f"✓ {test_name} テスト成功")
            else:
                failed += 1
                log.error(f"✗ {test_name} テスト失敗")
        except Exception as e:
            failed += 1
            log.error(f"✗ {test_name} テスト例外: {e}")
    
    # 結果サマリー
    log.info(f"=== 基本テスト結果サマリー ===")
    log.info(f"成功: {passed}件")
    log.info(f"失敗: {failed}件")  
    log.info(f"合計: {passed + failed}件")
    
    if failed == 0:
        log.info("🎉 全ての基本テストが成功しました！")
        return True
    else:
        log.error("❌ 一部のテストが失敗しました")
        return False


def main():
    """メイン実行関数"""
    success = run_basic_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()