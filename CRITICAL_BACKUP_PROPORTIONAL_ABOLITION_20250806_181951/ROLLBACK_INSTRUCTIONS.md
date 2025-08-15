# 緊急ロールバック手順書
## 按分廃止プロジェクト失敗時の完全復旧手順

### 作成日時: 2025-08-06 18:19:51
### バックアップ対象: 按分計算ロジック廃止前の完全システム

---

## 🚨 緊急復旧手順（システム破綻時）

### STEP 1: 即座停止
```bash
# 現在実行中のプロセスを全て停止
pkill -f python
pkill -f streamlit
pkill -f dash
```

### STEP 2: 破損ファイル退避
```bash
# 失敗したファイルを証拠保全
FAILURE_DIR="FAILURE_EVIDENCE_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$FAILURE_DIR"
cp shift_suite/ "$FAILURE_DIR/" -r
cp app.py "$FAILURE_DIR/"
cp dash_app.py "$FAILURE_DIR/"
```

### STEP 3: 完全復旧
```bash
# バックアップからの完全復元
rm -rf shift_suite/
cp -r CRITICAL_BACKUP_PROPORTIONAL_ABOLITION_20250806_181951/shift_suite/ ./
cp CRITICAL_BACKUP_PROPORTIONAL_ABOLITION_20250806_181951/app.py ./
cp CRITICAL_BACKUP_PROPORTIONAL_ABOLITION_20250806_181951/dash_app.py ./
cp CRITICAL_BACKUP_PROPORTIONAL_ABOLITION_20250806_181951/requirements.txt ./
```

### STEP 4: システム動作確認
```bash
# 基本動作テスト
python -c "import shift_suite; print('Module import: OK')"
python -c "from shift_suite.tasks.shortage import calculate_shortage; print('Core function: OK')"
```

---

## 📋 バックアップ内容詳細

### バックアップファイル一覧:
- `shift_suite/` - 全モジュール（按分計算ロジック含む）
- `app.py` - メインアプリケーション
- `dash_app.py` - ダッシュボードアプリ
- `requirements.txt` - 依存関係定義

### 重要な按分関連ファイル:
- `shift_suite/tasks/shortage.py` - 按分計算メインロジック
- `shift_suite/tasks/proportional_calculator.py` - 按分計算専用モジュール
- `shift_suite/tasks/time_axis_shortage_calculator.py` - 時間軸計算
- `shift_suite/tasks/utils.py` - ユーティリティ関数

---

## ⚠️ 復旧後の確認項目

1. **データ整合性チェック**: extracted_results/の結果が373時間で一致するか
2. **機能動作確認**: ダッシュボードの表示が正常か
3. **エラーログ確認**: 異常メッセージがないか
4. **パフォーマンス確認**: 処理時間が30秒程度で完了するか

---

## 🔄 段階的復旧オプション

### オプション1: 完全復旧
→ 上記STEP1-4を実行

### オプション2: 部分復旧  
→ 按分計算のみ復旧、他改善は維持

### オプション3: 選択的復旧
→ 特定モジュールのみ復旧

---

**この手順書は按分廃止プロジェクトの生命線です。**
**システム破綻時は冷静にこの手順に従ってください。**