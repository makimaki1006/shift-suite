#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
システムアーキテクチャ全体の詳細ログを追加
各コンポーネント間のデータフローを完全に追跡
"""

import re

def add_comprehensive_logging():
    """dash_app.pyに包括的なログを追加"""
    
    # 1. handle_file_upload の詳細ログ
    handle_file_upload_logging = '''
def handle_file_upload(contents, filename):
    """ZIPファイルアップロード処理のコールバック"""
    import json
    
    log.info("="*80)
    log.info("[SYSTEM FLOW] 1. FRONTEND -> CALLBACK LAYER")
    log.info("="*80)
    log.info(f"[handle_file_upload] ENTRY POINT")
    log.info(f"  - Function: handle_file_upload")
    log.info(f"  - Filename: {filename}")
    log.info(f"  - Contents type: {type(contents)}")
    log.info(f"  - Contents is None: {contents is None}")
    
    if contents:
        # コンテンツの詳細情報
        log.info(f"  - Contents length: {len(contents)}")
        log.info(f"  - Contents preview: {contents[:100]}...")
        
        # Base64フォーマットの確認
        if ',' in contents:
            header, data = contents.split(',', 1)
            log.info(f"  - Data header: {header}")
            log.info(f"  - Data length: {len(data)}")
        else:
            log.info(f"  - WARNING: No comma separator found in contents")
    
    log.info("[handle_file_upload] ========== UPLOAD STARTED ==========")
    
    if contents is None:
        log.info("[handle_file_upload] BRANCH: No contents")
        # デフォルトシナリオがある場合はそれを使用
        if CURRENT_SCENARIO_DIR:
            scenarios = [CURRENT_SCENARIO_DIR.name]
            log.info(f"[handle_file_upload] Using default scenario: {scenarios}")
            
            result = (
                None,
                [{'label': s, 'value': s} for s in scenarios],
                scenarios[0] if scenarios else None,
                {'display': 'block'}
            )
            
            log.info(f"[handle_file_upload] RETURN (default): {json.dumps(str(result)[:200])}")
            return result
            
        log.info("[handle_file_upload] No contents and no default scenario")
        result = (None, [], None, {'display': 'none'})
        log.info(f"[handle_file_upload] RETURN (empty): {result}")
        return result
    
    try:
        log.info("[handle_file_upload] BRANCH: Processing upload")
        log.info(f"[handle_file_upload] Starting to process upload for: {filename}")
        
        # ファイルタイプをチェック
        if not filename.lower().endswith('.zip'):
            log.warning(f"[handle_file_upload] Not a ZIP file: {filename}")
            result = (None, [], None, {'display': 'none'})
            log.info(f"[handle_file_upload] RETURN (not zip): {result}")
            return result
        
        # process_upload関数を呼び出し
        log.info("="*80)
        log.info("[SYSTEM FLOW] 2. CALLBACK -> PROCESSING LAYER")
        log.info("="*80)
        log.info(f"[handle_file_upload] Calling process_upload...")
        log.info(f"  - Input filename: {filename}")
        log.info(f"  - Input contents length: {len(contents)}")
        
        result = process_upload(contents, filename)
        
        log.info("="*80)
        log.info("[SYSTEM FLOW] 3. PROCESSING -> CALLBACK LAYER")
        log.info("="*80)
        log.info(f"[handle_file_upload] process_upload returned")
        log.info(f"  - Return type: {type(result)}")
        log.info(f"  - Is tuple: {isinstance(result, tuple)}")
        if isinstance(result, tuple):
            log.info(f"  - Tuple length: {len(result)}")
            log.info(f"  - Element types: {[type(x).__name__ for x in result]}")
        log.info(f"  - Return value preview: {str(result)[:500]}")
        
        if isinstance(result, tuple) and len(result) == 4:
            data, options, value, style = result
            log.info(f"[handle_file_upload] SUCCESS - Unpacked 4 values")
            log.info(f"  - data type: {type(data)}")
            log.info(f"  - options: {options}")
            log.info(f"  - value: {value}")
            log.info(f"  - style: {style}")
            
            log.info("="*80)
            log.info("[SYSTEM FLOW] 4. CALLBACK -> FRONTEND LAYER")
            log.info("="*80)
            log.info(f"[handle_file_upload] RETURN (success): Sending to frontend")
            return data, options, value, style
        else:
            # エラーの場合
            log.error(f"[handle_file_upload] UNEXPECTED result format")
            log.error(f"  - Expected: tuple of 4 elements")
            log.error(f"  - Got: {type(result)}")
            result = (None, [], None, {'display': 'none'})
            log.info(f"[handle_file_upload] RETURN (error): {result}")
            return result
            
    except Exception as e:
        log.error(f"[handle_file_upload] EXCEPTION occurred: {e}", exc_info=True)
        import traceback
        log.error(f"[handle_file_upload] Full traceback:\\n{traceback.format_exc()}")
        result = (None, [], None, {'display': 'none'})
        log.info(f"[handle_file_upload] RETURN (exception): {result}")
        return result
    finally:
        log.info(f"[handle_file_upload] ========== UPLOAD ENDED ==========")
        log.info("="*80)
'''

    # 2. process_upload の詳細ログ
    process_upload_logging = '''
    # 追加のログポイント：
    
    # ZIP展開部分
    log.info("[PROCESSING LAYER] ZIP extraction details:")
    log.info(f"  - ZIP size: {len(decoded)} bytes")
    log.info(f"  - Temp directory: {temp_dir_path}")
    
    # シナリオ検出部分
    log.info("[PROCESSING LAYER] Scenario detection:")
    for item in temp_dir_path.iterdir():
        log.info(f"  - Found: {item.name} (is_dir: {item.is_dir()})")
    
    # 返却値の構築
    log.info("[PROCESSING LAYER] Building return value:")
    log.info(f"  - Data dict keys: {list(result_data.keys()) if isinstance(result_data, dict) else 'N/A'}")
    log.info(f"  - Options count: {len(scenario_options)}")
    log.info(f"  - Selected value: {first_scenario}")
    log.info(f"  - Style: {style_dict}")
'''

    # 3. コールバック登録の確認
    callback_registration = '''
    # アプリケーション起動時
    log.info("="*80)
    log.info("[SYSTEM ARCHITECTURE] Callback Registration")
    log.info("="*80)
    
    # 各コールバックの登録状態を確認
    for callback in app.callback_map:
        log.info(f"Registered callback: {callback}")
'''

    print("包括的ログ追加スクリプト")
    print("=" * 60)
    print()
    print("以下のログを追加することで、システム全体のフローを追跡できます：")
    print()
    print("1. FRONTEND -> CALLBACK LAYER")
    print("   - ファイルアップロード時のデータ形式")
    print("   - Base64エンコーディングの確認")
    print()
    print("2. CALLBACK -> PROCESSING LAYER")
    print("   - process_upload への入力")
    print("   - パラメータの詳細")
    print()
    print("3. PROCESSING LAYER")
    print("   - ZIP解凍の詳細")
    print("   - ファイルシステム操作")
    print("   - シナリオ検出ロジック")
    print()
    print("4. PROCESSING -> CALLBACK LAYER")
    print("   - 返却値の形式")
    print("   - データ構造の確認")
    print()
    print("5. CALLBACK -> FRONTEND LAYER")
    print("   - Dashへの返却値")
    print("   - UI更新のトリガー")
    
    return handle_file_upload_logging

if __name__ == "__main__":
    add_comprehensive_logging()