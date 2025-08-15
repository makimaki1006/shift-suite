# 複数事業所統合分析ガイド

## 概要
包括レポート生成器を複数事業所の分析結果をまとめてLLMに与えることを想定した構造化形式に修正しました。

## 新しいレポート形式の特徴

### 1. 機械読み取り可能な構造化データ
```
FACILITY_ANALYSIS_REPORT
================================================================================
FACILITY_ID: out_mean_based
ANALYSIS_PERIOD: 2024-01-01 〜 2024-03-31
REPORT_GENERATED: 2025-01-25 14:30:00
TOTAL_RECORDS: 15432
================================================================================

SECTION: BASIC_STATISTICS
----------------------------------------
TOTAL_STAFF: 18
ANALYSIS_DAYS: 90
ROLE_TYPES: 3
ROLE_LIST: 介護職員,看護師,生活相談員
EMPLOYMENT_TYPES: 2
EMPLOYMENT_LIST: 正職員,パート

SUBSECTION: ANALYSIS_DATA_VOLUME
SHORTAGE_RECORDS: 144
TOTAL_SHORTAGE_HOURS: 127.5
TOTAL_EXCESS_HOURS: 89.3
FATIGUE_RECORDS: 18
FATIGUE_AVG: 52.34
FATIGUE_MAX: 87.22
FATIGUE_MIN: 23.11
```

### 2. CSV風データ形式（LLMが処理しやすい）
```
SECTION: TIME_SERIES_DATA
----------------------------------------
SUBSECTION: MONTHLY_BASIC_STATS
MONTH:2024-01|STAFF:18|DAYS:31
MONTH:2024-02|STAFF:18|DAYS:29
MONTH:2024-03|STAFF:17|DAYS:31

SUBSECTION: MONTHLY_ROLE_RECORDS
MONTH:2024-01|ROLE:介護職員|RECORDS:1240
MONTH:2024-01|ROLE:看護師|RECORDS:186
MONTH:2024-01|ROLE:生活相談員|RECORDS:93
```

### 3. 職員個別データの完全記録
```
SECTION: STAFF_INDIVIDUAL_DATA
----------------------------------------
SUBSECTION: STAFF_BASIC_STATS
STAFF:田中太郎|WORK_DAYS:87
STAFF:佐藤花子|WORK_DAYS:85
STAFF:鈴木次郎|WORK_DAYS:90

SUBSECTION: STAFF_FATIGUE_SCORES
STAFF:田中太郎|FATIGUE_SCORE:67.45
STAFF:佐藤花子|FATIGUE_SCORE:42.33
STAFF:鈴木次郎|FATIGUE_SCORE:78.91

SUBSECTION: STAFF_FAIRNESS_DATA
STAFF:田中太郎|NIGHT_RATIO:0.250|UNFAIRNESS_SCORE:0.045
STAFF:佐藤花子|NIGHT_RATIO:0.200|UNFAIRNESS_SCORE:0.023
```

## 複数事業所統合分析のメリット

### 1. 施設間比較が容易
- 各施設のFACILITY_IDで区別
- 同一フォーマットで統一された数値データ
- 規模の異なる施設でも正規化して比較可能

### 2. LLM分析に最適化
- Key:Value形式で構造化
- 人間の解釈を排除した純粋数値
- パターン認識とトレンド分析に最適

### 3. 統計処理に適したデータ形式
- パイプ区切り（|）による明確な区分
- 欠損データは"N/A"で統一
- 数値精度の統一（小数点以下の桁数統一）

## 実際の使用シナリオ

### シナリオ1: 3施設の比較分析
```
A施設レポート: FACILITY_ID: facility_A
B施設レポート: FACILITY_ID: facility_B  
C施設レポート: FACILITY_ID: facility_C

→ LLMに全3レポートを入力して横断分析
```

### シナリオ2: 時系列での施設状況追跡
```
同一施設の月次レポート:
- REPORT_GENERATED: 2024-01-31 (1月分)
- REPORT_GENERATED: 2024-02-29 (2月分)  
- REPORT_GENERATED: 2024-03-31 (3月分)

→ 施設の改善推移を定量的に追跡
```

### シナリオ3: ベンチマーク分析
```
優良施設のパターン:
FATIGUE_AVG: 45.2
SHORTAGE_TOTAL: 23.1
UNFAIRNESS_AVG: 0.032

→ 他施設の目標値として活用
```

## LLMへの指示例

### 基本分析プロンプト
```
以下は3つの介護施設のシフト分析レポートです。各施設を比較分析してください。

[facility_A_report.txt の内容]
[facility_B_report.txt の内容]  
[facility_C_report.txt の内容]

比較観点:
1. 人員不足状況の比較
2. 職員疲労度の施設間差異
3. 夜勤配分の公平性
4. 改善提案の優先順位
```

### トレンド分析プロンプト
```
以下は同一施設の3ヶ月間の推移データです。改善・悪化のトレンドを分析してください。

[month1_report.txt の内容]
[month2_report.txt の内容]
[month3_report.txt の内容]

分析観点:
1. 数値的な改善・悪化の傾向
2. 季節性や周期性の有無
3. 要注意指標の特定
```

## 技術的な利点

### 1. パース処理の簡易性
- 正規表現での簡単な抽出
- セクション別の分離処理
- キー・バリューペアの自動抽出

### 2. データ統合の容易性
- 同一キーでの数値比較
- 施設IDによる自動グルーピング
- 時系列データの自動ソート

### 3. 拡張性
- 新しい分析項目の追加が容易
- 施設数の制限なし
- 任意の期間での集計対応

これで複数事業所の分析結果を効率的にLLMで処理できる完全な構造化レポートシステムが完成しました。