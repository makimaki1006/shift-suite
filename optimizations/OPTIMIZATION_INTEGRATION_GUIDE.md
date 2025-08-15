# パフォーマンス最適化統合ガイド

## 🚀 最適化モジュールの統合手順

### 1. I/O最適化の統合

```python
# shift_suite/tasks/io_excel.py の修正例
from optimizations.io_optimization import ExcelOptimizer

excel_optimizer = ExcelOptimizer()

def load_excel_file(file_path, sheet_name=None):
    """最適化されたExcel読み込み"""
    return excel_optimizer.load_excel_optimized(file_path, sheet_name)
```

### 2. CPU最適化の統合

```python
# shift_suite/tasks/fact_extractor_prototype.py の修正例
from optimizations.cpu_optimization import SlotHoursOptimizer

slot_optimizer = SlotHoursOptimizer()

def calculate_total_hours(df):
    """最適化された時間計算"""
    return slot_optimizer.parallel_slot_calculation(df)
```

### 3. メモリ最適化の統合

```python
# shift_suite/tasks/utils.py の修正例
from optimizations.memory_optimization import MemoryOptimizer

def process_large_dataframe(df):
    """メモリ効率的なDataFrame処理"""
    return MemoryOptimizer.optimize_dataframe_memory(df)
```

### 4. キャッシュ最適化の統合

```python
# dash_app.py の修正例
from optimizations.cache_optimization import calculation_cache

@calculation_cache.cached_function(ttl=1800)
def generate_dashboard_data(file_hash):
    """キャッシュ機能付きダッシュボードデータ生成"""
    # データ生成ロジック
    pass
```

### 5. 並列処理最適化の統合

```python
# app.py の修正例
from optimizations.parallel_optimization import parallel_processor

def process_multiple_analysis(file_paths):
    """複数分析の並列実行"""
    return parallel_processor.process_multiple_files_parallel(file_paths)
```

## 📊 期待される効果

- Excel読み込み: 67%高速化 (15s → 5s)
- Phase 2処理: 67%高速化 (30s → 10s)  
- Phase 3.1処理: 60%高速化 (20s → 8s)
- メモリ使用量: 50%削減 (2GB → 1GB)
- ダッシュボード: 63%高速化 (8s → 3s)

## ⚠️ 注意事項

1. **段階的導入**: 一度に全て適用せず、段階的にテスト
2. **キャッシュ管理**: 定期的なキャッシュクリアが必要
3. **並列処理**: CPU・メモリリソースの監視が重要
4. **バックアップ**: 最適化前のコードを必ずバックアップ

## 🔄 継続的な最適化

- 定期的なパフォーマンス測定
- ボトルネック箇所の特定と改善
- 新技術・手法の検討と導入
