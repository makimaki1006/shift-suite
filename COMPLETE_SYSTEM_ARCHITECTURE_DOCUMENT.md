# シフト分析システム完全構造解析書
**C:\ShiftAnalysis 全ファイル・機能・構造の客観的分析報告**

---

## 📊 システム概要統計

| 項目 | 数量 | 詳細 |
|------|------|------|
| 総ファイル数 | 53,590 | 全ファイル形式含む |
| Pythonファイル | 22,188 | 実行可能プログラム |
| コアモジュール | 90+ | shift_suite/tasks内 |
| UIアプリケーション | 2 | app.py + dash_app.py |
| テスト・デバッグファイル | 500+ | test_*, debug_*, analyze_* |
| 分析結果データ | 数千 | parquet, csv, json形式 |
| ドキュメント | 数百 | md, json形式のレポート |
| バックアップ | 20+ | BACKUP_*ディレクトリ |

---

## 🏗️ MECE構造分析（相互排他的・集合的網羅的）

### 【A層】ユーザーインターフェース（排他選択制）

#### A1. Streamlit統合版アプリ
```
📄 app.py (3,000行+)
├─ 機能: 全機能統合UI、分析フロー制御
├─ バージョン: v1.30.0（休暇分析機能追加版）  
├─ 特徴: ファイルアップロード、パラメータ設定、結果表示
└─ 依存: streamlit, plotly, pandas, shift_suite.*
```

#### A2. Dash高速版ビューア
```
📄 dash_app.py (2,000行+)
├─ 機能: 高速分析ビューア、リアルタイム更新
├─ 特徴: app.py機能完全再現、パフォーマンス最適化
├─ 依存: dash, plotly, pandas, shift_suite.*
└─ 排他関係: app.pyと同時実行不可
```

### 【B層】コアエンジン（必須4モジュール）

#### B1. データ読み込みエンジン
```
📄 shift_suite/tasks/io_excel.py
├─ バージョン: v2.8.0（休暇コード明示的処理対応版）
├─ 機能: Excel読み込み、日付解析、勤務コード認識
├─ 重要処理: COL_ALIASES辞書による列名正規化
└─ 関連: utils._parse_as_date, constants.SLOT_MINUTES
```

#### B2. 不足計算エンジン
```
📄 shift_suite/tasks/shortage.py  
├─ バージョン: v2.7.0（最終修正版）
├─ 機能: 人員不足計算、統計処理、時間軸分析
├─ 重要変更: need_per_date_slot.parquet最優先利用
└─ 連携: proportional_calculator, time_axis_shortage_calculator
```

#### B3. 可視化エンジン
```
📄 shift_suite/tasks/heatmap.py
├─ バージョン: v1.8.1（日曜日Need計算修正版）
├─ 機能: ヒートマップ生成、Need計算、Excel出力
├─ 依存: openpyxl, ColorScaleRule, PatternFill
└─ 処理: validate_need_calculation, derive_max_staff
```

#### B4. 共通処理基盤
```
📄 shift_suite/tasks/utils.py
├─ バージョン: v1.3.0（動的スロット対応版）
├─ 機能: 共通ユーティリティ、データ検証、メタデータ管理
├─ 重要機能: _parse_as_date, _valid_df, gen_labels
└─ エンコーディング: UTF-8明示（Windows文字化け対策）
```

### 【C層】拡張分析モジュール群（90+モジュール）

#### C1. 基本分析モジュール（8個）
```
📁 基本分析/
├─ build_stats.py      # 統計構築
├─ cluster.py          # クラスタリング分析  
├─ fairness.py         # 公平性分析
├─ fatigue.py          # 疲労度分析
├─ forecast.py         # 予測分析
├─ anomaly.py          # 異常検知
├─ skill_nmf.py        # スキル行列因子分解
└─ assignment.py       # 割り当て最適化
```

#### C2. 専門計算エンジン（12個）
```
📁 専門計算/
├─ time_axis_shortage_calculator.py      # 時間軸不足計算
├─ proportional_calculator.py            # 按分計算
├─ occupation_specific_calculator.py     # 職種別計算
├─ shortage_factor_analyzer.py           # 不足要因分析
├─ unified_shortage_calculator.py        # 統一不足計算
├─ daily_cost.py                         # 日次コスト計算
├─ optimal_hire_plan.py                  # 最適採用計画
├─ cost_benefit.py                       # 費用対効果
├─ hire_plan.py                          # 採用計画
├─ turnover_prediction.py                # 離職予測
├─ fatigue_prediction.py                 # 疲労予測
└─ demand_prediction_model.py            # 需要予測モデル
```

