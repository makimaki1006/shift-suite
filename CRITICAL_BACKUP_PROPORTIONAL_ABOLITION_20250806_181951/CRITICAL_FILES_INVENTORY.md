# 按分廃止プロジェクト - 重要ファイル一覧表

## 作成日時: 2025-08-06 18:19:51

---

## 🎯 按分計算関連の核心ファイル

### 1. proportional_calculator.py
**場所**: `shift_suite/tasks/proportional_calculator.py`  
**機能**: 按分計算の核心ロジック  
**重要度**: ★★★★★ (最高)  
**影響範囲**: 全シスてムの不足計算

**主要関数**:
- `ProportionalCalculator.calculate_proportional_shortage()` (行44-48)
- `calculate_proportional_shortage()` (行252-254) - 外部公開関数

### 2. shortage.py  
**場所**: `shift_suite/tasks/shortage.py`  
**機能**: 過不足分析メインモジュール  
**重要度**: ★★★★★ (最高)  
**影響範囲**: 全システムの分析結果

**按分関連箇所**:
- `from .proportional_calculator import calculate_proportional_shortage` (行23)
- メイン処理での按分実行箇所(要詳細調査)

### 3. time_axis_shortage_calculator.py
**場所**: `shift_suite/tasks/time_axis_shortage_calculator.py`  
**機能**: 時間軸での不足計算  
**重要度**: ★★★★ (高)  
**影響範囲**: 時系列分析結果

---

## 🔄 修正対象の特定

### Phase 1対象: 単一職種詳細分析
**ターゲット**: 「介護」職種のみを按分廃止  
**修正ファイル**: 
1. `proportional_calculator.py` - 職種別直接計算ロジック追加
2. `shortage.py` - 按分vs直接計算の選択ロジック追加

### Phase 2対象: 主要職種拡張  
**ターゲット**: 介護・看護師・運転士の3職種
**修正ファイル**: 
1. 上記2ファイルの拡張
2. 新規職種別計算モジュールの追加検討

---

## ⚠️ 依存関係マップ

```
dash_app.py
    ↓ 
shortage.py  
    ↓
proportional_calculator.py (←ここを修正)
    ↓
utils.py, constants.py
```

**影響度評価**: proportional_calculator.py修正 → shortage.py → dash_app.py全体に波及

---

## 🛡️ バックアップ検証完了項目

- ✅ proportional_calculator.py (完全バックアップ済み)
- ✅ shortage.py (完全バックアップ済み) 
- ✅ time_axis_shortage_calculator.py (完全バックアップ済み)
- ✅ utils.py (ユーティリティ関数バックアップ済み)
- ✅ constants.py (定数定義バックアップ済み)
- ✅ app.py (メインアプリバックアップ済み)
- ✅ dash_app.py (ダッシュボードバックアップ済み)

---

**重要**: このファイル一覧は按分廃止プロジェクトの作業対象を明確化します。  
**修正前に必ず全ファイルの動作を確認してください。**