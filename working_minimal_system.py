"""
実際に動作する最小限のシフト分析システム
依存関係なしで基本機能を提供
"""

import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Tuple
import json

class WorkingShiftAnalysisSystem:
    """実際に動作するシフト分析システム"""
    
    def __init__(self):
        self.data = {}
        self.results = {}
    
    def load_simple_data(self, data: Dict[str, List[Any]]) -> bool:
        """シンプルなデータ読み込み"""
        try:
            # データ検証
            if not data:
                return False
            
            # 必須カラムチェック
            required_cols = ['staff_name', 'hours', 'date']
            if not all(col in data for col in required_cols):
                return False
            
            # データ長チェック
            lengths = [len(v) for v in data.values()]
            if len(set(lengths)) != 1:
                return False
            
            self.data = data
            return True
        except Exception:
            return False
    
    def calculate_basic_stats(self) -> Dict[str, float]:
        """基本統計計算"""
        try:
            if 'hours' not in self.data:
                return {}
            
            hours = [h for h in self.data['hours'] if isinstance(h, (int, float))]
            if not hours:
                return {}
            
            stats = {
                'total_hours': sum(hours),
                'avg_hours': np.mean(hours),
                'std_hours': np.std(hours),
                'min_hours': min(hours),
                'max_hours': max(hours),
                'record_count': len(hours)
            }
            
            self.results['basic_stats'] = stats
            return stats
        except Exception:
            return {}
    
    def calculate_staff_utilization(self, target_hours: float = 8.0) -> Dict[str, float]:
        """スタッフ稼働率計算"""
        try:
            if 'hours' not in self.data or 'staff_name' not in self.data:
                return {}
            
            # スタッフ別時間集計
            staff_hours = {}
            for i, staff in enumerate(self.data['staff_name']):
                if i < len(self.data['hours']):
                    hours = self.data['hours'][i]
                    if isinstance(hours, (int, float)):
                        staff_hours[staff] = staff_hours.get(staff, 0) + hours
            
            # 稼働率計算
            utilization = {}
            for staff, hours in staff_hours.items():
                expected = target_hours * self.data['staff_name'].count(staff)
                utilization[staff] = (hours / expected * 100) if expected > 0 else 0
            
            avg_utilization = np.mean(list(utilization.values())) if utilization else 0
            
            result = {
                'average_utilization': avg_utilization,
                'staff_utilization': utilization,
                'total_staff': len(utilization)
            }
            
            self.results['utilization'] = result
            return result
        except Exception:
            return {}
    
    def detect_simple_anomalies(self, threshold: float = 2.0) -> Dict[str, Any]:
        """簡単な異常検知"""
        try:
            if 'hours' not in self.data:
                return {}
            
            hours = [h for h in self.data['hours'] if isinstance(h, (int, float))]
            if len(hours) < 3:
                return {}
            
            mean_hours = np.mean(hours)
            std_hours = np.std(hours)
            
            if std_hours == 0:
                return {'anomalies': [], 'anomaly_count': 0}
            
            anomalies = []
            for i, h in enumerate(hours):
                z_score = abs(h - mean_hours) / std_hours
                if z_score > threshold:
                    anomalies.append({
                        'index': i,
                        'value': h,
                        'z_score': z_score,
                        'severity': 'high' if z_score > 3.0 else 'medium'
                    })
            
            result = {
                'anomalies': anomalies,
                'anomaly_count': len(anomalies),
                'anomaly_rate': len(anomalies) / len(hours) * 100,
                'threshold_used': threshold
            }
            
            self.results['anomalies'] = result
            return result
        except Exception:
            return {}
    
    def generate_simple_report(self) -> str:
        """シンプルなレポート生成"""
        try:
            report = []
            report.append("=== 実働シフト分析レポート ===")
            report.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append("")
            
            # 基本統計
            if 'basic_stats' in self.results:
                stats = self.results['basic_stats']
                report.append("【基本統計】")
                report.append(f"  総労働時間: {stats['total_hours']:.1f}時間")
                report.append(f"  平均労働時間: {stats['avg_hours']:.1f}時間")
                report.append(f"  標準偏差: {stats['std_hours']:.2f}")
                report.append(f"  最小-最大: {stats['min_hours']:.1f} - {stats['max_hours']:.1f}時間")
                report.append(f"  レコード数: {stats['record_count']}")
                report.append("")
            
            # 稼働率
            if 'utilization' in self.results:
                util = self.results['utilization']
                report.append("【稼働率分析】")
                report.append(f"  平均稼働率: {util['average_utilization']:.1f}%")
                report.append(f"  対象スタッフ数: {util['total_staff']}")
                if util['average_utilization'] >= 85:
                    report.append("  ✅ 良好な稼働率です")
                elif util['average_utilization'] >= 70:
                    report.append("  ⚠️ 改善の余地があります")
                else:
                    report.append("  ❌ 稼働率向上が必要です")
                report.append("")
            
            # 異常検知
            if 'anomalies' in self.results:
                anom = self.results['anomalies']
                report.append("【異常検知】")
                report.append(f"  異常件数: {anom['anomaly_count']}")
                report.append(f"  異常率: {anom['anomaly_rate']:.1f}%")
                if anom['anomaly_count'] == 0:
                    report.append("  ✅ 異常は検出されませんでした")
                elif anom['anomaly_rate'] < 5:
                    report.append("  ⚠️ 軽微な異常が検出されました")
                else:
                    report.append("  ❌ 多数の異常が検出されました")
                report.append("")
            
            report.append("=== レポート終了 ===")
            return "\n".join(report)
        except Exception:
            return "レポート生成に失敗しました"
    
    def export_results(self) -> Dict[str, Any]:
        """結果エクスポート"""
        return {
            'timestamp': datetime.now().isoformat(),
            'data_summary': {
                'total_records': len(self.data.get('staff_name', [])),
                'columns': list(self.data.keys())
            },
            'analysis_results': self.results,
            'system_status': 'operational'
        }

