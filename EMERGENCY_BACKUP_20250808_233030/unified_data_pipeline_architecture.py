#!/usr/bin/env python3
"""
統一データパイプラインアーキテクチャ
全体最適化による一貫したデータフロー管理システム

Data Flow: 入稿 → 分解 → 分析 → 加工 → 可視化
- 動的データ対応
- 一貫性保証
- セキュリティ・パフォーマンス最適化
"""

from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import pandas as pd
import json
import hashlib
import logging
from datetime import datetime, timedelta
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import weakref

# ============================================================================
# 1. 統一データタイプ・ステージ定義
# ============================================================================

class DataStage(Enum):
    """データ処理ステージ定義"""
    RAW_INPUT = "raw_input"           # 入稿: Excel、ZIP等の生データ
    DECOMPOSED = "decomposed"         # 分解: パースされた構造化データ
    ANALYZED = "analyzed"             # 分析: 計算・統計処理済み
    PROCESSED = "processed"           # 加工: 可視化用データ変換
    VISUALIZED = "visualized"         # 可視化: 最終出力データ

class DataType(Enum):
    """統一データタイプ分類"""
    # 基本データ
    INTERMEDIATE = "intermediate_data"
    NEED_DATA = "need_data"
    SHORTAGE = "shortage_data"
    
    # 按分廃止関連
    PROPORTIONAL_ABOLITION_ROLE = "proportional_abolition_role"
    PROPORTIONAL_ABOLITION_ORG = "proportional_abolition_organization"
    
    # 分析結果
    HEATMAP = "heatmap_data"
    FORECAST = "forecast_data"
    OPTIMIZATION = "optimization_data"

class Priority(Enum):
    """処理優先度"""
    CRITICAL = 1    # 按分廃止等の重要分析
    HIGH = 2        # リアルタイム表示データ
    NORMAL = 3      # 通常分析データ
    LOW = 4         # バックグラウンド処理

@dataclass
class DataMetadata:
    """統一データメタデータ"""
    data_type: DataType
    stage: DataStage
    priority: Priority
    created_at: datetime
    updated_at: datetime
    hash_value: str
    size_bytes: int
    dependencies: List[str] = field(default_factory=list)
    processing_time_ms: Optional[int] = None
    error_count: int = 0
    cache_ttl_seconds: int = 3600  # デフォルト1時間
    
    def is_expired(self) -> bool:
        """キャッシュ期限切れ判定"""
        return datetime.now() > self.updated_at + timedelta(seconds=self.cache_ttl_seconds)

# ============================================================================
# 2. 統一データレジストリ（動的データ対応）
# ============================================================================

