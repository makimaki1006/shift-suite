#!/usr/bin/env python3
"""
簡易アウトプット検証スクリプト - 実際のファイル内容を直接確認
"""

import os
import json
from pathlib import Path

def verify_output():
    """アウトプットの直接検証"""
    project_root = Path(__file__).parent
    results = {
        "zip_files": {},
        "extracted_results": {},
        "key_findings": [],
        "quality_assessment": {}
    }
    
    # 1. ZIPファイルの確認
    print("=== ZIPファイル分析 ===")
    zip_files = [
        "analysis_results (1).zip",
        "analysis_results.zip"
    ]
    
    for zip_file in zip_files:
        zip_path = project_root / zip_file
        if zip_path.exists():
            file_size = zip_path.stat().st_size
            results["zip_files"][zip_file] = {
                "exists": True,
                "size_bytes": file_size,
                "size_mb": round(file_size / 1024 / 1024, 2)
            }
            print(f"✓ {zip_file}: {file_size:,} bytes ({round(file_size / 1024 / 1024, 2)} MB)")
        else:
            results["zip_files"][zip_file] = {"exists": False}
            print(f"✗ {zip_file}: 見つかりません")
    
    # 2. extracted_resultsの内容確認
    print("\n=== extracted_results内容分析 ===")
    extracted_dir = project_root / "extracted_results"
    
    if extracted_dir.exists():
        # ファイル統計
        all_files = list(extracted_dir.rglob("*"))
        file_files = [f for f in all_files if f.is_file()]
        
        results["extracted_results"]["total_files"] = len(file_files)
        results["extracted_results"]["total_dirs"] = len([f for f in all_files if f.is_dir()])
        
        # ファイル形式別統計
        extensions = {}
        for f in file_files:
            ext = f.suffix.lower()
            if ext not in extensions:
                extensions[ext] = 0
            extensions[ext] += 1
        
        results["extracted_results"]["file_types"] = extensions
        print(f"総ファイル数: {len(file_files)}")
        print("ファイル形式:")
        for ext, count in sorted(extensions.items(), key=lambda x: x[1], reverse=True):
            print(f"  {ext or '(no extension)'}: {count}ファイル")
        
        # 3. 重要ファイルの内容確認
        print("\n=== 重要ファイル内容 ===")
        key_files = [
            ("out_median_based/stats_summary.txt", "統計サマリー"),
            ("out_median_based/hire_plan.txt", "採用計画"),
            ("leave_analysis.csv", "休暇分析"),
            ("out_median_based/forecast.summary.txt", "予測サマリー")
        ]
        
        for rel_path, description in key_files:
            file_path = extracted_dir / rel_path
            if file_path.exists():
                print(f"\n[{description}] {rel_path}:")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if len(content) > 500:
                            print(f"  (ファイルサイズ: {len(content)}文字, 最初の500文字のみ表示)")
                            print(content[:500] + "...")
                        else:
                            print(content if content else "  (空ファイル)")
                        
                        results["key_findings"].append({
                            "file": rel_path,
                            "description": description,
                            "content_size": len(content),
                            "sample": content[:200] if content else "(empty)"
                        })
                except Exception as e:
                    print(f"  読み込みエラー: {e}")
            else:
                print(f"\n[{description}] {rel_path}: 見つかりません")
        
        # 4. シナリオ別サイズ分析
        print("\n=== シナリオ別分析 ===")
        scenarios = ["out_mean_based", "out_median_based", "out_p25_based"]
        scenario_stats = {}
        
        for scenario in scenarios:
            scenario_dir = extracted_dir / scenario
            if scenario_dir.exists():
                files = list(scenario_dir.iterdir())
                total_size = sum(f.stat().st_size for f in files if f.is_file())
                scenario_stats[scenario] = {
                    "files": len([f for f in files if f.is_file()]),
                    "size_bytes": total_size,
                    "size_mb": round(total_size / 1024 / 1024, 2)
                }
                print(f"{scenario}: {len(files)}ファイル, {round(total_size / 1024 / 1024, 2)} MB")
        
        results["extracted_results"]["scenarios"] = scenario_stats
    
    # 5. 品質評価
    print("\n=== 品質評価 ===")
    
    # 実用的情報の割合
    total_files = results["extracted_results"].get("total_files", 0)
    useful_extensions = ['.txt', '.csv', '.xlsx', '.json']
    useful_files = sum(results["extracted_results"]["file_types"].get(ext, 0) for ext in useful_extensions)
    
    if total_files > 0:
        accessibility_ratio = useful_files / total_files
        results["quality_assessment"]["accessibility_ratio"] = round(accessibility_ratio, 2)
        print(f"アクセシブルなファイル形式: {useful_files}/{total_files} ({round(accessibility_ratio * 100, 1)}%)")
    
    # 重複シナリオ
    if len(scenario_stats) > 1:
        total_scenario_size = sum(s["size_bytes"] for s in scenario_stats.values())
        redundancy_factor = (len(scenario_stats) - 1) / len(scenario_stats)
        redundant_size_mb = round(total_scenario_size * redundancy_factor / 1024 / 1024, 2)
        results["quality_assessment"]["redundant_size_mb"] = redundant_size_mb
        print(f"シナリオ重複による冗長データ: 約{redundant_size_mb} MB")
    
    # プロジェクトサイズ対出力サイズ
    project_size_mb = 990  # 既知の値
    output_size_mb = sum(z["size_mb"] for z in results["zip_files"].values() if z.get("exists", False))
    output_ratio = output_size_mb / project_size_mb
    results["quality_assessment"]["output_ratio"] = round(output_ratio, 4)
    print(f"出力/プロジェクトサイズ比: {round(output_ratio * 100, 2)}%")
    
    # 結果を保存
    output_file = project_root / "simple_output_verification_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n詳細結果を保存: {output_file}")
    
    return results

if __name__ == "__main__":
    print("🔍 簡易アウトプット品質検証")
    print("=" * 50)
    results = verify_output()
    print("=" * 50)
    print("検証完了")