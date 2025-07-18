"""
shift_suite.tasks.turnover_prediction - 離職リスク予測モデル
────────────────────────────────────────────────────────────────
■ 実装内容
  1. 離職リスク因子の特定（働き方パターン、疲労度、公平性など）
  2. 機械学習による離職確率予測
  3. 早期警告システム
  4. 離職リスク軽減提案
  5. チーム離職リスク分析
"""

from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
from sklearn.linear_model import LogisticRegression
import warnings

from .utils import log, save_df_parquet, write_meta

# XGBoost (optional)
try:
    import xgboost as xgb
    _HAS_XGBOOST = True
    log.info("[turnover_prediction] XGBoost detected — Enhanced model available")
except ImportError:
    _HAS_XGBOOST = False
    log.warning("[turnover_prediction] XGBoost not available — Using sklearn models")


class TurnoverPredictionEngine:
    """離職リスク予測エンジン"""
    
    def __init__(self, 
                 model_type: str = 'ensemble',
                 lookback_months: int = 6,
                 enable_early_warning: bool = True):
        """
        Parameters
        ----------
        model_type : str, default 'ensemble'
            使用するモデルタイプ ('logistic', 'random_forest', 'xgboost', 'ensemble')
        lookback_months : int, default 6
            過去何ヶ月分のデータを使って予測するか
        enable_early_warning : bool, default True
            早期警告システムを有効にするか
        """
        self.model_type = model_type
        self.lookback_months = lookback_months
        self.enable_early_warning = enable_early_warning
        
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.feature_importance: Dict[str, float] = {}
        self.risk_thresholds: Dict[str, float] = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.8
        }
        
        log.info(f"[TurnoverPredictionEngine] Initialized with model_type={model_type}, lookback={lookback_months}months")
    
    def extract_turnover_features(self, long_df: pd.DataFrame, staff_metadata: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """離職リスク特徴量の抽出"""
        features_list = []
        
        # 現在の日付を基準とする
        current_date = pd.Timestamp.now()
        
        for staff in long_df['staff'].unique():
            staff_df = long_df[long_df['staff'] == staff].copy()
            
            if len(staff_df) < 10:  # 最小限のデータ量チェック
                continue
            
            # 時系列データの準備
            staff_df['date'] = pd.to_datetime(staff_df['ds'])
            staff_df = staff_df.sort_values('date')
            
            # 月次集計
            monthly_data = []
            end_date = staff_df['date'].max()
            start_date = end_date - pd.DateOffset(months=self.lookback_months)
            
            for month_offset in range(self.lookback_months):
                month_end = end_date - pd.DateOffset(months=month_offset)
                month_start = month_end - pd.DateOffset(months=1)
                
                month_data = staff_df[
                    (staff_df['date'] >= month_start) & 
                    (staff_df['date'] < month_end)
                ]
                
                if month_data.empty:
                    continue
                
                # 基本勤務統計
                total_hours = len(month_data) * 0.5  # 30分スロット想定
                work_days = month_data['date'].dt.date.nunique()
                avg_hours_per_day = total_hours / work_days if work_days > 0 else 0
                
                # 勤務時間の不規則性
                daily_hours = month_data.groupby(month_data['date'].dt.date).size() * 0.5
                hours_variance = daily_hours.var() if len(daily_hours) > 1 else 0
                
                # 勤務開始時刻の不規則性
                start_times = month_data['date'].dt.hour + month_data['date'].dt.minute / 60
                start_time_variance = start_times.var() if len(start_times) > 1 else 0
                
                # 夜勤比率
                night_hours = month_data[
                    (month_data['date'].dt.hour >= 20) | 
                    (month_data['date'].dt.hour < 6)
                ]
                night_ratio = len(night_hours) / len(month_data) if len(month_data) > 0 else 0
                
                # 週末勤務比率
                weekend_hours = month_data[month_data['date'].dt.weekday >= 5]
                weekend_ratio = len(weekend_hours) / len(month_data) if len(month_data) > 0 else 0
                
                # 勤務コードの多様性
                task_diversity = month_data['code'].nunique() if 'code' in month_data.columns else 1
                
                # 連続勤務パターン
                work_dates = sorted(month_data['date'].dt.date.unique())
                consecutive_days = self._calculate_max_consecutive_days(work_dates)
                
                # 休暇取得頻度（勤務がない日を休暇と仮定）
                calendar_days = (month_end - month_start).days
                rest_days = calendar_days - work_days
                rest_ratio = rest_days / calendar_days if calendar_days > 0 else 0
                
                monthly_features = {
                    'staff': staff,
                    'month': month_end.strftime('%Y-%m'),
                    'total_hours': total_hours,
                    'work_days': work_days,
                    'avg_hours_per_day': avg_hours_per_day,
                    'hours_variance': hours_variance,
                    'start_time_variance': start_time_variance,
                    'night_ratio': night_ratio,
                    'weekend_ratio': weekend_ratio,
                    'task_diversity': task_diversity,
                    'consecutive_days': consecutive_days,
                    'rest_ratio': rest_ratio,
                    'months_from_current': month_offset
                }
                
                monthly_data.append(monthly_features)
            
            if monthly_data:
                # スタッフレベルの集計特徴量
                monthly_df = pd.DataFrame(monthly_data)
                
                # 傾向分析（時系列の傾向）
                recent_3m = monthly_df[monthly_df['months_from_current'] < 3]
                older_3m = monthly_df[monthly_df['months_from_current'] >= 3]
                
                if len(recent_3m) > 0 and len(older_3m) > 0:
                    # 勤務時間の変化傾向
                    hours_trend = recent_3m['total_hours'].mean() - older_3m['total_hours'].mean()
                    
                    # 不規則性の変化
                    variance_trend = recent_3m['hours_variance'].mean() - older_3m['hours_variance'].mean()
                    
                    # 夜勤比率の変化
                    night_trend = recent_3m['night_ratio'].mean() - older_3m['night_ratio'].mean()
                else:
                    hours_trend = 0
                    variance_trend = 0
                    night_trend = 0
                
                # 全期間の統計
                staff_features = {
                    'staff': staff,
                    'avg_total_hours': monthly_df['total_hours'].mean(),
                    'std_total_hours': monthly_df['total_hours'].std(),
                    'avg_work_days': monthly_df['work_days'].mean(),
                    'avg_hours_variance': monthly_df['hours_variance'].mean(),
                    'avg_start_time_variance': monthly_df['start_time_variance'].mean(),
                    'avg_night_ratio': monthly_df['night_ratio'].mean(),
                    'avg_weekend_ratio': monthly_df['weekend_ratio'].mean(),
                    'avg_task_diversity': monthly_df['task_diversity'].mean(),
                    'max_consecutive_days': monthly_df['consecutive_days'].max(),
                    'avg_rest_ratio': monthly_df['rest_ratio'].mean(),
                    'hours_trend': hours_trend,
                    'variance_trend': variance_trend,
                    'night_trend': night_trend,
                    'work_consistency': 1.0 / (monthly_df['hours_variance'].mean() + 1),  # 高いほど一貫性がある
                    'schedule_stability': 1.0 / (monthly_df['start_time_variance'].mean() + 1)
                }
                
                # 外部メタデータとの結合
                if staff_metadata is not None and staff in staff_metadata.index:
                    meta = staff_metadata.loc[staff]
                    staff_features.update({
                        'tenure_months': meta.get('tenure_months', 12),  # デフォルト1年
                        'age_group': meta.get('age_group', 'unknown'),
                        'employment_type': meta.get('employment_type', 'unknown'),
                        'department': meta.get('department', 'unknown')
                    })
                else:
                    # デフォルト値
                    staff_features.update({
                        'tenure_months': 12,
                        'age_group': 'unknown',
                        'employment_type': 'unknown',
                        'department': 'unknown'
                    })
                
                features_list.append(staff_features)
        
        if not features_list:
            return pd.DataFrame()
        
        return pd.DataFrame(features_list)
    
    def _calculate_max_consecutive_days(self, work_dates: List[dt.date]) -> int:
        """連続勤務日数の最大値を計算"""
        if not work_dates:
            return 0
        
        max_consecutive = 1
        current_consecutive = 1
        
        for i in range(1, len(work_dates)):
            if (work_dates[i] - work_dates[i-1]).days == 1:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 1
        
        return max_consecutive
    
    def generate_synthetic_labels(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """離職ラベルの合成生成（実際のデータがない場合）"""
        # 離職リスク因子に基づいてラベルを生成
        risk_scores = []
        
        for _, row in features_df.iterrows():
            risk_score = 0
            
            # 勤務時間の不安定性
            if row['std_total_hours'] > row['avg_total_hours'] * 0.3:
                risk_score += 0.2
            
            # 長時間労働
            if row['avg_total_hours'] > 200:  # 月200時間以上
                risk_score += 0.3
            
            # 夜勤比率が高い
            if row['avg_night_ratio'] > 0.4:
                risk_score += 0.2
            
            # 勤務開始時刻の不規則性
            if row['avg_start_time_variance'] > 3:
                risk_score += 0.2
            
            # 連続勤務日数が多い
            if row['max_consecutive_days'] > 7:
                risk_score += 0.15
            
            # 休息時間が少ない
            if row['avg_rest_ratio'] < 0.2:
                risk_score += 0.15
            
            # 勤務パターンの悪化傾向
            if row['hours_trend'] < -20:  # 勤務時間の大幅減少
                risk_score += 0.25
            if row['variance_trend'] > 10:  # 不規則性の増加
                risk_score += 0.2
            
            # 勤務期間の影響
            if row['tenure_months'] < 6:
                risk_score += 0.1  # 新人は離職リスクが高い
            elif row['tenure_months'] > 60:
                risk_score -= 0.1  # 長期勤務者は安定
            
            risk_scores.append(min(risk_score, 1.0))
        
        # リスクスコアを離職確率に変換
        # 閾値を使ってバイナリラベルを生成
        features_df['risk_score'] = risk_scores
        features_df['will_turnover'] = (np.array(risk_scores) > 0.6).astype(int)
        
        return features_df
    
    def prepare_model_data(self, features_df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """機械学習用データの準備"""
        # カテゴリカル変数のエンコーディング
        df_model = features_df.copy()
        
        # カテゴリカル特徴量のエンコーディング
        categorical_features = ['age_group', 'employment_type', 'department']
        
        for feature in categorical_features:
            if feature in df_model.columns:
                le = LabelEncoder()
                df_model[feature + '_encoded'] = le.fit_transform(df_model[feature].astype(str))
        
        # 特徴量の選択
        feature_columns = [
            'avg_total_hours', 'std_total_hours', 'avg_work_days',
            'avg_hours_variance', 'avg_start_time_variance', 'avg_night_ratio',
            'avg_weekend_ratio', 'avg_task_diversity', 'max_consecutive_days',
            'avg_rest_ratio', 'hours_trend', 'variance_trend', 'night_trend',
            'work_consistency', 'schedule_stability', 'tenure_months'
        ]
        
        # エンコードされたカテゴリカル特徴量を追加
        encoded_features = [col for col in df_model.columns if col.endswith('_encoded')]
        feature_columns.extend(encoded_features)
        
        # 実際に存在する特徴量のみを使用
        available_features = [col for col in feature_columns if col in df_model.columns]
        
        X = df_model[available_features].fillna(0).values
        y = df_model['will_turnover'].values
        
        return X, y, available_features
    
    def train_models(self, X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
        """機械学習モデルの訓練"""
        log.info("[TurnoverPredictionEngine] Training turnover prediction models...")
        
        # データ分割
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        
        # スケーリング
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        self.scalers['main'] = scaler
        
        results = {}
        
        # 1. ロジスティック回帰
        if self.model_type in ['logistic', 'ensemble']:
            log_model = LogisticRegression(random_state=42, max_iter=1000)
            log_model.fit(X_train_scaled, y_train)
            
            log_pred_proba = log_model.predict_proba(X_test_scaled)[:, 1]
            log_auc = roc_auc_score(y_test, log_pred_proba) if len(np.unique(y_test)) > 1 else 0.5
            
            self.models['logistic'] = log_model
            results['logistic'] = {
                'auc': log_auc,
                'feature_importance': dict(zip(feature_names, abs(log_model.coef_[0])))
            }
        
        # 2. ランダムフォレスト
        if self.model_type in ['random_forest', 'ensemble']:
            rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
            rf_model.fit(X_train, y_train)
            
            rf_pred_proba = rf_model.predict_proba(X_test)[:, 1]
            rf_auc = roc_auc_score(y_test, rf_pred_proba) if len(np.unique(y_test)) > 1 else 0.5
            
            self.models['random_forest'] = rf_model
            results['random_forest'] = {
                'auc': rf_auc,
                'feature_importance': dict(zip(feature_names, rf_model.feature_importances_))
            }
        
        # 3. XGBoost
        if _HAS_XGBOOST and self.model_type in ['xgboost', 'ensemble']:
            xgb_model = xgb.XGBClassifier(random_state=42, eval_metric='logloss')
            xgb_model.fit(X_train, y_train)
            
            xgb_pred_proba = xgb_model.predict_proba(X_test)[:, 1]
            xgb_auc = roc_auc_score(y_test, xgb_pred_proba) if len(np.unique(y_test)) > 1 else 0.5
            
            self.models['xgboost'] = xgb_model
            results['xgboost'] = {
                'auc': xgb_auc,
                'feature_importance': dict(zip(feature_names, xgb_model.feature_importances_))
            }
        
        # アンサンブルモデル
        if self.model_type == 'ensemble' and len(self.models) > 1:
            # 各モデルの予測を平均
            ensemble_pred = np.mean([
                model.predict_proba(X_test_scaled if 'logistic' in name else X_test)[:, 1]
                for name, model in self.models.items()
            ], axis=0)
            
            ensemble_auc = roc_auc_score(y_test, ensemble_pred) if len(np.unique(y_test)) > 1 else 0.5
            results['ensemble'] = {'auc': ensemble_auc}
        
        # 特徴量重要度の統合
        if results:
            # 最高AUCのモデルの特徴量重要度を使用
            best_model = max(results.keys(), key=lambda k: results[k]['auc'])
            if 'feature_importance' in results[best_model]:
                self.feature_importance = results[best_model]['feature_importance']
        
        log.info(f"[TurnoverPredictionEngine] Models trained - Best AUC: {max([r['auc'] for r in results.values()]):.4f}")
        
        return results
    
    def predict_turnover_risk(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """離職リスクの予測"""
        if not self.models:
            log.warning("[TurnoverPredictionEngine] No trained models available")
            return pd.DataFrame()
        
        # データ準備
        X, _, feature_names = self.prepare_model_data(features_df)
        
        predictions = []
        
        for idx, (_, row) in enumerate(features_df.iterrows()):
            staff = row['staff']
            
            # 各モデルの予測
            model_predictions = {}
            
            for model_name, model in self.models.items():
                if model_name == 'logistic':
                    X_scaled = self.scalers['main'].transform([X[idx]])
                    pred_proba = model.predict_proba(X_scaled)[0, 1]
                else:
                    pred_proba = model.predict_proba([X[idx]])[0, 1]
                
                model_predictions[model_name] = pred_proba
            
            # アンサンブル予測
            if len(model_predictions) > 1:
                ensemble_pred = np.mean(list(model_predictions.values()))
            else:
                ensemble_pred = list(model_predictions.values())[0]
            
            # リスクレベルの判定
            if ensemble_pred >= self.risk_thresholds['high']:
                risk_level = 'high'
            elif ensemble_pred >= self.risk_thresholds['medium']:
                risk_level = 'medium'
            elif ensemble_pred >= self.risk_thresholds['low']:
                risk_level = 'low'
            else:
                risk_level = 'very_low'
            
            prediction_result = {
                'staff': staff,
                'turnover_probability': ensemble_pred,
                'risk_level': risk_level,
                'prediction_date': dt.datetime.now().strftime('%Y-%m-%d'),
                **{f'{model}_prob': prob for model, prob in model_predictions.items()}
            }
            
            predictions.append(prediction_result)
        
        return pd.DataFrame(predictions)
    
    def generate_risk_alerts(self, predictions_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """離職リスクアラートの生成"""
        alerts = []
        
        # 高リスクスタッフ
        high_risk = predictions_df[predictions_df['risk_level'] == 'high']
        
        for _, staff_risk in high_risk.iterrows():
            alerts.append({
                'staff': staff_risk['staff'],
                'level': 'critical',
                'type': 'high_turnover_risk',
                'message': f"{staff_risk['staff']}さんの離職リスクが高く検出されました（確率: {staff_risk['turnover_probability']:.1%}）",
                'probability': staff_risk['turnover_probability'],
                'recommendations': self._get_retention_recommendations(staff_risk['staff'])
            })
        
        # 中リスクでも数が多い場合は警告
        medium_risk = predictions_df[predictions_df['risk_level'] == 'medium']
        if len(medium_risk) >= 3:
            alerts.append({
                'staff': 'team',
                'level': 'warning',
                'type': 'team_turnover_risk',
                'message': f"中程度の離職リスクスタッフが{len(medium_risk)}名います。チーム全体の働き方見直しを検討してください。",
                'affected_staff': medium_risk['staff'].tolist(),
                'recommendations': ['チーム全体の負荷分散', '働き方の見直し', '定期面談の実施']
            })
        
        return alerts
    
    def _get_retention_recommendations(self, staff: str) -> List[str]:
        """個別スタッフへの離職防止提案"""
        recommendations = [
            '上司との定期面談の実施',
            'キャリアパス相談の機会提供',
            '勤務時間・シフトの調整検討',
            '業務負荷の見直し'
        ]
        
        # 特徴量重要度に基づいた具体的提案
        if self.feature_importance:
            top_factors = sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)[:3]
            
            for factor, _ in top_factors:
                if 'hours' in factor:
                    recommendations.append('労働時間の管理・調整')
                elif 'night' in factor:
                    recommendations.append('夜勤頻度の見直し')
                elif 'variance' in factor:
                    recommendations.append('勤務スケジュールの安定化')
                elif 'rest' in factor:
                    recommendations.append('休暇取得の促進')
        
        return list(set(recommendations))  # 重複除去
    
    def analyze_team_turnover_risk(self, predictions_df: pd.DataFrame) -> Dict[str, Any]:
        """チーム全体の離職リスク分析"""
        analysis = {
            'total_staff': len(predictions_df),
            'high_risk_count': len(predictions_df[predictions_df['risk_level'] == 'high']),
            'medium_risk_count': len(predictions_df[predictions_df['risk_level'] == 'medium']),
            'average_risk': predictions_df['turnover_probability'].mean(),
            'risk_distribution': predictions_df['risk_level'].value_counts().to_dict()
        }
        
        # リスクが高い場合の影響分析
        if analysis['high_risk_count'] > 0:
            analysis['business_impact'] = {
                'potential_loss_percentage': (analysis['high_risk_count'] / analysis['total_staff']) * 100,
                'critical_warning': analysis['high_risk_count'] >= 3,
                'immediate_action_required': analysis['average_risk'] > 0.6
            }
        
        # 改善提案
        improvement_suggestions = []
        
        if analysis['average_risk'] > 0.4:
            improvement_suggestions.append('チーム全体の働き方改革が必要')
        
        if analysis['high_risk_count'] > 0:
            improvement_suggestions.append('高リスクスタッフとの個別面談を早急に実施')
        
        if analysis['medium_risk_count'] > analysis['total_staff'] * 0.3:
            improvement_suggestions.append('職場環境の全体的な見直しを推奨')
        
        analysis['improvement_suggestions'] = improvement_suggestions
        
        return analysis


def predict_staff_turnover(
    long_df: pd.DataFrame,
    output_path: Path,
    *,
    model_type: str = 'ensemble',
    lookback_months: int = 6,
    staff_metadata: Optional[pd.DataFrame] = None
) -> Path:
    """
    スタッフの離職リスク予測を実行
    
    Parameters
    ----------
    long_df : pd.DataFrame
        シフトデータ（long形式）
    output_path : Path
        出力ファイルパス
    model_type : str, default 'ensemble'
        使用するモデルタイプ
    lookback_months : int, default 6
        分析対象期間（月数）
    staff_metadata : pd.DataFrame, optional
        スタッフメタデータ（年齢、雇用形態等）
    
    Returns
    -------
    Path
        出力ファイルパス
    """
    log.info(f"[predict_staff_turnover] Starting turnover prediction")
    
    # 予測エンジンの初期化
    engine = TurnoverPredictionEngine(
        model_type=model_type,
        lookback_months=lookback_months,
        enable_early_warning=True
    )
    
    # 特徴量抽出
    features_df = engine.extract_turnover_features(long_df, staff_metadata)
    if features_df.empty:
        log.warning("[predict_staff_turnover] No features extracted")
        return output_path
    
    # 合成ラベルの生成（実際の離職データがない場合）
    features_with_labels = engine.generate_synthetic_labels(features_df)
    
    # モデル用データの準備
    X, y, feature_names = engine.prepare_model_data(features_with_labels)
    
    # モデル訓練
    training_results = engine.train_models(X, y, feature_names)
    
    # 離職リスク予測
    predictions_df = engine.predict_turnover_risk(features_with_labels)
    
    # アラート生成
    alerts = engine.generate_risk_alerts(predictions_df)
    
    # チーム分析
    team_analysis = engine.analyze_team_turnover_risk(predictions_df)
    
    # 結果の保存
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_df_parquet(predictions_df, output_path)
    
    # メタデータ保存
    write_meta(
        output_path.with_suffix('.meta.json'),
        model_type=model_type,
        lookback_months=lookback_months,
        training_results=training_results,
        feature_importance=engine.feature_importance,
        alerts_count=len(alerts),
        critical_alerts=[a for a in alerts if a['level'] == 'critical'],
        team_analysis=team_analysis,
        created=str(dt.datetime.now())
    )
    
    # アラートの保存
    if alerts:
        alerts_df = pd.DataFrame(alerts)
        save_df_parquet(alerts_df, output_path.with_stem(output_path.stem + '_alerts'))
    
    log.info(f"[predict_staff_turnover] Turnover prediction completed → {output_path}")
    log.info(f"[predict_staff_turnover] Generated {len(alerts)} alerts ({len([a for a in alerts if a['level'] == 'critical'])} critical)")
    
    return output_path


__all__ = ['TurnoverPredictionEngine', 'predict_staff_turnover']