"""
完全復旧のための関数マッピングテーブル
オリジナル（shift-suite-main/dash_app.py）から現在のapp_callbacks.pyへのマッピング
"""

FUNCTION_MAPPING = {
    # タブ関数マッピング
    'create_overview_tab': {
        'original_location': 'L2106-2488',
        'current_location': 'L3855-3991',
        'status': 'partial',  # partial/empty/missing
        'features': ['基本KPI表示'],
        'missing_features': ['エグゼクティブサマリー', '全タブサマリー', 'アラート', 'シナジー分析']
    },
    
    'create_heatmap_tab': {
        'original_location': 'L2490-2580',
        'current_location': 'L3487-3570',
        'status': 'empty',
        'features': [],
        'missing_features': ['px.imshow実装', 'カラーマップ選択', '時系列フィルター', 'ズーム機能']
    },
    
    'create_shortage_tab': {
        'original_location': 'L2613-2730',
        'current_location': 'L3571-3625',
        'status': 'partial',
        'features': ['職種別棒グラフ', '雇用形態別棒グラフ'],
        'missing_features': ['ヒートマップ表示', 'Top3表示', 'AI因子分析']
    },
    
    'create_fatigue_tab': {
        'original_location': 'L2731-2889',
        'current_location': 'L3637-3657',
        'status': 'partial',
        'features': ['基本棒グラフ'],
        'missing_features': ['3D散布図', 'リスクレベル分類', '高リスク者アラート', 'KPIカード']
    },
    
    'create_fairness_tab': {
        'original_location': 'L3534-3697',
        'current_location': 'L3660-3669',
        'status': 'empty',
        'features': [],
        'missing_features': ['6種類の可視化', '散布図マトリックス', 'ヒートマップ', 'レーダーチャート', 'ランキング']
    },
    
    'create_leave_analysis_tab': {
        'original_location': 'L2890-3081',
        'current_location': 'L3672-3679',
        'status': 'empty',
        'features': [],
        'missing_features': ['勤務予定推移', '日別内訳', '曜日・月期間別', '集中日分析']
    },
    
    'create_cost_analysis_tab': {
        'original_location': 'L3084-3115',
        'current_location': 'L3682-3691',
        'status': 'empty',
        'features': [],
        'missing_features': ['動的シミュレーション', 'RadioItems切り替え', 'リアルタイム計算']
    },
    
    'create_hire_plan_tab': {
        'original_location': 'L3118-3198',
        'current_location': 'L3694-3701',
        'status': 'empty',
        'features': [],
        'missing_features': ['必要FTE計算', '採用戦略提案', '最適採用計画']
    },
    
    'create_forecast_tab': {
        'original_location': 'L3395-3531',
        'current_location': 'L3702-3709',
        'status': 'empty',
        'features': [],
        'missing_features': ['Prophet予測', '信頼区間', '詳細データテーブル']
    },
    
    'create_gap_analysis_tab': {
        'original_location': 'L3700-3729',
        'current_location': 'L3710-3717',
        'status': 'empty',
        'features': [],
        'missing_features': ['乖離ヒートマップ', 'サマリーテーブル']
    },
    
    'create_summary_report_tab': {
        'original_location': 'L3732-3747',
        'current_location': 'L3718-3725',
        'status': 'empty',
        'features': [],
        'missing_features': ['Markdown生成', '自動要約']
    },
    
    'create_ppt_report_tab': {
        'original_location': 'L3750-3763',
        'current_location': 'L3726-3733',
        'status': 'empty',
        'features': [],
        'missing_features': ['PowerPoint生成', 'ボタンハンドラ']
    },
    
    'create_individual_analysis_tab': {
        'original_location': 'L3766-3807',
        'current_location': 'L3734-3741',
        'status': 'empty',
        'features': [],
        'missing_features': ['スタッフ選択', 'シナジー分析4種', '相関マトリックス', 'キャッシュ']
    },
    
    'create_team_analysis_tab': {
        'original_location': 'L3810-3858',
        'current_location': 'L3742-3749',
        'status': 'empty',
        'features': [],
        'missing_features': ['チーム構成', 'ダイナミクス分析', 'パフォーマンス指標', 'カバー率']
    },
    
    'create_blueprint_analysis_tab': {
        'original_location': 'L3861-4010',
        'current_location': 'L3750-3761',
        'status': 'empty',
        'features': [],
        'missing_features': ['暗黙知分析', '客観的事実', '統合分析', 'インタラクティブタブ']
    },
    
    'create_ai_analysis_tab': {
        'original_location': 'L7404-7500+',
        'current_location': 'L3762-3773',
        'status': 'empty',
        'features': [],
        'missing_features': ['AIインサイト生成', '自動改善提案']
    },
    
    'create_fact_book_tab': {
        'original_location': 'not_found',
        'current_location': 'L3774-3782',
        'status': 'empty',
        'features': [],
        'missing_features': ['統合レポート', '包括的分析']
    },
    
    'create_mind_reader_tab': {
        'original_location': 'not_found',
        'current_location': 'L3783-3792',
        'status': 'empty',
        'features': [],
        'missing_features': ['メタ分析', 'パターン検出']
    },
    
    'create_export_tab': {
        'original_location': 'not_found',
        'current_location': 'L3793-3854',
        'status': 'empty',
        'features': [],
        'missing_features': ['Excel出力', 'CSV出力', 'PDF生成']
    },
    
    'create_optimization_tab': {
        'original_location': 'not_found',
        'current_location': 'L3628-3634',
        'status': 'empty',
        'features': [],
        'missing_features': ['最適化分析']
    }
}

