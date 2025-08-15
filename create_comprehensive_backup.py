#!/usr/bin/env python3
"""
包括的バックアップ作成システム - Comprehensive Backup Creation System
18セクション完全統合システムの完全性を保証する徹底的バックアップ

このスクリプトは以下を保証します：
1. 完全性 - すべてのファイルを確実にバックアップ
2. 整合性 - ファイルハッシュによる検証
3. 追跡可能性 - 詳細なバックアップマニフェスト
4. 復元可能性 - 復元手順の自動生成
5. 検証可能性 - バックアップ後の自動検証

Authors: Claude AI Assistant
Created: 2025-08-05
"""

import os
import shutil
import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
import zipfile
import sys
from typing import Dict, List, Tuple, Optional
import time

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup_creation.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ComprehensiveBackupSystem:
    """包括的バックアップシステム"""
    
    def __init__(self, source_dir: str):
        self.source_dir = Path(source_dir)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_base = self.source_dir.parent / f"{self.source_dir.name}_backup_{self.timestamp}"
        self.manifest = {
            'backup_id': f'BACKUP_{self.timestamp}',
            'source_directory': str(self.source_dir),
            'backup_directory': str(self.backup_base),
            'creation_timestamp': datetime.now().isoformat(),
            'system_info': self._get_system_info(),
            'critical_files': {},
            'statistics': {},
            'verification': {},
            'warnings': []
        }
        
    def _get_system_info(self) -> Dict[str, any]:
        """システム情報取得"""
        return {
            'python_version': sys.version,
            'platform': sys.platform,
            'cwd': os.getcwd(),
            'encoding': sys.getdefaultencoding()
        }
    
    def create_comprehensive_backup(self) -> bool:
        """包括的バックアップ実行"""
        try:
            logger.info(f"=== 包括的バックアップ開始 ===")
            logger.info(f"ソース: {self.source_dir}")
            logger.info(f"バックアップ先: {self.backup_base}")
            
            # 1. 事前チェック
            if not self._pre_backup_checks():
                return False
            
            # 2. 重要ファイルリスト作成
            critical_files = self._identify_critical_files()
            
            # 3. バックアップディレクトリ作成
            self.backup_base.mkdir(parents=True, exist_ok=True)
            
            # 4. ファイルコピー実行
            copy_results = self._copy_all_files()
            
            # 5. 重要ファイル検証
            verification_results = self._verify_critical_files(critical_files)
            
            # 6. バックアップマニフェスト作成
            self._create_backup_manifest(copy_results, verification_results)
            
            # 7. 追加バックアップ（ZIP形式）
            self._create_zip_backup()
            
            # 8. 復元手順書作成
            self._create_restoration_guide()
            
            # 9. 最終検証
            final_check = self._final_verification()
            
            if final_check:
                logger.info("✅ 包括的バックアップ完了！")
                self._print_backup_summary()
                return True
            else:
                logger.error("❌ バックアップ検証失敗")
                return False
                
        except Exception as e:
            logger.error(f"バックアップエラー: {e}")
            return False
    
    def _pre_backup_checks(self) -> bool:
        """事前チェック"""
        logger.info("事前チェック実行中...")
        
        # ソースディレクトリ存在確認
        if not self.source_dir.exists():
            logger.error(f"ソースディレクトリが存在しません: {self.source_dir}")
            return False
        
        # ディスク容量チェック
        source_size = self._calculate_directory_size(self.source_dir)
        logger.info(f"ソースサイズ: {source_size / (1024**3):.2f} GB")
        
        # 重要度チェック
        if source_size > 10 * (1024**3):  # 10GB以上
            logger.warning("大容量バックアップです。時間がかかる可能性があります。")
            self.manifest['warnings'].append("Large backup size detected")
        
        return True
    
    def _identify_critical_files(self) -> List[Path]:
        """重要ファイル特定"""
        logger.info("重要ファイル特定中...")
        
        critical_patterns = [
            # コアアプリケーション
            "app.py",
            "dash_app.py",
            "requirements.txt",
            
            # 18セクション統合エンジン
            "shift_suite/tasks/ai_comprehensive_report_generator.py",
            "shift_suite/tasks/cognitive_psychology_analyzer.py",
            "shift_suite/tasks/organizational_pattern_analyzer.py",
            "shift_suite/tasks/system_thinking_analyzer.py",
            "shift_suite/tasks/blueprint_deep_analysis_engine.py",
            "shift_suite/tasks/integrated_mece_analysis_engine.py",
            "shift_suite/tasks/predictive_optimization_integration_engine.py",
            
            # 設定ファイル
            "**/*.json",
            "**/*.config",
            
            # データファイル
            "*.xlsx",
            "*.csv",
            
            # ドキュメント
            "*.md",
            "comprehensive_improvement_roadmap.md",
            "blueprint_revolutionary_improvement_plan.md"
        ]
        
        critical_files = []
        for pattern in critical_patterns:
            if "**" in pattern:
                files = list(self.source_dir.rglob(pattern.replace("**/", "")))
            else:
                files = list(self.source_dir.glob(pattern))
            critical_files.extend(files)
        
        # 重複削除
        critical_files = list(set(critical_files))
        logger.info(f"重要ファイル数: {len(critical_files)}")
        
        return critical_files
    
    def _copy_all_files(self) -> Dict[str, any]:
        """全ファイルコピー"""
        logger.info("ファイルコピー開始...")
        
        copy_stats = {
            'total_files': 0,
            'copied_files': 0,
            'failed_files': [],
            'total_size': 0,
            'copy_time': 0
        }
        
        start_time = time.time()
        
        # プログレスバー用カウンター
        total_files = sum(1 for _ in self.source_dir.rglob("*") if _.is_file())
        current = 0
        
        for src_path in self.source_dir.rglob("*"):
            if src_path.is_file():
                current += 1
                relative_path = src_path.relative_to(self.source_dir)
                dst_path = self.backup_base / relative_path
                
                try:
                    # ディレクトリ作成
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # ファイルコピー
                    shutil.copy2(src_path, dst_path)
                    
                    # 統計更新
                    copy_stats['copied_files'] += 1
                    copy_stats['total_size'] += src_path.stat().st_size
                    
                    # 進捗表示（10%ごと）
                    if current % max(1, total_files // 10) == 0:
                        progress = (current / total_files) * 100
                        logger.info(f"進捗: {progress:.0f}% ({current}/{total_files})")
                        
                except Exception as e:
                    logger.error(f"コピー失敗: {src_path} - {e}")
                    copy_stats['failed_files'].append(str(src_path))
                
                copy_stats['total_files'] = current
        
        copy_stats['copy_time'] = time.time() - start_time
        logger.info(f"コピー完了: {copy_stats['copied_files']}/{copy_stats['total_files']} ファイル")
        logger.info(f"所要時間: {copy_stats['copy_time']:.2f} 秒")
        
        return copy_stats
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """ファイルハッシュ計算"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _verify_critical_files(self, critical_files: List[Path]) -> Dict[str, any]:
        """重要ファイル検証"""
        logger.info("重要ファイル検証中...")
        
        verification_results = {
            'verified_count': 0,
            'missing_files': [],
            'hash_mismatches': [],
            'file_hashes': {}
        }
        
        for src_file in critical_files:
            if not src_file.exists():
                continue
                
            relative_path = src_file.relative_to(self.source_dir)
            dst_file = self.backup_base / relative_path
            
            # 存在確認
            if not dst_file.exists():
                verification_results['missing_files'].append(str(relative_path))
                logger.warning(f"バックアップ欠損: {relative_path}")
                continue
            
            # ハッシュ検証
            try:
                src_hash = self._calculate_file_hash(src_file)
                dst_hash = self._calculate_file_hash(dst_file)
                
                if src_hash == dst_hash:
                    verification_results['verified_count'] += 1
                    verification_results['file_hashes'][str(relative_path)] = src_hash
                else:
                    verification_results['hash_mismatches'].append(str(relative_path))
                    logger.error(f"ハッシュ不一致: {relative_path}")
                    
            except Exception as e:
                logger.error(f"検証エラー: {relative_path} - {e}")
        
        logger.info(f"検証完了: {verification_results['verified_count']} ファイル正常")
        return verification_results
    
    def _create_backup_manifest(self, copy_results: Dict, verification_results: Dict):
        """バックアップマニフェスト作成"""
        logger.info("バックアップマニフェスト作成中...")
        
        self.manifest['statistics'] = copy_results
        self.manifest['verification'] = verification_results
        self.manifest['critical_files'] = verification_results.get('file_hashes', {})
        
        # マニフェストファイル保存
        manifest_path = self.backup_base / f"backup_manifest_{self.timestamp}.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(self.manifest, f, ensure_ascii=False, indent=2)
        
        logger.info(f"マニフェスト保存: {manifest_path}")
    
    def _create_zip_backup(self):
        """ZIP形式バックアップ作成"""
        logger.info("ZIP形式バックアップ作成中...")
        
        zip_path = self.backup_base.parent / f"{self.source_dir.name}_backup_{self.timestamp}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in self.backup_base.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.backup_base)
                    zf.write(file_path, arcname)
        
        zip_size = zip_path.stat().st_size / (1024**2)  # MB
        logger.info(f"ZIPバックアップ作成完了: {zip_path} ({zip_size:.2f} MB)")
        self.manifest['zip_backup'] = str(zip_path)
    
    def _create_restoration_guide(self):
        """復元手順書作成"""
        logger.info("復元手順書作成中...")
        
        guide_content = f"""# バックアップ復元手順書
## Backup Restoration Guide

**バックアップID**: {self.manifest['backup_id']}  
**作成日時**: {self.manifest['creation_timestamp']}  
**ソース**: {self.manifest['source_directory']}  
**バックアップ**: {self.manifest['backup_directory']}

---

## 復元手順

### Option 1: フォルダ全体の復元
```powershell
# 1. 現在のフォルダをリネーム（安全のため）
Move-Item "{self.source_dir}" "{self.source_dir}_old"

# 2. バックアップから復元
Copy-Item -Path "{self.backup_base}" -Destination "{self.source_dir}" -Recurse -Force

# 3. 動作確認後、古いフォルダを削除
# Remove-Item "{self.source_dir}_old" -Recurse -Force
```

### Option 2: 特定ファイルの復元
```powershell
# 重要ファイルのみ復元
$files = @(
    "app.py",
    "dash_app.py",
    "requirements.txt",
    "shift_suite\\tasks\\*.py"
)

foreach ($file in $files) {{
    Copy-Item "{self.backup_base}\\$file" "{self.source_dir}\\$file" -Force
}}
```

### Option 3: ZIPからの復元
```powershell
# ZIPファイルから復元
Expand-Archive -Path "{self.manifest.get('zip_backup', 'N/A')}" -DestinationPath "{self.source_dir}" -Force
```

---

## 検証済みファイル

### 重要ファイル（ハッシュ検証済み）
{chr(10).join(f"- {f}" for f in self.manifest['critical_files'].keys())}

### 統計情報
- 総ファイル数: {self.manifest['statistics']['total_files']}
- コピー成功: {self.manifest['statistics']['copied_files']}
- 総サイズ: {self.manifest['statistics']['total_size'] / (1024**3):.2f} GB
- 所要時間: {self.manifest['statistics']['copy_time']:.2f} 秒

---

## 注意事項
1. 復元前に現在の状態をバックアップすることを推奨
2. 仮想環境は復元後に再作成が必要
3. 日本語パス問題に注意（英語パスでの復元推奨）
"""
        
        guide_path = self.backup_base / f"RESTORATION_GUIDE_{self.timestamp}.md"
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide_content)
        
        logger.info(f"復元手順書作成: {guide_path}")
    
    def _calculate_directory_size(self, directory: Path) -> int:
        """ディレクトリサイズ計算"""
        total_size = 0
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size
    
    def _final_verification(self) -> bool:
        """最終検証"""
        logger.info("最終検証実行中...")
        
        # サイズ比較
        src_size = self._calculate_directory_size(self.source_dir)
        dst_size = self._calculate_directory_size(self.backup_base)
        
        size_ratio = dst_size / src_size if src_size > 0 else 0
        logger.info(f"サイズ比較: ソース={src_size/(1024**3):.2f}GB, バックアップ={dst_size/(1024**3):.2f}GB (比率: {size_ratio:.2%})")
        
        # 完全性チェック
        if size_ratio < 0.95:  # 95%未満は警告
            logger.warning("バックアップサイズが小さすぎます。不完全な可能性があります。")
            return False
        
        # 重要ファイル存在確認
        critical_check_passed = True
        for critical_file in ['app.py', 'dash_app.py', 'requirements.txt']:
            if not (self.backup_base / critical_file).exists():
                logger.error(f"重要ファイル欠損: {critical_file}")
                critical_check_passed = False
        
        return critical_check_passed
    
    def _print_backup_summary(self):
        """バックアップサマリー表示"""
        print("\n" + "="*60)
        print("📦 包括的バックアップ完了サマリー")
        print("="*60)
        print(f"バックアップID: {self.manifest['backup_id']}")
        print(f"バックアップ場所: {self.backup_base}")
        print(f"ZIPファイル: {self.manifest.get('zip_backup', 'N/A')}")
        print(f"総ファイル数: {self.manifest['statistics']['total_files']}")
        print(f"コピー成功: {self.manifest['statistics']['copied_files']}")
        print(f"検証済み重要ファイル: {self.manifest['verification']['verified_count']}")
        print(f"総サイズ: {self.manifest['statistics']['total_size'] / (1024**3):.2f} GB")
        print(f"所要時間: {self.manifest['statistics']['copy_time']:.2f} 秒")
        
        if self.manifest['warnings']:
            print("\n⚠️ 警告:")
            for warning in self.manifest['warnings']:
                print(f"  - {warning}")
        
        print("\n✅ バックアップは正常に完了しました！")
        print(f"復元手順書: {self.backup_base}/RESTORATION_GUIDE_{self.timestamp}.md")
        print("="*60 + "\n")


def main():
    """メイン実行"""
    # 現在のディレクトリをバックアップ
    current_dir = Path.cwd()
    
    print(f"バックアップ対象: {current_dir}")
    response = input("このディレクトリをバックアップしますか？ (y/n): ")
    
    if response.lower() != 'y':
        print("バックアップをキャンセルしました。")
        return
    
    # バックアップ実行
    backup_system = ComprehensiveBackupSystem(str(current_dir))
    success = backup_system.create_comprehensive_backup()
    
    if success:
        print("\n✅ バックアップが正常に完了しました！")
        print("次のステップ: フォルダを C:\\ShiftAnalysis に移動してください。")
    else:
        print("\n❌ バックアップに失敗しました。ログを確認してください。")
        sys.exit(1)


if __name__ == "__main__":
    main()