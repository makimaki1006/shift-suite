# シフト分析システム品質チェック分析

## 📋 概要
データフロー段階②-⑤について、エラー回避、順当性、柔軟性、動的対応性の観点で品質チェック実施。

---

## ② データ分解段階 品質チェック ✅

### **ファイル**: `shift_suite/tasks/io_excel.py` (329-701行)

#### **🛡️ エラー回避 (エラーハンドリング)**
- **Excel読み込みエラー対応** (181-189行)
  ```python
  try:
      raw = pd.read_excel(xlsx, sheet_name=sheet_name, dtype=str).fillna("")
  except FileNotFoundError as e:
      log.error("Excel file not found: %s", e)
      raise
  except pd.errors.EmptyDataError as e:
      log.error("勤務区分シート '%s' が空です: %s", sheet_name, e)
      raise ValueError(f"勤務区分シート '{sheet_name}' が空です") from e
  ```

- **必須列不足チェック** (196-202行)
  ```python
  required_cols = {"code", "start", "end"}
  if not required_cols.issubset(raw.columns):
      missing = required_cols - set(raw.columns)
      log.error(f"勤務区分シート '{sheet_name}' に必須列 {missing} がありません")
      raise ValueError(f"勤務区分シート '{sheet_name}' に必須列 {missing} がありません")
  ```

- **年月セル読み込みエラー対応** (385-387行)
  ```python
  except Exception as e:
      log.error(f"年月セル '{year_month_cell_location}' の読み込み失敗: {e}")
      raise ValueError("年月セルの取得に失敗しました") from e
  ```

#### **✅ 順当性 (処理フロー正当性)**
1. **段階的データ変換**: Excel → 勤務区分定義 → 時系列データ → 休日除外
2. **データ完整性チェック**: 各段階で必須項目確認
3. **ログによる追跡**: 処理状況を詳細記録（633-645行）
4. **根本的休日除外**: 最終段階で完全除外（647-699行）

#### **🔄 柔軟性 (データ形式対応)**
- **列名エイリアス対応** (25-52行)
  ```python
  COL_ALIASES = {"記号": "code", "コード": "code", "開始": "start", "終了": "end"}
  SHEET_COL_ALIAS = {"氏名": "staff", "職種": "role", "雇用形態": "employment"}
  ```

- **多様な時刻形式対応** (81-114行)
  - Excelシリアル値、HH:MM、HH:MM:SS形式
  - 24:00 → 00:00 自動変換
  - 日付またぎ夜勤対応

- **休暇コード柔軟判定** (56-65行、148-172行)
  ```python
  LEAVE_CODES = {"×": "希望休", "休": "施設休", "有": "有給", "欠": "欠勤"}
  ```

#### **⚡ 動的対応性 (実行時適応)**
- **動的スロット展開** (117-145行): 15分/30分/60分間隔自動対応
- **動的日付解析** (296-314行): 年月情報と日付の動的結合
- **動的休日除外** (647-699行): 実データに基づく除外パターン検出

---

## ③ データ分析段階 品質チェック ✅

### **A. ヒートマップ分析** (`heatmap.py`)

#### **🛡️ エラー回避**
- **空データ対応** (145-149行)
  ```python
  if actual_staff_by_slot_and_date.empty:
      log.warning("[heatmap] 入力実績データが空です。デフォルトの0 needを返します。")
      return default_dow_need_df
  ```

- **日付範囲チェック** (185-190行)
  ```python
  if not cols_to_process_dow:
      log.warning(f"参照期間 ({ref_start_date} - {ref_end_date}) に該当する実績データがありません。")
      return default_dow_need_df
  ```

#### **✅ 順当性**
1. **Need計算プロセス**: 実績データ → 曜日別集計 → 統計的Need算出
2. **休日フィルタリング**: 通常勤務のみ抽出（34-35行）
3. **段階的集計**: 時間×日付 → 職種別 → 雇用形態別

#### **🔄 柔軟性**
- **統計手法選択**: 中央値/平均値/25パーセンタイル対応
- **外れ値除去**: IQR方式による柔軟な除去
- **動的列名解決**: エイリアス自動マッピング（41-51行）

#### **⚡ 動的対応性**
- **動的Need計算**: 参照期間・手法の実行時変更対応
- **動的休日検出**: holidays引数による休日除外

### **B. 不足分析** (`shortage.py`)

#### **🛡️ エラー回避**
- **ファイル存在確認** (66-75行)
  ```python
  try:
      heat_all_df = pd.read_parquet(out_dir_path / "heat_ALL.parquet")
  except FileNotFoundError:
      log.error("[shortage] heat_ALL.parquet が見つかりません。処理を中断します。")
      return None
  ```

