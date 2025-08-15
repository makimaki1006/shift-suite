# API・データフロー仕様書

**対象システム**: Shift-Suite Phase 2/3.1  
**API バージョン**: 1.0  
**作成日**: 2025年08月03日

## 📋 概要

本文書は、Shift-Suiteシステム内のデータフローとAPI仕様を記載します。

## 🌊 データフロー全体図

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Excel     │───▶│  io_excel   │───▶│ long_df     │
│ 勤務データ   │    │ 読み込み     │    │ 正規化      │
└─────────────┘    └─────────────┘    └─────────────┘
                                           │
┌─────────────┐    ┌─────────────┐      │
│ Phase 3.1   │◀───│   Phase 2   │◀─────┘
│LightWeight  │    │FactExtractor│
│AnomalyDet   │    │Prototype    │
└─────────────┘    └─────────────┘
        │                   │
        └───────┬───────────┘
                ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│FactBook     │───▶│DashFactBook │───▶│  dash_app   │
│Visualizer   │    │Integration  │    │ WebUI       │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 📊 データ構造仕様

### 1. 入力データ（Excel）

#### 必須列
```json
{
  "date": "勤務日（YYYY-MM-DD形式）",
  "staff_id": "職員ID（文字列）",
  "start_time": "開始時間（HH:MM形式）",
  "end_time": "終了時間（HH:MM形式）",
  "work_type": "勤務タイプ（日勤/夜勤等）",
  "department": "部署・病棟（オプション）"
}
```

#### データ例
```csv
date,staff_id,start_time,end_time,work_type,department
2024-08-01,STAFF001,09:00,17:00,日勤,内科病棟
2024-08-01,STAFF002,17:00,09:00,夜勤,内科病棟
```

### 2. 中間データ（long_df）

#### parsed_slots_count（重要）
```python
# データ型: int
# 意味: 30分単位のスロット数
# 例: 8時間勤務 = 16スロット
parsed_slots_count = 16

# 時間変換（Phase 2/3.1で実施）
SLOT_HOURS = 0.5
actual_hours = parsed_slots_count * SLOT_HOURS  # 16 * 0.5 = 8.0時間
```

### 3. 出力データ

#### shortage_summary.txt
```
total_lack_hours: 670
total_excess_hours: 505
```

## 🔧 Phase 2 API仕様

### FactExtractorPrototype

#### クラス定義
```python
class FactExtractorPrototype:
    def __init__(self, config: Dict[str, Any])
    def extract_facts(self, data: pd.DataFrame) -> Dict[str, Any]
    def calculate_hours(self, slots_data: pd.Series) -> pd.Series
```

#### 主要メソッド

##### calculate_hours()
```python
def calculate_hours(self, slots_data: pd.Series) -> pd.Series:
    """スロット数を時間に変換"""
    SLOT_HOURS = 0.5
    return slots_data * SLOT_HOURS  # 修正済み: 正確な変換
```

#### 重要な修正点
```python
# 修正前（誤り）
total_hours = group['parsed_slots_count'].sum()  # スロット数をそのまま時間扱い

# 修正後（正確）
total_hours = group['parsed_slots_count'].sum() * SLOT_HOURS  # 正しい時間変換
```

## 🔍 Phase 3.1 API仕様

### LightweightAnomalyDetector

#### クラス定義
```python
class LightweightAnomalyDetector:
    def __init__(self, config: Dict[str, Any])
    def detect_anomalies(self, data: pd.DataFrame) -> Dict[str, Any]
    def calculate_monthly_hours(self, work_data: pd.DataFrame) -> pd.DataFrame
```

#### 主要メソッド

##### calculate_monthly_hours()
```python
def calculate_monthly_hours(self, work_data: pd.DataFrame) -> pd.DataFrame:
    """月次労働時間計算"""
    SLOT_HOURS = 0.5
    monthly_hours = work_data.groupby(['staff', 'year_month'])['parsed_slots_count'].sum() * SLOT_HOURS
    return monthly_hours
```

## 🎨 統合レイヤー API

### FactBookVisualizer

#### 機能
- Phase 2/3.1の結果を可視化用に変換
- グラフ・チャート用データの生成
- レポート出力用データの整形

#### インターフェース
```python
class FactBookVisualizer:
    def create_heatmap_data(self, facts: Dict) -> Dict
    def create_timeline_data(self, facts: Dict) -> Dict
    def create_summary_stats(self, facts: Dict) -> Dict
```

### DashFactBookIntegration

#### 機能
- Dash Webアプリケーションとの統合
- インタラクティブUI用データ提供
- リアルタイム更新対応

#### エンドポイント
```python
@app.callback(...)
def update_heatmap(selected_date):
    # FactBookVisualizerからデータ取得
    # Dash コンポーネント用に変換
    return updated_figure

@app.callback(...)
def update_summary(filters):
    # 条件に基づいた集計
    # サマリー情報の更新
    return summary_data
```

## 🔄 データ変換仕様

### 1. Excel → long_df

