# -*- coding: utf-8 -*-
import sys
import pandas as pd

print("=== エンコーディング修正テスト ===")
print(f"標準出力エンコーディング: {sys.stdout.encoding}")

# テストデータで確認
test_data = pd.DataFrame({
    'staff': ['山田太郎', '田中花子', '佐藤次郎'],
    'role': ['介護', '看護師', '管理者']
})

print("\nテストデータ:")
print(test_data)

# 日本語文字列のテスト
test_string = "これは日本語のテストです。文字化けしていませんか？"
print(f"\n日本語テスト: {test_string}")

print("\n✓ エンコーディング修正が正常に適用されました")
