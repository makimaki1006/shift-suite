# データ保護・暗号化モジュール
import hashlib
import os
from pathlib import Path

class DataProtector:
    """データ保護クラス"""
    
    def __init__(self):
        self.security_dir = Path("security")
        self.security_dir.mkdir(exist_ok=True)
    
    def hash_personal_identifier(self, identifier: str) -> str:
        """個人識別子のハッシュ化"""
        return hashlib.sha256(identifier.encode()).hexdigest()
    
    def anonymize_excel_data(self, df):
        """Excelデータの匿名化"""
        df_anonymized = df.copy()
        
        # 個人識別可能な列の検出と匿名化
        personal_columns = ['name', '名前', 'employee_id', '職員ID']
        
        for col in df_anonymized.columns:
            col_lower = col.lower()
            if any(pc in col_lower for pc in personal_columns):
                df_anonymized[col] = df_anonymized[col].apply(
                    lambda x: self.hash_personal_identifier(str(x)) if str(x) != 'nan' else x
                )
        
        return df_anonymized

# データ保護インスタンス
data_protector = DataProtector()
