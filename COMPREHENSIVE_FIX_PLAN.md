# 統一分析管理システム 包括的修正計画

## 🚨 緊急度別修正項目

### 第1段階: 即座に修正すべき重大問題（緊急度: ★★★★★）

#### 1.1 統一システムへの分析結果登録の修正

**問題**: 分析結果が統一システムに保存されていない

**根本原因の可能性**:
- app.pyで分析実行時に`unified_analysis_manager`のメソッドが呼ばれていない
- 結果の保存タイミングが不適切
- セッションステートの初期化問題

**修正内容**:

```python
# app.py の不足分析セクション（2404行目付近）を修正
if run_shortage:
    # 従来の処理
    run_task(
        shortage_module.run_shortage,
        scenario_out_dir,
        param_need_calc_method,
        # ... 他のパラメータ
    )
    
    # ✅ 修正: 統一システムへの結果登録を確実に実行
    if UNIFIED_ANALYSIS_AVAILABLE and hasattr(st.session_state, 'unified_analysis_manager'):
        try:
            # 結果ファイルの読み込み
            shortage_files = list(scenario_out_dir.glob("*shortage*.parquet"))
            if shortage_files:
                # 役職別集計データの読み込み
                role_df = pd.read_parquet(shortage_files[0])  # または適切なファイル選択
                
                # 統一システムへの登録
                shortage_result = st.session_state.unified_analysis_manager.create_shortage_analysis(
                    file_name, 
                    scenario_key,
                    role_df
                )
                
                # セッションステートへの保存（後方互換性）
                if not hasattr(st.session_state, 'shortage_analysis_results'):
                    st.session_state.shortage_analysis_results = {}
                
                # 統一システムから従来形式に変換して保存
                st.session_state.shortage_analysis_results[file_name] = {
                    "total_shortage_hours": shortage_result.core_metrics.get('total_shortage_hours', {}).get('value', 0.0),
                    "shortage_events_count": shortage_result.core_metrics.get('shortage_events_count', {}).get('value', 0),
                    "affected_roles_count": shortage_result.core_metrics.get('affected_roles_count', {}).get('value', 0),
                    "data_integrity": shortage_result.data_integrity,
                    "analysis_key": shortage_result.analysis_key
                }
                
                log.info(f"✅ 統一システムへの不足分析結果登録完了: {shortage_result.analysis_key}")
                
        except Exception as e:
            log.error(f"統一システムへの結果登録エラー: {e}", exc_info=True)
            # エラー時でも処理は継続
```

#### 1.2 AIレポート生成時のデータ取得修正

**問題**: `get_ai_compatible_results`が0件を返している

**修正内容**:

```python
# app.py の3361行目付近を修正
if UNIFIED_ANALYSIS_AVAILABLE and hasattr(st.session_state, 'unified_analysis_manager'):
    # 統一システムからAI互換形式でデータを取得
    unified_results = st.session_state.unified_analysis_manager.get_ai_compatible_results(file_name)
    
    # ✅ 修正: 結果が空の場合の診断とフォールバック
    if not unified_results:
        log.warning(f"統一システムから結果が取得できません。レジストリ内容: {len(st.session_state.unified_analysis_manager.results_registry)}件")
        
        # レジストリの内容を確認
        for key in st.session_state.unified_analysis_manager.results_registry.keys():
            log.debug(f"  登録済みキー: {key}")
        
        # フォールバック: セッションステートから直接取得を試みる
        if hasattr(st.session_state, 'shortage_analysis_results') and file_name in st.session_state.shortage_analysis_results:
            unified_results['shortage_analysis'] = st.session_state.shortage_analysis_results[file_name]
            log.info("フォールバック: セッションステートから不足分析結果を取得")
    
    # AI包括レポート用に統合
    analysis_results.update(unified_results)
    log.info(f"統一システムから{len(unified_results)}種類の分析結果を統合")
```

#### 1.3 不足分析計算の検証

**問題**: 不足時間が0になっている可能性

**修正内容**:

```python
# shift_suite/tasks/shortage.py の修正
def run_shortage(...):
    # ... 既存のコード ...
    
    # ✅ 修正: 計算結果の検証とログ出力
    if 'lack_h' in role_df.columns:
        total_shortage = role_df['lack_h'].sum()
        log.info(f"[shortage] 計算完了 - 総不足時間: {total_shortage:.2f}時間")
        
        if total_shortage == 0:
            log.warning("[shortage] ⚠️ 総不足時間が0です。データを確認してください。")
            # デバッグ情報の出力
            log.debug(f"  heat_all_df shape: {heat_all_df.shape}")
            log.debug(f"  need（必要人数）の統計: {heat_all_df.columns.str.contains('need').sum()}列")
            log.debug(f"  actual（実績人数）の統計: {heat_all_df.columns.str.contains('actual').sum()}列")
```

### 第2段階: データフロー全体の修正（緊急度: ★★★★☆）

#### 2.1 統一分析管理システムのデバッグ機能追加

