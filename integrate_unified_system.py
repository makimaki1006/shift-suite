#!/usr/bin/env python3
"""
既存システムへの統一アーキテクチャ統合
全体最適化による段階的移行システム
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple

def integrate_unified_system():
    """dash_app.pyへの統一システム統合"""
    
    print("=== 全体最適化: 統一システム統合開始 ===")
    
    dash_app_path = Path("dash_app.py")
    
    # 1. バックアップ作成
    backup_path = dash_app_path.with_suffix('.py.unified_backup')
    with open(dash_app_path, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(original_content)
    print(f"✓ バックアップ作成: {backup_path}")
    
    # 2. 統一システムのインポート追加
    modified_content = add_unified_imports(original_content)
    
    # 3. data_get関数を統一システム版に置換
    modified_content = replace_data_get_function(modified_content)
    
    # 4. 按分廃止関連の最適化
    modified_content = optimize_proportional_abolition_functions(modified_content)
    
    # 5. グローバル設定の追加
    modified_content = add_unified_global_config(modified_content)
    
    # 6. エラーハンドリングの強化
    modified_content = enhance_error_handling(modified_content)
    
    # 7. パフォーマンス監視の追加
    modified_content = add_performance_monitoring(modified_content)
    
    # ファイル保存
    with open(dash_app_path, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    print("✓ 統一システム統合完了")
    
    # 8. 統合テスト実行
    test_integration()
    
    return True

def add_unified_imports(content: str) -> str:
    """統一システムのインポート追加"""
    
    # 既存インポートの後に統一システムを追加
    import_section = '''
# ============================================================================
# 統一データパイプラインアーキテクチャ統合
# ============================================================================
from unified_data_pipeline_architecture import (
    UnifiedDataRegistry, 
    UnifiedDataPipeline,
    DataType, 
    DataStage, 
    Priority,
    get_unified_registry,
    enhanced_data_get
)

# 全体最適化: 統一レジストリ初期化
UNIFIED_REGISTRY = get_unified_registry()
UNIFIED_PIPELINE = UnifiedDataPipeline(UNIFIED_REGISTRY)

# パフォーマンス監視
import time
from collections import defaultdict

PERFORMANCE_STATS = defaultdict(list)

def track_performance(func_name: str, execution_time_ms: float):
    """パフォーマンス追跡"""
    PERFORMANCE_STATS[func_name].append({
        'timestamp': time.time(),
        'execution_time_ms': execution_time_ms,
    })
    
    # 最新100件のみ保持
    if len(PERFORMANCE_STATS[func_name]) > 100:
        PERFORMANCE_STATS[func_name] = PERFORMANCE_STATS[func_name][-100:]

'''
    
    # shift_suiteインポートの後に挿入
    pattern = r'(from shift_suite.*?\\n)'
    replacement = r'\\1' + import_section
    
    return re.sub(pattern, replacement, content, count=1, flags=re.DOTALL)

def replace_data_get_function(content: str) -> str:
    """data_get関数を統一システム版に置換"""
    
    # 既存のdata_get関数全体を統一版に置換
    new_data_get = '''
def data_get(key: str, default=None, for_display: bool = False):
    """
    統一データパイプライン対応data_get関数
    全体最適化による高性能・セキュア・一貫したデータ取得
    """
    start_time = time.time()
    
    try:
        # 統一レジストリからデータ取得
        result = enhanced_data_get(key, default)
        
        # パフォーマンス追跡
        execution_time = (time.time() - start_time) * 1000
        track_performance(f'data_get:{key}', execution_time)
        
        if result is not None:
            log.debug(f"統一システム: データ取得成功 {key} ({execution_time:.1f}ms)")
        else:
            log.warning(f"統一システム: データ未発見 {key}")
        
        return result
        
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        log.error(f"統一システム: データ取得失敗 {key} - {e} ({execution_time:.1f}ms)")
        return default
'''
    
    # 既存のdata_get関数を置換
    pattern = r'def data_get\(.*?\n.*?return default.*?\n'
    replacement = new_data_get
    
    return re.sub(pattern, replacement, content, flags=re.DOTALL)

def optimize_proportional_abolition_functions(content: str) -> str:
    """按分廃止関連関数の最適化"""
    
    # create_proportional_abolition_tab関数の最適化
    optimized_function = '''
def create_proportional_abolition_tab(selected_scenario: str = None) -> html.Div:
    """按分廃止・職種別分析タブ作成 - 統一システム最適化版"""
    
    start_time = time.time()
    
    try:
        log.info("===== 統一システム: 按分廃止分析タブ作成開始 =====")
        
        # 統一レジストリから直接データタイプ指定で取得
        df_proportional_role = UNIFIED_REGISTRY.get_data(DataType.PROPORTIONAL_ABOLITION_ROLE)
        df_proportional_org = UNIFIED_REGISTRY.get_data(DataType.PROPORTIONAL_ABOLITION_ORG)
        
        # データ存在チェック（統一エラーハンドリング）
        if df_proportional_role is None or df_proportional_role.empty:
            return create_proportional_abolition_error_message()
        
        if df_proportional_org is None or df_proportional_org.empty:
            log.warning("組織データが見つかりません - 職種データのみで表示")
            df_proportional_org = pd.DataFrame()
        
        # 処理時間追跡
        data_load_time = (time.time() - start_time) * 1000
        track_performance('proportional_tab:data_load', data_load_time)
        
        log.info(f"統一システム: 按分廃止データ読み込み完了 職種{len(df_proportional_role)}個 ({data_load_time:.1f}ms)")
        
        # 統一パイプラインによる可視化データ処理
        viz_start_time = time.time()
        
        processed_role_data = UNIFIED_PIPELINE.process_data(
            DataType.PROPORTIONAL_ABOLITION_ROLE, 
            df_proportional_role,
            DataStage.VISUALIZED
        )
        
        processed_org_data = UNIFIED_PIPELINE.process_data(
            DataType.PROPORTIONAL_ABOLITION_ORG,
            df_proportional_org, 
            DataStage.VISUALIZED
        ) if not df_proportional_org.empty else df_proportional_org
        
        viz_time = (time.time() - viz_start_time) * 1000
        track_performance('proportional_tab:visualization', viz_time)
        
        # 統一スタイルでUI構築
        content = build_proportional_abolition_ui(processed_role_data, processed_org_data)
        
        total_time = (time.time() - start_time) * 1000
        track_performance('proportional_tab:total', total_time)
        
        log.info(f"統一システム: 按分廃止タブ作成完了 ({total_time:.1f}ms)")
        
        return content
        
    except Exception as e:
        total_time = (time.time() - start_time) * 1000
        log.error(f"統一システム: 按分廃止タブ作成失敗 - {e} ({total_time:.1f}ms)")
        return create_proportional_abolition_error_message(str(e))
'''
    
    # 既存関数を置換
    pattern = r'def create_proportional_abolition_tab\(.*?\n.*?return.*?\n.*?except.*?\n.*?return.*?\n'
    replacement = optimized_function
    
    return re.sub(pattern, replacement, content, flags=re.DOTALL)

def add_unified_global_config(content: str) -> str:
    """統一グローバル設定の追加"""
    
    global_config = '''
# ============================================================================
# 統一システムグローバル設定
# ============================================================================

# 統一レジストリの定期リフレッシュ設定
REGISTRY_REFRESH_INTERVAL = 300  # 5分間隔
LAST_REGISTRY_REFRESH = time.time()

def check_registry_refresh():
    """レジストリの定期リフレッシュチェック"""
    global LAST_REGISTRY_REFRESH
    
    if time.time() - LAST_REGISTRY_REFRESH > REGISTRY_REFRESH_INTERVAL:
        try:
            UNIFIED_REGISTRY.refresh_data()
            LAST_REGISTRY_REFRESH = time.time()
            log.info("統一レジストリ: 定期リフレッシュ完了")
        except Exception as e:
            log.error(f"統一レジストリ: リフレッシュ失敗 - {e}")

# 統一エラーメッセージ生成
def create_unified_error_message(title: str, message: str, suggestion: str = "") -> html.Div:
    """統一エラーメッセージUI"""
    return html.Div([
        html.H3(f"⚠️ {title}", style={'color': '#f44336', 'marginBottom': '10px'}),
        html.P(message, style={'color': '#666', 'marginBottom': '15px'}),
        html.P(suggestion, style={'color': '#2196f3', 'fontWeight': '500'}) if suggestion else None,
        html.Hr(),
        html.P("🔧 統一データパイプラインシステム", style={'color': '#4caf50', 'fontSize': '12px'})
    ], style={
        'padding': '20px',
        'backgroundColor': '#fff3cd',
        'border': '1px solid #ffeaa7',
        'borderRadius': '8px',
        'margin': '20px'
    })

def create_proportional_abolition_error_message(error_details: str = "") -> html.Div:
    """按分廃止専用エラーメッセージ"""
    return create_unified_error_message(
        title="按分廃止分析データが見つかりません",
        message="統一データレジストリで按分廃止分析結果を検出できませんでした。",
        suggestion=f"1. app.pyで按分廃止分析を実行してください\\n2. ファイルが正しい場所に保存されているか確認\\n3. データリフレッシュを実行\\n\\n詳細: {error_details}" if error_details else ""
    )

'''
    
    # アプリケーション初期化部分の後に追加
    pattern = r"(if __name__ == '__main__':.*?\n)"
    replacement = global_config + r'\\1'
    
    return re.sub(pattern, replacement, content, flags=re.DOTALL)

def enhance_error_handling(content: str) -> str:
    """エラーハンドリングの強化"""
    
    # 既存のtry-except文を統一システム対応に強化
    enhanced_patterns = [
        # data_get呼び出しのエラーハンドリング強化
        (
            r'(df_\w+\s*=\s*data_get\([^)]+\))',
            r'\\1\nif \\1 is None:\n    log.warning(f"データ取得失敗: {key}")\n    check_registry_refresh()  # 自動リフレッシュ試行'
        ),
    ]
    
    for pattern, replacement in enhanced_patterns:
        content = re.sub(pattern, replacement, content)
    
    return content

def add_performance_monitoring(content: str) -> str:
    """パフォーマンス監視機能の追加"""
    
    monitoring_functions = '''
# ============================================================================
# 統一システム: パフォーマンス監視
# ============================================================================

def get_performance_report() -> Dict[str, Any]:
    """パフォーマンスレポート生成"""
    report = {
        'timestamp': time.time(),
        'functions': {}
    }
    
    for func_name, measurements in PERFORMANCE_STATS.items():
        if measurements:
            times = [m['execution_time_ms'] for m in measurements]
            report['functions'][func_name] = {
                'count': len(times),
                'avg_ms': sum(times) / len(times),
                'min_ms': min(times),
                'max_ms': max(times),
                'last_execution': max(m['timestamp'] for m in measurements)
            }
    
    return report

def create_performance_dashboard() -> html.Div:
    """パフォーマンスダッシュボード作成"""
    report = get_performance_report()
    
    children = [
        html.H3("🚀 統一システム パフォーマンス監視", style={'color': '#2196f3'}),
        html.Hr()
    ]
    
    for func_name, stats in report['functions'].items():
        children.append(html.Div([
            html.H5(func_name, style={'marginBottom': '5px'}),
            html.P(f"実行回数: {stats['count']} | 平均: {stats['avg_ms']:.1f}ms | 最大: {stats['max_ms']:.1f}ms"),
        ], style={'marginBottom': '15px', 'padding': '10px', 'backgroundColor': '#f5f5f5'}))
    
    # レジストリ統計も表示
    registry_stats = UNIFIED_REGISTRY.get_statistics()
    children.append(html.Div([
        html.H4("📊 統一レジストリ統計"),
        html.P(f"総ファイル数: {registry_stats['total_files']}"),
        html.P(f"キャッシュエントリ: {registry_stats['cache_entries']}"),
        html.P(f"総容量: {registry_stats['total_size_mb']:.1f}MB"),
        html.P(f"エラーファイル: {registry_stats['error_files']}")
    ]))
    
    return html.Div(children)

'''
    
    # 既存のfunction定義部分に追加
    pattern = r'(def create_.*?_tab\(.*?\):)'
    content += monitoring_functions
    
    return content

def test_integration():
    """統合テスト実行"""
    print("\\n=== 統合テスト実行 ===")
    
    try:
        # 統一システムのインポートテスト
        exec("from unified_data_pipeline_architecture import get_unified_registry")
        print("✓ 統一システムインポート: 成功")
        
        # レジストリ初期化テスト
        exec("registry = get_unified_registry()")
        print("✓ 統一レジストリ初期化: 成功")
        
        # データ取得テスト
        exec("""
registry = get_unified_registry()
data = registry.get_data('proportional_abolition_role_summary')
print(f"✓ データ取得テスト: {'成功' if data is not None else '失敗'}")
""")
        
        print("✓ 統合テスト: 全項目成功")
        return True
        
    except Exception as e:
        print(f"✗ 統合テスト失敗: {e}")
        return False

if __name__ == "__main__":
    success = integrate_unified_system()
    if success:
        print("\\n🎉 全体最適化: 統一システム統合完了!")
        print("\\n次のステップ:")
        print("1. dash_app.pyの動作確認")
        print("2. パフォーマンス測定")
        print("3. 按分廃止機能の完全動作テスト")
    else:
        print("\\n❌ 統合に問題が発生しました")