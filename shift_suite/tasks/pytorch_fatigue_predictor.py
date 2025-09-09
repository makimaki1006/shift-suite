"""
PyTorch LSTM-based Fatigue Prediction System
科学的根拠に基づく深層学習疲労予測モデル
"""

import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import warnings

log = logging.getLogger(__name__)


class FatigueLSTMModel(nn.Module):
    """LSTM-based fatigue prediction model"""
    
    def __init__(self, input_size: int, hidden_size: int = 64, num_layers: int = 2, dropout: float = 0.2):
        super(FatigueLSTMModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True
        )
        
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_size,
            num_heads=8,
            dropout=dropout,
            batch_first=True
        )
        
        self.fc_layers = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 2, hidden_size // 4),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 4, 1),
            nn.Sigmoid()  # 疲労度 0-1 の範囲
        )
        
    def forward(self, x):
        # LSTM forward pass
        lstm_out, (h_n, c_n) = self.lstm(x)
        
        # Self-attention mechanism
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
        
        # Use last timestep output
        final_out = attn_out[:, -1, :]
        
        # Final prediction
        fatigue_score = self.fc_layers(final_out)
        
        return fatigue_score


class PyTorchFatiguePredictor:
    """PyTorch based fatigue prediction system with LSTM and attention"""
    
    def __init__(self, sequence_length: int = 14, device: str = None):
        self.sequence_length = sequence_length  # 14日間の履歴を使用
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = [
            'work_hours', 'is_night_shift', 'consecutive_days',
            'weekly_total_hours', 'shift_irregularity_score',
            'workload_intensity', 'recovery_time', 'is_weekend',
            'overtime_hours', 'break_duration', 'commute_time'
        ]
        
        # 科学的疲労閾値（産業医学基準）
        self.fatigue_thresholds = {
            'normal': 0.3,
            'caution': 0.5,
            'warning': 0.7,
            'danger': 0.8
        }
        
        log.info(f"[PyTorchFatiguePredictor] Initialized with device: {self.device}")
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """特徴量エンジニアリング"""
        result_df = df.copy()
        
        # 基本特徴量
        result_df['work_hours'] = result_df.get('work_hours', 0)
        result_df['is_night_shift'] = result_df.get('is_night_shift', 0)
        result_df['is_weekend'] = result_df.get('is_weekend', 0)
        
        # 連続勤務日数の計算
        result_df['consecutive_days'] = 0
        for staff in result_df['staff'].unique():
            staff_mask = result_df['staff'] == staff
            staff_data = result_df[staff_mask].sort_values('date')
            consecutive = 0
            consecutive_list = []
            
            for _, row in staff_data.iterrows():
                if row['work_hours'] > 0:
                    consecutive += 1
                else:
                    consecutive = 0
                consecutive_list.append(consecutive)
            
            result_df.loc[staff_mask, 'consecutive_days'] = consecutive_list
        
        # 週間労働時間の計算
        result_df['weekly_total_hours'] = 0
        for staff in result_df['staff'].unique():
            staff_mask = result_df['staff'] == staff
            staff_data = result_df[staff_mask].sort_values('date')
            
            weekly_hours = []
            for i in range(len(staff_data)):
                start_idx = max(0, i - 6)
                week_hours = staff_data.iloc[start_idx:i+1]['work_hours'].sum()
                weekly_hours.append(week_hours)
            
            result_df.loc[staff_mask, 'weekly_total_hours'] = weekly_hours
        
        # シフト不規則性スコア
        result_df['shift_irregularity_score'] = 0
        for staff in result_df['staff'].unique():
            staff_mask = result_df['staff'] == staff
            staff_data = result_df[staff_mask].sort_values('date')
            
            irregularity_scores = []
            for i in range(len(staff_data)):
                if i < 4:
                    irregularity_scores.append(0)
                else:
                    # 過去4日間の勤務開始時間の分散
                    past_4_days = staff_data.iloc[i-3:i+1]
                    work_days = past_4_days[past_4_days['work_hours'] > 0]
                    if len(work_days) >= 2:
                        # 簡易的な不規則性スコア（実際には開始時間データが必要）
                        night_shift_variance = work_days['is_night_shift'].var()
                        irregularity_scores.append(min(1.0, night_shift_variance * 2))
                    else:
                        irregularity_scores.append(0)
            
            result_df.loc[staff_mask, 'shift_irregularity_score'] = irregularity_scores
        
        # 追加特徴量（推定値）
        result_df['workload_intensity'] = np.where(
            result_df['work_hours'] > 10, 1.0,
            np.where(result_df['work_hours'] > 8, 0.7, 0.4)
        )
        
        result_df['recovery_time'] = np.where(
            result_df['work_hours'] == 0, 24,  # 休日は24時間回復
            np.where(result_df['work_hours'] <= 8, 16, 12)  # 勤務時間による回復時間
        )
        
        result_df['overtime_hours'] = np.maximum(0, result_df['work_hours'] - 8)
        result_df['break_duration'] = np.where(result_df['work_hours'] > 6, 1, 0.5)
        result_df['commute_time'] = 1.0  # 仮定値
        
        return result_df
    
    def create_sequences(self, data: np.ndarray, target: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """時系列データをLSTM用のシーケンスに変換"""
        X, y = [], []
        
        for i in range(self.sequence_length, len(data)):
            X.append(data[i-self.sequence_length:i])
            y.append(target[i])
        
        return np.array(X), np.array(y)
    
    def calculate_scientific_fatigue_target(self, df: pd.DataFrame) -> np.ndarray:
        """科学的根拠に基づく疲労度ターゲット値の計算"""
        fatigue_scores = []
        
        for _, row in df.iterrows():
            # 科学的疲労モデル（improved_fatigue_prediction.pyベース）
            
            # 連続勤務による疲労（指数的増加）
            consecutive_days = row['consecutive_days']
            if consecutive_days <= 2:
                consecutive_fatigue = consecutive_days * 0.1
            else:
                consecutive_fatigue = min(1.0, 0.2 + (consecutive_days - 2) ** 1.5 * 0.15)
            
            # 夜勤による疲労
            night_fatigue = row['is_night_shift'] * 0.4
            
            # 週間労働時間による疲労
            weekly_hours = row['weekly_total_hours']
            if weekly_hours <= 40:
                weekly_fatigue = weekly_hours / 40 * 0.3
            else:
                excess_hours = weekly_hours - 40
                weekly_fatigue = min(1.0, 0.3 + (excess_hours / 10) ** 1.3 * 0.4)
            
            # シフト不規則性による疲労
            irregularity_fatigue = row['shift_irregularity_score'] * 0.25
            
            # 重み付き合計（産業医学基準）
            total_fatigue = (
                consecutive_fatigue * 0.40 +
                night_fatigue * 0.30 +
                weekly_fatigue * 0.20 +
                irregularity_fatigue * 0.10
            )
            
            fatigue_scores.append(min(1.0, total_fatigue))
        
        return np.array(fatigue_scores)
    
    def train_model(self, df: pd.DataFrame, epochs: int = 100, batch_size: int = 32, 
                   learning_rate: float = 0.001) -> Dict:
        """モデルの訓練"""
        log.info("[PyTorchFatiguePredictor] Starting model training")
        
        # 特徴量準備
        processed_df = self.prepare_features(df)
        
        # 科学的疲労度ターゲット計算
        fatigue_target = self.calculate_scientific_fatigue_target(processed_df)
        
        # 特徴量選択と正規化
        feature_data = processed_df[self.feature_columns].values
        feature_data_scaled = self.scaler.fit_transform(feature_data)
        
        # シーケンス作成
        X, y = self.create_sequences(feature_data_scaled, fatigue_target)
        
        if len(X) < 100:
            warnings.warn("訓練データが不足しています。より多くのデータが推奨されます。")
        
        # 訓練・検証分割
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=False
        )
        
        # PyTorchテンソルに変換
        X_train_tensor = torch.FloatTensor(X_train).to(self.device)
        y_train_tensor = torch.FloatTensor(y_train).to(self.device)
        X_test_tensor = torch.FloatTensor(X_test).to(self.device)
        y_test_tensor = torch.FloatTensor(y_test).to(self.device)
        
        # モデル初期化
        input_size = len(self.feature_columns)
        self.model = FatigueLSTMModel(input_size).to(self.device)
        
        # 最適化とロス関数
        optimizer = optim.Adam(self.model.parameters(), lr=learning_rate, weight_decay=1e-5)
        criterion = nn.MSELoss()
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10, factor=0.5)
        
        # 訓練ループ
        train_losses, val_losses = [], []
        best_val_loss = float('inf')
        patience_counter = 0
        
        for epoch in range(epochs):
            # 訓練モード
            self.model.train()
            optimizer.zero_grad()
            
            train_pred = self.model(X_train_tensor).squeeze()
            train_loss = criterion(train_pred, y_train_tensor)
            
            train_loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            optimizer.step()
            
            # 検証
            self.model.eval()
            with torch.no_grad():
                val_pred = self.model(X_test_tensor).squeeze()
                val_loss = criterion(val_pred, y_test_tensor)
            
            train_losses.append(train_loss.item())
            val_losses.append(val_loss.item())
            
            scheduler.step(val_loss)
            
            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                # モデル保存
                torch.save(self.model.state_dict(), 'best_fatigue_model.pth')
            else:
                patience_counter += 1
                if patience_counter > 20:
                    log.info(f"Early stopping at epoch {epoch}")
                    break
            
            if epoch % 20 == 0:
                log.info(f"Epoch {epoch}: Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
        
        # 最良モデルをロード
        self.model.load_state_dict(torch.load('best_fatigue_model.pth'))
        
        # 性能評価
        self.model.eval()
        with torch.no_grad():
            final_pred = self.model(X_test_tensor).squeeze()
            mse = criterion(final_pred, y_test_tensor).item()
            mae = torch.mean(torch.abs(final_pred - y_test_tensor)).item()
            
            # 相関係数
            pred_np = final_pred.cpu().numpy()
            test_np = y_test_tensor.cpu().numpy()
            correlation = np.corrcoef(pred_np, test_np)[0, 1]
        
        training_results = {
            'final_mse': mse,
            'final_mae': mae,
            'correlation': correlation,
            'train_losses': train_losses,
            'val_losses': val_losses,
            'total_epochs': len(train_losses),
            'best_val_loss': best_val_loss
        }
        
        log.info(f"[PyTorchFatiguePredictor] Training completed. MSE: {mse:.4f}, MAE: {mae:.4f}, Correlation: {correlation:.4f}")
        
        return training_results
    
    def predict_fatigue(self, df: pd.DataFrame) -> pd.DataFrame:
        """疲労度予測"""
        if self.model is None:
            raise ValueError("モデルが訓練されていません。train_model()を先に実行してください。")
        
        processed_df = self.prepare_features(df)
        result_df = processed_df.copy()
        
        # 特徴量正規化
        feature_data = processed_df[self.feature_columns].values
        feature_data_scaled = self.scaler.transform(feature_data)
        
        predictions = []
        
        # スタッフごとに予測
        for staff in processed_df['staff'].unique():
            staff_mask = processed_df['staff'] == staff
            staff_data = feature_data_scaled[staff_mask]
            
            staff_predictions = []
            
            for i in range(len(staff_data)):
                if i < self.sequence_length:
                    # 初期期間は科学的計算による代替
                    row = processed_df[staff_mask].iloc[i]
                    scientific_score = self._calculate_scientific_fallback(row)
                    staff_predictions.append(scientific_score)
                else:
                    # LSTM予測
                    sequence = staff_data[i-self.sequence_length:i]
                    sequence_tensor = torch.FloatTensor(sequence).unsqueeze(0).to(self.device)
                    
                    self.model.eval()
                    with torch.no_grad():
                        pred = self.model(sequence_tensor).item()
                    
                    staff_predictions.append(pred)
            
            predictions.extend(staff_predictions)
        
        result_df['fatigue_score'] = predictions
        result_df['risk_level'] = result_df['fatigue_score'].apply(self._classify_risk_level)
        
        return result_df
    
    def _calculate_scientific_fallback(self, row: pd.Series) -> float:
        """初期期間用の科学的疲労度計算"""
        consecutive_fatigue = min(1.0, row['consecutive_days'] * 0.15)
        night_fatigue = row['is_night_shift'] * 0.4
        weekly_fatigue = min(1.0, row['weekly_total_hours'] / 40 * 0.3)
        irregularity_fatigue = row['shift_irregularity_score'] * 0.25
        
        return min(1.0, 
                  consecutive_fatigue * 0.40 +
                  night_fatigue * 0.30 +
                  weekly_fatigue * 0.20 +
                  irregularity_fatigue * 0.10)
    
    def _classify_risk_level(self, fatigue_score: float) -> str:
        """疲労度によるリスク分類"""
        if fatigue_score < self.fatigue_thresholds['normal']:
            return 'normal'
        elif fatigue_score < self.fatigue_thresholds['caution']:
            return 'caution'
        elif fatigue_score < self.fatigue_thresholds['warning']:
            return 'warning'
        else:
            return 'danger'
    
    def predict_future_fatigue(self, current_data: pd.DataFrame, 
                              future_shifts: pd.DataFrame, days_ahead: int = 7) -> Dict:
        """将来疲労度予測"""
        if self.model is None:
            raise ValueError("モデルが訓練されていません。")
        
        predictions = {}
        
        for staff in current_data['staff'].unique():
            staff_current = current_data[current_data['staff'] == staff]
            staff_future = future_shifts[future_shifts['staff'] == staff]
            
            if len(staff_current) < self.sequence_length:
                log.warning(f"スタッフ {staff} の履歴データが不足しています")
                continue
            
            # 現在の疲労度
            current_fatigue = self.predict_fatigue(staff_current.tail(1))['fatigue_score'].iloc[0]
            
            # 将来予測（簡易版）
            future_fatigue_scores = []
            
            for day in range(days_ahead):
                if day < len(staff_future):
                    future_row = staff_future.iloc[day]
                    # 簡易的な将来疲労度計算
                    daily_increase = 0.1 + (future_row.get('is_night_shift', 0) * 0.2)
                    if future_row.get('work_hours', 0) > 0:
                        next_fatigue = min(1.0, current_fatigue + daily_increase)
                    else:
                        next_fatigue = current_fatigue * 0.7  # 休日回復
                    
                    future_fatigue_scores.append(next_fatigue)
                    current_fatigue = next_fatigue
                else:
                    future_fatigue_scores.append(current_fatigue * 0.9)
            
            predictions[staff] = {
                'future_fatigue': future_fatigue_scores,
                'max_fatigue': max(future_fatigue_scores) if future_fatigue_scores else 0,
                'risk_days': sum(1 for f in future_fatigue_scores if f > self.fatigue_thresholds['warning']),
                'recommendations': self._generate_recommendations(future_fatigue_scores)
            }
        
        return predictions
    
    def _generate_recommendations(self, future_fatigue: List[float]) -> List[str]:
        """疲労度に基づく推奨事項"""
        recommendations = []
        max_fatigue = max(future_fatigue) if future_fatigue else 0
        
        if max_fatigue > self.fatigue_thresholds['danger']:
            recommendations.extend([
                '🚨 緊急：連続勤務の制限が必要',
                '🏥 産業医面談の実施を強く推奨',
                '⏰ 勤務時間の短縮を検討'
            ])
        elif max_fatigue > self.fatigue_thresholds['warning']:
            recommendations.extend([
                '⚠️ 注意：夜勤回数の調整を検討',
                '💤 十分な休息時間の確保',
                '📊 疲労度の継続監視'
            ])
        elif max_fatigue > self.fatigue_thresholds['caution']:
            recommendations.append('👀 観察：疲労度の継続監視')
        
        return recommendations


def create_pytorch_fatigue_predictor(sequence_length: int = 14) -> PyTorchFatiguePredictor:
    """PyTorch疲労予測エンジンの作成"""
    return PyTorchFatiguePredictor(sequence_length=sequence_length)


if __name__ == "__main__":
    # テスト用のサンプルデータ
    import random
    from datetime import date
    
    # サンプルデータ生成
    sample_data = []
    start_date = date(2025, 1, 1)
    
    for staff_id in ['A', 'B', 'C']:
        for day in range(60):  # 60日間のデータ
            current_date = start_date + timedelta(days=day)
            
            # ランダムなシフトパターン
            is_working = random.random() > 0.2  # 80%の確率で勤務
            work_hours = random.choice([0, 8, 9, 10, 12]) if is_working else 0
            is_night = random.random() > 0.7 if is_working else False
            is_weekend = current_date.weekday() >= 5
            
            sample_data.append({
                'staff': staff_id,
                'date': current_date,
                'work_hours': work_hours,
                'is_night_shift': int(is_night),
                'is_weekend': int(is_weekend)
            })
    
    sample_df = pd.DataFrame(sample_data)
    
    # PyTorch疲労予測テスト
    predictor = PyTorchFatiguePredictor()
    
    print("🧠 PyTorch LSTM疲労予測システムのテスト開始")
    
    # モデル訓練
    training_results = predictor.train_model(sample_df, epochs=50, batch_size=16)
    
    print(f"✅ 訓練完了:")
    print(f"   MSE: {training_results['final_mse']:.4f}")
    print(f"   MAE: {training_results['final_mae']:.4f}")
    print(f"   相関係数: {training_results['correlation']:.4f}")
    
    # 疲労度予測
    predicted_df = predictor.predict_fatigue(sample_df)
    
    print(f"\n📊 疲労度予測結果（最新5日間）:")
    latest_results = predicted_df.tail(15)[['staff', 'date', 'fatigue_score', 'risk_level']]
    print(latest_results.to_string(index=False))
    
    # 将来予測
    future_data = sample_df.tail(21)  # 最新3週間をベース
    future_predictions = predictor.predict_future_fatigue(
        sample_df, future_data, days_ahead=7
    )
    
    print(f"\n🔮 将来疲労度予測（7日先まで）:")
    for staff, pred in future_predictions.items():
        print(f"スタッフ {staff}:")
        print(f"  最大疲労度: {pred['max_fatigue']:.3f}")
        print(f"  警告レベル日数: {pred['risk_days']}日")
        print(f"  推奨事項: {', '.join(pred['recommendations'])}")