#!/usr/bin/env python
"""
動的需要予測エンジン

実際のシフトデータから学習し、将来の人員需要を予測する
機械学習ベースの需要予測システム
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import LabelEncoder, StandardScaler
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class PredictiveDemandEngine:
    """動的需要予測エンジン"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.shift_data = None
        self.models = {}
        self.feature_importance = {}
        self.prediction_accuracy = {}
        
    def load_and_prepare_data(self) -> pd.DataFrame:
        """データの読み込みと前処理"""
        intermediate_file = self.data_dir / "intermediate_data.parquet"
        
        if not intermediate_file.exists():
            raise FileNotFoundError(f"データファイルが見つかりません: {intermediate_file}")
        
        df = pd.read_parquet(intermediate_file)
        log.info(f"データ読み込み: {len(df):,}レコード")
        
        # 特徴量エンジニアリング
        df = self._engineer_features(df)
        
        self.shift_data = df
        return df
    
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """高度な特徴量エンジニアリング"""
        df = df.copy()
        
        # 時間関連特徴量
        df['datetime'] = pd.to_datetime(df['ds'])
        df['date'] = df['datetime'].dt.date
        df['hour'] = df['datetime'].dt.hour
        df['minute'] = df['datetime'].dt.minute
        df['weekday'] = df['datetime'].dt.weekday
        df['month'] = df['datetime'].dt.month
        df['quarter'] = df['datetime'].dt.quarter
        df['day_of_month'] = df['datetime'].dt.day
        df['week_of_year'] = df['datetime'].dt.isocalendar().week
        
        # 時間帯分類
        df['time_category'] = df['hour'].apply(self._categorize_time)
        
        # 曜日分類
        df['day_type'] = df['weekday'].apply(lambda x: 'weekend' if x >= 5 else 'weekday')
        
        # ラグ特徴量（前日・前週の需要）
        df = self._create_lag_features(df)
        
        # 移動平均特徴量
        df = self._create_moving_average_features(df)
        
        # 職種・雇用形態のエンコーディング
        le_role = LabelEncoder()
        le_employment = LabelEncoder()
        
        df['role_encoded'] = le_role.fit_transform(df['role'].fillna('unknown'))
        df['employment_encoded'] = le_employment.fit_transform(df['employment'].fillna('unknown'))
        
        # 交互作用特徴量
        df['hour_weekday'] = df['hour'] * 10 + df['weekday']
        df['role_hour'] = df['role_encoded'] * 100 + df['hour']
        
        # 季節性特徴量
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['weekday_sin'] = np.sin(2 * np.pi * df['weekday'] / 7)
        df['weekday_cos'] = np.cos(2 * np.pi * df['weekday'] / 7)
        
        return df
    
    def _categorize_time(self, hour: int) -> str:
        """時間帯の分類"""
        if 6 <= hour < 9:
            return 'morning'
        elif 9 <= hour < 12:
            return 'mid_morning'
        elif 12 <= hour < 14:
            return 'lunch'
        elif 14 <= hour < 17:
            return 'afternoon'
        elif 17 <= hour < 20:
            return 'evening'
        elif 20 <= hour < 23:
            return 'night'
        else:
            return 'deep_night'
    
    def _create_lag_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """ラグ特徴量の作成"""
        df = df.sort_values(['role', 'staff', 'datetime'])
        
        # 職種別ラグ特徴量
        for role in df['role'].unique():
            role_mask = df['role'] == role
            role_data = df[role_mask].copy()
            
            # 日次集計
            daily_demand = role_data.groupby(['date'])['parsed_slots_count'].sum().reset_index()
            daily_demand['date'] = pd.to_datetime(daily_demand['date'])
            
            # 前日需要
            daily_demand['prev_day_demand'] = daily_demand['parsed_slots_count'].shift(1)
            
            # 前週同曜日需要
            daily_demand['prev_week_demand'] = daily_demand['parsed_slots_count'].shift(7)
            
            # 元データにマージ
            df.loc[role_mask, 'date_temp'] = pd.to_datetime(df.loc[role_mask, 'date'])
            df = df.merge(
                daily_demand[['date', 'prev_day_demand', 'prev_week_demand']],
                left_on='date_temp',
                right_on='date',
                how='left',
                suffixes=('', f'_{role}')
            )
        
        # 不要な列を削除
        df = df.drop(columns=[col for col in df.columns if 'date_temp' in col or col.endswith('_date')])
        
        return df
    
    def _create_moving_average_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """移動平均特徴量の作成"""
        df = df.sort_values(['role', 'datetime'])
        
        for role in df['role'].unique():
            role_mask = df['role'] == role
            role_data = df[role_mask].copy()
            
            # 3日移動平均
            role_data['ma_3d'] = role_data['parsed_slots_count'].rolling(window=3, min_periods=1).mean()
            
            # 7日移動平均  
            role_data['ma_7d'] = role_data['parsed_slots_count'].rolling(window=7, min_periods=1).mean()
            
            # 移動標準偏差
            role_data['std_7d'] = role_data['parsed_slots_count'].rolling(window=7, min_periods=1).std()
            
            df.loc[role_mask, 'ma_3d'] = role_data['ma_3d']
            df.loc[role_mask, 'ma_7d'] = role_data['ma_7d']
            df.loc[role_mask, 'std_7d'] = role_data['std_7d'].fillna(0)
        
        return df
    
    def train_predictive_models(self) -> Dict[str, Dict]:
        """予測モデルの訓練"""
        if self.shift_data is None:
            raise ValueError("データが読み込まれていません")
        
        df = self.shift_data
        
        # 特徴量の選択
        feature_columns = [
            'hour', 'weekday', 'month', 'day_of_month',
            'role_encoded', 'employment_encoded',
            'hour_sin', 'hour_cos', 'weekday_sin', 'weekday_cos',
            'hour_weekday', 'role_hour',
            'ma_3d', 'ma_7d', 'std_7d'
        ]
        
        # ラグ特徴量を追加（存在する場合）
        lag_features = [col for col in df.columns if 'prev_' in col]
        feature_columns.extend(lag_features)
        
        # 存在する特徴量のみを使用
        available_features = [col for col in feature_columns if col in df.columns]
        
        X = df[available_features].fillna(0)
        y = df['parsed_slots_count']
        
        log.info(f"使用特徴量: {len(available_features)}個")
        log.info(f"訓練データ: {len(X)}サンプル")
        
        # 職種別モデル訓練
        model_results = {}
        
        for role in df['role'].unique():
            role_mask = df['role'] == role
            X_role = X[role_mask]
            y_role = y[role_mask]
            
            if len(X_role) < 10:  # データ不足の場合はスキップ
                log.warning(f"職種 {role} はデータ不足のためスキップ")
                continue
            
            # 訓練・テストデータ分割
            X_train, X_test, y_train, y_test = train_test_split(
                X_role, y_role, test_size=0.2, random_state=42
            )
            
            # 複数モデルの比較
            models = {
                'random_forest': RandomForestRegressor(
                    n_estimators=100, 
                    max_depth=10, 
                    random_state=42,
                    n_jobs=-1
                ),
                'gradient_boosting': GradientBoostingRegressor(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42
                )
            }
            
            best_model = None
            best_score = float('inf')
            model_comparison = {}
            
            for model_name, model in models.items():
                try:
                    # 訓練
                    model.fit(X_train, y_train)
                    
                    # 予測
                    y_pred = model.predict(X_test)
                    
                    # 評価
                    mae = mean_absolute_error(y_test, y_pred)
                    mse = mean_squared_error(y_test, y_pred)
                    rmse = np.sqrt(mse)
                    
                    # クロスバリデーション
                    cv_scores = cross_val_score(model, X_train, y_train, cv=3, scoring='neg_mean_absolute_error')
                    cv_mae = -cv_scores.mean()
                    
                    model_comparison[model_name] = {
                        'mae': mae,
                        'rmse': rmse,
                        'cv_mae': cv_mae,
                        'feature_importance': dict(zip(available_features, model.feature_importances_)) if hasattr(model, 'feature_importances_') else {}
                    }
                    
                    if mae < best_score:
                        best_score = mae
                        best_model = model
                    
                    log.info(f"職種 {role} - {model_name}: MAE={mae:.3f}, RMSE={rmse:.3f}")
                    
                except Exception as e:
                    log.error(f"職種 {role} - {model_name} 訓練エラー: {e}")
            
            if best_model is not None:
                self.models[role] = best_model
                model_results[role] = {
                    'best_model': type(best_model).__name__,
                    'performance': model_comparison,
                    'data_size': len(X_role),
                    'features_used': available_features
                }
                
                # 特徴量重要度の保存
                if hasattr(best_model, 'feature_importances_'):
                    self.feature_importance[role] = dict(zip(available_features, best_model.feature_importances_))
        
        log.info(f"モデル訓練完了: {len(self.models)}職種")
        return model_results
    
    def predict_future_demand(self, forecast_days: int = 7) -> Dict[str, Dict]:
        """将来需要の予測"""
        if not self.models:
            raise ValueError("モデルが訓練されていません")
        
        predictions = {}
        last_date = pd.to_datetime(self.shift_data['ds']).max()
        
        # 予測期間の生成
        future_dates = pd.date_range(
            start=last_date + timedelta(days=1),
            periods=forecast_days * 48,  # 30分スロット想定
            freq='30T'
        )
        
        # 職種別予測
        for role, model in self.models.items():
            try:
                role_predictions = []
                
                for future_time in future_dates:
                    # 特徴量の作成
                    features = self._create_prediction_features(future_time, role)
                    
                    # 予測実行
                    predicted_demand = model.predict([features])[0]
                    predicted_demand = max(0, predicted_demand)  # 負の値を防ぐ
                    
                    role_predictions.append({
                        'datetime': future_time.isoformat(),
                        'predicted_demand': float(predicted_demand),
                        'hour': future_time.hour,
                        'weekday': future_time.weekday(),
                        'confidence': self._estimate_prediction_confidence(role, features)
                    })
                
                predictions[role] = {
                    'predictions': role_predictions,
                    'total_predicted_hours': sum(p['predicted_demand'] for p in role_predictions) * 0.5,
                    'avg_daily_demand': sum(p['predicted_demand'] for p in role_predictions) * 0.5 / forecast_days
                }
                
                log.info(f"職種 {role} 予測完了: {len(role_predictions)}時間帯")
                
            except Exception as e:
                log.error(f"職種 {role} 予測エラー: {e}")
        
        return predictions
    
    def _create_prediction_features(self, future_time: datetime, role: str) -> List[float]:
        """予測用特徴量の作成"""
        features = []
        
        # 基本時間特徴量
        hour = future_time.hour
        weekday = future_time.weekday()
        month = future_time.month
        day_of_month = future_time.day
        
        # エンコーディング（訓練時の値を使用）
        role_encoded = hash(role) % 100  # 簡易エンコーディング
        employment_encoded = 0  # デフォルト値
        
        # 周期特徴量
        hour_sin = np.sin(2 * np.pi * hour / 24)
        hour_cos = np.cos(2 * np.pi * hour / 24)
        weekday_sin = np.sin(2 * np.pi * weekday / 7)
        weekday_cos = np.cos(2 * np.pi * weekday / 7)
        
        # 交互作用特徴量
        hour_weekday = hour * 10 + weekday
        role_hour = role_encoded * 100 + hour
        
        # 移動平均（過去データから推定）
        ma_3d = self._estimate_moving_average(role, 3)
        ma_7d = self._estimate_moving_average(role, 7)
        std_7d = self._estimate_moving_std(role, 7)
        
        features = [
            hour, weekday, month, day_of_month,
            role_encoded, employment_encoded,
            hour_sin, hour_cos, weekday_sin, weekday_cos,
            hour_weekday, role_hour,
            ma_3d, ma_7d, std_7d
        ]
        
        return features
    
    def _estimate_moving_average(self, role: str, window: int) -> float:
        """移動平均の推定"""
        role_data = self.shift_data[self.shift_data['role'] == role]
        if len(role_data) >= window:
            return role_data['parsed_slots_count'].tail(window).mean()
        return role_data['parsed_slots_count'].mean() if len(role_data) > 0 else 1.0
    
    def _estimate_moving_std(self, role: str, window: int) -> float:
        """移動標準偏差の推定"""
        role_data = self.shift_data[self.shift_data['role'] == role]
        if len(role_data) >= window:
            return role_data['parsed_slots_count'].tail(window).std()
        return role_data['parsed_slots_count'].std() if len(role_data) > 0 else 0.5
    
    def _estimate_prediction_confidence(self, role: str, features: List[float]) -> float:
        """予測信頼度の推定"""
        # 簡易的な信頼度推定
        role_data = self.shift_data[self.shift_data['role'] == role]
        data_size = len(role_data)
        
        # データサイズベースの信頼度
        size_confidence = min(1.0, data_size / 100)
        
        # 時間帯ベースの信頼度（営業時間内は高い）
        hour = int(features[0])
        time_confidence = 0.9 if 8 <= hour <= 18 else 0.6
        
        return (size_confidence + time_confidence) / 2

