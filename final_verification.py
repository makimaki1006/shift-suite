#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
タブコンテンツ表示修正の最終検証
"""

def verify_all_fixes():
    print("="*60)
    print("最終検証: タブコンテンツ表示修正")
    print("="*60)
    
    with open('dash_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    results = {
        'completed': [],
        'issues': []
    }
    
    # 1. update_sub_tabsのコールバック確認
    print("\n[1] update_sub_tabs コールバック")
    print("-"*40)
    
    # Check in the content directly
    if "@app.callback(\n    Output('sub-tabs-container', 'children'),\n    Input('main-tab-groups', 'value')" in content:
        print("[OK] @app.callback デコレータ存在")
        results['completed'].append("update_sub_tabs callback")
    else:
        print("[NG] @app.callbackデコレータなし")
        results['issues'].append("update_sub_tabs callback missing")
    
    # 2. update_tab_visibilityの修正確認
    print("\n[2] update_tab_visibility修正")
    print("-"*40)
    
    if "Input('sub-tabs', 'value')" in content:
        print("[OK] sub-tabsをInput追加済み")
        results['completed'].append("sub-tabs Input added")
    else:
        print("[NG] sub-tabsがInputにない")
        results['issues'].append("sub-tabs Input missing")
    
    # 3. data-loaded出力の確認
    print("\n[3] data-loaded store更新")
    print("-"*40)
    
    if "Output('data-loaded', 'data')" in content:
        print("[OK] data-loaded出力追加")
        results['completed'].append("data-loaded output")
    else:
        print("[NG] data-loadedへの出力なし")
        results['issues'].append("data-loaded output missing")
    
    # 4. return文の更新確認
    print("\n[4] return文の更新")
    print("-"*40)
    
    return_count = content.count("return kpi_data, create_main_ui_tabs(), True")
    if return_count >= 1:
        print(f"[OK] {return_count}箇所でdata-loaded=Trueを返却")
        results['completed'].append(f"{return_count} return statements updated")
    else:
        print("[NG] return文が更新されていない")
        results['issues'].append("return statements not updated")
    
    # 5. 結果サマリー
    print("\n" + "="*60)
    print("検証結果サマリー")
    print("="*60)
    
    print(f"\n完了した修正: {len(results['completed'])}件")
    for fix in results['completed']:
        print(f"  [OK] {fix}")
    
    if results['issues']:
        print(f"\n残っている問題: {len(results['issues'])}件")
        for issue in results['issues']:
            print(f"  [NG] {issue}")
    else:
        print("\n[SUCCESS] すべての修正が正常に適用されています！")
    
    print("\n[次のステップ]")
    print("1. python dash_app.py でアプリ起動")
    print("2. ブラウザで http://localhost:8050 にアクセス")
    print("3. タブをクリックしてコンテンツが表示されることを確認")
    
    return len(results['issues']) == 0

if __name__ == "__main__":
    success = verify_all_fixes()
    exit(0 if success else 1)