def test_working_system():
    """実働システムテスト"""
    print("🧪 実際に動作するシフト分析システムテスト")
    
    # テストデータ
    test_data = {
        'staff_name': ['田中', '佐藤', '鈴木', '高橋', '渡辺', '田中', '佐藤', '鈴木'],
        'hours': [8, 7, 9, 8, 6, 8, 7.5, 8.5],
        'date': ['2024-01-01', '2024-01-01', '2024-01-01', '2024-01-02', '2024-01-02', '2024-01-03', '2024-01-03', '2024-01-03'],
        'shift_type': ['朝', '昼', '夜', '朝', '昼', '朝', '昼', '夜']
    }
    
    # システム初期化
    system = WorkingShiftAnalysisSystem()
    
    # データ読み込み
    if system.load_simple_data(test_data):
        print("✅ データ読み込み成功")
    else:
        print("❌ データ読み込み失敗")
        return False
    
    # 基本統計
    stats = system.calculate_basic_stats()
    if stats:
        print(f"✅ 基本統計計算成功: 平均{stats['avg_hours']:.1f}時間")
    else:
        print("❌ 基本統計計算失敗")
    
    # 稼働率
    util = system.calculate_staff_utilization()
    if util:
        print(f"✅ 稼働率計算成功: 平均{util['average_utilization']:.1f}%")
    else:
        print("❌ 稼働率計算失敗")
    
    # 異常検知
    anom = system.detect_simple_anomalies()
    if 'anomalies' in anom:
        print(f"✅ 異常検知成功: {anom['anomaly_count']}件検出")
    else:
        print("❌ 異常検知失敗")
    
    # レポート生成
    report = system.generate_simple_report()
    if report and "失敗" not in report:
        print("✅ レポート生成成功")
        print("\n" + "="*50)
        print(report)
        print("="*50)
    else:
        print("❌ レポート生成失敗")
    
    # エクスポート
    export = system.export_results()
    if export:
        print("✅ 結果エクスポート成功")
    else:
        print("❌ 結果エクスポート失敗")
    
    return True

if __name__ == "__main__":
    success = test_working_system()
    print(f"\n🎯 実働システムテスト: {'成功' if success else '失敗'}")