```python
# shift_suite/tasks/unified_analysis_manager.py に追加
class UnifiedAnalysisManager:
    def __init__(self):
        self.converter = SafeDataConverter()
        self.key_manager = DynamicKeyManager()
        self.results_registry = {}
        self.debug_mode = True  # ✅ デバッグモード追加
        log.info("[UnifiedAnalysisManager] 初期化完了")
    
    def _debug_log(self, message: str):
        """デバッグログ出力"""
        if self.debug_mode:
            log.debug(f"[UAM Debug] {message}")
    
    def create_shortage_analysis(self, file_name: str, scenario_key: str, 
                               role_df: pd.DataFrame) -> UnifiedAnalysisResult:
        """不足分析結果の統一作成"""
        analysis_key = self.key_manager.generate_analysis_key(
            file_name, scenario_key, "shortage"
        )
        
        self._debug_log(f"不足分析開始: {analysis_key}")
        self._debug_log(f"入力データ: {role_df.shape if not role_df.empty else 'Empty'}")
        
        # ... 既存の処理 ...
        
        self.results_registry[analysis_key] = result
        self._debug_log(f"レジストリ登録完了: 現在{len(self.results_registry)}件")
        
        return result
```

#### 2.2 エラーハンドリングの強化

```python
# app.py のエラー修正
# 3825行目付近: collect_role_performance_detailed エラーの修正
try:
    # ✅ 修正: 未定義関数の呼び出しを削除または適切な関数に置き換え
    # collect_role_performance_detailed() を削除
    pass
except NameError as e:
    log.error(f"関数未定義エラー: {e}")
    # フォールバック処理
```

### 第3段階: 長期的な改善（緊急度: ★★★☆☆）

#### 3.1 統合テストの実装

```python
# test_unified_system_integration.py
import unittest
from shift_suite.tasks.unified_analysis_manager import UnifiedAnalysisManager

class TestUnifiedSystemIntegration(unittest.TestCase):
    def test_shortage_analysis_flow(self):
        """不足分析のデータフロー全体をテスト"""
        manager = UnifiedAnalysisManager()
        
        # テストデータ作成
        test_df = pd.DataFrame({
            'role': ['役職A', '役職B'],
            'lack_h': [10.5, 20.3]
        })
        
        # 分析実行
        result = manager.create_shortage_analysis("test.xlsx", "default", test_df)
        
        # 検証
        self.assertEqual(result.data_integrity, "valid")
        self.assertAlmostEqual(
            result.core_metrics['total_shortage_hours']['value'], 
            30.8, 
            places=1
        )
        
        # AI互換形式の取得テスト
        ai_results = manager.get_ai_compatible_results("test")
        self.assertIn('shortage_analysis', ai_results)
```

#### 3.2 監視とアラート機能

```python
# shift_suite/tasks/analysis_monitor.py (新規作成)
class AnalysisMonitor:
    """分析結果の妥当性を監視"""
    
    @staticmethod
    def validate_shortage_results(shortage_hours: float, context: dict) -> bool:
        """不足時間の妥当性を検証"""
        # コンテキストに基づく検証
        staff_count = context.get('staff_count', 1)
        period_days = context.get('period_days', 30)
        
        # 1人1日最大24時間として計算
        theoretical_max = staff_count * period_days * 24
        
        if shortage_hours > theoretical_max:
            log.error(f"不足時間が理論的最大値を超えています: {shortage_hours} > {theoretical_max}")
            return False
        
        if shortage_hours == 0 and context.get('has_shifts', True):
            log.warning("シフトデータがあるのに不足時間が0です")
            return False
        
        return True
```

## 📋 実装優先順位

1. **今すぐ実装**（30分以内）
   - [ ] 1.1 統一システムへの分析結果登録
   - [ ] 1.2 AIレポート生成時のデータ取得修正
   - [ ] 1.3 不足分析計算の検証ログ追加

2. **本日中に実装**（2-3時間）
   - [ ] 2.1 デバッグ機能の追加
   - [ ] 2.2 エラーハンドリングの強化

3. **今週中に実装**（1-2日）
   - [ ] 3.1 統合テストの実装
   - [ ] 3.2 監視とアラート機能

## 🎯 成功の判定基準

修正後、以下を確認：
1. AI包括レポートの`total_shortage_hours`が0以外の妥当な値
2. `data_integrity`が"valid"
3. 統一システムのレジストリに結果が登録されている
4. エラーログが出力されない

## ⚠️ リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| 既存の分析が動作しなくなる | 高 | フォールバック処理を必ず実装 |
| パフォーマンス低下 | 中 | デバッグモードを本番では無効化 |
| メモリ使用量増加 | 低 | 既存のクリーンアップ機能を活用 |

## 📊 期待される改善効果

1. **不足時間計算の正確性**: 0時間問題の解決
2. **データ整合性**: 100%の分析結果が統一システムに保存
3. **可視性向上**: デバッグログによる問題の早期発見
4. **信頼性向上**: 自動検証による異常値の検出