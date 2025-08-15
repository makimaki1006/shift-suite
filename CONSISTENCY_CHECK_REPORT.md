# 修正一貫性チェック報告書

## 🔍 **問題の特定**

### **最新コミット分析**
- **コミット**: "Fix critical leave code recognition issues" (2025-07-23)
- **修正ファイル**: `shift_suite/tasks/io_excel.py`, `shift_suite/tasks/utils.py`
- **修正内容**: 休暇コード認識ロジックの修正

### **現在の修正状況**
```
修正済み: shift_suite/tasks/utils.py
新関数: apply_rest_exclusion_filter(exclude_leave_records: bool = False)
新パラメータ: for_display: bool = False, exclude_leave_records: bool = False
```

### **一貫性問題の発見**
```
✅ utils.py: 新パラメータ対応済み
❌ dash_app.py: 古いシグネチャで呼び出し
❌ app.py: 修正状況不明
❌ 他の関連ファイル: 未確認
```

---

## 🚨 **具体的な不整合**

### **1. dash_app.py の問題**
```python
# 現在の呼び出し (行2045, 2055, 2065)
df = apply_rest_exclusion_filter(df, f"data_get({key})", for_display=for_display)

# utils.py の新シグネチャ
def apply_rest_exclusion_filter(df, context="unknown", for_display=False, exclude_leave_records=False)
```

**問題**: `exclude_leave_records` パラメータが渡されていない

### **2. 潜在的な影響**
```
- 休暇データの処理が部分的にしか修正されていない
- dash_app.py では旧ロジックが動作
- io_excel.py では新ロジックが動作  
- データの不整合が発生する可能性
```

---

## 🎯 **必要な修正**

### **即座修正必要事項**
1. **dash_app.py の呼び出し修正**
2. **app.py の確認・修正**  
3. **他の関連ファイルの一貫性確認**
4. **テストによる動作確認**

### **修正範囲の特定**
```
要確認ファイル:
□ dash_app.py (確認済み - 修正必要)
□ app.py
□ その他 apply_rest_exclusion_filter を使用するファイル
```

---

## 📋 **次のアクション**

### **慎重な修正手順**
1. 全ての `apply_rest_exclusion_filter` 使用箇所を特定
2. 各ファイルでの呼び出しパラメータを確認
3. 新シグネチャに合わせて統一修正
4. 修正後の動作テスト実行
5. 休暇データ処理の一貫性確認

### **修正の優先度**
```
Priority 1: dash_app.py の呼び出し修正
Priority 2: app.py の確認・修正
Priority 3: 関連ファイル全体の一貫性確保
Priority 4: 統合テスト実行
```

**この一貫性問題を解決することで、システム全体で統一された休暇データ処理を実現します。**