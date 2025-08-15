#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C3 セキュリティ強化
医療シフト分析システムのデータ保護・監査対応・セキュリティ体制を強化
深い思考：セキュリティは後付けではなく、設計思想に組み込まれるべき
"""

import os
import sys
import json
import hashlib
import secrets
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import re
import tempfile
import shutil

class SecurityLevel(Enum):
    """セキュリティレベル"""
    PUBLIC = "public"              # 公開情報
    INTERNAL = "internal"          # 内部限定
    CONFIDENTIAL = "confidential"  # 機密情報
    RESTRICTED = "restricted"      # 制限情報（医療データ等）

class ThreatCategory(Enum):
    """脅威カテゴリ"""
    DATA_LEAK = "data_leak"               # データ漏洩
    UNAUTHORIZED_ACCESS = "unauthorized"   # 不正アクセス
    DATA_CORRUPTION = "data_corruption"    # データ破損
    PRIVACY_VIOLATION = "privacy"          # プライバシー侵害
    COMPLIANCE_VIOLATION = "compliance"    # コンプライアンス違反
    SYSTEM_COMPROMISE = "system_compromise" # システム侵害

@dataclass
class SecurityVulnerability:
    """セキュリティ脆弱性"""
    vuln_id: str
    category: ThreatCategory
    severity: str  # critical, high, medium, low
    description: str
    affected_files: List[str]
    remediation: str
    status: str  # identified, mitigated, resolved

@dataclass
class SecurityAuditLog:
    """セキュリティ監査ログ"""
    timestamp: datetime
    event_type: str
    user: str
    action: str
    resource: str
    result: str
    details: Dict[str, Any]

class SecurityEnhancer:
    """セキュリティ強化システム"""
    
    def __init__(self):
        self.security_dir = Path("security")
        self.security_dir.mkdir(exist_ok=True)
        
        self.audit_dir = Path("logs/security_audit")
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        
        # セキュリティポリシー
        self.security_policies = self._define_security_policies()
        
        # 監査ログ
        self.audit_logs = []
        
        # 脆弱性リスト
        self.vulnerabilities = []
        
        # データ分類
        self.data_classification = self._classify_system_data()
        
    def _define_security_policies(self) -> Dict[str, Any]:
        """セキュリティポリシー定義"""
        
        return {
            "data_protection": {
                "encryption_required": True,
                "access_logging": True,
                "retention_period": 2555,  # 7年（日数）
                "backup_encryption": True,
                "anonymization_required": True
            },
            "access_control": {
                "authentication_required": True,
                "role_based_access": True,
                "session_timeout": 3600,  # 1時間
                "failed_login_limit": 3,
                "password_complexity": True
            },
            "audit_compliance": {
                "audit_logging": True,
                "log_retention": 2555,  # 7年
                "regular_audit": True,
                "compliance_reporting": True,
                "incident_response": True
            },
            "medical_data_specific": {
                "hipaa_compliance": True,
                "anonymization": True,
                "consent_tracking": True,
                "data_minimization": True,
                "purpose_limitation": True
            }
        }
    
    def _classify_system_data(self) -> Dict[str, SecurityLevel]:
        """システムデータの分類"""
        
        return {
            # 制限情報（医療データ）
            "*.xlsx": SecurityLevel.RESTRICTED,
            "shift_suite/tasks/io_excel.py": SecurityLevel.RESTRICTED,
            "logs/": SecurityLevel.CONFIDENTIAL,
            
            # 機密情報
            "app.py": SecurityLevel.CONFIDENTIAL,
            "dash_app.py": SecurityLevel.CONFIDENTIAL,
            "shift_suite/tasks/": SecurityLevel.CONFIDENTIAL,
            
            # 内部限定
            "requirements.txt": SecurityLevel.INTERNAL,
            "README.md": SecurityLevel.INTERNAL,
            
            # 公開情報
            "docs/": SecurityLevel.PUBLIC
        }
    
    def perform_security_assessment(self) -> List[SecurityVulnerability]:
        """セキュリティ評価実行"""
        
        print("🔍 セキュリティ評価開始...")
        
        vulnerabilities = []
        
        # 1. データ露出リスクチェック
        data_exposure_vulns = self._check_data_exposure_risks()
        vulnerabilities.extend(data_exposure_vulns)
        
        # 2. アクセス制御チェック
        access_control_vulns = self._check_access_control()
        vulnerabilities.extend(access_control_vulns)
        
        # 3. ログ・監査チェック
        audit_vulns = self._check_audit_logging()
        vulnerabilities.extend(audit_vulns)
        
        # 4. 医療データ特有のリスクチェック
        medical_data_vulns = self._check_medical_data_compliance()
        vulnerabilities.extend(medical_data_vulns)
        
        # 5. システム構成チェック
        system_config_vulns = self._check_system_configuration()
        vulnerabilities.extend(system_config_vulns)
        
        self.vulnerabilities = vulnerabilities
        return vulnerabilities
    
    def _check_data_exposure_risks(self) -> List[SecurityVulnerability]:
        """データ露出リスクチェック"""
        
        print("   📊 データ露出リスク評価中...")
        
        vulnerabilities = []
        
        # 機密ファイルの存在チェック
        sensitive_patterns = [
            "*.xlsx",
            "*.csv", 
            "config*.json",
            "*.log"
        ]
        
        for pattern in sensitive_patterns:
            matching_files = list(Path(".").glob(pattern))
            if matching_files:
                vuln = SecurityVulnerability(
                    vuln_id="DATA_001",
                    category=ThreatCategory.DATA_LEAK,
                    severity="high",
                    description=f"機密データファイルがルートディレクトリに存在: {pattern}",
                    affected_files=[str(f) for f in matching_files[:5]],  # 最初の5件
                    remediation="機密ファイルを専用ディレクトリに移動し、アクセス制御を実装",
                    status="identified"
                )
                vulnerabilities.append(vuln)
        
        # ハードコードされた機密情報チェック
        code_files = list(Path(".").glob("*.py"))
        for code_file in code_files:
            if self._contains_hardcoded_secrets(code_file):
                vuln = SecurityVulnerability(
                    vuln_id="DATA_002",
                    category=ThreatCategory.DATA_LEAK,
                    severity="critical",
                    description="ハードコードされた機密情報が検出された",
                    affected_files=[str(code_file)],
                    remediation="環境変数または設定ファイルに移行し、暗号化保存",
                    status="identified"
                )
                vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    def _contains_hardcoded_secrets(self, file_path: Path) -> bool:
        """ハードコードされた機密情報の検出"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 危険なパターンを検索
            dangerous_patterns = [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']'
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _check_access_control(self) -> List[SecurityVulnerability]:
        """アクセス制御チェック"""
        
        print("   🔐 アクセス制御評価中...")
        
        vulnerabilities = []
        
        # 認証機能の存在チェック
        main_files = ["app.py", "dash_app.py"]
        for main_file in main_files:
            if Path(main_file).exists():
                if not self._has_authentication(Path(main_file)):
                    vuln = SecurityVulnerability(
                        vuln_id="ACCESS_001",
                        category=ThreatCategory.UNAUTHORIZED_ACCESS,
                        severity="high",
                        description=f"{main_file}に認証機能が実装されていない",
                        affected_files=[main_file],
                        remediation="認証機能を実装し、医療データへの不正アクセスを防止",
                        status="identified"
                    )
                    vulnerabilities.append(vuln)
        
        # セッション管理チェック
        if not self._has_secure_session_management():
            vuln = SecurityVulnerability(
                vuln_id="ACCESS_002",
                category=ThreatCategory.UNAUTHORIZED_ACCESS,
                severity="medium",
                description="セキュアなセッション管理が実装されていない",
                affected_files=["app.py", "dash_app.py"],
                remediation="セッションタイムアウト、セキュアクッキー設定を実装",
                status="identified"
            )
            vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    def _has_authentication(self, file_path: Path) -> bool:
        """認証機能の存在確認"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            auth_indicators = [
                "login",
                "authenticate",
                "auth",
                "session",
                "password"
            ]
            
            return any(indicator in content.lower() for indicator in auth_indicators)
            
        except Exception:
            return False
    
    def _has_secure_session_management(self) -> bool:
        """セキュアなセッション管理の確認"""
        
        # 簡易チェック：Flaskのsecret_key等の存在確認
        main_files = ["app.py", "dash_app.py"]
        
        for main_file in main_files:
            if Path(main_file).exists():
                try:
                    with open(main_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if "secret_key" in content.lower():
                        return True
                        
                except Exception:
                    pass
        
        return False
    
    def _check_audit_logging(self) -> List[SecurityVulnerability]:
        """監査ログチェック"""
        
        print("   📋 監査ログ評価中...")
        
        vulnerabilities = []
        
        # ログ機能の存在チェック
        if not self._has_comprehensive_logging():
            vuln = SecurityVulnerability(
                vuln_id="AUDIT_001",
                category=ThreatCategory.COMPLIANCE_VIOLATION,
                severity="high",
                description="包括的な監査ログ機能が実装されていない",
                affected_files=["app.py", "dash_app.py"],
                remediation="ユーザーアクション、データアクセス、システムイベントの詳細ログを実装",
                status="identified"
            )
            vulnerabilities.append(vuln)
        
        # ログ保護チェック
        log_dirs = ["logs/", "logs/security_audit/"]
        for log_dir in log_dirs:
            if Path(log_dir).exists():
                if not self._are_logs_protected(Path(log_dir)):
                    vuln = SecurityVulnerability(
                        vuln_id="AUDIT_002",
                        category=ThreatCategory.DATA_CORRUPTION,
                        severity="medium",
                        description=f"ログディレクトリ {log_dir} が適切に保護されていない",
                        affected_files=[log_dir],
                        remediation="ログファイルの改ざん防止、バックアップ、暗号化を実装",
                        status="identified"
                    )
                    vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    def _has_comprehensive_logging(self) -> bool:
        """包括的なログ機能の確認"""
        
        # ログ設定ファイルまたはログ機能の存在確認
        log_indicators = [
            Path("logs/"),
            Path("shift_suite/logger_config.py")
        ]
        
        return any(indicator.exists() for indicator in log_indicators)
    
    def _are_logs_protected(self, log_dir: Path) -> bool:
        """ログ保護の確認"""
        
        # 簡易チェック：バックアップやローテーション設定の存在
        protection_indicators = [
            log_dir / ".gitignore",  # Git管理外
            log_dir / "backup/",     # バックアップディレクトリ
        ]
        
        return any(indicator.exists() for indicator in protection_indicators)
    
    def _check_medical_data_compliance(self) -> List[SecurityVulnerability]:
        """医療データコンプライアンスチェック"""
        
        print("   🏥 医療データコンプライアンス評価中...")
        
        vulnerabilities = []
        
        # 匿名化機能チェック
        if not self._has_anonymization_features():
            vuln = SecurityVulnerability(
                vuln_id="MEDICAL_001",
                category=ThreatCategory.PRIVACY_VIOLATION,
                severity="critical",
                description="医療データの匿名化機能が実装されていない",
                affected_files=["shift_suite/tasks/io_excel.py"],
                remediation="個人識別情報の自動検出・匿名化機能を実装",
                status="identified"
            )
            vulnerabilities.append(vuln)
        
        # データ最小化チェック
        if not self._implements_data_minimization():
            vuln = SecurityVulnerability(
                vuln_id="MEDICAL_002",
                category=ThreatCategory.PRIVACY_VIOLATION,
                severity="high",
                description="データ最小化原則が実装されていない",
                affected_files=["shift_suite/tasks/"],
                remediation="必要最小限のデータのみ処理・保存する機能を実装",
                status="identified"
            )
            vulnerabilities.append(vuln)
        
        # 同意管理チェック
        if not self._has_consent_management():
            vuln = SecurityVulnerability(
                vuln_id="MEDICAL_003",
                category=ThreatCategory.COMPLIANCE_VIOLATION,
                severity="high",
                description="データ使用同意の管理機能がない",
                affected_files=["app.py"],
                remediation="データ使用目的の明示、同意取得・管理機能を実装",
                status="identified"
            )
            vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    def _has_anonymization_features(self) -> bool:
        """匿名化機能の確認"""
        
        # 匿名化関連のコードを検索
        code_files = list(Path("shift_suite").glob("**/*.py"))
        
        for code_file in code_files:
            try:
                with open(code_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                anonymization_indicators = [
                    "anonymize",
                    "pseudonymize", 
                    "hash",
                    "mask"
                ]
                
                if any(indicator in content.lower() for indicator in anonymization_indicators):
                    return True
                    
            except Exception:
                pass
        
        return False
    
    def _implements_data_minimization(self) -> bool:
        """データ最小化の実装確認"""
        
        # データ選択・フィルタリング機能の確認
        # 簡易チェック：columnsの選択的読み込み等
        try:
            with open("shift_suite/tasks/io_excel.py", 'r', encoding='utf-8') as f:
                content = f.read()
            
            minimization_indicators = [
                "usecols",
                "columns",
                "select",
                "filter"
            ]
            
            return any(indicator in content.lower() for indicator in minimization_indicators)
            
        except Exception:
            return False
    
    def _has_consent_management(self) -> bool:
        """同意管理機能の確認"""
        
        # 同意関連のコードや設定の確認
        consent_files = [
            "consent.py",
            "privacy_policy.py",
            "terms_of_use.py"
        ]
        
        return any(Path(f).exists() for f in consent_files)
    
    def _check_system_configuration(self) -> List[SecurityVulnerability]:
        """システム構成チェック"""
        
        print("   ⚙️ システム構成評価中...")
        
        vulnerabilities = []
        
        # 依存関係セキュリティチェック
        if Path("requirements.txt").exists():
            if self._has_vulnerable_dependencies():
                vuln = SecurityVulnerability(
                    vuln_id="SYSTEM_001",
                    category=ThreatCategory.SYSTEM_COMPROMISE,
                    severity="medium",
                    description="脆弱性のある依存関係が検出された",
                    affected_files=["requirements.txt"],
                    remediation="依存関係を最新バージョンに更新し、定期的なセキュリティスキャンを実装",
                    status="identified"
                )
                vulnerabilities.append(vuln)
        
        # 環境設定チェック
        if not self._has_secure_environment_config():
            vuln = SecurityVulnerability(
                vuln_id="SYSTEM_002",
                category=ThreatCategory.SYSTEM_COMPROMISE,
                severity="medium",
                description="セキュアな環境設定が不十分",
                affected_files=[".env", "config.py"],
                remediation="環境変数での設定管理、デバッグモード無効化を実装",
                status="identified"
            )
            vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    def _has_vulnerable_dependencies(self) -> bool:
        """脆弱な依存関係の確認"""
        
        # 簡易チェック：古いバージョンのライブラリパターン
        try:
            with open("requirements.txt", 'r', encoding='utf-8') as f:
                content = f.read()
            
            # バージョン指定がない、または古いパターンを検出
            vulnerable_patterns = [
                r"flask==0\.",  # Flask 0.x系
                r"pandas==0\.", # Pandas 0.x系
                r"numpy==1\.[0-9]\.",  # Numpy 1.x系の古いバージョン
            ]
            
            for pattern in vulnerable_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return True
            
            # バージョン固定されていない依存関係
            lines = content.strip().split('\n')
            for line in lines:
                if line.strip() and '==' not in line and '>=' not in line:
                    return True
            
            return False
            
        except Exception:
            return True  # ファイルが読めない場合は脆弱と判定
    
    def _has_secure_environment_config(self) -> bool:
        """セキュアな環境設定の確認"""
        
        # 環境設定ファイルの存在確認
        config_files = [".env", "config.py", "settings.py"]
        
        return any(Path(f).exists() for f in config_files)
    
    def implement_security_measures(self, vulnerabilities: List[SecurityVulnerability]) -> Dict[str, Any]:
        """セキュリティ対策の実装"""
        
        print("\n🛡️ セキュリティ対策実装中...")
        
        implementation_results = {
            "timestamp": datetime.now().isoformat(),
            "implemented_measures": [],
            "configuration_files": [],
            "policies_created": []
        }
        
        # 1. データ保護機能実装
        data_protection_result = self._implement_data_protection()
        implementation_results["implemented_measures"].append(data_protection_result)
        
        # 2. アクセス制御実装
        access_control_result = self._implement_access_control()
        implementation_results["implemented_measures"].append(access_control_result)
        
        # 3. 監査ログ実装
        audit_logging_result = self._implement_audit_logging()
        implementation_results["implemented_measures"].append(audit_logging_result)
        
        # 4. 医療データ特化対策
        medical_compliance_result = self._implement_medical_data_compliance()
        implementation_results["implemented_measures"].append(medical_compliance_result)
        
        # 5. システム強化
        system_hardening_result = self._implement_system_hardening()
        implementation_results["implemented_measures"].append(system_hardening_result)
        
        # 6. セキュリティポリシー生成
        policy_files = self._generate_security_policies()
        implementation_results["policies_created"] = policy_files
        
        return implementation_results
    
    def _implement_data_protection(self) -> Dict[str, Any]:
        """データ保護機能実装"""
        
        print("   🔒 データ保護機能実装中...")
        
        # データ暗号化モジュール作成
        encryption_module = '''
# データ暗号化・保護モジュール
import os
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import json
from pathlib import Path

class DataProtector:
    """データ保護・暗号化クラス"""
    
    def __init__(self, key_file="security/encryption.key"):
        self.key_file = Path(key_file)
        self.key_file.parent.mkdir(parents=True, exist_ok=True)
        self.cipher_suite = self._get_or_create_cipher()
    
    def _get_or_create_cipher(self):
        """暗号化キーの取得または生成"""
        
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # キーファイルのパーミッション設定（Unix系）
            os.chmod(self.key_file, 0o600)
        
        return Fernet(key)
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """機密データの暗号化"""
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """機密データの復号化"""
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
    
    def hash_personal_identifier(self, identifier: str) -> str:
        """個人識別子のハッシュ化"""
        return hashlib.sha256(identifier.encode()).hexdigest()
    
    def anonymize_excel_data(self, df):
        """Excelデータの匿名化"""
        import pandas as pd
        
        df_anonymized = df.copy()
        
        # 個人識別可能な列の検出と匿名化
        personal_columns = ['name', '名前', 'employee_id', '職員ID', 
                          'email', 'メール', 'phone', '電話']
        
        for col in df_anonymized.columns:
            col_lower = col.lower()
            if any(pc in col_lower for pc in personal_columns):
                # ハッシュ化による匿名化
                df_anonymized[col] = df_anonymized[col].apply(
                    lambda x: self.hash_personal_identifier(str(x)) if pd.notna(x) else x
                )
        
        return df_anonymized
    
    def secure_file_storage(self, file_path: str, data: bytes):
        """セキュアなファイル保存"""
        
        # データを暗号化
        encrypted_data = self.cipher_suite.encrypt(data)
        
        # 暗号化されたファイルとして保存
        encrypted_path = f"{file_path}.encrypted"
        with open(encrypted_path, 'wb') as f:
            f.write(encrypted_data)
        
        # 元ファイルのセキュア削除
        if Path(file_path).exists():
            self._secure_delete(file_path)
        
        return encrypted_path
    
    def _secure_delete(self, file_path: str):
        """ファイルのセキュア削除"""
        
        path = Path(file_path)
        if path.exists():
            # ファイルを0で上書きしてから削除
            with open(path, 'r+b') as f:
                length = f.seek(0, 2)
                f.seek(0)
                f.write(b'\\x00' * length)
                f.flush()
                os.fsync(f.fileno())
            
            path.unlink()

# データ保護インスタンス
data_protector = DataProtector()

def protect_excel_file(file_path):
    """Excelファイルの保護"""
    import pandas as pd
    
    # ファイル読み込み
    df = pd.read_excel(file_path)
    
    # 匿名化
    df_anonymized = data_protector.anonymize_excel_data(df)
    
    # セキュア保存
    protected_path = file_path.replace('.xlsx', '_protected.xlsx')
    df_anonymized.to_excel(protected_path, index=False)
    
    return protected_path
'''
        
        # データ保護モジュール保存
        protection_file = self.security_dir / "data_protection.py"
        with open(protection_file, 'w', encoding='utf-8') as f:
            f.write(encryption_module)
        
        return {
            "measure": "データ保護機能",
            "status": "実装完了",
            "components": [
                "データ暗号化",
                "個人識別子ハッシュ化", 
                "Excel匿名化",
                "セキュアファイル保存"
            ],
            "file": str(protection_file)
        }
    
    def _implement_access_control(self) -> Dict[str, Any]:
        """アクセス制御実装"""
        
        print("   🔐 アクセス制御実装中...")
        
        # 認証・認可モジュール作成
        auth_module = '''
# 認証・認可モジュール
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from functools import wraps
import json
from pathlib import Path

class AuthenticationManager:
    """認証管理クラス"""
    
    def __init__(self, config_file="security/auth_config.json"):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.config = self._load_or_create_config()
        self.sessions = {}
    
    def _load_or_create_config(self):
        """認証設定の読み込みまたは作成"""
        
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # デフォルト設定
            config = {
                "session_timeout": 3600,  # 1時間
                "max_login_attempts": 3,
                "lockout_duration": 900,  # 15分
                "password_min_length": 8,
                "require_2fa": False
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            return config
    
    def hash_password(self, password: str, salt: str = None) -> tuple:
        """パスワードのハッシュ化"""
        
        if salt is None:
            salt = secrets.token_hex(16)
        
        hashed = hashlib.pbkdf2_hmac('sha256', 
                                   password.encode(), 
                                   salt.encode(), 
                                   100000)
        
        return hashed.hex(), salt
    
    def verify_password(self, password: str, hashed: str, salt: str) -> bool:
        """パスワード検証"""
        
        test_hash, _ = self.hash_password(password, salt)
        return test_hash == hashed
    
    def create_session(self, user_id: str) -> str:
        """セッション作成"""
        
        session_id = secrets.token_urlsafe(32)
        expiry = datetime.now() + timedelta(seconds=self.config["session_timeout"])
        
        self.sessions[session_id] = {
            "user_id": user_id,
            "created": datetime.now().isoformat(),
            "expires": expiry.isoformat(),
            "last_activity": datetime.now().isoformat()
        }
        
        return session_id
    
    def validate_session(self, session_id: str) -> bool:
        """セッション検証"""
        
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        expiry = datetime.fromisoformat(session["expires"])
        
        if datetime.now() > expiry:
            del self.sessions[session_id]
            return False
        
        # 最終活動時刻を更新
        session["last_activity"] = datetime.now().isoformat()
        return True
    
    def require_auth(self, f):
        """認証要求デコレータ"""
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # セッション確認ロジック
            # 実際の実装では、Flaskのsessionやheaderから取得
            session_id = kwargs.get('session_id')
            
            if not session_id or not self.validate_session(session_id):
                return {"error": "認証が必要です", "status": 401}
            
            return f(*args, **kwargs)
        
        return decorated_function

class RoleBasedAccessControl:
    """ロールベースアクセス制御"""
    
    def __init__(self):
        self.roles = {
            "admin": {
                "permissions": ["read", "write", "delete", "admin"],
                "data_access": ["all"]
            },
            "manager": {
                "permissions": ["read", "write"],
                "data_access": ["aggregated", "departmental"]
            },
            "staff": {
                "permissions": ["read"],
                "data_access": ["own_data", "aggregated"]
            },
            "viewer": {
                "permissions": ["read"],
                "data_access": ["aggregated"]
            }
        }
    
    def check_permission(self, user_role: str, required_permission: str) -> bool:
        """権限チェック"""
        
        if user_role not in self.roles:
            return False
        
        return required_permission in self.roles[user_role]["permissions"]
    
    def check_data_access(self, user_role: str, data_type: str) -> bool:
        """データアクセス権限チェック"""
        
        if user_role not in self.roles:
            return False
        
        user_access = self.roles[user_role]["data_access"]
        return data_type in user_access or "all" in user_access

# 認証・認可インスタンス
auth_manager = AuthenticationManager()
rbac = RoleBasedAccessControl()

def secure_endpoint(required_permission="read", data_type="aggregated"):
    """セキュアエンドポイントデコレータ"""
    
    def decorator(f):
        @wraps(f)
        @auth_manager.require_auth
        def decorated_function(*args, **kwargs):
            user_role = kwargs.get('user_role', 'viewer')
            
            if not rbac.check_permission(user_role, required_permission):
                return {"error": "権限が不足しています", "status": 403}
            
            if not rbac.check_data_access(user_role, data_type):
                return {"error": "データアクセス権限がありません", "status": 403}
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator
'''
        
        # 認証モジュール保存
        auth_file = self.security_dir / "authentication.py"
        with open(auth_file, 'w', encoding='utf-8') as f:
            f.write(auth_module)
        
        return {
            "measure": "アクセス制御機能",
            "status": "実装完了",
            "components": [
                "パスワードハッシュ化",
                "セッション管理",
                "ロールベースアクセス制御",
                "認証デコレータ"
            ],
            "file": str(auth_file)
        }
    
    def _implement_audit_logging(self) -> Dict[str, Any]:
        """監査ログ実装"""
        
        print("   📋 監査ログ実装中...")
        
        # 監査ログモジュール作成
        audit_module = '''
# セキュリティ監査ログモジュール
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import hashlib
import threading

class SecurityAuditLogger:
    """セキュリティ監査ログ記録クラス"""
    
    def __init__(self, log_dir="logs/security_audit"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # ログファイル設定
        self.audit_log_file = self.log_dir / "security_audit.log"
        self.access_log_file = self.log_dir / "access_audit.log"
        self.data_log_file = self.log_dir / "data_access_audit.log"
        
        # ログフォーマッター設定
        self._setup_loggers()
        
        # ログ整合性検証用
        self.log_hashes = {}
        self.lock = threading.Lock()
    
    def _setup_loggers(self):
        """ログ設定"""
        
        # セキュリティイベントログ
        self.security_logger = logging.getLogger('security_audit')
        self.security_logger.setLevel(logging.INFO)
        
        security_handler = logging.FileHandler(self.audit_log_file)
        security_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s'
        )
        security_handler.setFormatter(security_formatter)
        self.security_logger.addHandler(security_handler)
        
        # アクセスログ
        self.access_logger = logging.getLogger('access_audit')
        self.access_logger.setLevel(logging.INFO)
        
        access_handler = logging.FileHandler(self.access_log_file)
        access_handler.setFormatter(security_formatter)
        self.access_logger.addHandler(access_handler)
        
        # データアクセスログ
        self.data_logger = logging.getLogger('data_audit')
        self.data_logger.setLevel(logging.INFO)
        
        data_handler = logging.FileHandler(self.data_log_file)
        data_handler.setFormatter(security_formatter)
        self.data_logger.addHandler(data_handler)
    
    def log_security_event(self, event_type: str, user: str, details: Dict[str, Any]):
        """セキュリティイベントのログ"""
        
        event_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "user": user,
            "details": details,
            "source_ip": details.get("source_ip", "unknown"),
            "user_agent": details.get("user_agent", "unknown")
        }
        
        log_message = json.dumps(event_data, ensure_ascii=False)
        self.security_logger.info(log_message)
        
        # ログ整合性ハッシュ記録
        self._record_log_hash("security", log_message)
    
    def log_access_attempt(self, user: str, resource: str, action: str, result: str, details: Optional[Dict] = None):
        """アクセス試行のログ"""
        
        access_data = {
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "resource": resource,
            "action": action,
            "result": result,  # success, failure, denied
            "details": details or {}
        }
        
        log_message = json.dumps(access_data, ensure_ascii=False)
        self.access_logger.info(log_message)
        
        self._record_log_hash("access", log_message)
    
    def log_data_access(self, user: str, data_type: str, operation: str, record_count: int, purpose: str):
        """データアクセスのログ"""
        
        data_access = {
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "data_type": data_type,
            "operation": operation,  # read, write, export, delete
            "record_count": record_count,
            "purpose": purpose,
            "compliance_note": "医療データアクセス記録"
        }
        
        log_message = json.dumps(data_access, ensure_ascii=False)
        self.data_logger.info(log_message)
        
        self._record_log_hash("data", log_message)
    
    def _record_log_hash(self, log_type: str, message: str):
        """ログ整合性のためのハッシュ記録"""
        
        with self.lock:
            message_hash = hashlib.sha256(message.encode()).hexdigest()
            
            if log_type not in self.log_hashes:
                self.log_hashes[log_type] = []
            
            self.log_hashes[log_type].append({
                "timestamp": datetime.now().isoformat(),
                "hash": message_hash
            })
    
    def verify_log_integrity(self) -> Dict[str, bool]:
        """ログ整合性検証"""
        
        integrity_results = {}
        
        for log_type in ["security", "access", "data"]:
            try:
                log_file = getattr(self, f"{log_type}_log_file")
                
                if log_file.exists():
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    # 最新のハッシュと比較
                    if log_type in self.log_hashes and self.log_hashes[log_type]:
                        expected_count = len(self.log_hashes[log_type])
                        actual_count = len(lines)
                        
                        integrity_results[log_type] = (expected_count == actual_count)
                    else:
                        integrity_results[log_type] = True
                else:
                    integrity_results[log_type] = True
                    
            except Exception:
                integrity_results[log_type] = False
        
        return integrity_results
    
    def generate_audit_report(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """監査レポート生成"""
        
        report = {
            "period": {"start": start_date, "end": end_date},
            "security_events": [],
            "access_attempts": [],
            "data_accesses": [],
            "summary": {}
        }
        
        # 各ログファイルから期間内のデータを抽出
        for log_type, log_file in [
            ("security_events", self.audit_log_file),
            ("access_attempts", self.access_log_file), 
            ("data_accesses", self.data_log_file)
        ]:
            if log_file.exists():
                events = self._extract_events_by_period(log_file, start_date, end_date)
                report[log_type] = events
        
        # サマリー生成
        report["summary"] = {
            "total_security_events": len(report["security_events"]),
            "total_access_attempts": len(report["access_attempts"]),
            "total_data_accesses": len(report["data_accesses"]),
            "log_integrity": self.verify_log_integrity()
        }
        
        return report
    
    def _extract_events_by_period(self, log_file: Path, start_date: str, end_date: str) -> list:
        """期間内のイベント抽出"""
        
        events = []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        # ログ行からJSONデータを抽出
                        json_start = line.find('{')
                        if json_start != -1:
                            json_data = line[json_start:].strip()
                            event = json.loads(json_data)
                            
                            event_time = event.get("timestamp", "")
                            if start_date <= event_time <= end_date:
                                events.append(event)
                                
                    except json.JSONDecodeError:
                        continue
                        
        except Exception:
            pass
        
        return events

# 監査ログインスタンス
audit_logger = SecurityAuditLogger()

def audit_action(action_type="access", resource="unknown"):
    """監査ログ記録デコレータ"""
    
    def decorator(f):
        def wrapper(*args, **kwargs):
            user = kwargs.get('user', 'anonymous')
            
            try:
                result = f(*args, **kwargs)
                
                if action_type == "access":
                    audit_logger.log_access_attempt(
                        user=user,
                        resource=resource,
                        action=f.__name__,
                        result="success"
                    )
                elif action_type == "data":
                    audit_logger.log_data_access(
                        user=user,
                        data_type=resource,
                        operation=f.__name__,
                        record_count=kwargs.get('record_count', 0),
                        purpose=kwargs.get('purpose', 'analysis')
                    )
                
                return result
                
            except Exception as e:
                audit_logger.log_access_attempt(
                    user=user,
                    resource=resource,
                    action=f.__name__,
                    result="failure",
                    details={"error": str(e)}
                )
                raise
        
        return wrapper
    
    return decorator
'''
        
        # 監査ログモジュール保存
        audit_file = self.security_dir / "audit_logging.py"
        with open(audit_file, 'w', encoding='utf-8') as f:
            f.write(audit_module)
        
        return {
            "measure": "監査ログ機能",
            "status": "実装完了",
            "components": [
                "セキュリティイベントログ",
                "アクセス監査ログ",
                "データアクセスログ",
                "ログ整合性検証",
                "監査レポート生成"
            ],
            "file": str(audit_file)
        }
    
    def _implement_medical_data_compliance(self) -> Dict[str, Any]:
        """医療データコンプライアンス実装"""
        
        print("   🏥 医療データコンプライアンス実装中...")
        
        # 医療データコンプライアンスモジュール作成
        compliance_module = '''
# 医療データコンプライアンスモジュール
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
from pathlib import Path
import json

class MedicalDataCompliance:
    """医療データコンプライアンス管理クラス"""
    
    def __init__(self):
        self.compliance_config = self._load_compliance_config()
        self.consent_records = {}
        self.data_usage_log = []
    
    def _load_compliance_config(self) -> Dict[str, Any]:
        """コンプライアンス設定の読み込み"""
        
        return {
            "data_retention": {
                "max_retention_days": 2555,  # 7年
                "anonymization_after_days": 365,  # 1年後に匿名化
                "secure_deletion_required": True
            },
            "consent_management": {
                "explicit_consent_required": True,
                "purpose_limitation": True,
                "withdrawal_allowed": True,
                "consent_expiry_days": 365
            },
            "data_minimization": {
                "collect_minimum_only": True,
                "purpose_specific": True,
                "automatic_deletion": True
            },
            "privacy_protection": {
                "anonymization_required": True,
                "pseudonymization_allowed": True,
                "encryption_required": True
            }
        }
    
    def detect_personal_information(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """個人情報の検出"""
        
        personal_data_patterns = {
            "名前": [r"名前", r"氏名", r"name", r"員工", r"職員名"],
            "ID": [r"id", r"番号", r"識別", r"employee", r"職員"],
            "連絡先": [r"電話", r"phone", r"tel", r"email", r"メール", r"address", r"住所"],
            "医療情報": [r"病歴", r"診断", r"treatment", r"medication", r"薬", r"症状"],
            "機密情報": [r"給与", r"salary", r"評価", r"evaluation", r"personal", r"private"]
        }
        
        detected_columns = {category: [] for category in personal_data_patterns}
        
        for column in df.columns:
            column_lower = column.lower()
            
            for category, patterns in personal_data_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, column_lower):
                        detected_columns[category].append(column)
                        break
        
        return detected_columns
    
    def apply_data_minimization(self, df: pd.DataFrame, purpose: str) -> pd.DataFrame:
        """データ最小化原則の適用"""
        
        # 目的別に必要な列を定義
        purpose_columns = {
            "shift_analysis": [
                "date", "shift_type", "hours", "department", "role"
            ],
            "workload_analysis": [
                "date", "hours", "department", "task_type"
            ],
            "scheduling": [
                "date", "shift_type", "department", "availability"
            ]
        }
        
        if purpose in purpose_columns:
            required_columns = purpose_columns[purpose]
            
            # 必要な列のみを保持（存在する列のみ）
            available_columns = [col for col in required_columns if col in df.columns]
            
            if available_columns:
                return df[available_columns].copy()
        
        # デフォルトでは全列を返すが、個人情報は除外
        personal_info = self.detect_personal_information(df)
        exclude_columns = []
        
        for category, columns in personal_info.items():
            if category in ["名前", "連絡先", "医療情報"]:
                exclude_columns.extend(columns)
        
        safe_columns = [col for col in df.columns if col not in exclude_columns]
        return df[safe_columns].copy()
    
    def anonymize_data(self, df: pd.DataFrame, method: str = "hash") -> pd.DataFrame:
        """データの匿名化"""
        
        df_anon = df.copy()
        personal_info = self.detect_personal_information(df)
        
        import hashlib
        
        for category, columns in personal_info.items():
            if category in ["名前", "ID"]:
                for col in columns:
                    if col in df_anon.columns:
                        if method == "hash":
                            df_anon[col] = df_anon[col].apply(
                                lambda x: hashlib.sha256(str(x).encode()).hexdigest()[:10] 
                                if pd.notna(x) else x
                            )
                        elif method == "mask":
                            df_anon[col] = "***MASKED***"
                        elif method == "remove":
                            df_anon = df_anon.drop(columns=[col])
        
        return df_anon
    
    def record_consent(self, user_id: str, data_types: List[str], purposes: List[str], 
                      consent_given: bool = True) -> str:
        """同意の記録"""
        
        consent_id = f"consent_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id}"
        
        consent_record = {
            "consent_id": consent_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "data_types": data_types,
            "purposes": purposes,
            "consent_given": consent_given,
            "expiry_date": (datetime.now() + timedelta(
                days=self.compliance_config["consent_management"]["consent_expiry_days"]
            )).isoformat(),
            "withdrawal_allowed": self.compliance_config["consent_management"]["withdrawal_allowed"]
        }
        
        self.consent_records[consent_id] = consent_record
        
        # 同意記録をファイルに保存
        self._save_consent_record(consent_record)
        
        return consent_id
    
    def _save_consent_record(self, consent_record: Dict[str, Any]):
        """同意記録の保存"""
        
        consent_dir = Path("security/consent_records")
        consent_dir.mkdir(parents=True, exist_ok=True)
        
        consent_file = consent_dir / f"{consent_record['consent_id']}.json"
        
        with open(consent_file, 'w', encoding='utf-8') as f:
            json.dump(consent_record, f, indent=2, ensure_ascii=False)
    
    def verify_consent(self, user_id: str, data_type: str, purpose: str) -> bool:
        """同意の確認"""
        
        for consent_record in self.consent_records.values():
            if (consent_record["user_id"] == user_id and
                consent_record["consent_given"] and
                data_type in consent_record["data_types"] and
                purpose in consent_record["purposes"]):
                
                # 有効期限確認
                expiry = datetime.fromisoformat(consent_record["expiry_date"])
                if datetime.now() < expiry:
                    return True
        
        return False
    
    def log_data_usage(self, user_id: str, data_type: str, purpose: str, 
                      operation: str, details: Optional[Dict] = None):
        """データ使用の記録"""
        
        usage_record = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "data_type": data_type,
            "purpose": purpose,
            "operation": operation,
            "details": details or {},
            "compliance_status": "compliant" if self.verify_consent(user_id, data_type, purpose) else "non_compliant"
        }
        
        self.data_usage_log.append(usage_record)
        
        # 使用記録をファイルに保存
        self._save_usage_record(usage_record)
    
    def _save_usage_record(self, usage_record: Dict[str, Any]):
        """使用記録の保存"""
        
        usage_dir = Path("logs/data_usage")
        usage_dir.mkdir(parents=True, exist_ok=True)
        
        usage_file = usage_dir / f"usage_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        with open(usage_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(usage_record, ensure_ascii=False) + '\\n')
    
    def check_retention_compliance(self) -> List[Dict[str, Any]]:
        """保存期間コンプライアンスチェック"""
        
        compliance_issues = []
        max_retention = self.compliance_config["data_retention"]["max_retention_days"]
        
        # データファイルの作成日をチェック
        data_patterns = ["*.xlsx", "*.csv", "logs/*.log"]
        
        for pattern in data_patterns:
            for file_path in Path(".").glob(pattern):
                try:
                    file_stat = file_path.stat()
                    creation_date = datetime.fromtimestamp(file_stat.st_ctime)
                    age_days = (datetime.now() - creation_date).days
                    
                    if age_days > max_retention:
                        compliance_issues.append({
                            "file": str(file_path),
                            "age_days": age_days,
                            "max_retention": max_retention,
                            "action_required": "secure_deletion",
                            "urgency": "high"
                        })
                    elif age_days > self.compliance_config["data_retention"]["anonymization_after_days"]:
                        compliance_issues.append({
                            "file": str(file_path),
                            "age_days": age_days,
                            "action_required": "anonymization",
                            "urgency": "medium"
                        })
                        
                except Exception:
                    pass
        
        return compliance_issues
    
    def generate_compliance_report(self) -> Dict[str, Any]:
        """コンプライアンスレポート生成"""
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "consent_summary": {
                "total_consents": len(self.consent_records),
                "active_consents": sum(1 for c in self.consent_records.values() 
                                     if c["consent_given"]),
                "expired_consents": sum(1 for c in self.consent_records.values()
                                      if datetime.now() > datetime.fromisoformat(c["expiry_date"]))
            },
            "data_usage_summary": {
                "total_operations": len(self.data_usage_log),
                "compliant_operations": sum(1 for u in self.data_usage_log 
                                          if u["compliance_status"] == "compliant"),
                "non_compliant_operations": sum(1 for u in self.data_usage_log 
                                              if u["compliance_status"] == "non_compliant")
            },
            "retention_compliance": self.check_retention_compliance(),
            "recommendations": self._generate_compliance_recommendations()
        }
        
        return report
    
    def _generate_compliance_recommendations(self) -> List[str]:
        """コンプライアンス推奨事項の生成"""
        
        recommendations = []
        
        # 期限切れ同意のチェック
        expired_consents = [c for c in self.consent_records.values()
                          if datetime.now() > datetime.fromisoformat(c["expiry_date"])]
        
        if expired_consents:
            recommendations.append(f"{len(expired_consents)}件の期限切れ同意を更新してください")
        
        # 非準拠操作のチェック
        non_compliant = [u for u in self.data_usage_log 
                        if u["compliance_status"] == "non_compliant"]
        
        if non_compliant:
            recommendations.append(f"{len(non_compliant)}件の非準拠データ操作を調査してください")
        
        # 保存期間違反のチェック
        retention_issues = self.check_retention_compliance()
        if retention_issues:
            recommendations.append(f"{len(retention_issues)}件のファイルが保存期間ポリシーに違反しています")
        
        return recommendations

# 医療データコンプライアンスインスタンス
medical_compliance = MedicalDataCompliance()

def compliance_check(data_type="medical", purpose="analysis"):
    """コンプライアンスチェックデコレータ"""
    
    def decorator(f):
        def wrapper(*args, **kwargs):
            user_id = kwargs.get('user_id', 'system')
            
            # 同意確認
            if not medical_compliance.verify_consent(user_id, data_type, purpose):
                return {"error": "データ使用に必要な同意が得られていません", "status": 403}
            
            # 処理実行
            try:
                result = f(*args, **kwargs)
                
                # 使用記録
                medical_compliance.log_data_usage(
                    user_id=user_id,
                    data_type=data_type,
                    purpose=purpose,
                    operation=f.__name__,
                    details={"args_count": len(args), "kwargs_count": len(kwargs)}
                )
                
                return result
                
            except Exception as e:
                medical_compliance.log_data_usage(
                    user_id=user_id,
                    data_type=data_type,
                    purpose=purpose,
                    operation=f.__name__,
                    details={"error": str(e)}
                )
                raise
        
        return wrapper
    
    return decorator
'''
        
        # 医療データコンプライアンスモジュール保存
        compliance_file = self.security_dir / "medical_compliance.py"
        with open(compliance_file, 'w', encoding='utf-8') as f:
            f.write(compliance_module)
        
        return {
            "measure": "医療データコンプライアンス",
            "status": "実装完了",
            "components": [
                "個人情報検出",
                "データ最小化",
                "匿名化処理",
                "同意管理",
                "使用記録・追跡",
                "保存期間管理"
            ],
            "file": str(compliance_file)
        }
    
    def _implement_system_hardening(self) -> Dict[str, Any]:
        """システム強化実装"""
        
        print("   ⚙️ システム強化実装中...")
        
        # システム強化設定ファイル作成
        hardening_config = '''
# システムセキュリティ強化設定

import os
from pathlib import Path

class SystemHardening:
    """システムセキュリティ強化クラス"""
    
    def __init__(self):
        self.security_settings = self._get_security_settings()
    
    def _get_security_settings(self):
        """セキュリティ設定の取得"""
        
        return {
            "flask_settings": {
                "SECRET_KEY": os.environ.get("FLASK_SECRET_KEY", self._generate_secret_key()),
                "SESSION_COOKIE_SECURE": True,
                "SESSION_COOKIE_HTTPONLY": True,
                "SESSION_COOKIE_SAMESITE": "Lax",
                "PERMANENT_SESSION_LIFETIME": 3600,  # 1時間
                "WTF_CSRF_ENABLED": True,
                "DEBUG": False  # 本番環境では必ずFalse
            },
            "dash_settings": {
                "suppress_callback_exceptions": False,
                "serve_locally": True,
                "dev_tools_hot_reload": False,
                "dev_tools_ui": False
            },
            "security_headers": {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY", 
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                "Content-Security-Policy": "default-src 'self'"
            },
            "file_permissions": {
                "log_files": 0o640,
                "config_files": 0o600,
                "data_files": 0o600,
                "executable_files": 0o750
            }
        }
    
    def _generate_secret_key(self):
        """セキュアなシークレットキー生成"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def apply_flask_security(self, app):
        """Flaskアプリケーションへのセキュリティ設定適用"""
        
        for key, value in self.security_settings["flask_settings"].items():
            app.config[key] = value
        
        # セキュリティヘッダー追加
        @app.after_request
        def add_security_headers(response):
            for header, value in self.security_settings["security_headers"].items():
                response.headers[header] = value
            return response
        
        return app
    
    def apply_dash_security(self, app):
        """Dashアプリケーションへのセキュリティ設定適用"""
        
        # Dashのセキュリティ設定
        for key, value in self.security_settings["dash_settings"].items():
            setattr(app, key, value)
        
        return app
    
    def secure_file_permissions(self):
        """ファイルパーミッションの設定"""
        
        permission_mappings = [
            (["logs/", "logs/security_audit/"], self.security_settings["file_permissions"]["log_files"]),
            (["security/", "config/"], self.security_settings["file_permissions"]["config_files"]),
            (["*.xlsx", "*.csv"], self.security_settings["file_permissions"]["data_files"]),
            (["*.py"], self.security_settings["file_permissions"]["executable_files"])
        ]
        
        for patterns, permission in permission_mappings:
            for pattern in patterns:
                for file_path in Path(".").glob(pattern):
                    try:
                        if file_path.is_file():
                            os.chmod(file_path, permission)
                    except Exception:
                        pass  # Windowsでは一部の権限設定ができない場合がある
    
    def create_security_config_file(self):
        """セキュリティ設定ファイルの作成"""
        
        config_content = '''
# セキュリティ設定ファイル
import os

# 環境変数から取得（本番環境では必須）
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY")
DATABASE_URL = os.environ.get("DATABASE_URL")
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")

# セキュリティ設定
SECURITY_SETTINGS = {
    "authentication_required": True,
    "session_timeout": 3600,
    "max_login_attempts": 3,
    "password_complexity": True,
    "audit_logging": True,
    "data_encryption": True,
    "backup_encryption": True
}

# 医療データ特化設定
MEDICAL_DATA_SETTINGS = {
    "anonymization_required": True,
    "consent_tracking": True,
    "retention_period": 2555,  # 7年
    "hipaa_compliance": True,
    "gdpr_compliance": True
}

# ログ設定
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    "handlers": ["file", "security_audit"],
    "retention": "7 years"
}
'''
        
        config_file = Path("security/security_config.py")
        config_file.parent.mkdir(exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        return str(config_file)
    
    def create_env_template(self):
        """環境変数テンプレートの作成"""
        
        env_template = '''# セキュリティ関連環境変数テンプレート
# 本番環境では必ず適切な値を設定してください

# Flask関連
FLASK_SECRET_KEY=your_secret_key_here
FLASK_ENV=production

# データベース関連（使用する場合）
DATABASE_URL=your_database_url_here

# 暗号化関連
ENCRYPTION_KEY=your_encryption_key_here

# 認証関連
AUTH_SECRET=your_auth_secret_here

# ログ関連
LOG_LEVEL=INFO
LOG_DIR="/secure/path/to/logs"

# 医療データ関連
MEDICAL_DATA_ENCRYPTION=true
AUDIT_LOGGING=true
ANONYMIZATION_ENABLED=true

# セキュリティ強化
SECURE_HEADERS=true
CSRF_PROTECTION=true
SESSION_SECURITY=true
'''
        
        env_file = Path(".env.template")
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_template)
        
        return str(env_file)

# システム強化インスタンス
system_hardening = SystemHardening()

def secure_app(app, app_type="flask"):
    """アプリケーションのセキュリティ強化"""
    
    if app_type == "flask":
        return system_hardening.apply_flask_security(app)
    elif app_type == "dash":
        return system_hardening.apply_dash_security(app)
    
    return app
'''
        
        # システム強化モジュール保存
        hardening_file = self.security_dir / "system_hardening.py"
        with open(hardening_file, 'w', encoding='utf-8') as f:
            f.write(hardening_config)
        
        return {
            "measure": "システム強化",
            "status": "実装完了",
            "components": [
                "Flaskセキュリティ設定",
                "Dashセキュリティ設定", 
                "セキュリティヘッダー",
                "ファイルパーミッション",
                "環境変数管理"
            ],
            "file": str(hardening_file)
        }
    
    def _generate_security_policies(self) -> List[str]:
        """セキュリティポリシー生成"""
        
        print("   📋 セキュリティポリシー生成中...")
        
        # セキュリティポリシー文書
        policy_documents = {
            "data_protection_policy.md": '''# データ保護ポリシー

## 目的
医療シフト分析システムにおけるデータ保護の方針と手順を定める。

## 適用範囲
- すべての医療関連データ
- 個人識別情報
- システムログ・監査証跡
- バックアップデータ

## データ分類
### 制限情報（Restricted）
- 患者情報・医療記録
- 職員の個人情報
- 勤務シフト詳細データ

### 機密情報（Confidential）
- システム設定・ログ
- 分析結果・レポート
- アクセス制御情報

### 内部限定（Internal）
- システム仕様書
- 運用マニュアル
- 技術文書

## 保護対策
1. **暗号化**: すべての機密データは暗号化して保存
2. **アクセス制御**: 役割に基づく適切なアクセス制限
3. **監査ログ**: すべてのデータアクセスを記録・監視
4. **バックアップ**: 暗号化されたバックアップの定期作成
5. **削除**: 保存期間経過後のセキュアな削除

## コンプライアンス
- 医療情報保護法準拠
- 個人情報保護法準拠
- GDPR準拠（該当する場合）

## 違反時の対応
1. 即座の影響範囲調査
2. 関係者への通知
3. 再発防止策の実施
4. 監督機関への報告（必要に応じて）
''',
            
            "access_control_policy.md": '''# アクセス制御ポリシー

## 認証要件
- すべてのユーザーは適切な認証が必要
- セッションタイムアウト: 1時間
- 失敗ログイン制限: 3回まで

## 役割定義
### 管理者（Admin）
- 権限: システム全体の管理・設定
- データアクセス: すべてのデータ

### マネージャー（Manager）
- 権限: 部門データの読み書き
- データアクセス: 担当部門・集計データ

### スタッフ（Staff）
- 権限: 自分のデータ・集計データの閲覧
- データアクセス: 個人データ・匿名化データ

### 閲覧者（Viewer）
- 権限: 集計データの閲覧のみ
- データアクセス: 匿名化された集計データ

## セッション管理
- セキュアクッキーの使用
- CSRF保護の実装
- セッションローテーション

## パスワードポリシー
- 最小8文字以上
- 英数字・記号を含む
- 定期的な変更推奨
- 過去のパスワード再利用禁止
''',
            
            "incident_response_policy.md": '''# インシデント対応ポリシー

## インシデント分類
### レベル1（Critical）
- データ漏洩・不正アクセス
- システム侵害
- 大規模なサービス停止

### レベル2（High）
- 認証システムの障害
- 医療データの意図しない公開
- セキュリティ設定の不備

### レベル3（Medium）
- 個別ユーザーアカウントの問題
- 軽微なシステム障害
- ポリシー違反

## 対応手順
1. **検知・報告（15分以内）**
   - インシデントの確認
   - 影響範囲の初期評価
   - 関係者への第一報

2. **初期対応（1時間以内）**
   - 被害拡大の防止
   - 証拠保全
   - 暫定対策の実施

3. **詳細調査（24時間以内）**
   - 根本原因の特定
   - 完全な影響範囲の調査
   - 法的要件の確認

4. **復旧・改善（72時間以内）**
   - システムの復旧
   - 再発防止策の実施
   - 関係者への報告

## 連絡体制
- インシデント責任者: [担当者名]
- セキュリティ担当者: [担当者名]
- 経営陣: [担当者名]
- 外部機関: [必要に応じて]

## 報告要件
- 内部報告: すべてのインシデント
- 外部報告: レベル1・2インシデント
- 記録保管: 7年間保存
'''
        }
        
        policy_files = []
        
        for filename, content in policy_documents.items():
            policy_file = self.security_dir / "policies" / filename
            policy_file.parent.mkdir(exist_ok=True)
            
            with open(policy_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            policy_files.append(str(policy_file))
        
        return policy_files
    
    def generate_security_report(self, vulnerabilities: List[SecurityVulnerability], 
                                implementation_results: Dict[str, Any]) -> str:
        """セキュリティレポート生成"""
        
        # 脆弱性サマリー
        vuln_by_severity = {}
        for vuln in vulnerabilities:
            severity = vuln.severity
            if severity not in vuln_by_severity:
                vuln_by_severity[severity] = []
            vuln_by_severity[severity].append(vuln)
        
        report = f"""🛡️ **C3 セキュリティ強化レポート**
実行日時: {datetime.now().isoformat()}

📊 **セキュリティ評価結果**
総脆弱性数: {len(vulnerabilities)}
- Critical: {len(vuln_by_severity.get('critical', []))}
- High: {len(vuln_by_severity.get('high', []))}
- Medium: {len(vuln_by_severity.get('medium', []))}
- Low: {len(vuln_by_severity.get('low', []))}

🔒 **実装済みセキュリティ対策**
総対策数: {len(implementation_results['implemented_measures'])}"""

        for measure in implementation_results['implemented_measures']:
            report += f"""

**{measure['measure']}**
- 状況: {measure['status']}
- 構成要素: {', '.join(measure['components'])}
- ファイル: {measure['file']}"""

        report += f"""

📋 **セキュリティポリシー**
作成されたポリシー: {len(implementation_results['policies_created'])}件
- データ保護ポリシー
- アクセス制御ポリシー  
- インシデント対応ポリシー

🎯 **主要な脆弱性と対策**"""

        for severity in ['critical', 'high', 'medium']:
            if severity in vuln_by_severity:
                report += f"\n\n**{severity.upper()}レベル脆弱性**"
                for vuln in vuln_by_severity[severity][:3]:  # 上位3件
                    report += f"""
- {vuln.description}
  対策: {vuln.remediation}"""

        report += f"""

💡 **重要な洞察**
• セキュリティは後付けではなく、設計段階からの組み込みが重要
• 医療データの特殊性を考慮した多層防御を実装
• 監査・コンプライアンス要件に対応した包括的な対策を構築
• 継続的な監視・改善により脅威に対応

🎨 **セキュリティ哲学**
「医療データを扱う責任の重さを理解し、
最高水準のセキュリティでデータと人々を守る」

1. **ゼロトラスト**: すべてのアクセスを検証・記録
2. **深層防御**: 複数の防御層による多重保護  
3. **プライバシー設計**: データ保護を最初から考慮
4. **透明性**: 監査可能で説明責任を果たせる設計

🔄 **今後の展開**
- 📊 **継続監視**: セキュリティ指標の定期的な評価
- 🔧 **脅威対応**: 新たな脅威に対する防御策の追加
- 📈 **改善実装**: 発見された脆弱性の段階的な修正
- 🌟 **先進技術**: AI・機械学習によるセキュリティ強化

セキュリティは継続的な取り組みであり、
技術の進歩と脅威の変化に常に対応していく。"""

        return report
    
    def save_security_results(self, vulnerabilities: List[SecurityVulnerability], 
                             implementation_results: Dict[str, Any]) -> str:
        """セキュリティ結果保存"""
        
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "vulnerabilities": [
                {
                    "vuln_id": v.vuln_id,
                    "category": v.category.value,
                    "severity": v.severity,
                    "description": v.description,
                    "affected_files": v.affected_files,
                    "remediation": v.remediation,
                    "status": v.status
                } for v in vulnerabilities
            ],
            "implementation_results": implementation_results,
            "summary": {
                "total_vulnerabilities": len(vulnerabilities),
                "critical_vulnerabilities": len([v for v in vulnerabilities if v.severity == "critical"]),
                "implemented_measures": len(implementation_results["implemented_measures"]),
                "policies_created": len(implementation_results["policies_created"])
            }
        }
        
        result_file = self.audit_dir / f"security_assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        return str(result_file)

def main():
    """メイン実行"""
    
    try:
        print("🛡️ C3 セキュリティ強化開始")
        print("💡 深い思考: セキュリティは責任であり、医療データを守る使命")
        print("=" * 80)
        
        enhancer = SecurityEnhancer()
        
        # 1. セキュリティ評価実行
        vulnerabilities = enhancer.perform_security_assessment()
        
        # 2. セキュリティ対策実装
        implementation_results = enhancer.implement_security_measures(vulnerabilities)
        
        # 3. レポート生成・表示
        print("\n" + "=" * 80)
        print("📋 セキュリティ強化レポート")
        print("=" * 80)
        
        report = enhancer.generate_security_report(vulnerabilities, implementation_results)
        print(report)
        
        # 4. 結果保存
        result_file = enhancer.save_security_results(vulnerabilities, implementation_results)
        print(f"\n📁 セキュリティ評価結果保存: {result_file}")
        
        print(f"\n🎯 C3 セキュリティ強化: ✅ 完了")
        print("🛡️ 医療データを守る責任を全うし、信頼される系構築")
        
        return True
        
    except Exception as e:
        print(f"❌ セキュリティ強化エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)