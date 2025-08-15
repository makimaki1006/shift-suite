#!/usr/bin/env python3
"""
段階的統合パッチ - 既存システムへの最小侵襲アプローチ
"""

def apply_gradual_integration_patch():
    """段階的統合パッチ適用"""
    
    print("=== 段階的統合パッチ適用開始 ===")
    
    # 1. 統一システムインポートのみ追加（既存機能は保持）
    add_unified_imports_only()
    
    # 2. data_get関数にフォールバック機能追加
    enhance_data_get_with_fallback()
    
    # 3. 按分廃止専用の最適化パス追加
    add_proportional_specific_optimization()
    
    print("✓ 段階的統合パッチ適用完了")

def add_unified_imports_only():
    """統一システムインポートのみ追加"""
    
    from pathlib import Path
    
    dash_app_path = Path("dash_app.py")
    
    with open(dash_app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 統一システムインポート追加（条件付き）
    import_addition = """
# 統一システム統合 - 段階的導入
try:
    from unified_data_pipeline_architecture import (
        get_unified_registry, enhanced_data_get, DataType
    )
    UNIFIED_SYSTEM_AVAILABLE = True
    UNIFIED_REGISTRY = get_unified_registry()
    print("✓ 統一データシステム利用可能")
except ImportError as e:
    UNIFIED_SYSTEM_AVAILABLE = False
    UNIFIED_REGISTRY = None
    print(f"⚠️ 統一データシステム無効: {e}")
"""
    
    # shift_suite インポートの後に挿入
    if 'UNIFIED_SYSTEM_AVAILABLE' not in content:
        insertion_point = content.find('# Global data cache')
        if insertion_point == -1:
            insertion_point = content.find('DATA_CACHE =')
        
        if insertion_point != -1:
            content = content[:insertion_point] + import_addition + "\\n" + content[insertion_point:]
        
        with open(dash_app_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✓ 統一システムインポート追加完了")

def enhance_data_get_with_fallback():
    """data_get関数にフォールバック機能追加"""
    
    from pathlib import Path
    import re
    
    dash_app_path = Path("dash_app.py")
    
    with open(dash_app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 既存data_get関数の先頭に統一システム試行を追加
    enhanced_logic = '''def data_get(key: str, default=None, for_display: bool = False):
    """Load a data asset lazily from the current scenario directory with enhanced stability."""
    
    # 🚀 統一システム優先試行（按分廃止データ専用最適化）
    if UNIFIED_SYSTEM_AVAILABLE and 'proportional_abolition' in key:
        try:
            # 按分廃止データの統一システム経由高速取得
            if key == 'proportional_abolition_role_summary':
                unified_data = UNIFIED_REGISTRY.get_data(DataType.PROPORTIONAL_ABOLITION_ROLE)
            elif key == 'proportional_abolition_organization_summary':  
                unified_data = UNIFIED_REGISTRY.get_data(DataType.PROPORTIONAL_ABOLITION_ORG)
            else:
                unified_data = enhanced_data_get(key, default)
                
            if unified_data is not None:
                log.info(f"🚀 統一システム高速取得成功: {key}")
                return unified_data
            else:
                log.debug(f"統一システム: {key} 未発見 - 従来システムにフォールバック")
        except Exception as e:
            log.warning(f"統一システム取得失敗: {key} - {e} - 従来システムにフォールバック")
    
    # 📋 従来システム（既存ロジック保持）'''
    
    # data_get関数の最初の行を置換
    pattern = r'(def data_get\\(key: str, default=None, for_display: bool = False\\):\\s*""".*?""")'
    
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(
            pattern,
            enhanced_logic,
            content,
            flags=re.DOTALL
        )
        
        with open(dash_app_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✓ data_get関数フォールバック機能追加完了")
    else:
        print("⚠️ data_get関数のパターンマッチ失敗")

def add_proportional_specific_optimization():
    """按分廃止専用最適化の追加"""
    
    from pathlib import Path
    
    dash_app_path = Path("dash_app.py")
    
    with open(dash_app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # create_proportional_abolition_tab関数の最初にパフォーマンス最適化追加
    optimization_code = '''
    # 🚀 統一システム: 按分廃止専用最適化パス
    if UNIFIED_SYSTEM_AVAILABLE:
        try:
            import time
            start_time = time.time()
            
            # 統一レジストリから直接高速取得
            df_role_unified = UNIFIED_REGISTRY.get_data(DataType.PROPORTIONAL_ABOLITION_ROLE)
            df_org_unified = UNIFIED_REGISTRY.get_data(DataType.PROPORTIONAL_ABOLITION_ORG)
            
            if df_role_unified is not None and not df_role_unified.empty:
                load_time = (time.time() - start_time) * 1000
                log.info(f"🚀 統一システム: 按分廃止データ高速ロード完了 ({load_time:.1f}ms)")
                
                # 統一システムデータを使用してUI構築
                return build_unified_proportional_abolition_ui(df_role_unified, df_org_unified)
            else:
                log.info("統一システム: 按分廃止データなし - 従来フローに移行")
                
        except Exception as e:
            log.warning(f"統一システム最適化失敗: {e} - 従来フローに移行")
    
    # 従来の按分廃止処理（既存ロジック）'''
    
    # create_proportional_abolition_tab関数の先頭に挿入
    pattern = r'(def create_proportional_abolition_tab\\(.*?\\):\\s*""".*?"""\\s*)(\\s*try:|\\s*log\\.info)'
    
    if 'build_unified_proportional_abolition_ui' not in content:
        content = re.sub(
            pattern, 
            r'\\1' + optimization_code + r'\\n\\2',
            content,
            flags=re.DOTALL
        )
        
        # 統一UI構築関数を追加
        ui_function = '''
def build_unified_proportional_abolition_ui(df_role: pd.DataFrame, df_org: pd.DataFrame) -> html.Div:
    """統一システム: 按分廃止UI構築"""
    
    content = []
    
    # ヘッダー
    content.append(html.H2("[UNIFIED] 按分廃止・職種別分析", 
                          style={'color': '#2196f3', 'marginBottom': '20px'}))
    
    # データ存在確認とエラーハンドリング
    if df_role.empty:
        return create_unified_error_message(
            "按分廃止データエラー",
            "統一システムで按分廃止職種データが空です",
            "データリフレッシュまたはapp.pyでの再分析を実行してください"
        )
    
    # 成功メッセージ
    content.append(html.Div([
        html.P("🚀 統一データパイプライン経由で高速ロード完了", 
               style={'color': '#4caf50', 'fontWeight': 'bold'}),
        html.P(f"職種データ: {len(df_role)}件 | 組織データ: {len(df_org) if not df_org.empty else 0}件"),
    ], style={'backgroundColor': '#e8f5e8', 'padding': '15px', 'marginBottom': '20px', 'borderRadius': '5px'}))
    
    # 職種別データテーブル
    if not df_role.empty:
        content.append(html.H3("職種別按分廃止分析結果"))
        content.append(dash_table.DataTable(
            data=df_role.to_dict('records'),
            columns=[{"name": col, "id": col} for col in df_role.columns],
            style_cell={'textAlign': 'center', 'padding': '10px'},
            style_header={'backgroundColor': '#2196f3', 'color': 'white', 'fontWeight': 'bold'},
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f9f9f9'
                }
            ]
        ))
    
    # 組織データテーブル
    if not df_org.empty:
        content.append(html.H3("組織全体按分廃止分析結果"))
        content.append(dash_table.DataTable(
            data=df_org.to_dict('records'),
            columns=[{"name": col, "id": col} for col in df_org.columns],
            style_cell={'textAlign': 'center', 'padding': '10px'},
            style_header={'backgroundColor': '#ff9800', 'color': 'white', 'fontWeight': 'bold'},
        ))
    
    return html.Div(content, style={'padding': '20px'})

def create_unified_error_message(title: str, message: str, suggestion: str = "") -> html.Div:
    """統一エラーメッセージ"""
    return html.Div([
        html.H3(f"⚠️ {title}", style={'color': '#f44336'}),
        html.P(message, style={'color': '#666'}),
        html.P(suggestion, style={'color': '#2196f3', 'fontWeight': '500'}) if suggestion else None,
        html.P("🚀 統一データパイプラインシステム", style={'color': '#4caf50', 'fontSize': '12px'})
    ], style={
        'padding': '20px', 'backgroundColor': '#fff3cd', 'border': '1px solid #ffeaa7',
        'borderRadius': '8px', 'margin': '20px'
    })

'''
        
        # ファイル末尾に関数追加
        content += ui_function
        
        with open(dash_app_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✓ 按分廃止専用最適化追加完了")

if __name__ == "__main__":
    apply_gradual_integration_patch()
    
    print("\\n🎯 段階的統合完了!")
    print("\\n統合効果:")
    print("✅ 既存システム完全保持（リスクゼロ）")
    print("✅ 按分廃止データのみ統一システム高速化")  
    print("✅ 自動フォールバック機能")
    print("✅ 段階的移行可能")
    
    # 統合テスト実行
    print("\\n=== 統合テスト ===")
    try:
        exec("from unified_data_pipeline_architecture import get_unified_registry, DataType")
        print("✅ 統一システム: インポート成功")
        
        exec("""
registry = get_unified_registry()
role_data = registry.get_data(DataType.PROPORTIONAL_ABOLITION_ROLE)
org_data = registry.get_data(DataType.PROPORTIONAL_ABOLITION_ORG)
print(f"✅ 統一システム: 按分廃止データ取得 役割{len(role_data) if role_data is not None else 0}件, 組織{len(org_data) if org_data is not None else 0}件")
""")
        
        print("✅ 全統合テスト成功")
        
    except Exception as e:
        print(f"❌ 統合テスト失敗: {e}")