"""
C2実装前バックアップ作成システム
安全性分析結果（100/100）を受けて、慎重なバックアップ戦略を実行
"""

import os
import shutil
import json
import hashlib
from datetime import datetime
from pathlib import Path
import zipfile
import tempfile

class C2PreImplementationBackup:
    """C2実装前専用バックアップシステム"""
    
    def __init__(self):
        self.base_path = "/mnt/c/Users/fuji1/OneDrive/デスクトップ/シフト分析"
        self.backup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir = f"C2_PRE_IMPLEMENTATION_BACKUP_{self.backup_timestamp}"
        self.backup_full_path = os.path.join(self.base_path, self.backup_dir)
        
        # 重要ファイル（安全性分析で確認済み）
        self.critical_files = [
            "app.py",
            "dash_app.py",
            "shift_suite/__init__.py",
            "shift_suite/tasks/utils.py", 
            "shift_suite/tasks/shortage.py",
            "shift_suite/tasks/fact_extractor_prototype.py",  # Phase 2
            "shift_suite/tasks/lightweight_anomaly_detector.py"  # Phase 3.1
        ]
        
        # モバイル関連ファイル（既存実装保護）
        self.mobile_files = [
            "dash_components/visualization_engine.py",
            "improved_ui_components.py",
            "dash_app_backup.py"
        ]
        
        # 設定・データファイル
        self.config_files = [
            "requirements.txt",
            "shift_suite/config.json"
        ]
        
        # 最近の実装成果物
        self.recent_implementations = [
            "C1_FEATURE_EXPANSION_LITE.py",
            "C1_implementation_summary.json",
            "C2_SAFETY_ANALYSIS.py",
            "C2_safety_analysis_report_20250803_223812.json"
        ]
        
    def create_comprehensive_backup(self):
        """包括的バックアップ作成"""
        print(f"🛡️ C2実装前バックアップ開始...")
        print(f"📁 バックアップ先: {self.backup_dir}")
        
        try:
            # バックアップディレクトリ作成
            os.makedirs(self.backup_full_path, exist_ok=True)
            
            backup_report = {
                'timestamp': datetime.now().isoformat(),
                'backup_type': 'c2_pre_implementation',
                'backup_directory': self.backup_dir,
                'safety_analysis_passed': True,
                'safety_score': 100,
                'files_backed_up': {},
                'verification': {},
                'summary': {}
            }
            
            # 1. 重要ファイルのバックアップ
            print("\\n📋 重要ファイルバックアップ...")
            critical_results = self._backup_critical_files()
            backup_report['files_backed_up']['critical'] = critical_results
            
            # 2. モバイル関連ファイルのバックアップ
            print("\\n📱 モバイル関連ファイルバックアップ...")
            mobile_results = self._backup_mobile_files()
            backup_report['files_backed_up']['mobile'] = mobile_results
            
            # 3. 設定ファイルのバックアップ
            print("\\n⚙️ 設定ファイルバックアップ...")
            config_results = self._backup_config_files()
            backup_report['files_backed_up']['config'] = config_results
            
            # 4. 最近の実装ファイルのバックアップ
            print("\\n🚀 最近実装ファイルバックアップ...")
            recent_results = self._backup_recent_implementations()
            backup_report['files_backed_up']['recent'] = recent_results
            
            # 5. shift_suiteディレクトリ全体のバックアップ
            print("\\n📦 shift_suiteディレクトリ完全バックアップ...")
            suite_results = self._backup_shift_suite_directory()
            backup_report['files_backed_up']['shift_suite'] = suite_results
            
            # 6. バックアップ検証
            print("\\n✅ バックアップ検証...")
            verification_results = self._verify_backup()
            backup_report['verification'] = verification_results
            
            # 7. バックアップサマリー
            backup_report['summary'] = self._generate_backup_summary(backup_report)
            
            # レポート保存
            report_file = os.path.join(self.backup_full_path, 'backup_report.json')
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(backup_report, f, ensure_ascii=False, indent=2)
            
            # 圧縮アーカイブ作成
            print("\\n📦 圧縮アーカイブ作成...")
            archive_path = self._create_compressed_archive()
            backup_report['archive_path'] = archive_path
            
            print(f"\\n🎯 バックアップ完了!")
            print(f"📁 バックアップ場所: {self.backup_full_path}")
            print(f"📦 圧縮アーカイブ: {archive_path}")
            print(f"📋 レポート: {report_file}")
            
            return backup_report
            
        except Exception as e:
            error_report = {
                'timestamp': datetime.now().isoformat(),
                'backup_type': 'c2_pre_implementation_error',
                'error': str(e),
                'status': 'failed'
            }
            print(f"❌ バックアップエラー: {str(e)}")
            return error_report
    
    def _backup_critical_files(self):
        """重要ファイルのバックアップ"""
        results = {}
        critical_dir = os.path.join(self.backup_full_path, 'critical_files')
        os.makedirs(critical_dir, exist_ok=True)
        
        for file_path in self.critical_files:
            source_path = os.path.join(self.base_path, file_path)
            
            if os.path.exists(source_path):
                # ディレクトリ構造を保持してコピー
                dest_path = os.path.join(critical_dir, file_path)
                dest_dir = os.path.dirname(dest_path)
                os.makedirs(dest_dir, exist_ok=True)
                
                shutil.copy2(source_path, dest_path)
                
                # ファイルハッシュ計算
                file_hash = self._calculate_file_hash(source_path)
                file_size = os.path.getsize(source_path)
                
                results[file_path] = {
                    'status': 'backed_up',
                    'source_size': file_size,
                    'hash': file_hash,
                    'backup_path': dest_path
                }
                
                print(f"  ✅ {file_path} ({file_size} bytes)")
            else:
                results[file_path] = {
                    'status': 'not_found',
                    'error': 'ファイルが存在しません'
                }
                print(f"  ❌ {file_path} (見つかりません)")
        
        return results
    
    def _backup_mobile_files(self):
        """モバイル関連ファイルのバックアップ"""
        results = {}
        mobile_dir = os.path.join(self.backup_full_path, 'mobile_files')
        os.makedirs(mobile_dir, exist_ok=True)
        
        for file_path in self.mobile_files:
            source_path = os.path.join(self.base_path, file_path)
            
            if os.path.exists(source_path):
                dest_path = os.path.join(mobile_dir, file_path)
                dest_dir = os.path.dirname(dest_path)
                os.makedirs(dest_dir, exist_ok=True)
                
                shutil.copy2(source_path, dest_path)
                
                file_hash = self._calculate_file_hash(source_path)
                file_size = os.path.getsize(source_path)
                
                results[file_path] = {
                    'status': 'backed_up',
                    'source_size': file_size,
                    'hash': file_hash,
                    'backup_path': dest_path
                }
                
                print(f"  ✅ {file_path} ({file_size} bytes)")
            else:
                results[file_path] = {
                    'status': 'not_found',
                    'note': 'オプションファイル（存在しなくても問題なし）'
                }
                print(f"  ⚪ {file_path} (オプション - 存在せず)")
        
        return results
    
    def _backup_config_files(self):
        """設定ファイルのバックアップ"""
        results = {}
        config_dir = os.path.join(self.backup_full_path, 'config_files')
        os.makedirs(config_dir, exist_ok=True)
        
        for file_path in self.config_files:
            source_path = os.path.join(self.base_path, file_path)
            
            if os.path.exists(source_path):
                dest_path = os.path.join(config_dir, os.path.basename(file_path))
                shutil.copy2(source_path, dest_path)
                
                file_hash = self._calculate_file_hash(source_path)
                file_size = os.path.getsize(source_path)
                
                results[file_path] = {
                    'status': 'backed_up',
                    'source_size': file_size,
                    'hash': file_hash,
                    'backup_path': dest_path
                }
                
                print(f"  ✅ {file_path} ({file_size} bytes)")
        
        return results
    
    def _backup_recent_implementations(self):
        """最近の実装ファイルのバックアップ"""
        results = {}
        recent_dir = os.path.join(self.backup_full_path, 'recent_implementations')
        os.makedirs(recent_dir, exist_ok=True)
        
        for file_path in self.recent_implementations:
            source_path = os.path.join(self.base_path, file_path)
            
            if os.path.exists(source_path):
                dest_path = os.path.join(recent_dir, os.path.basename(file_path))
                shutil.copy2(source_path, dest_path)
                
                file_hash = self._calculate_file_hash(source_path)
                file_size = os.path.getsize(source_path)
                
                results[file_path] = {
                    'status': 'backed_up',
                    'source_size': file_size,
                    'hash': file_hash,
                    'backup_path': dest_path
                }
                
                print(f"  ✅ {file_path} ({file_size} bytes)")
        
        return results
    
    def _backup_shift_suite_directory(self):
        """shift_suiteディレクトリ完全バックアップ"""
        source_dir = os.path.join(self.base_path, 'shift_suite')
        dest_dir = os.path.join(self.backup_full_path, 'shift_suite_complete')
        
        if os.path.exists(source_dir):
            shutil.copytree(source_dir, dest_dir, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            
            # ディレクトリサイズ計算
            total_size = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, dirnames, filenames in os.walk(dest_dir)
                for filename in filenames
            )
            
            # ファイル数カウント
            file_count = sum(
                len(filenames)
                for dirpath, dirnames, filenames in os.walk(dest_dir)
            )
            
            print(f"  ✅ shift_suiteディレクトリ完全バックアップ ({file_count}ファイル, {total_size} bytes)")
            
            return {
                'status': 'backed_up',
                'total_size': total_size,
                'file_count': file_count,
                'backup_path': dest_dir
            }
        else:
            print(f"  ❌ shift_suiteディレクトリが見つかりません")
            return {
                'status': 'not_found',
                'error': 'shift_suiteディレクトリが存在しません'
            }
    
    def _verify_backup(self):
        """バックアップ検証"""
        verification = {
            'critical_files_verified': 0,
            'hash_mismatches': [],
            'missing_backups': [],
            'verification_passed': True
        }
        
        # 重要ファイルの検証
        for file_path in self.critical_files:
            source_path = os.path.join(self.base_path, file_path)
            backup_path = os.path.join(self.backup_full_path, 'critical_files', file_path)
            
            if os.path.exists(source_path) and os.path.exists(backup_path):
                source_hash = self._calculate_file_hash(source_path)
                backup_hash = self._calculate_file_hash(backup_path)
                
                if source_hash == backup_hash:
                    verification['critical_files_verified'] += 1
                    print(f"  ✅ {file_path} 検証成功")
                else:
                    verification['hash_mismatches'].append(file_path)
                    verification['verification_passed'] = False
                    print(f"  ❌ {file_path} ハッシュ不一致")
            elif os.path.exists(source_path):
                verification['missing_backups'].append(file_path)
                verification['verification_passed'] = False
                print(f"  ❌ {file_path} バックアップ欠損")
        
        return verification
    
    def _calculate_file_hash(self, file_path):
        """ファイルハッシュ計算"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _generate_backup_summary(self, backup_report):
        """バックアップサマリー生成"""
        files_backed_up = backup_report['files_backed_up']
        
        total_files = 0
        total_size = 0
        successful_backups = 0
        
        for category, files in files_backed_up.items():
            if isinstance(files, dict):
                if category == 'shift_suite':
                    if files.get('status') == 'backed_up':
                        total_files += files.get('file_count', 0)
                        total_size += files.get('total_size', 0)
                        successful_backups += 1
                else:
                    for file_path, file_info in files.items():
                        total_files += 1
                        if file_info.get('status') == 'backed_up':
                            total_size += file_info.get('source_size', 0)
                            successful_backups += 1
        
        verification = backup_report.get('verification', {})
        
        return {
            'total_files_attempted': total_files,
            'successful_backups': successful_backups,
            'total_backup_size': total_size,
            'verification_passed': verification.get('verification_passed', False),
            'critical_files_verified': verification.get('critical_files_verified', 0),
            'backup_integrity': 'excellent' if verification.get('verification_passed') else 'warning'
        }
    
    def _create_compressed_archive(self):
        """圧縮アーカイブ作成"""
        archive_name = f"{self.backup_dir}.zip"
        archive_path = os.path.join(self.base_path, archive_name)
        
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.backup_full_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, self.backup_full_path)
                    zipf.write(file_path, arcname)
        
        archive_size = os.path.getsize(archive_path)
        print(f"  ✅ 圧縮アーカイブ作成完了 ({archive_size} bytes)")
        
        return archive_path

def main():
    """C2実装前バックアップメイン実行"""
    print("🛡️ C2実装前バックアップシステム開始...")
    print("📊 安全性分析結果: 100/100 - 実装準備良好")
    
    backup_system = C2PreImplementationBackup()
    result = backup_system.create_comprehensive_backup()
    
    if 'error' in result:
        print(f"❌ バックアップ失敗: {result['error']}")
        return result
    
    # 成功サマリー表示
    summary = result.get('summary', {})
    
    print(f"\\n📊 バックアップサマリー:")
    print(f"📁 バックアップファイル: {summary.get('successful_backups', 0)}件")
    print(f"📦 総バックアップサイズ: {summary.get('total_backup_size', 0):,} bytes")
    print(f"✅ 検証結果: {summary.get('backup_integrity', 'unknown')}")
    print(f"🔒 重要ファイル検証: {summary.get('critical_files_verified', 0)}件成功")
    
    verification = result.get('verification', {})
    if verification.get('verification_passed'):
        print(f"\\n🎯 バックアップ検証成功 - C2実装準備完了")
    else:
        print(f"\\n⚠️ バックアップ検証に警告あり - 慎重に進行")
    
    print(f"\\n📋 次のステップ:")
    print(f"  1. C2.3 段階的実装計画策定")
    print(f"  2. C2.4 モバイルUI/UX改善実装")
    print(f"  3. C2.5 総合テスト・検証")
    
    return result

if __name__ == "__main__":
    result = main()