# ヘルパー関数マッピング
HELPER_FUNCTION_MAPPING = {
    'safe_figure_creation': {
        'original_location': 'L1636-1651',
        'current_location': 'L1635-1651',
        'status': 'exists'
    },
    'create_metric_card': {
        'original_location': 'L1610-1633',
        'current_location': 'L1610-1633',
        'status': 'exists'
    },
    'create_kpi_visualizations': {
        'original_location': 'L1508-1570',
        'current_location': 'L1508-1570',
        'status': 'exists'
    },
    'collect_all_tabs_summary': {
        'original_location': 'not_in_original',
        'current_location': 'L1653-1745',
        'status': 'exists'
    },
    'generate_executive_summary': {
        'original_location': 'not_in_original',
        'current_location': 'L1747-1781',
        'status': 'exists'
    },
    'create_tabs_quick_access': {
        'original_location': 'not_in_original',
        'current_location': 'L1783-1823',
        'status': 'exists'
    }
}

def get_restoration_priority():
    """復旧優先度を返す"""
    priority = [
        # Phase 1: Critical Visualizations
        'create_heatmap_tab',
        'create_shortage_tab',
        'create_fairness_tab',
        
        # Phase 2: Advanced Analytics
        'create_fatigue_tab',
        'create_leave_analysis_tab',
        'create_cost_analysis_tab',
        'create_hire_plan_tab',
        
        # Phase 3: Strategic Features
        'create_blueprint_analysis_tab',
        'create_individual_analysis_tab',
        'create_team_analysis_tab',
        'create_forecast_tab',
        
        # Phase 4: Reporting
        'create_gap_analysis_tab',
        'create_summary_report_tab',
        'create_ppt_report_tab',
        'create_export_tab',
        
        # Phase 5: AI & Integration
        'create_overview_tab',
        'create_ai_analysis_tab',
        'create_fact_book_tab',
        'create_mind_reader_tab',
        'create_optimization_tab'
    ]
    return priority

def calculate_restoration_progress():
    """復旧進捗を計算"""
    total_features = 0
    implemented_features = 0
    
    for func_name, details in FUNCTION_MAPPING.items():
        total_features += len(details['features']) + len(details['missing_features'])
        implemented_features += len(details['features'])
    
    if total_features == 0:
        return 0
    
    return (implemented_features / total_features) * 100

if __name__ == "__main__":
    progress = calculate_restoration_progress()
    print(f"現在の復旧進捗: {progress:.1f}%")
    print(f"実装済みタブ: {sum(1 for f in FUNCTION_MAPPING.values() if f['status'] != 'empty')}/21")
    print(f"完全実装タブ: {sum(1 for f in FUNCTION_MAPPING.values() if not f['missing_features'])}/21")