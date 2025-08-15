# 夜勤→明け番連続勤務のlong_df表現とNeed計算への影響分析レポート

## 調査概要

analysis_results (17).zipのlong_dfデータにおける夜勤から明け番への連続勤務の表現方法と、それがNeed計算に与える問題を詳細に調査しました。

## 1. 連続勤務パターンの発見

### 調査対象データ
- **ファイル**: 勤務表　勤務時間_トライアル.xlsx
- **期間**: 2025年6月1日-30日（30日間）
- **発見された連続勤務パターン**: **91件**

### 役職別分布
| 役職 | 連続勤務パターン数 |
|------|-------------------|
| 3F介護 | 31件 |
| 4F介護 | 25件 |
| 3F副主任 | 7件 |
| 3F主任 | 6件 |
| 生活援助課統括主任・4F主任 | 6件 |
| 2F副主任 | 6件 |
| 生活援助課統括主任・4F主任 | 5件 |
| 2F介護 | 5件 |

## 2. 連続勤務の表現方法

### 元データでの表現
```
職員: 花田
6月4日: 夜 (夜勤シフト)
6月5日: 明 (明け番シフト)
```

### long_df変換後の表現
```
staff_name | date       | time  | shift_code | role     | employment
-----------|------------|-------|------------|----------|----------
花田       | 2025-06-04 | 23:45 | 夜         | 介護     | 正社員
花田       | 2025-06-05 | 00:00 | 明         | 介護     | 正社員
花田       | 2025-06-05 | 00:15 | 明         | 介護     | 正社員
```

## 3. 問題の特定

### 3.1 連続勤務の分離問題
- **実際**: 1人が23:00-10:00まで連続で勤務
- **システム認識**: 2つの独立したシフト記録
  - 夜勤記録（6月4日 23:45）
  - 明け番記録（6月5日 00:00）

### 3.2 職員レベルでの追跡不可能
- 同一職員の連続勤務という情報が失われる
- 日付境界（0:00）で記録が分離される
- シフトコードの変化（夜→明）により関連性が見えなくなる

### 3.3 時系列での不整合
- 夜勤: 2025-06-04 23:45 で記録終了
- 明け番: 2025-06-05 00:00 で記録開始
- 15分間のギャップが発生（23:45-00:00）
- 実際は連続勤務なのに断続的に見える

## 4. Need計算への深刻な影響

### 4.1 ダブルカウンティング問題
**実際の状況**:
- 1人の職員が夜勤→明け番で連続勤務
- 実質的には1人分の労働力

**システムの解釈**:
- 夜勤担当者: 1人（23:59まで）
- 明け番担当者: 1人（00:00から）
- 合計: 2人分の労働力として計算

### 4.2 Need計算の過大評価
```python
# 誤った計算例
time_slot_23_45 = {
    "staff_count": 1,  # 夜勤者（花田）
    "need": 1
}

time_slot_00_00 = {
    "staff_count": 1,  # 明け番者（花田）- 同じ人！
    "need": 1
}

# システムは合計2人いると誤認
total_perceived_staff = 2
actual_staff = 1  # 実際は1人
```

### 4.3 人員充足率の歪み
- **計算上**: 人員充足率 = 200%（2人/1人）
- **実際**: 人員充足率 = 100%（1人/1人）
- **結果**: 人員不足の隠蔽、過剰配置の錯覚

## 5. 具体的な事例分析

### 事例1: 花田職員（生活援助課統括主任・4F主任）
```
2025-06-04 夜勤 → 2025-06-05 明け番
2025-06-08 夜勤 → 2025-06-09 明け番
2025-06-12 夜勤 → 2025-06-13 明け番
2025-06-16 夜勤 → 2025-06-17 明け番
2025-06-24 夜勤 → 2025-06-25 明け番
```

各ケースで以下の問題が発生:
1. 連続勤務が2つのシフトとして記録
2. 同一職員のダブルカウンティング
3. Need計算の精度低下

## 6. システムへの影響と問題点

### 6.1 データ構造の根本的欠陥
- long_df形式では連続勤務の概念が存在しない
- 各レコードは独立したタイムスロットとして処理
- 職員の勤務継続性情報が失われる

### 6.2 Need計算アルゴリズムの限界
```python
# 現在のアルゴリズム（問題あり）
def calculate_need(date, time_slot):
    staff_count = len(long_df[
        (long_df['date'] == date) & 
        (long_df['time'] == time_slot)
    ])
    return staff_count  # 連続勤務を考慮しない
```

### 6.3 運用上の問題
- シフト計画の精度低下
- 人員配置の最適化阻害
- 労務管理の効率性低下
- コスト計算の不正確性

## 7. 解決策の提案

### 7.1 連続勤務識別機能の追加
```python
def identify_continuous_shifts(long_df):
    """連続勤務パターンを識別"""
    continuous_shifts = []
    for staff in long_df['staff_name'].unique():
        staff_data = long_df[long_df['staff_name'] == staff].sort_values(['date', 'time'])
        
        # 夜勤→明け番パターンを検出
        for i in range(len(staff_data) - 1):
            current = staff_data.iloc[i]
            next_shift = staff_data.iloc[i + 1]
            
            if (current['shift_code'] == '夜' and 
                next_shift['shift_code'] == '明' and
                is_consecutive_day(current['date'], next_shift['date'])):
                
                continuous_shifts.append({
                    'staff': staff,
                    'start_date': current['date'],
                    'end_date': next_shift['date'],
                    'type': 'night_to_morning'
                })
    
    return continuous_shifts
```

### 7.2 Need計算の修正
```python
def calculate_need_with_continuous_shifts(date, time_slot, continuous_shifts):
    """連続勤務を考慮したNeed計算"""
    regular_staff = get_regular_staff(date, time_slot)
    
    # 連続勤務者の重複を除去
    continuous_staff = get_continuous_shift_staff(date, time_slot, continuous_shifts)
    
    # 重複除去後の実際の人員数
    actual_staff_count = len(set(regular_staff + continuous_staff))
    
    return actual_staff_count
```

### 7.3 データモデルの拡張
```python
class ContinuousShift:
    def __init__(self, staff_name, start_datetime, end_datetime, shift_types):
        self.staff_name = staff_name
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.shift_types = shift_types  # ['夜', '明']
        self.duration = end_datetime - start_datetime
```

## 8. 結論

### 8.1 重要な発見
1. **91件の連続勤務パターン**が1ヶ月間で確認された
2. **全ての連続勤務**でダブルカウンティング問題が発生
3. **Need計算の根本的な不正確性**が判明

### 8.2 影響の深刻度
- **高**: Need計算の信頼性に直接影響
- **高**: 人員配置の最適化を阻害
- **中**: 運用コストの増加要因
- **中**: データ分析の精度低下

### 8.3 対応の緊急性
連続勤務のダブルカウンティングは、シフト分析システムの根幹に関わる問題であり、**即座の対応が必要**です。Need計算の正確性確保は、適切な人員配置と労務管理の基盤となるためです。

## 9. 次のアクションアイテム

1. **連続勤務検出機能の実装**（優先度: 高）
2. **Need計算アルゴリズムの修正**（優先度: 高）
3. **データ検証機能の追加**（優先度: 中）
4. **運用テストの実施**（優先度: 中）
5. **ドキュメントの更新**（優先度: 低）

---

**報告書作成日**: 2025年7月16日  
**調査対象**: analysis_results (17).zip long_dfデータ  
**調査期間**: 2025年6月1日-30日  
**発見された問題**: 91件の連続勤務ダブルカウンティング