# Shift-Suite 設定資料集
## 統一分析管理システム - 完全設定マニュアル

**Version:** 2.0  
**Date:** 2025-07-30  
**Status:** Production Ready  

---

## 📖 目次

1. [アプリケーション哲学](#1-アプリケーション哲学)
2. [動的システム設計原則](#2-動的システム設計原則)
3. [全体最適化アーキテクチャ](#3-全体最適化アーキテクチャ)
4. [技術仕様とAPI仕様](#4-技術仕様とapi仕様)
5. [運用ガイドライン](#5-運用ガイドライン)
6. [設定パラメータ詳細](#6-設定パラメータ詳細)
7. [トラブルシューティング](#7-トラブルシューティング)

---

## 1. アプリケーション哲学

### 1.1 基本理念

**Shift-Suite**は、**「全ては動的に、全ては全体最適に」**を根本哲学とする統一分析管理システムです。

#### 🔄 完全動的主義
- **すべてのデータ処理は動的**：固定値やハードコーディングを排除
- **リアルタイム適応**：データ構造の変化に即座に対応
- **設定駆動型**：ユーザーの設定に基づく完全柔軟な処理

#### 🌍 全体最適化原則
- **個別最適の排除**：部分的な修正ではなく、システム全体の調和を追求
- **統合的データフロー**：分析結果の一元管理と一貫性保証
- **予測的エラー処理**：問題発生前の予防的対策

#### 🏗️ 拡張性・保守性
- **MECE原則**：Mutually Exclusive, Collectively Exhaustive
- **Truth-Driven Analysis**：実データ優先の分析手法
- **Memory-Efficient Design**：長期運用に耐える効率的設計

### 1.2 設計思想の背景

従来のシフト分析システムでは以下の問題が頻発していました：

❌ **問題点**
- 固定されたスロット時間（30分固定）による柔軟性の欠如
- 個別モジュールの最適化による全体不整合
- データ形式の変更に対する脆弱性
- 分析結果の散在による管理困難

✅ **Shift-Suiteの解決策**
- **動的スロット設定**：5分〜1440分（24時間）の任意設定
- **統一分析管理システム**：全分析結果の一元化
- **適応型データ処理**：任意のExcel構造への対応
- **自動品質保証**：データ整合性の自動検証

---

## 2. 動的システム設計原則

### 2.1 コア設計原則

#### 🎯 **原則1: Configuration-Driven Everything**
すべての設定は外部設定ファイルまたはユーザー入力によって動的に決定されます。

```python
# ❌ 悪い例：固定値
SLOT_MINUTES = 30  # ハードコーディング

# ✅ 良い例：動的設定
slot_minutes = get_dynamic_slot_minutes(config)  # 設定から取得
```

#### 🔄 **原則2: Adaptive Data Processing**
データ構造の変化に自動適応する処理を実装します。

```python
# ✅ 動的カラム検出
def detect_available_columns(df):
    """利用可能なカラムを動的に検出"""
    score_columns = ['fatigue_score', 'final_score', 'balance_score']
    return next((col for col in score_columns if col in df.columns), None)
```

#### 🌐 **原則3: Global Consistency**
システム全体で一貫した状態を維持します。

```python
# ✅ 統一分析管理
class UnifiedAnalysisManager:
    """全分析結果の統一管理"""
    def __init__(self):
        self.results_registry = {}  # 一元化されたレジストリ
        self.converter = SafeDataConverter()  # 安全な型変換
```

### 2.2 動的設定システム

#### 📋 設定階層
1. **デフォルト設定** (`constants.py`)
2. **施設タイプ設定** (`config/facility_types/*.json`)
3. **施設固有設定** (`config/facilities/*.json`)
4. **ユーザー設定** (Streamlitインターフェース)
5. **実行時設定** (分析実行時の動的調整)

#### 🔧 動的パラメータ例

```python
# スロット時間の動的設定
DEFAULT_SLOT_MINUTES = 30
SLOT_RANGE = {
    "min": 5,      # 最小5分
    "max": 1440,   # 最大24時間
    "default": 30  # デフォルト30分
}

# 夜勤時間帯の動的定義
NIGHT_SHIFT_CONFIG = {
    "start_time": "22:00",  # 設定可能
    "end_time": "05:59",    # 設定可能
    "timezone_aware": True  # タイムゾーン対応
}
```

### 2.3 実装パターン

#### 🏭 Factory Pattern
設定に基づいて適切なクラスインスタンスを生成

```python
class AnalysisFactory:
    @staticmethod
    def create_analyzer(analysis_type: str, config: dict):
        """設定に基づく分析器の動的生成"""
        analyzers = {
            'shortage': ShortageAnalyzer,
            'fatigue': FatigueAnalyzer,
            'fairness': FairnessAnalyzer
        }
        return analyzers[analysis_type](config)
```

#### 🔌 Strategy Pattern
実行時に処理方法を選択

```python
class DataProcessingStrategy:
    def process_excel_data(self, file_path: str, slot_minutes: int):
        """スロット時間に応じた処理戦略の選択"""
        if slot_minutes <= 15:
            return self._high_resolution_processing(file_path)
        elif slot_minutes <= 60:
            return self._standard_processing(file_path)
        else:
            return self._low_resolution_processing(file_path)
```

---

## 3. 全体最適化アーキテクチャ

### 3.1 システム構成図

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐     │
│  │   Upload    │  │  Analysis   │  │   Reporting     │     │
│  │  Interface  │  │  Controls   │  │   Dashboard     │     │
│  └─────────────┘  └─────────────┘  └─────────────────┘     │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│              Unified Analysis Manager                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │               Results Registry                      │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │   │
│  │  │  Shortage   │ │   Fatigue   │ │  Fairness   │    │   │
│  │  │   Results   │ │   Results   │ │   Results   │    │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘    │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            Safe Data Converter                     │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Dynamic Key Manager                      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                Analysis Modules                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐     │
│  │  shortage   │  │   fatigue   │  │    fairness     │     │
│  │  analyzer   │  │  analyzer   │  │    analyzer     │     │
│  └─────────────┘  └─────────────┘  └─────────────────┘     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐     │
│  │   heatmap   │  │   forecast  │  │      cost       │     │
│  │  generator  │  │   engine    │  │    analyzer     │     │
│  └─────────────┘  └─────────────┘  └─────────────────┘     │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                   Data Layer                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Enhanced Data Ingestion               │   │
│  │  • Dynamic Excel Structure Detection               │   │
│  │  • Automatic Column Mapping                        │   │
│  │  • Data Quality Assessment                         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 データフロー設計

#### 🔄 統合データフロー

1. **データ取り込み** (`Enhanced Data Ingestion`)
   - Excel構造の動的解析
   - 自動カラムマッピング
   - データ品質評価

2. **統一前処理** (`Unified Analysis Manager`)
   - 型安全変換 (`SafeDataConverter`)
   - キー管理 (`DynamicKeyManager`)
   - エラーハンドリング

3. **並列分析実行**
   - 各分析モジュールの独立実行
   - 結果の統一フォーマット化
   - レジストリへの自動登録

4. **結果統合** (`AI Compatible Results`)
   - 分析結果の一元管理
   - 重複排除と最新結果選択
   - レポート生成用データ変換

### 3.3 全体最適化の具体例

#### 🎯 **問題：スロット時間の不整合**

**従来の個別最適アプローチ：**
```python
# ❌ 各モジュールで個別にスロット時間を定義
# shortage.py
SHORTAGE_SLOT_HOURS = 0.5

# fatigue.py  
FATIGUE_SLOT_MINUTES = 30

# heatmap.py
HEATMAP_INTERVAL = 1800  # 秒
```

**Shift-Suiteの全体最適アプローチ：**
```python
# ✅ 統一設定システム
class DynamicSlotConfiguration:
    def __init__(self, slot_minutes: int):
        self.slot_minutes = slot_minutes
        self.slot_hours = slot_minutes / 60.0
        self.slot_seconds = slot_minutes * 60
    
    def get_compatible_value(self, target_unit: str):
        """要求された単位での値を返す"""
        units = {
            'minutes': self.slot_minutes,
            'hours': self.slot_hours, 
            'seconds': self.slot_seconds
        }
        return units.get(target_unit, self.slot_minutes)
```

#### 🎯 **問題：分析結果の散在**

**従来の個別最適アプローチ：**
```python
# ❌ 各モジュールが独立してファイル出力
shortage_results.to_parquet("shortage_output.parquet")
fatigue_results.to_csv("fatigue_scores.csv")  
fairness_data.to_excel("fairness_report.xlsx")
```

**Shift-Suiteの全体最適アプローチ：**
```python
# ✅ 統一結果管理システム
unified_manager = UnifiedAnalysisManager()

# 各分析の結果を統一システムに登録
shortage_result = unified_manager.create_shortage_analysis(file_name, scenario_key, data)
fatigue_result = unified_manager.create_fatigue_analysis(file_name, scenario_key, data)
fairness_result = unified_manager.create_fairness_analysis(file_name, scenario_key, data)

# AI向け統合レポートの自動生成
comprehensive_report = unified_manager.get_ai_compatible_results(file_pattern)
```

---

## 4. 技術仕様とAPI仕様

### 4.1 システム要件

#### 🖥️ **動作環境**
- **Python:** 3.12 以上（必須）
- **メモリ:** 最小 4GB（推奨 8GB以上）
- **ストレージ:** 最小 2GB（分析データ用）
- **OS:** Windows 10/11, macOS 10.15+, Linux（Ubuntu 20.04+）

#### 📦 **依存関係**
```txt
# コアライブラリ
pandas>=2.2.0          # データ処理
numpy>=1.26.0           # 数値計算
openpyxl>=3.1.0         # Excel読み込み
streamlit>=1.44.0       # Webインターフェース

# 機械学習・統計
scikit-learn>=1.4.2     # ML分析
lightgbm>=4.3.0         # 勾配ブースティング
prophet>=1.1.6          # 時系列予測

# 可視化
plotly>=5.20.0          # インタラクティブグラフ
matplotlib>=3.8.0       # 静的グラフ

# 最適化
ortools>=9.7.0          # 制約最適化
```

### 4.2 API仕様

#### 🔌 **UnifiedAnalysisManager API**

```python
class UnifiedAnalysisManager:
    """統一分析結果管理システム"""
    
    def __init__(self) -> None:
        """初期化"""
        
    def create_shortage_analysis(
        self, 
        file_name: str, 
        scenario_key: str, 
        role_df: pd.DataFrame
    ) -> UnifiedAnalysisResult:
        """不足分析結果の作成"""
        
    def create_fatigue_analysis(
        self,
        file_name: str,
        scenario_key: str, 
        fatigue_df: Optional[pd.DataFrame] = None,
        combined_df: Optional[pd.DataFrame] = None
    ) -> UnifiedAnalysisResult:
        """疲労分析結果の作成"""
        
    def create_fairness_analysis(
        self,
        file_name: str,
        scenario_key: str,
        fairness_df: pd.DataFrame
    ) -> List[UnifiedAnalysisResult]:
        """公平性分析結果の作成"""
        
    def get_ai_compatible_results(
        self, 
        file_pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """AI包括レポート用結果取得"""
        
    def cleanup_old_results(
        self, 
        max_age_hours: int = 24
    ) -> None:
        """古い結果の自動クリーンアップ"""
```

#### 🔧 **設定管理API**

```python
# 動的設定の取得
import shift_suite.config as config

slot_minutes = config.get('slot_minutes', 30)
night_start = config.get('night_shift_start', '22:00')
facility_type = config.get('facility_type', 'general_hospital')

# 設定の動的更新
config.update({
    'slot_minutes': 15,
    'analysis_depth': 'comprehensive'
})
```

#### 📊 **分析実行API**

```python
# 標準的な分析実行フロー
from shift_suite import shortage, fatigue, fairness

# 1. データ読み込み
data = load_excel_data(file_path, slot_minutes=30)

# 2. 不足分析実行
shortage_result = shortage.analyze(data, config)

# 3. 疲労分析実行  
fatigue_result = fatigue.analyze(data, config)

# 4. 公平性分析実行
fairness_result = fairness.analyze(data, config)

# 5. 統合レポート生成
comprehensive_report = generate_comprehensive_report([
    shortage_result, fatigue_result, fairness_result
])
```

### 4.3 データ形式仕様

#### 📋 **Excel入力フォーマット**

**必須カラム：**
- `date` または `日付`：日付情報
- `staff_id` または `職員ID`：職員識別子
- `shift_code` または `勤務コード`：シフトコード

**推奨カラム：**
- `role` または `職種`：職種情報
- `department` または `部署`：部署情報
- `shift_start` または `開始時間`：勤務開始時間
- `shift_end` または `終了時間`：勤務終了時間

**動的対応：**
- カラム名の自動検出
- 日本語・英語混在対応
- 複数シート対応

#### 📊 **出力フォーマット**

```json
{
  "analysis_type": "comprehensive",
  "timestamp": "2025-07-30T10:00:00",
  "file_info": {
    "name": "デイ_テスト用データ_休日精緻.xlsx",
    "size": 1024000,
    "sheets": ["勤務表", "職員マスタ"]
  },
  "results": {
    "shortage_analysis": {
      "total_shortage_hours": 45.5,
      "shortage_events_count": 12,
      "affected_roles_count": 8,
      "severity_level": "medium"
    },
    "fatigue_analysis": {
      "avg_fatigue_score": 0.65,
      "high_fatigue_staff_count": 3,
      "total_staff_analyzed": 25
    },
    "fairness_analysis": {
      "avg_fairness_score": 0.82,
      "low_fairness_staff_count": 2,
      "improvement_rate": 0.92
    }
  },
  "metadata": {
    "processing_time_seconds": 2.34,
    "data_quality_score": 0.95,
    "config_used": {
      "slot_minutes": 30,
      "analysis_depth": "standard"
    }
  }
}
```

---

## 5. 運用ガイドライン

### 5.1 日常運用フロー

#### 🔄 **標準分析フロー**

1. **事前準備**
   ```bash
   # 仮想環境のアクティベート
   source venv-py311/Scripts/activate  # Windows
   # または
   source venv-py311/bin/activate      # macOS/Linux
   ```

2. **アプリケーション起動**
   ```bash
   streamlit run app.py
   ```

3. **データアップロード**
   - Excelファイルの選択
   - シート選択（複数対応）
   - 設定確認（スロット時間等）

4. **分析実行**
   - 不足分析 → 疲労分析 → 公平性分析の順序推奨
   - 各分析完了後の結果確認
   - 異常値の早期発見

5. **レポート生成**
   - AI向け包括レポートの生成
   - 結果ダウンロード（ZIP形式）
   - ログファイルの確認

#### 📊 **品質管理チェックリスト**

**データ品質チェック：**
- [ ] 日付形式の統一性
- [ ] 職員IDの重複確認
- [ ] シフトコードの妥当性
- [ ] 時間データの整合性

**分析結果検証：**
- [ ] 不足時間の妥当性（0以上の値）
- [ ] 疲労スコアの範囲（0-1）
- [ ] 公平性指標の一貫性
- [ ] 異常値の有無

**システム動作確認：**
- [ ] メモリ使用量の監視
- [ ] ログエラーの確認
- [ ] 処理時間の記録
- [ ] 結果の完全性

### 5.2 トラブル対応

#### 🚨 **一般的な問題と解決策**

**問題1: インポートエラー**
```
ImportError: cannot import name 'xxx' from 'shift_suite.tasks.xxx'
```
**解決策:**
```bash
# 依存関係の再インストール
pip install -r requirements.txt --force-reinstall
```

**問題2: Excel読み込みエラー**
```
UnicodeDecodeError: 'cp932' codec can't decode byte
```
**解決策:**
```python
# app.pyで文字エンコーディングを明示的に指定
pd.read_excel(file_path, encoding='utf-8')
```

**問題3: メモリ不足**
```
MemoryError: Unable to allocate array
```
**解決策:**
```python
# データのチャンク処理を有効化
large_file_config = {
    'chunk_size': 1000,
    'memory_efficient': True
}
```

#### 🔧 **高度なトラブルシューティング**

**デバッグ情報の取得:**
```python
# ログレベルの変更
import logging
logging.getLogger('shift_suite').setLevel(logging.DEBUG)

# 統一システムの状態確認
if hasattr(st.session_state, 'unified_analysis_manager'):
    manager = st.session_state.unified_analysis_manager
    print(f"レジストリサイズ: {len(manager.results_registry)}")
    print(f"登録済みキー: {list(manager.results_registry.keys())}")
```

**設定の動的確認:**
```python
# 現在の設定を確認
import shift_suite.config as config
current_config = config._load_config()
print(json.dumps(current_config, indent=2, ensure_ascii=False))
```

### 5.3 性能最適化

#### ⚡ **処理速度の最適化**

**大量データ処理：**
```python
# チャンク処理の活用
def process_large_dataset(file_path, chunk_size=1000):
    for chunk in pd.read_excel(file_path, chunksize=chunk_size):
        yield process_chunk(chunk)

# 並列処理の利用
from concurrent.futures import ProcessPoolExecutor
with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(analyze_chunk, data_chunks))
```

**メモリ効率の改善：**
```python
# 不要なデータの早期削除
def memory_efficient_analysis(data):
    result = perform_analysis(data)
    del data  # 明示的にメモリ解放
    gc.collect()
    return result
```

#### 📈 **スケーラビリティ設定**

**施設規模別設定：**
```json
{
  "small_facility": {
    "max_staff": 50,
    "chunk_size": 500,
    "parallel_workers": 2
  },
  "large_facility": {
    "max_staff": 500,
    "chunk_size": 100,
    "parallel_workers": 8
  }
}
```

---

## 6. 設定パラメータ詳細

### 6.1 基本パラメータ

#### ⚙️ **時間設定**

```python
# constants.py
DEFAULT_SLOT_MINUTES = 30        # デフォルトスロット時間
SLOT_RANGE = {
    "min": 5,                    # 最小スロット時間（分）
    "max": 1440,                 # 最大スロット時間（分）
    "recommended": [15, 30, 60]  # 推奨値
}

# 夜勤時間帯
NIGHT_START_TIME = dt.time(22, 0)  # 22:00
NIGHT_END_TIME = dt.time(5, 59)    # 05:59
```

#### 💰 **コスト設定**

```python
WAGE_RATES = {
    "regular_staff": 1500,        # 正規職員時給（円）
    "temporary_staff": 2200,      # 派遣職員時給（円）
    "night_differential": 1.25,   # 夜勤手当倍率
    "weekend_differential": 1.1   # 休日手当倍率
}

COST_PARAMETERS = {
    "recruit_cost_per_hire": 200_000,     # 採用コスト（円）
    "penalty_per_shortage_hour": 4_000,   # 不足時間ペナルティ（円）
    "monthly_hours_fte": 160              # 月間標準労働時間
}
```

### 6.2 分析パラメータ

#### 📊 **統計的閾値**

```python
STATISTICAL_THRESHOLDS = {
    "confidence_level": 0.95,           # 統計的信頼水準
    "correlation_threshold": 0.7,       # 相関分析閾値
    "significance_alpha": 0.05,         # 有意水準
    "min_sample_size": 10,              # 最小サンプルサイズ
    "high_confidence_threshold": 0.8    # 高信頼度判定閾値
}
```

#### 😴 **疲労度パラメータ**

```python
FATIGUE_PARAMETERS = {
    "min_rest_hours": 11,               # 最小休憩時間（法的要件）
    "consecutive_3_days_weight": 0.6,   # 3連勤重み
    "consecutive_4_days_weight": 0.3,   # 4連勤重み
    "night_shift_threshold": 0.3,       # 夜勤比率閾値
    "fatigue_alert_threshold": 0.8      # 疲労アラート閾値
}
```

#### 👥 **チームダイナミクス**

```python
TEAM_DYNAMICS_PARAMETERS = {
    "compatibility_threshold_excellent": 0.9,  # 相性優秀閾値
    "emergency_score_threshold": 0.6,          # 緊急対応基本閾値
    "learning_default_speed": 0.5,             # デフォルト学習速度
    "mentoring_capacity_default": 0.5,         # デフォルト指導能力
    "stress_high_threshold": 0.8               # 高ストレス耐性閾値
}
```

### 6.3 施設タイプ別設定

#### 🏥 **医療施設タイプ**

```json
// config/facility_types/general_hospital.json
{
  "facility_type": "general_hospital",
  "display_name": "総合病院",
  "slot_minutes_default": 30,
  "night_shift_mandatory": true,
  "minimum_staff_ratios": {
    "nurse": 0.6,
    "doctor": 0.2,
    "support": 0.2
  },
  "quality_requirements": {
    "minimum_experience_ratio": 0.4,
    "maximum_consecutive_days": 4,
    "emergency_response_required": true
  }
}
```

```json
// config/facility_types/nursing_home.json  
{
  "facility_type": "nursing_home",
  "display_name": "介護施設",
  "slot_minutes_default": 60,
  "night_shift_mandatory": true,
  "minimum_staff_ratios": {
    "care_worker": 0.7,
    "nurse": 0.2,
    "support": 0.1
  },
  "quality_requirements": {
    "minimum_experience_ratio": 0.3,
    "maximum_consecutive_days": 5,
    "emergency_response_required": false
  }
}
```

#### 🏢 **個別施設設定**

```json
// config/facilities/sample_hospital.json
{
  "facility_id": "hospital_001",
  "facility_name": "○○総合病院",
  "facility_type": "general_hospital",
  "custom_settings": {
    "slot_minutes": 15,
    "night_premium_rate": 1.3,
    "weekend_premium_rate": 1.2,
    "holiday_calendar": "japan_national_holidays"
  },
  "departments": {
    "ICU": {
      "minimum_staff": 3,
      "required_certification": ["ICU_specialist"],
      "night_shift_ratio": 1.0
    },
    "general_ward": {
      "minimum_staff": 2,
      "night_shift_ratio": 0.8
    }
  }
}
```

---

## 7. トラブルシューティング

### 7.1 一般的な問題

#### 🚨 **起動時エラー**

**エラー:** `ModuleNotFoundError: No module named 'pandas'`
```bash
# 解決策1: 仮想環境の確認
which python
which pip

# 解決策2: 依存関係の再インストール  
pip install -r requirements.txt

# 解決策3: 仮想環境の再作成
python -m venv venv-new
source venv-new/Scripts/activate
pip install -r requirements.txt
```

**エラー:** `UnicodeEncodeError: 'cp932' codec can't encode character`
```python
# 解決策: 環境変数の設定
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

# または起動時に指定
set PYTHONIOENCODING=utf-8 && streamlit run app.py
```

#### 📊 **データ処理エラー**

**エラー:** `shortage hours calculated as 0`
```python
# 診断: デバッグログの確認
import logging
logging.getLogger('shift_suite').setLevel(logging.DEBUG)

# 確認ポイント:
# 1. スロット時間の設定
# 2. データの型変換
# 3. 統一システムの登録状況
```

**エラー:** `Empty results from unified analysis manager`
```python
# 診断手順:
if hasattr(st.session_state, 'unified_analysis_manager'):
    manager = st.session_state.unified_analysis_manager
    print(f"Registry size: {len(manager.results_registry)}")
    print(f"Available keys: {list(manager.results_registry.keys())}")
    
    # ファイル名パターンの確認
    from pathlib import Path
    file_stem = Path(uploaded_file.name).stem
    print(f"Searching for pattern: {file_stem}")
```

### 7.2 高度なデバッグ

#### 🔍 **システム状態の診断**

```python
def system_health_check():
    """システム全体の健全性チェック"""
    checks = []
    
    # 1. 依存関係チェック
    try:
        import pandas, numpy, streamlit, plotly
        checks.append("✅ Core dependencies: OK")
    except ImportError as e:
        checks.append(f"❌ Missing dependency: {e}")
    
    # 2. 設定ファイルチェック
    config_path = Path("shift_suite/config.json")
    if config_path.exists():
        checks.append("✅ Config file: Found")
    else:
        checks.append("❌ Config file: Missing")
    
    # 3. メモリ使用量チェック
    import psutil
    memory_percent = psutil.virtual_memory().percent
    if memory_percent < 80:
        checks.append(f"✅ Memory usage: {memory_percent}%")
    else:
        checks.append(f"⚠️ High memory usage: {memory_percent}%")
    
    return checks
```

#### 📈 **性能プロファイリング**

```python
import cProfile
import pstats

def profile_analysis(data_file):
    """分析処理の性能プロファイリング"""
    profiler = cProfile.Profile()
    profiler.enable()
    
    # 分析実行
    result = run_comprehensive_analysis(data_file)
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # 上位10件の表示
    
    return result
```

### 7.3 ログ分析

#### 📝 **ログファイルの構造**

```
shift_suite.log
├── [INFO] システム起動ログ
├── [DEBUG] データ処理詳細  
├── [WARNING] 注意事項
├── [ERROR] エラー情報
└── [CRITICAL] 重大な問題

shortage_analysis.log  
├── [INFO] 不足分析の詳細
├── [DEBUG] スロット別処理
└── [WARNING] データ品質問題
```

#### 🔎 **ログ解析スクリプト**

```python
def analyze_logs(log_file="shift_suite.log"):
    """ログファイルの自動解析"""
    error_patterns = []
    warning_patterns = []
    
    with open(log_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if '[ERROR]' in line:
                error_patterns.append((line_num, line.strip()))
            elif '[WARNING]' in line:
                warning_patterns.append((line_num, line.strip()))
    
    print(f"Errors found: {len(error_patterns)}")
    print(f"Warnings found: {len(warning_patterns)}")
    
    return {'errors': error_patterns, 'warnings': warning_patterns}
```

---

## 📚 参考資料

### 関連ドキュメント
- [STARTUP_GUIDE.md](./STARTUP_GUIDE.md) - 基本的な起動手順
- [README.md](./README.md) - プロジェクト概要
- [COMPREHENSIVE_FIX_SUMMARY.md](./COMPREHENSIVE_FIX_SUMMARY.md) - 最新の修正内容

### 設定ファイル
- `shift_suite/config.json` - メイン設定
- `shift_suite/tasks/constants.py` - システム定数
- `requirements.txt` - 依存関係定義

### サポート
- GitHub Issues: プロジェクトリポジトリのIssuesページ
- ログファイル: `shift_suite.log`, `shortage_analysis.log`
- デバッグ情報: Streamlitインターフェースのエラー表示

---

**このドキュメントは動的システムの設計思想を体現しており、システムの拡張に合わせて継続的に更新されます。**

**最終更新: 2025-07-30**  
**バージョン: 2.0**  
**文書管理: 統一分析管理システム**