class UnifiedDataRegistry:
    """
    統一データレジストリ - 全データの一元管理
    - 動的データソース検出
    - 依存関係管理
    - 自動キャッシュ管理
    - セキュアファイルアクセス
    """
    
    def __init__(self, base_paths: List[Path]):
        self.base_paths = [Path(p) for p in base_paths]
        self.metadata_store: Dict[str, DataMetadata] = {}
        self.cache_store: Dict[str, Any] = {}
        self.lock = threading.RLock()
        self.observers: List[weakref.ref] = []
        
        # セキュリティ設定
        self.allowed_extensions = {'.parquet', '.csv', '.xlsx', '.json'}
        self.max_file_size = 500 * 1024 * 1024  # 500MB
        
        self._setup_logging()
        self._scan_available_data()
    
    def _setup_logging(self):
        """統一ログ設定"""
        self.logger = logging.getLogger('UnifiedDataRegistry')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _scan_available_data(self):
        """利用可能データの動的スキャン"""
        with self.lock:
            self.logger.info("データソース動的スキャン開始")
            
            for base_path in self.base_paths:
                if not base_path.exists():
                    self.logger.warning(f"パス不存在: {base_path}")
                    continue
                
                # 再帰的ファイルスキャン
                for file_path in base_path.rglob('*'):
                    if (file_path.is_file() and 
                        file_path.suffix.lower() in self.allowed_extensions):
                        
                        self._register_file(file_path)
            
            self.logger.info(f"スキャン完了: {len(self.metadata_store)}ファイル登録")
    
    def _register_file(self, file_path: Path):
        """ファイル登録処理"""
        try:
            # セキュリティチェック
            if not self._security_check(file_path):
                return
            
            # データタイプ自動判定
            data_type = self._infer_data_type(file_path)
            if not data_type:
                return
            
            # メタデータ生成
            stat = file_path.stat()
            hash_val = self._compute_file_hash(file_path)
            
            metadata = DataMetadata(
                data_type=data_type,
                stage=self._infer_stage(file_path),
                priority=self._infer_priority(data_type),
                created_at=datetime.fromtimestamp(stat.st_ctime),
                updated_at=datetime.fromtimestamp(stat.st_mtime),
                hash_value=hash_val,
                size_bytes=stat.st_size
            )
            
            self.metadata_store[str(file_path)] = metadata
            
            self.logger.debug(f"ファイル登録: {file_path.name} ({data_type.value})")
            
        except Exception as e:
            self.logger.error(f"ファイル登録失敗: {file_path} - {e}")
    
    def _security_check(self, file_path: Path) -> bool:
        """セキュリティチェック"""
        try:
            # ファイルサイズチェック
            if file_path.stat().st_size > self.max_file_size:
                self.logger.warning(f"ファイルサイズ超過: {file_path}")
                return False
            
            # 読み取り権限チェック
            if not file_path.exists() or not file_path.is_file():
                return False
                
            # パストラバーサル攻撃防止
            resolved_path = file_path.resolve()
            for base_path in self.base_paths:
                if str(resolved_path).startswith(str(base_path.resolve())):
                    return True
            
            self.logger.warning(f"パス違反: {file_path}")
            return False
            
        except Exception as e:
            self.logger.error(f"セキュリティチェック失敗: {file_path} - {e}")
            return False
    
    def _infer_data_type(self, file_path: Path) -> Optional[DataType]:
        """ファイル名からデータタイプを自動推定"""
        name = file_path.name.lower()
        
        # 按分廃止関連
        if 'proportional_abolition_role' in name:
            return DataType.PROPORTIONAL_ABOLITION_ROLE
        elif 'proportional_abolition_org' in name:
            return DataType.PROPORTIONAL_ABOLITION_ORG
        
        # 基本データ
        elif 'intermediate_data' in name:
            return DataType.INTERMEDIATE
        elif 'need_per_date' in name:
            return DataType.NEED_DATA
        elif 'shortage' in name:
            return DataType.SHORTAGE
        elif 'heat' in name:
            return DataType.HEATMAP
        elif 'forecast' in name:
            return DataType.FORECAST
        elif 'optim' in name:
            return DataType.OPTIMIZATION
        
        return None
    
    def _infer_stage(self, file_path: Path) -> DataStage:
        """処理ステージの推定"""
        name = file_path.name.lower()
        
        if any(x in name for x in ['raw', 'input', '.xlsx']):
            return DataStage.RAW_INPUT
        elif any(x in name for x in ['intermediate', 'decomposed']):
            return DataStage.DECOMPOSED
        elif any(x in name for x in ['analyzed', 'calculated']):
            return DataStage.ANALYZED
        elif any(x in name for x in ['processed', 'summary']):
            return DataStage.PROCESSED
        else:
            return DataStage.VISUALIZED
    
    def _infer_priority(self, data_type: DataType) -> Priority:
        """優先度の推定"""
        critical_types = {
            DataType.PROPORTIONAL_ABOLITION_ROLE,
            DataType.PROPORTIONAL_ABOLITION_ORG
        }
        
        if data_type in critical_types:
            return Priority.CRITICAL
        elif data_type in {DataType.SHORTAGE, DataType.INTERMEDIATE}:
            return Priority.HIGH
        else:
            return Priority.NORMAL
    
    def _compute_file_hash(self, file_path: Path) -> str:
        """ファイルハッシュ計算"""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return "error"
    
    def get_data(self, data_type: Union[DataType, str], 
                 stage: Optional[DataStage] = None,
                 force_reload: bool = False) -> Optional[pd.DataFrame]:
        """統一データ取得インターface"""
        
        if isinstance(data_type, str):
            # 従来のキー名も対応
            data_type = self._legacy_key_mapping(data_type)
        
        with self.lock:
            # 適切なファイルを検索
            candidates = []
            for file_path, metadata in self.metadata_store.items():
                if metadata.data_type == data_type:
                    if stage is None or metadata.stage == stage:
                        candidates.append((file_path, metadata))
            
            if not candidates:
                self.logger.warning(f"データ未発見: {data_type}")
                return None
            
            # 優先度・更新日時でソート
            candidates.sort(key=lambda x: (x[1].priority.value, -x[1].updated_at.timestamp()))
            
            file_path, metadata = candidates[0]
            
            # キャッシュチェック
            cache_key = f"{data_type}:{file_path}"
            if not force_reload and cache_key in self.cache_store:
                if not metadata.is_expired():
                    self.logger.debug(f"キャッシュヒット: {data_type}")
                    return self.cache_store[cache_key]
            
            # データ読み込み
            start_time = datetime.now()
            try:
                data = self._load_file(Path(file_path))
                processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
                
                # キャッシュ更新
                self.cache_store[cache_key] = data
                metadata.processing_time_ms = processing_time
                metadata.error_count = 0
                
                self.logger.info(f"データ読み込み完了: {data_type} ({processing_time}ms)")
                return data
                
            except Exception as e:
                metadata.error_count += 1
                self.logger.error(f"データ読み込み失敗: {data_type} - {e}")
                return None
    
    def _legacy_key_mapping(self, key: str) -> DataType:
        """従来キー名の互換性マッピング"""
        mapping = {
            'proportional_abolition_role_summary': DataType.PROPORTIONAL_ABOLITION_ROLE,
            'proportional_abolition_organization_summary': DataType.PROPORTIONAL_ABOLITION_ORG,
            'intermediate_data': DataType.INTERMEDIATE,
            'shortage_role_summary': DataType.SHORTAGE,
            'long_df': DataType.INTERMEDIATE,
        }
        
        return mapping.get(key, DataType.INTERMEDIATE)
    
    def _load_file(self, file_path: Path) -> pd.DataFrame:
        """ファイル読み込み処理"""
        suffix = file_path.suffix.lower()
        
        if suffix == '.parquet':
            return pd.read_parquet(file_path)
        elif suffix == '.csv':
            return pd.read_csv(file_path, encoding='utf-8')
        elif suffix == '.xlsx':
            return pd.read_excel(file_path)
        elif suffix == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return pd.json_normalize(data)
        else:
            raise ValueError(f"未対応ファイル形式: {suffix}")
    
    def refresh_data(self):
        """データソースの再スキャン"""
        self.logger.info("データソース再スキャン開始")
        old_count = len(self.metadata_store)
        
        # 既存データクリア
        self.metadata_store.clear()
        self.cache_store.clear()
        
        # 再スキャン
        self._scan_available_data()
        
        new_count = len(self.metadata_store)
        self.logger.info(f"再スキャン完了: {old_count} → {new_count}")
        
        # 監視者に通知
        self._notify_observers()
    
    def _notify_observers(self):
        """監視者への変更通知"""
        dead_refs = []
        for ref in self.observers:
            observer = ref()
            if observer is None:
                dead_refs.append(ref)
            else:
                try:
                    observer.on_data_updated()
                except Exception as e:
                    self.logger.error(f"監視者通知失敗: {e}")
        
        # 死んだ参照を削除
        for ref in dead_refs:
            self.observers.remove(ref)
    
    def add_observer(self, observer):
        """監視者の登録"""
        self.observers.append(weakref.ref(observer))
    
    def get_statistics(self) -> Dict[str, Any]:
        """レジストリ統計情報"""
        stats = {
            'total_files': len(self.metadata_store),
            'cache_entries': len(self.cache_store),
            'data_types': {},
            'stages': {},
            'priorities': {},
            'total_size_mb': 0,
            'error_files': 0
        }
        
        for metadata in self.metadata_store.values():
            # データタイプ別統計
            dt = metadata.data_type.value
            stats['data_types'][dt] = stats['data_types'].get(dt, 0) + 1
            
            # ステージ別統計
            stage = metadata.stage.value
            stats['stages'][stage] = stats['stages'].get(stage, 0) + 1
            
            # 優先度別統計
            priority = metadata.priority.value
            stats['priorities'][priority] = stats['priorities'].get(priority, 0) + 1
            
            stats['total_size_mb'] += metadata.size_bytes / (1024 * 1024)
            
            if metadata.error_count > 0:
                stats['error_files'] += 1
        
        return stats

