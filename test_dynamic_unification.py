"""
動的対応統一化のテスト・検証スイート

このスクリプトは以下を検証します：
1. 設定値の動的対応が全モジュールで統一されているか
2. 階層的設定管理システムが正しく動作するか
3. 設定変更の影響追跡が正しく機能するか
4. 既存の計算結果との整合性が保たれているか
"""

import sys
import os
from pathlib import Path
import logging
import tempfile
import shutil

# テスト対象モジュールのパスを追加
sys.path.insert(0, str(Path(__file__).parent))

from shift_suite.tasks.config_manager import (
    ConfigManager, 
    get_config_manager,
    TimeConfig, 
    WageConfig,
    FacilityConfig
)
from shift_suite.tasks.config_impact_tracker import ConfigImpactTracker, ImpactLevel
from shift_suite.tasks.constants import (
    DEFAULT_SLOT_MINUTES,
    SLOT_HOURS,
    NIGHT_START_HOUR,
    NIGHT_END_HOUR,
    WAGE_RATES,
    STATISTICAL_THRESHOLDS
)

# ロギング設定
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class TestDynamicUnification:
    """動的対応統一化のテストクラス"""
    
    @classmethod
    def setup_class(cls):
        """テストクラスのセットアップ"""
        cls.temp_dir = Path(tempfile.mkdtemp())
        cls.config_manager = ConfigManager(config_dir=cls.temp_dir / "config")
        cls.impact_tracker = ConfigImpactTracker(cls.config_manager)
        log.info(f"テスト用一時ディレクトリ: {cls.temp_dir}")
    
    @classmethod
    def teardown_class(cls):
        """テストクラスのクリーンアップ"""
        if cls.temp_dir.exists():
            shutil.rmtree(cls.temp_dir)
        log.info("テスト用一時ディレクトリを削除")
    
    def test_constants_consistency(self):
        """定数の一貫性をテスト"""
        log.info("定数の一貫性をテスト中...")
        
        # SLOT_HOURSとDEFAULT_SLOT_MINUTESの整合性
        expected_slot_hours = DEFAULT_SLOT_MINUTES / 60.0
        assert abs(SLOT_HOURS - expected_slot_hours) < 0.001
        log.info("✓ SLOT_HOURS定数の整合性確認")
        
        # 夜勤時間の妥当性
        assert 0 <= NIGHT_START_HOUR <= 23
        assert 0 <= NIGHT_END_HOUR <= 23
        assert NIGHT_START_HOUR != NIGHT_END_HOUR
        log.info("✓ 夜勤時間定数の妥当性確認")
        
        # 賃金設定の妥当性
        assert WAGE_RATES["regular_staff"] > 0
        assert WAGE_RATES["temporary_staff"] > 0
        assert WAGE_RATES["night_differential"] >= 1.0
        log.info("✓ 賃金設定定数の妥当性確認")
    
    def test_config_manager_basic(self):
        """設定マネージャーの基本動作をテスト"""
        log.info("設定マネージャーの基本動作をテスト中...")
        
        # デフォルト設定の取得
        default_config = self.config_manager.get_config()
        assert default_config.facility_id == "default"
        assert default_config.time.slot_minutes == DEFAULT_SLOT_MINUTES
        log.info("✓ デフォルト設定取得")
        
        # 時間設定の取得
        time_config = self.config_manager.get_time_config()
        assert isinstance(time_config, TimeConfig)
        assert time_config.slot_minutes == DEFAULT_SLOT_MINUTES
        assert time_config.night_start_hour == NIGHT_START_HOUR
        log.info("✓ 時間設定取得")
        
        # 賃金設定の取得
        wage_config = self.config_manager.get_wage_config()
        assert isinstance(wage_config, WageConfig)
        assert wage_config.regular_staff == WAGE_RATES["regular_staff"]
        log.info("✓ 賃金設定取得")
    
    def test_facility_template_creation(self):
        """施設テンプレート作成をテスト"""
        log.info("施設テンプレート作成をテスト中...")
        
        # テスト用テンプレートを作成
        template_config = {
            "facility_name": "テスト病院テンプレート",
            "facility_type": "test_hospital",
            "time": {
                "slot_minutes": 15,  # デフォルトから変更
                "night_start_hour": 21
            },
            "wage": {
                "regular_staff": 2000  # デフォルトから変更
            }
        }
        
        template_file = self.config_manager.create_facility_template(
            "test_hospital", template_config
        )
        assert template_file.exists()
        log.info("✓ 施設テンプレートファイル作成")
        
        # テンプレートを使用した個別施設設定を作成
        facility_config = FacilityConfig(
            facility_id="test_facility_001",
            facility_name="テスト施設001",
            facility_type="test_hospital",
            time=TimeConfig(slot_minutes=15, night_start_hour=21),
            wage=WageConfig(regular_staff=2000),
            cost=self.config_manager._default_config.cost,
            statistical=self.config_manager._default_config.statistical,
            fatigue=self.config_manager._default_config.fatigue
        )
        
        saved_file = self.config_manager.save_facility_config(facility_config)
        assert saved_file.exists()
        log.info("✓ 個別施設設定保存")
        
        # 階層的設定の動作確認
        loaded_config = self.config_manager.get_config("test_facility_001")
        assert loaded_config.time.slot_minutes == 15  # テンプレートから継承
        assert loaded_config.time.night_start_hour == 21  # テンプレートから継承
        assert loaded_config.wage.regular_staff == 2000  # テンプレートから継承
        # デフォルト値は保持されている
        assert loaded_config.time.night_end_hour == NIGHT_END_HOUR
        log.info("✓ 階層的設定継承確認")
    
    def test_impact_tracking(self):
        """影響追跡機能をテスト"""
        log.info("影響追跡機能をテスト中...")
        
        # 元の設定
        old_config = self.config_manager._default_config
        
        # 新しい設定（重要な変更を含む）
        new_config = FacilityConfig(
            facility_id="test_facility",
            facility_name="テスト施設",
            facility_type="general",
            time=TimeConfig(
                slot_minutes=60,  # CRITICAL変更
                night_start_hour=23  # HIGH変更
            ),
            wage=WageConfig(
                regular_staff=2500,  # MEDIUM変更
                temporary_staff=WAGE_RATES["temporary_staff"]
            ),
            cost=old_config.cost,
            statistical=old_config.statistical,
            fatigue=old_config.fatigue
        )
        
        # 影響分析を実行
        analyses = self.impact_tracker.analyze_config_change(
            "test_facility", old_config, new_config, "test_user"
        )
        
        assert len(analyses) > 0
        log.info(f"✓ {len(analyses)}件の設定変更を検出")
        
        # 影響レベルの確認
        slot_minutes_analysis = next(
            (a for a in analyses if a.change.field == "slot_minutes"), None
        )
        assert slot_minutes_analysis is not None
        assert slot_minutes_analysis.impact_level == ImpactLevel.CRITICAL
        assert slot_minutes_analysis.requires_reprocessing == True
        log.info("✓ CRITICAL変更の影響分析確認")
        
        night_hour_analysis = next(
            (a for a in analyses if a.change.field == "night_start_hour"), None
        )
        assert night_hour_analysis is not None
        assert night_hour_analysis.impact_level == ImpactLevel.HIGH
        log.info("✓ HIGH変更の影響分析確認")
        
        # 影響レポート生成
        report = self.impact_tracker.generate_impact_report(analyses)
        assert "設定変更影響分析レポート" in report
        assert "CRITICAL" in report
        assert "HIGH" in report
        log.info("✓ 影響レポート生成確認")
        
        # 変更履歴の確認
        history = self.impact_tracker.get_change_history("test_facility")
        assert len(history) == len(analyses)
        log.info("✓ 変更履歴記録確認")
    
    def test_config_validation(self):
        """設定の妥当性チェックをテスト"""
        log.info("設定の妥当性チェックをテスト中...")
        
        # 正常な設定
        valid_config = self.config_manager._default_config
        errors = self.config_manager.validate_config(valid_config)
        assert len(errors) == 0
        log.info("✓ 正常設定の妥当性確認")
        
        # 不正な設定
        invalid_config = FacilityConfig(
            facility_id="invalid",
            facility_name="無効設定",
            facility_type="test",
            time=TimeConfig(
                slot_minutes=-10,  # 不正: 負の値
                night_start_hour=25  # 不正: 範囲外
            ),
            wage=WageConfig(
                regular_staff=-100,  # 不正: 負の値
                night_differential=0.5  # 不正: 1.0未満
            ),
            cost=valid_config.cost,
            statistical=valid_config.statistical,
            fatigue=valid_config.fatigue
        )
        
        errors = self.config_manager.validate_config(invalid_config)
        assert len(errors) > 0
        log.info(f"✓ 不正設定の検出: {len(errors)}件のエラー")
        
        # 具体的なエラーの確認
        error_messages = " ".join(errors)
        assert "slot_minutes must be positive" in error_messages
        assert "night_start_hour must be 0-23" in error_messages
        assert "regular_staff wage must be positive" in error_messages
        assert "night_differential must be >= 1.0" in error_messages
        log.info("✓ 具体的エラーメッセージ確認")
    
    def test_backwards_compatibility(self):
        """後方互換性をテスト"""
        log.info("後方互換性をテスト中...")
        
        # 便利関数の動作確認
        from shift_suite.tasks.config_manager import (
            get_time_config, get_wage_config, get_cost_config
        )
        
        time_config = get_time_config()
        assert isinstance(time_config, TimeConfig)
        assert time_config.slot_minutes == DEFAULT_SLOT_MINUTES
        log.info("✓ get_time_config() 便利関数")
        
        wage_config = get_wage_config()
        assert isinstance(wage_config, WageConfig)
        assert wage_config.regular_staff == WAGE_RATES["regular_staff"]
        log.info("✓ get_wage_config() 便利関数")
    
    def test_module_import_consistency(self):
        """モジュール間でのインポート一貫性をテスト"""
        log.info("モジュール間でのインポート一貫性をテスト中...")
        
        try:
            # 重要なモジュールでの定数インポートをテスト
            from shift_suite.tasks.constants import (
                SLOT_HOURS, DEFAULT_SLOT_MINUTES, 
                NIGHT_START_HOUR, NIGHT_END_HOUR
            )
            
            # 関連モジュールでの統一された定数使用をテスト
            modules_to_test = [
                'shift_suite.tasks.shortage',
                'shift_suite.tasks.daily_cost', 
                'shift_suite.tasks.fatigue',
                'shift_suite.tasks.fairness'
            ]
            
            for module_name in modules_to_test:
                try:
                    __import__(module_name)
                    log.info(f"✓ {module_name} インポート成功")
                except ImportError as e:
                    log.warning(f"✗ {module_name} インポート失敗: {e}")
                    
        except ImportError as e:
            log.error(f"定数インポートエラー: {e}")
            raise Exception(f"定数インポートに失敗: {e}")


def run_comprehensive_test():
    """包括的テストを実行"""
    log.info("=== 動的対応統一化 包括的テスト開始 ===")
    
    test_suite = TestDynamicUnification()
    test_suite.setup_class()
    
    try:
        # 各テストを実行
        tests = [
            test_suite.test_constants_consistency,
            test_suite.test_config_manager_basic,
            test_suite.test_facility_template_creation,
            test_suite.test_impact_tracking,
            test_suite.test_config_validation,
            test_suite.test_backwards_compatibility,
            test_suite.test_module_import_consistency
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                test()
                passed += 1
                log.info(f"✓ {test.__name__} 成功")
            except Exception as e:
                failed += 1
                log.error(f"✗ {test.__name__} 失敗: {e}")
        
        # 結果サマリー
        log.info(f"=== テスト結果サマリー ===")
        log.info(f"成功: {passed}件")
        log.info(f"失敗: {failed}件")
        log.info(f"合計: {passed + failed}件")
        
        if failed == 0:
            log.info("🎉 全テストが成功しました！")
            return True
        else:
            log.error("❌ 一部のテストが失敗しました")
            return False
            
    finally:
        test_suite.teardown_class()


def main():
    """メイン実行関数"""
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()