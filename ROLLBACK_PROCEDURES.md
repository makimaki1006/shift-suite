# Need積算修正 ロールバック手順書

**作成日**: 2025年8月7日  
**バックアップディレクトリ**: `BACKUP_NEED_ORIGINAL_20250807_142246`  
**目的**: Need積算修正で問題が発生した場合の確実な復旧手順

## 🚨 緊急時連絡フロー

### 即座に実行すべき判断基準
以下のいずれかが発生した場合、**即座にロールバックを実行**：

1. **過不足分析結果が異常値**
   - 組織全体で1日100時間超の不足または過多
   - 介護系職種で1日50時間超の極端な値

2. **システムエラー**
   - Needファイル読み込みエラー
   - 過不足分析プロセスの異常停止
   - ダッシュボード表示異常

3. **現場からの緊急フィードバック**
   - 「修正後の数字が全く現実的でない」
   - 「以前より悪化した」

## 🔄 ロールバック手順

### Phase 1: 緊急停止 (5分以内)

```bash
# 1. 現在のNeedファイルを一時退避
cd "C:\ShiftAnalysis\extracted_results\out_p25_based"
mkdir "TEMP_NEW_NEED_FILES_$(date +%Y%m%d_%H%M%S)"
move need_per_date_slot_role_*.parquet "TEMP_NEW_NEED_FILES_*/"
```

### Phase 2: バックアップファイルの復旧 (10分以内)

```bash
# 2. バックアップファイルを本番環境に復元
cd "C:\ShiftAnalysis"
copy "BACKUP_NEED_ORIGINAL_20250807_142246\need_per_date_slot_role_*.parquet" "extracted_results\out_p25_based\"
```

### Phase 3: 復旧後検証 (15分以内)

```bash
# 3. 復旧検証スクリプト実行
cd "C:\ShiftAnalysis"
python rollback_verification.py
```

## 📝 復旧検証チェックリスト

### 必須確認項目
- [ ] 9つのNeedファイルが正常に復元された
- [ ] ファイルサイズが元の値と一致している  
- [ ] 組織全体過不足分析が正常実行される
- [ ] ダッシュボードが正常表示される
- [ ] 修正前のベースライン値に戻っている

### データ整合性確認
- [ ] 介護系職種のNeed/実配置比率が0.09-0.54倍に戻っている
- [ ] 組織全体で22.7時間/日の配置過多状態に戻っている
- [ ] 各職種の過不足値がベースラインと一致している

## ⚠️ ロールバック後の対応

### 1. 問題原因の調査
- 修正アルゴリズムの問題点特定
- テストデータでの再検証
- 調整係数の見直し

### 2. 現場への説明
- ロールバック実施の報告
- 問題発生原因の簡潔な説明  
- 次回修正計画の提示

### 3. 再修正の準備
- 問題箇所の修正
- より慎重なテスト実施
- 段階的適用の検討

## 🔧 ロールバック実行スクリプト

以下のPythonスクリプトを`rollback_verification.py`として保存：

```python
#!/usr/bin/env python3
"""
Need積算修正ロールバック後の検証スクリプト
"""
import pandas as pd
from pathlib import Path
import json

def verify_rollback():
    scenario_dir = Path('extracted_results/out_p25_based')
    
    # 1. Needファイル存在確認
    need_files = list(scenario_dir.glob('need_per_date_slot_role_*.parquet'))
    print(f'Needファイル数: {len(need_files)} (期待値: 9)')
    
    if len(need_files) != 9:
        print('❌ ERROR: Needファイル数が不正')
        return False
    
    # 2. 組織分析実行テスト
    try:
        from comprehensive_organizational_shortage_analyzer import run_comprehensive_organizational_analysis
        result = run_comprehensive_organizational_analysis()
        
        if result:
            daily_diff = result['detailed_results'][0]['daily_difference']
            print(f'組織全体日次差分: {daily_diff:.1f}時間/日')
            
            # ベースライン値(-22.7時間/日)との比較
            if abs(daily_diff + 22.7) < 2.0:  # 2時間以内の誤差
                print('✅ OK: ベースライン値に復旧')
                return True
            else:
                print('❌ ERROR: ベースライン値と大きく乖離')
                return False
    
    except Exception as e:
        print(f'❌ ERROR: 分析実行失敗 - {e}')
        return False

if __name__ == "__main__":
    success = verify_rollback()
    print(f'\\nロールバック検証結果: {"成功" if success else "失敗"}')
```

## 📞 緊急連絡先

**システム管理者**: [連絡先を記入]  
**現場責任者**: [連絡先を記入]  
**技術担当者**: [連絡先を記入]

## 📊 ロールバック履歴

| 実行日時 | 理由 | 実行者 | 復旧時間 | 備考 |
|---------|------|--------|----------|------|
| [記録用] | [記録用] | [記録用] | [記録用] | [記録用] |

---

**重要**: このロールバック手順書は緊急時用です。実行前に可能な限り現場責任者との確認を取ってください。