#### C3. MECE分析エンジン群（12個）
```
📁 MECE分析/
├─ axis2_staff_mece_extractor.py                    # スタッフ軸
├─ axis3_time_calendar_mece_extractor.py           # 時間・カレンダー軸
├─ axis4_demand_load_mece_extractor.py             # 需要・負荷軸  
├─ axis5_medical_care_quality_mece_extractor.py    # 医療・ケア品質軸
├─ axis6_cost_efficiency_mece_extractor.py         # コスト・効率軸
├─ axis7_legal_regulatory_mece_extractor.py        # 法的・規制軸
├─ axis8_staff_satisfaction_mece_extractor.py      # スタッフ満足度軸
├─ axis9_business_process_mece_extractor.py        # 業務プロセス軸
├─ axis10_risk_emergency_mece_extractor.py         # リスク・緊急軸
├─ axis11_performance_improvement_mece_extractor.py # パフォーマンス改善軸
├─ axis12_strategy_future_mece_extractor.py        # 戦略・将来軸
└─ mece_fact_extractor.py                          # MECE事実抽出
```

#### C4. 高度AI/ML分析（20個）
```
📁 AI・機械学習/
├─ advanced_blueprint_engine.py                    # 高度設計図エンジン
├─ advanced_blueprint_engine_v2.py                # 設計図エンジンv2
├─ advanced_anomaly_detector.py                   # 高度異常検知
├─ advanced_implicit_knowledge_engine.py          # 暗黙知エンジン
├─ advanced_processed_data_analyzer.py            # 高度データ分析
├─ ai_comprehensive_report_generator.py           # AIレポート生成
├─ blueprint_integrated_system.py                 # 設計図統合システム
├─ compound_constraint_discovery_system.py        # 複合制約発見
├─ integrated_constraint_extraction_system.py     # 制約抽出システム  
├─ cognitive_psychology_analyzer.py               # 認知心理分析
├─ organizational_pattern_analyzer.py             # 組織パターン分析
├─ system_thinking_analyzer.py                    # システム思考分析
├─ team_dynamics_analyzer.py                      # チーム力学分析
├─ shift_mind_reader.py                          # シフト思考読取
├─ shift_creation_logic_analyzer.py              # シフト作成ロジック分析
├─ predictive_optimization_integration_engine.py  # 予測最適化統合
├─ integrated_mece_analysis_engine.py            # MECE分析統合エンジン
├─ truth_assured_decomposer.py                   # 真実保証分解器
├─ hierarchical_truth_analyzer.py                # 階層真実分析
└─ optimization_algorithms.py                     # 最適化アルゴリズム
```

#### C5. 分析サブモジュール（8個）
```
📁 shift_suite/tasks/analyzers/
├─ attendance_behavior.py    # 出勤行動分析
├─ combined_score.py         # 統合スコア
├─ leave.py                  # 休暇分析
├─ low_staff_load.py         # 低人員負荷分析
├─ rest_time.py              # 休憩時間分析
├─ synergy.py                # シナジー分析
├─ team_dynamics.py          # チーム力学
└─ work_pattern.py           # 作業パターン分析
```

### 【D層】品質保証・テスト（500+ファイル）

#### D1. テスト実行ファイル（200+）
```
📁 テスト実行/
├─ test_*.py                 # 機能テスト群
├─ verify_*.py               # 検証スクリプト群  
├─ comprehensive_*.py        # 包括テスト群
└─ integration_*.py          # 統合テスト群
```

#### D2. デバッグ・分析ツール（300+）
```
📁 デバッグ/
├─ debug_*.py                # デバッグツール群
├─ analyze_*.py              # 分析ツール群
├─ investigate_*.py          # 調査ツール群
├─ check_*.py                # チェックツール群
└─ simple_*.py               # 簡易テスト群
```

### 【E層】データ層

#### E1. 処理済み分析結果
```
📁 extracted_results/
├─ out_p25_based/           # P25基準結果
├─ out_mean_based/          # 平均値基準結果  
├─ out_median_based/        # 中央値基準結果
└─ *.parquet, *.csv         # 構造化データ
```