# ============================================================================
# 3. 統一データパイプライン
# ============================================================================

class UnifiedDataPipeline:
    """
    統一データパイプライン
    入稿 → 分解 → 分析 → 加工 → 可視化 の一貫した処理
    """
    
    def __init__(self, registry: UnifiedDataRegistry):
        self.registry = registry
        self.pipeline_stages: Dict[DataStage, List[callable]] = {
            stage: [] for stage in DataStage
        }
        self.logger = logging.getLogger('UnifiedDataPipeline')
        
    def register_processor(self, stage: DataStage, processor: callable):
        """ステージ別処理関数の登録"""
        self.pipeline_stages[stage].append(processor)
        self.logger.info(f"プロセッサー登録: {stage.value} - {processor.__name__}")
    
    def process_data(self, data_type: DataType, 
                    input_data: Any = None,
                    target_stage: DataStage = DataStage.VISUALIZED) -> Any:
        """統一データ処理パイプライン"""
        
        current_data = input_data or self.registry.get_data(data_type)
        if current_data is None:
            raise ValueError(f"入力データなし: {data_type}")
        
        # ステージ順次処理
        for stage in DataStage:
            processors = self.pipeline_stages[stage]
            
            for processor in processors:
                try:
                    start_time = datetime.now()
                    current_data = processor(current_data, data_type)
                    processing_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    self.logger.info(f"処理完了: {stage.value}/{processor.__name__} ({processing_time:.1f}ms)")
                    
                except Exception as e:
                    self.logger.error(f"処理失敗: {stage.value}/{processor.__name__} - {e}")
                    raise
            
            if stage == target_stage:
                break
        
        return current_data