def run_predictive_analysis(data_dir: str, forecast_days: int = 7) -> Dict[str, any]:
    """予測分析の実行"""
    engine = PredictiveDemandEngine(Path(data_dir))
    
    try:
        # 1. データ準備
        log.info("=== データ準備 ===")
        engine.load_and_prepare_data()
        
        # 2. モデル訓練
        log.info("=== 予測モデル訓練 ===")
        model_results = engine.train_predictive_models()
        
        # 3. 将来需要予測
        log.info("=== 将来需要予測 ===")
        predictions = engine.predict_future_demand(forecast_days)
        
        # 4. 結果の統合
        final_result = {
            'model_performance': model_results,
            'future_predictions': predictions,
            'feature_importance': engine.feature_importance,
            'forecast_period': f"{forecast_days} days",
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        # 結果保存
        output_file = Path(data_dir) / "predictive_demand_analysis.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2)
        
        log.info(f"予測分析完了: {output_file}")
        
        # サマリー表示
        print("=== 予測需要分析結果 ===")
        total_predicted_hours = sum(
            pred['total_predicted_hours'] for pred in predictions.values()
        )
        print(f"予測期間: {forecast_days}日間")
        print(f"予測総需要: {total_predicted_hours:.1f}時間")
        print(f"訓練済みモデル: {len(model_results)}職種")
        
        return final_result
        
    except Exception as e:
        log.error(f"予測分析エラー: {e}")
        raise

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法: python predictive_demand_engine.py [データディレクトリ] [予測日数]")
        sys.exit(1)
    
    data_dir = sys.argv[1]
    forecast_days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    
    result = run_predictive_analysis(data_dir, forecast_days)
    print(f"\n{forecast_days}日間の需要予測が完了しました！")