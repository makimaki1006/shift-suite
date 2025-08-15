#!/usr/bin/env python3
"""
バックアップ検証スクリプト - Backup Verification Script
包括的バックアップの完全性を検証

このスクリプトは以下を検証します：
1. バックアップフォルダの存在
2. 重要ファイルの存在確認
3. ファイルハッシュの整合性チェック
4. バックアップサイズの妥当性
5. マニフェストファイルの検証

Authors: Claude AI Assistant
Created: 2025-08-05
"""

import os
import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
import sys
from typing import Dict, List, Optional

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BackupVerifier:
    """バックアップ検証システム"""
    
    def __init__(self, source_dir: str, backup_dir: str = None):
        self.source_dir = Path(source_dir)
        
        # バックアップディレクトリ自動検出
        if backup_dir is None:
            backup_dir = self._find_latest_backup()
        
        self.backup_dir = Path(backup_dir) if backup_dir else None
        self.verification_results = {
            'timestamp': datetime.now().isoformat(),
            'source_directory': str(self.source_dir),
            'backup_directory': str(self.backup_dir) if self.backup_dir else None,
            'tests_passed': 0,
            'tests_failed': 0,
            'warnings': [],
            'errors': [],
            'overall_status': 'PENDING'
        }
    
    def _find_latest_backup(self) -> Optional[str]:
        """最新のバックアップフォルダを検出"""
        parent_dir = self.source_dir.parent
        backup_pattern = f"{self.source_dir.name}_backup_*"
        
        backup_dirs = []
        for item in parent_dir.glob(backup_pattern):
            if item.is_dir():
                backup_dirs.append(item)
        
        if backup_dirs:
            # 最新のバックアップを選択（名前でソート）
            latest = sorted(backup_dirs, key=lambda x: x.name)[-1]
            logger.info(f"最新バックアップ検出: {latest}")
            return str(latest)
        
        return None
    
    def verify_backup(self) -> bool:
        """包括的バックアップ検証実行"""
        logger.info("=== バックアップ検証開始 ===")
        
        if not self.backup_dir:
            logger.error("バックアップディレクトリが見つかりません")
            return False
        
        # 1. 基本存在確認
        self._test_basic_existence()
        
        # 2. マニフェスト検証
        manifest = self._test_manifest_verification()
        
        # 3. 重要ファイル検証
        self._test_critical_files()
        
        # 4. サイズ比較検証
        self._test_size_comparison()
        
        # 5. ハッシュ整合性検証（サンプル）
        self._test_hash_integrity(manifest)
        
        # 6. 復元可能性テスト
        self._test_restoration_viability()
        
        # 最終結果判定
        return self._finalize_verification()
    
    def _test_basic_existence(self):
        """基本存在確認テスト"""
        logger.info("基本存在確認テスト実行中...")
        
        if self.backup_dir.exists():
            logger.info("✓ バックアップディレクトリ存在確認")
            self.verification_results['tests_passed'] += 1
        else:
            logger.error("✗ バックアップディレクトリが存在しません")
            self.verification_results['tests_failed'] += 1
            self.verification_results['errors'].append("Backup directory does not exist")
    
    def _test_manifest_verification(self) -> Optional[Dict]:
        """マニフェスト検証テスト"""
        logger.info("マニフェスト検証テスト実行中...")
        
        manifest_files = list(self.backup_dir.glob("backup_manifest_*.json"))
        
        if not manifest_files:
            logger.warning("⚠ マニフェストファイルが見つかりません")
            self.verification_results['warnings'].append("No manifest file found")
            return None
        
        try:
            manifest_path = manifest_files[0]  # 最初のマニフェストを使用
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            # 必須フィールド確認
            required_fields = ['backup_id', 'creation_timestamp', 'statistics', 'verification']
            missing_fields = [field for field in required_fields if field not in manifest]
            
            if missing_fields:
                logger.error(f"✗ マニフェスト必須フィールド不足: {missing_fields}")
                self.verification_results['tests_failed'] += 1
                self.verification_results['errors'].append(f"Missing manifest fields: {missing_fields}")
                return None
            else:
                logger.info("✓ マニフェスト形式確認")
                self.verification_results['tests_passed'] += 1
                return manifest
                
        except Exception as e:
            logger.error(f"✗ マニフェスト読み込みエラー: {e}")
            self.verification_results['tests_failed'] += 1
            self.verification_results['errors'].append(f"Manifest read error: {e}")
            return None
    
    def _test_critical_files(self):
        """重要ファイル検証テスト"""
        logger.info("重要ファイル検証テスト実行中...")
        
        critical_files = [
            "app.py",
            "dash_app.py",
            "requirements.txt",
            "shift_suite/tasks/ai_comprehensive_report_generator.py",
            "shift_suite/tasks/blueprint_deep_analysis_engine.py",
            "shift_suite/tasks/integrated_mece_analysis_engine.py",
            "shift_suite/tasks/predictive_optimization_integration_engine.py"
        ]
        
        missing_files = []
        present_files = []
        
        for file_path in critical_files:
            backup_file = self.backup_dir / file_path
            if backup_file.exists():
                present_files.append(file_path)
                logger.info(f"✓ {file_path}")
            else:
                missing_files.append(file_path)
                logger.error(f"✗ {file_path}")
        
        if missing_files:
            self.verification_results['tests_failed'] += 1
            self.verification_results['errors'].append(f"Missing critical files: {missing_files}")
        else:
            logger.info("✓ 全重要ファイル存在確認")
            self.verification_results['tests_passed'] += 1
    
    def _test_size_comparison(self):
        """サイズ比較検証テスト"""
        logger.info("サイズ比較検証テスト実行中...")
        
        try:
            source_size = self._calculate_directory_size(self.source_dir)
            backup_size = self._calculate_directory_size(self.backup_dir)
            
            size_ratio = backup_size / source_size if source_size > 0 else 0
            
            logger.info(f"ソースサイズ: {source_size / (1024**3):.2f} GB")
            logger.info(f"バックアップサイズ: {backup_size / (1024**3):.2f} GB")
            logger.info(f"サイズ比率: {size_ratio:.2%}")
            
            if size_ratio >= 0.95:  # 95%以上
                logger.info("✓ サイズ比較正常")
                self.verification_results['tests_passed'] += 1
            elif size_ratio >= 0.80:  # 80%以上
                logger.warning("⚠ サイズがやや小さい（80-95%）")
                self.verification_results['warnings'].append(f"Size ratio: {size_ratio:.2%}")
            else:
                logger.error("✗ サイズが大幅に不足（80%未満）")
                self.verification_results['tests_failed'] += 1
                self.verification_results['errors'].append(f"Size ratio too low: {size_ratio:.2%}")
                
        except Exception as e:
            logger.error(f"✗ サイズ比較エラー: {e}")
            self.verification_results['tests_failed'] += 1
            self.verification_results['errors'].append(f"Size comparison error: {e}")
    
    def _test_hash_integrity(self, manifest: Optional[Dict]):
        """ハッシュ整合性検証テスト（サンプル）"""
        logger.info("ハッシュ整合性検証テスト実行中...")
        
        if not manifest or 'critical_files' not in manifest:
            logger.warning("⚠ マニフェストにハッシュ情報がありません")
            self.verification_results['warnings'].append("No hash information in manifest")
            return
        
        hash_mismatches = []
        verified_files = 0
        
        # サンプル検証（最大5ファイル）
        sample_files = list(manifest['critical_files'].items())[:5]
        
        for file_path, expected_hash in sample_files:
            backup_file = self.backup_dir / file_path
            
            if not backup_file.exists():
                continue
            
            try:
                actual_hash = self._calculate_file_hash(backup_file)
                if actual_hash == expected_hash:
                    verified_files += 1
                    logger.info(f"✓ ハッシュ一致: {file_path}")
                else:
                    hash_mismatches.append(file_path)
                    logger.error(f"✗ ハッシュ不一致: {file_path}")
            except Exception as e:
                logger.error(f"ハッシュ計算エラー: {file_path} - {e}")
        
        if hash_mismatches:
            self.verification_results['tests_failed'] += 1
            self.verification_results['errors'].append(f"Hash mismatches: {hash_mismatches}")
        elif verified_files > 0:
            logger.info(f"✓ ハッシュ整合性確認 ({verified_files} ファイル)")
            self.verification_results['tests_passed'] += 1
    
    def _test_restoration_viability(self):
        """復元可能性テスト"""
        logger.info("復元可能性テスト実行中...")
        
        # 復元手順書の存在確認
        restoration_guides = list(self.backup_dir.glob("RESTORATION_GUIDE_*.md"))
        
        if restoration_guides:
            logger.info("✓ 復元手順書存在確認")
            self.verification_results['tests_passed'] += 1
        else:
            logger.warning("⚠ 復元手順書が見つかりません")
            self.verification_results['warnings'].append("No restoration guide found")
        
        # ZIP バックアップの存在確認
        zip_backups = list(self.backup_dir.parent.glob(f"{self.source_dir.name}_backup_*.zip"))
        
        if zip_backups:
            logger.info("✓ ZIPバックアップ存在確認")
            self.verification_results['tests_passed'] += 1
        else:
            logger.warning("⚠ ZIPバックアップが見つかりません")
            self.verification_results['warnings'].append("No ZIP backup found")
    
    def _calculate_directory_size(self, directory: Path) -> int:
        """ディレクトリサイズ計算"""
        total_size = 0
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                except (OSError, IOError):
                    # ファイルアクセスエラーは無視
                    pass
        return total_size
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """ファイルハッシュ計算"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _finalize_verification(self) -> bool:
        """最終検証結果判定"""
        total_tests = self.verification_results['tests_passed'] + self.verification_results['tests_failed']
        success_rate = self.verification_results['tests_passed'] / total_tests if total_tests > 0 else 0
        
        if self.verification_results['tests_failed'] == 0:
            self.verification_results['overall_status'] = 'PASSED'
            status = True
        elif success_rate >= 0.8:  # 80%以上成功
            self.verification_results['overall_status'] = 'PASSED_WITH_WARNINGS'
            status = True
        else:
            self.verification_results['overall_status'] = 'FAILED'
            status = False
        
        # 結果サマリー表示
        self._print_verification_summary()
        
        return status
    
    def _print_verification_summary(self):
        """検証結果サマリー表示"""
        print("\n" + "="*60)
        print("🔍 バックアップ検証結果サマリー")
        print("="*60)
        print(f"総合ステータス: {self.verification_results['overall_status']}")
        print(f"テスト成功: {self.verification_results['tests_passed']}")
        print(f"テスト失敗: {self.verification_results['tests_failed']}")
        print(f"警告数: {len(self.verification_results['warnings'])}")
        print(f"エラー数: {len(self.verification_results['errors'])}")
        
        if self.verification_results['warnings']:
            print("\n⚠️ 警告:")
            for warning in self.verification_results['warnings']:
                print(f"  - {warning}")
        
        if self.verification_results['errors']:
            print("\n❌ エラー:")
            for error in self.verification_results['errors']:
                print(f"  - {error}")
        
        if self.verification_results['overall_status'] in ['PASSED', 'PASSED_WITH_WARNINGS']:
            print("\n✅ バックアップは使用可能です！")
        else:
            print("\n❌ バックアップに重大な問題があります")
        
        print("="*60 + "\n")


def main():
    """メイン実行"""
    if len(sys.argv) > 2:
        source_dir = sys.argv[1]
        backup_dir = sys.argv[2]
    elif len(sys.argv) > 1:
        source_dir = sys.argv[1]
        backup_dir = None
    else:
        source_dir = Path.cwd()
        backup_dir = None
    
    print(f"検証対象: {source_dir}")
    
    verifier = BackupVerifier(str(source_dir), backup_dir)
    success = verifier.verify_backup()
    
    if success:
        print("✅ バックアップ検証完了 - 使用可能")
        sys.exit(0)
    else:
        print("❌ バックアップ検証失敗 - 要修正")
        sys.exit(1)


if __name__ == "__main__":
    main()