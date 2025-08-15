"""
Phase5検証デバッグ
"""
import os

# ファイル確認
files_to_check = [
    'C2_IMPLEMENTATION_SUMMARY.md',
    'c2-mobile-integrated.css',
    'c2-mobile-integrated.js',
    'c2-service-worker.js',
    'c2-mobile-config-integrated.json'
]

print("=== Phase5検証デバッグ ===")

for file_name in files_to_check:
    if os.path.exists(file_name):
        size = os.path.getsize(file_name)
        print(f"✅ {file_name}: {size} bytes")
        
        if file_name == 'C2_IMPLEMENTATION_SUMMARY.md':
            with open(file_name, 'r', encoding='utf-8') as f:
                content = f.read()
            
            indicators = [
                "モバイル表示の大幅改善",
                "既存機能100%保護", 
                "c2-mobile-integrated.css",
                "c2-mobile-integrated.js"
            ]
            
            print(f"\n📄 {file_name} 内容確認:")
            for indicator in indicators:
                found = indicator in content
                status = "✅" if found else "❌"
                print(f"  {status} {indicator}")
    else:
        print(f"❌ {file_name}: ファイル不在")

# Phase5結果ファイル確認
import glob
phase5_files = glob.glob('C2_Phase5_*.json')
print(f"\n📋 Phase5結果ファイル: {len(phase5_files)}件")
for f in phase5_files:
    print(f"  - {f}")