- **空データ時の適切な処理** (96-106行)
  ```python
  if not date_columns_in_heat_all:
      log.warning("[shortage] heat_ALL.parquet に日付データ列が見つかりませんでした。")
      empty_df = pd.DataFrame(index=time_labels)
      # 空ファイル生成で継続
  ```

#### **✅ 順当性**
1. **階層型Need計算**: 詳細Need → フォールバック曜日Need
2. **データ整合性**: heat_ALL.parquet ベースの実績データ使用
3. **メタデータ連携**: heatmap.meta.json からの休日情報取得

#### **🔄 柔軟性**
- **Need計算手法切替**: 詳細Need優先、曜日パターンフォールバック
- **コスト計算パラメータ**: wage_direct, wage_temp, penalty_per_lack

#### **⚡ 動的対応性**
- **自動スロット検出**: auto_detect_slot による間隔自動判定
- **動的Need再構築**: 実行時データ構造に適応（137-143行）

---

## ④ 結果加工段階 品質チェック

### **ファイル**: `app.py` (1699-1800行, 1615-1620行)

#### **🛡️ エラー回避**
- **ファイルコピーエラー対応**
  ```python
  try:
      shutil.copy(intermediate_parquet_path, scenario_out_dir / "intermediate_data.parquet")
  except Exception as e:
      log.error(f"中間データコピーエラー: {e}")
  ```

- **欠損値処理**: `.fillna(0)` による安全な欠損値補完

#### **✅ 順当性**
1. **ベースデータ作成**: 全組み合わせマスターデータ構築
2. **実績結合**: LEFT JOIN による完全性保証
3. **階層集計**: 時間別 → 職種別 → 雇用形態別

#### **🔄 柔軟性**
- **動的マスター生成**: 実データから利用可能オプション抽出
- **複数シナリオ対応**: 中央値/平均値/25パーセンタイル版並列生成

#### **⚡ 動的対応性**
- **動的集計レベル**: 実行時データに基づく集計軸決定
- **事前集計最適化**: パフォーマンス向上のための動的キャッシュ

---

## ⑤ 可視化段階 品質チェック

### **A. メイン表示** (`app.py`)

#### **🛡️ エラー回避**
- **データ存在確認**: 各表示前のデータ有効性チェック
- **グラフ生成エラー**: Plotly例外ハンドリング

#### **✅ 順当性**
1. **段階的表示**: サマリー → ヒートマップ → 詳細統計
2. **データ整合性**: 同一ソースからの一貫表示

#### **🔄 柔軟性**
- **複数表示形式**: メトリック/ヒートマップ/グラフ選択可能
- **カスタマイズ**: color_scale, aspect等の調整対応

### **B. 詳細ダッシュボード** (`dash_app.py`)

#### **🛡️ エラー回避**
- **キャッシュ機能** (376-390行)
  ```python
  def data_get(key: str, default=None):
      cached_value = DATA_CACHE.get(key)
      if cached_value is not None:
          return cached_value
      # ファイル検索・読み込み
  ```

- **安全な読み込み**: `safe_read_parquet()` 関数使用

#### **✅ 順当性**
1. **データフロー**: キャッシュ → ファイル → フィルタ → 表示
2. **休日除外統合**: 表示レベルでの二重チェック

#### **🔄 柔軟性**
- **動的フィルタリング**: 職種・雇用形態・日付範囲選択
- **比較表示**: 複数条件の並列表示

#### **⚡ 動的対応性**
- **リアルタイム更新**: 選択変更時の即座な再描画
- **インタラクティブ分析**: ドリルダウン・ズーム機能

---

## 📊 総合評価

### **強み**
1. **多段階エラーハンドリング**: 各段階での包括的例外処理
2. **データ完整性保証**: 必須項目チェック・型安全性
3. **柔軟なデータ形式対応**: エイリアス・多様な入力形式
4. **動的パラメータ対応**: 実行時設定変更
5. **根本的休日除外**: 上流での完全除外システム

### **改善推奨事項**
1. **段階④**: より詳細なファイル操作エラーハンドリング
2. **段階⑤**: グラフ生成時の例外処理強化
3. **全体**: メモリ使用量監視・制限機能

### **品質確認結果**
- **エラー回避**: ✅ 優秀
- **順当性**: ✅ 優秀  
- **柔軟性**: ✅ 優秀
- **動的対応性**: ✅ 優秀

**結論**: 全段階において高品質な実装。特に休日除外の根本的解決により、データの整合性と可視化の正確性を確保。