# ============================================================================
# 4. グローバルインスタンス初期化
# ============================================================================

# 統一レジストリの初期化
def create_unified_registry() -> UnifiedDataRegistry:
    """統一レジストリの作成"""
    base_paths = [
        Path('.'),  # カレントディレクトリ
        Path('extracted_results'),
        Path('out_mean_based'),
        Path('out_median_based'), 
        Path('out_p25_based'),
    ]
    
    # 存在するパスのみ使用
    valid_paths = [p for p in base_paths if p.exists() or p == Path('.')]
    
    registry = UnifiedDataRegistry(valid_paths)
    return registry

# グローバルレジストリインスタンス（シングルトン的使用）
_global_registry = None

def get_unified_registry() -> UnifiedDataRegistry:
    """グローバル統一レジストリの取得"""
    global _global_registry
    if _global_registry is None:
        _global_registry = create_unified_registry()
    return _global_registry

# ============================================================================
# 5. 互換性レイヤー（既存コードとの統合）
# ============================================================================

def enhanced_data_get(key: str, default=None, force_reload: bool = False) -> Any:
    """
    従来のdata_get関数の拡張版
    統一レジストリを使用した高性能・セキュアなデータ取得
    """
    registry = get_unified_registry()
    
    try:
        data = registry.get_data(key, force_reload=force_reload)
        return data if data is not None else default
    except Exception as e:
        registry.logger.error(f"enhanced_data_get失敗: {key} - {e}")
        return default

if __name__ == "__main__":
    # テスト実行
    registry = create_unified_registry()
    
    print("=== 統一データレジストリ統計 ===")
    stats = registry.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    print("\n=== 按分廃止データテスト ===")
    role_data = registry.get_data(DataType.PROPORTIONAL_ABOLITION_ROLE)
    if role_data is not None:
        print(f"按分廃止職種データ: {role_data.shape}")
    else:
        print("按分廃止職種データ: 未発見")
    
    org_data = registry.get_data(DataType.PROPORTIONAL_ABOLITION_ORG)
    if org_data is not None:
        print(f"按分廃止組織データ: {org_data.shape}")
    else:
        print("按分廃止組織データ: 未発見")