#### 変換処理
```python
def excel_to_longdf(excel_path: str) -> pd.DataFrame:
    """Excel勤務データを正規化形式に変換"""
    
    # 1. Excelファイル読み込み
    raw_data = pd.read_excel(excel_path)
    
    # 2. 時間計算（30分スロット）
    def calculate_slots(start_time: str, end_time: str) -> int:
        # 開始・終了時刻からスロット数を計算
        duration_minutes = get_duration_minutes(start_time, end_time)
        return duration_minutes // 30  # 30分単位のスロット
    
    # 3. parsed_slots_count列生成
    raw_data['parsed_slots_count'] = raw_data.apply(
        lambda row: calculate_slots(row['start_time'], row['end_time']), 
        axis=1
    )
    
    return raw_data
```

### 2. long_df → Phase 2/3.1

#### Phase 2変換
```python
def process_phase2(data: pd.DataFrame) -> Dict[str, Any]:
    """Phase 2ファクト抽出"""
    SLOT_HOURS = 0.5
    
    # グループ別集計（時間単位に変換）
    group_stats = data.groupby(['department', 'work_type']).agg({
        'parsed_slots_count': ['count', 'sum', 'mean']
    })
    
    # スロット数を時間に変換
    group_stats['total_hours'] = group_stats['parsed_slots_count']['sum'] * SLOT_HOURS
    
    return group_stats.to_dict()
```

#### Phase 3.1変換
```python
def process_phase31(data: pd.DataFrame) -> Dict[str, Any]:
    """Phase 3.1異常検知"""
    SLOT_HOURS = 0.5
    
    # 月次労働時間計算
    monthly_hours = data.groupby(['staff', 'year_month'])['parsed_slots_count'].sum() * SLOT_HOURS
    
    # 異常検知（過労働等）
    anomalies = monthly_hours[monthly_hours > 160]  # 月160時間超過
    
    return {
        'monthly_hours': monthly_hours.to_dict(),
        'anomalies': anomalies.to_dict()
    }
```

## 🛡️ エラーハンドリング

### 一般的なエラー

#### データ形式エラー
```python
class DataFormatError(Exception):
    """データ形式が不正な場合"""
    pass

# 使用例
try:
    parsed_slots = calculate_slots(start_time, end_time)
except ValueError as e:
    raise DataFormatError(f"時刻形式が不正: {e}")
```

#### 計算エラー
```python
class CalculationError(Exception):
    """計算処理でエラーが発生した場合"""
    pass

# SLOT_HOURS未定義エラー
try:
    hours = slots * SLOT_HOURS
except NameError:
    raise CalculationError("SLOT_HOURS定数が未定義")
```

### API レスポンス形式

#### 成功時
```json
{
  "status": "success",
  "data": {
    "total_hours": 670.0,
    "processed_records": 1234,
    "calculation_method": "slots * SLOT_HOURS"
  },
  "metadata": {
    "timestamp": "2024-08-03T18:30:00Z",
    "version": "1.0"
  }
}
```

#### エラー時
```json
{
  "status": "error",
  "error": {
    "code": "CALCULATION_ERROR",
    "message": "SLOT_HOURS定数が未定義",
    "details": {
      "file": "fact_extractor_prototype.py",
      "line": 123
    }
  },
  "metadata": {
    "timestamp": "2024-08-03T18:30:00Z",
    "version": "1.0"
  }
}
```

## 🔍 デバッグ・トレーシング

### ログ出力仕様

#### Phase 2ログ
```python
import logging

logger = logging.getLogger('phase2.fact_extractor')

def extract_facts(self, data):
    logger.info(f"処理開始: {len(data)}件のレコード")
    
    # SLOT_HOURS使用ログ
    SLOT_HOURS = 0.5
    logger.debug(f"SLOT_HOURS定数: {SLOT_HOURS}")
    
    total_hours = group['parsed_slots_count'].sum() * SLOT_HOURS
    logger.debug(f"時間変換: {group['parsed_slots_count'].sum()}スロット → {total_hours}時間")
```

#### データフロー追跡
```python
# 各段階でのデータ検証
def validate_data_flow():
    """データフローの整合性検証"""
    
    # 1. 入力データ検証
    assert 'parsed_slots_count' in data.columns
    assert data['parsed_slots_count'].dtype == 'int64'
    
    # 2. 変換結果検証
    hours = data['parsed_slots_count'] * SLOT_HOURS
    assert hours.dtype == 'float64'
    assert (hours >= 0).all()
    
    # 3. 出力データ検証
    assert 'total_hours' in result
    assert isinstance(result['total_hours'], (int, float))
```

## 📈 パフォーマンス仕様

### 処理性能要件

#### レスポンス時間
- **Phase 2処理**: 1000件あたり < 1秒
- **Phase 3.1処理**: 1000件あたり < 0.5秒
- **統合処理**: エンドツーエンド < 5秒

#### メモリ使用量
- **基本処理**: < 100MB
- **大量データ**: < 500MB
- **メモリリーク**: なし（ガベージコレクション対応）

### スケーラビリティ

#### データ量対応
```python
# 大量データ対応（チャンク処理）
def process_large_dataset(data: pd.DataFrame, chunk_size: int = 1000):
    """大量データをチャンク単位で処理"""
    
    results = []
    for chunk in data.groupby(data.index // chunk_size):
        chunk_result = process_chunk(chunk[1])
        results.append(chunk_result)
    
    return combine_results(results)
```

---
*本API仕様書は実装変更に伴い継続的に更新されます。*

**最終更新**: 2025年08月03日
