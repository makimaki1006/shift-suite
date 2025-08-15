# 運用・保守マニュアル

**対象システム**: Shift-Suite Phase 2/3.1  
**対象バージョン**: 1.0  
**作成日**: 2025年08月03日

## 📋 はじめに

本マニュアルは、Phase 2/3.1システムの日常運用と保守作業の手順を記載しています。

## 🔄 日常運用手順

### 1. システム状態確認（毎日）

#### 基本チェック
```bash
# システム稼働確認
python3 A3_LIGHTWEIGHT_MONITORING.py

# エラーログ確認
python3 A3_SIMPLE_ERROR_LOG_MONITOR.py

# パフォーマンス確認
python3 A3_SIMPLE_PERFORMANCE_MONITOR.py
```

#### 確認項目
- [ ] Phase 2/3.1ファイルの存在
- [ ] SLOT_HOURS使用数の確認（Phase 2: 4箇所、Phase 3.1: 1箇所）
- [ ] エラーログの確認
- [ ] 処理性能の確認

### 2. データ品質チェック（週次）

```bash
# データ品質監視
python3 A3_DATA_QUALITY_MONITOR_FIXED.py
```

#### 重要指標
- **計算精度**: SLOT_HOURS変換の正確性
- **数値整合性**: 670時間基準値との整合性
- **データ完全性**: 欠損・異常値の有無

### 3. 品質保証テスト（週次）

```bash
# 自動テスト実行
python3 B1_QUALITY_ASSURANCE_FRAMEWORK.py
```

#### 合格基準
- **クリティカルテスト**: 100%成功必須
- **全体合格率**: 95%以上推奨
- **改善機会**: 継続的に発見・実装

## 🚨 アラート対応手順

### 1. Critical アラート（即座対応）

#### Phase 2 SLOT_HOURS不足
```bash
# 状況確認
grep -n "* SLOT_HOURS" shift_suite/tasks/fact_extractor_prototype.py

# 期待値: 4箇所以上
# 不足の場合は即座修正
```

#### Phase 3.1 SLOT_HOURS不足
```bash
# 状況確認  
grep -n "* SLOT_HOURS" shift_suite/tasks/lightweight_anomaly_detector.py

# 期待値: 1箇所以上
# 不足の場合は即座修正
```

### 2. 重要ファイル欠損
```bash
# バックアップから復旧
cp COMPLETE_BACKUP_*/shift_suite/tasks/fact_extractor_prototype.py shift_suite/tasks/
cp COMPLETE_BACKUP_*/shift_suite/tasks/lightweight_anomaly_detector.py shift_suite/tasks/

# 整合性確認
python3 A3_LIGHTWEIGHT_MONITORING.py
```

### 3. 数値異常（670時間逸脱）
```bash
# 原因調査
python3 A3_DATA_QUALITY_MONITOR_FIXED.py

# 計算過程の検証
python3 B1_QUALITY_ASSURANCE_FRAMEWORK.py
```

## 🔧 定期保守作業

### 毎週の作業

#### 1. ログローテーション
```bash
# 古いログファイルのアーカイブ
cd logs
tar -czf archive_$(date +%Y%m%d).tar.gz *.log
rm *.log.$(date -d "7 days ago" +%Y%m%d)
```

#### 2. パフォーマンス分析
```bash
# 週次パフォーマンスレポート
python3 A3_SIMPLE_PERFORMANCE_MONITOR.py > weekly_performance_$(date +%Y%m%d).txt
```

### 毎月の作業

#### 1. 包括的品質レビュー
```bash
# 月次品質レポート生成
python3 A3_DATA_QUALITY_MONITOR_FIXED.py
python3 B1_QUALITY_ASSURANCE_FRAMEWORK.py

# 改善機会の評価
# → 継続的改善計画への反映
```

#### 2. バックアップ検証
```bash
# バックアップの完全性確認
python3 -c "
import os
from pathlib import Path
backup_dirs = [d for d in Path('.').iterdir() if d.name.startswith('COMPLETE_BACKUP_')]
latest_backup = max(backup_dirs, key=lambda x: x.stat().st_mtime)
print(f'最新バックアップ: {latest_backup}')
# 重要ファイルの存在確認
critical_files = [
    'shift_suite/tasks/fact_extractor_prototype.py',
    'shift_suite/tasks/lightweight_anomaly_detector.py'
]
for file in critical_files:
    if (latest_backup / file).exists():
        print(f'✓ {file}')
    else:
        print(f'✗ {file} - 要対応')
"
```

## 🔍 トラブルシューティング

### よくある問題と対処法

#### 1. 計算結果が2倍になる
**原因**: SLOT_HOURS乗算の欠落
```bash
# 確認
grep -c "* SLOT_HOURS" shift_suite/tasks/fact_extractor_prototype.py
# 結果が4未満の場合は修正が必要

# 対処: バックアップから復旧または手動修正
```

#### 2. パフォーマンス劣化
**原因**: 大量データ処理、依存関係問題
```bash
# 診断
python3 A3_SIMPLE_PERFORMANCE_MONITOR.py

# 対処
# - データ量の確認
# - 依存関係の更新
# - システムリソースの確認
```

#### 3. 数値の不整合
**原因**: 計算ロジックの変更、データ破損
```bash
# 診断
python3 A3_DATA_QUALITY_MONITOR_FIXED.py

# 対処
# - 計算過程の詳細確認
# - 元データの検証
# - 必要に応じてデータ再処理
```

## 📈 継続的改善

### 改善機会の特定
- **週次品質レビュー**で発見された課題
- **ユーザーフィードバック**からの要望
- **技術的負債**の蓄積状況

### 改善の実装プロセス
1. **問題・機会の特定**
2. **影響範囲の分析**
3. **解決案の設計**
4. **テスト計画の策定**
5. **段階的実装**
6. **効果測定**

### 改善の評価基準
- **技術的価値**: 精度向上、性能改善
- **ビジネス価値**: 運用効率、意思決定支援
- **ユーザー価値**: 使いやすさ、信頼性

## 📞 エスカレーション

### 連絡先・責任者

| 事象レベル | 対応者 | 連絡方法 | 対応時間 |
|-----------|--------|----------|----------|
| Critical | システム管理者 | 即座連絡 | 15分以内 |
| High | 運用責任者 | 2時間以内 | 1営業日以内 |
| Medium | 担当チーム | 1営業日以内 | 3営業日以内 |

### エスカレーション基準
- **Critical**: サービス停止、データ破損
- **High**: 機能障害、精度問題
- **Medium**: 性能劣化、軽微な不具合

## 📋 チェックリスト

### 日次点検
- [ ] システム稼働状況
- [ ] エラーログ確認
- [ ] アラート状況
- [ ] バックアップ状況

### 週次点検
- [ ] データ品質監視
- [ ] パフォーマンス分析
- [ ] 品質保証テスト
- [ ] 改善機会の評価

### 月次点検
- [ ] 包括的品質レビュー
- [ ] バックアップ検証
- [ ] 継続的改善計画の更新
- [ ] ドキュメント更新

---
*本マニュアルは実際の運用経験に基づき、継続的に改善されます。*

**緊急時連絡先**: [運用責任者情報]  
**最終更新**: 2025年08月03日