#### E2. 中間データ
```
📁 データファイル/
├─ daily_cost.parquet       # 日次コスト
├─ fairness_*.parquet       # 公平性データ
├─ leave_analysis.csv       # 休暇分析
├─ staff_balance_daily.csv  # 日次人員バランス
└─ concentration_requested.csv # 集中要請データ
```

### 【F層】環境・設定

#### F1. 依存関係管理
```
📄 requirements.txt         # Python依存パッケージ
📄 pyproject.toml          # プロジェクト設定
📄 runtime.txt             # ランタイム指定
```

#### F2. 実行制御
```
📄 cli.py                  # コマンドライン実行
📄 setup.sh                # セットアップスクリプト
📄 *.bat                   # Windows実行スクリプト
```

### 【G層】ドキュメント・メタ情報

#### G1. 分析レポート（数百ファイル）
```
📁 レポート/
├─ *.md                    # Markdownレポート
├─ *_REPORT.md             # 正式レポート
├─ *.json                  # JSON形式結果
└─ *_SUMMARY.md            # サマリー
```

#### G2. バックアップ・復旧
```
📁 バックアップ/
├─ BACKUP_*_2025*/         # タイムスタンプ付きバックアップ
├─ CRITICAL_BACKUP_*/      # 重要バックアップ
├─ EMERGENCY_BACKUP_*/     # 緊急バックアップ
└─ ROLLBACK_PROCEDURES.md  # ロールバック手順
```

---

## 🎯 実稼働構成の選択指針

### 最小構成（13ファイル）- 基本稼働
```
A層: app.py または dash_app.py     (1ファイル)
B層: io_excel.py + shortage.py + heatmap.py + utils.py    (4ファイル)
E層: extracted_results/out_p25_based/    (1ディレクトリ)
F層: requirements.txt + pyproject.toml + cli.py    (3ファイル)
合計: 13ファイル（基本シフト分析機能）
```

### 推奨構成（25ファイル）- 品質保証付き
```
最小構成 + D層主要テストファイル12個
機能: エラー検知、データ検証、結果確認
用途: 本格運用、信頼性重視
```

### 完全構成（90+ファイル）- 全機能
```
最小構成 + C層全モジュール90個
機能: 全分析機能、AI/ML、高度統計処理
用途: 研究開発、高度分析、カスタマイズ
```

---

## 🔄 システム動作フロー

### 基本実行フロー
```
1. UIアプリ起動 (app.py または dash_app.py)
2. Excelファイルアップロード
3. io_excel.py でデータ読み込み・正規化
4. shortage.py で不足分析実行
5. heatmap.py で可視化生成  
6. 結果をE層に保存・表示
```

### 拡張分析フロー
```
1. 基本フロー実行
2. C層モジュール選択実行
3. 複数分析結果の統合
4. AIレポート生成（ai_comprehensive_report_generator.py）
5. 包括的結果出力
```

---

## 📋 技術仕様詳細

### 主要依存ライブラリ
- **UI**: streamlit, dash, plotly
- **データ処理**: pandas, numpy, openpyxl
- **機械学習**: scikit-learn, tensorflow（一部）
- **可視化**: plotly, matplotlib
- **並列処理**: multiprocessing, threading

### ファイル形式
- **設定**: JSON, TOML
- **データ**: Parquet（高速）, CSV（互換性）, Excel（入力）
- **ログ**: TXT, JSON
- **レポート**: Markdown, JSON

### パフォーマンス特性
- **最小構成**: 軽量、高速起動
- **推奨構成**: バランス型、エラー耐性
- **完全構成**: 高機能、高メモリ使用

---

## 🎨 システムの特徴

### 設計思想
1. **モジュラー設計**: 各層が独立、拡張可能
2. **MECE構造**: 機能重複なし、漏れなし
3. **選択的実行**: 必要機能のみ選択可能
4. **品質重視**: 大量のテスト・検証機能

### 技術的優位性
1. **スケーラブル**: 13ファイル～90+ファイル対応
2. **保守性**: 明確な階層構造、豊富なドキュメント
3. **拡張性**: C層の90+モジュールによる高い拡張性
4. **安定性**: 500+のテスト・デバッグファイル

---

**この文書により、C:\ShiftAnalysis の全体構造・機能・運用方法を完全に理解可能**

---
*生成日時: 2025-01-11*  
*分析対象: C:\ShiftAnalysis 全53,590ファイル*  
*文書バージョン: v1.0（完全版）*