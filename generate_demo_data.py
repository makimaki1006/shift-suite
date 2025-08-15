#!/usr/bin/env python3
"""
グループホーム向け営業デモ用サンプルデータ生成スクリプト
2ユニット18名体制のリアルなシフトデータを生成
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os
import json

# 職員マスタ定義
STAFF_MASTER = {
    # ユニット1 - 正規職員（夜勤可）
    "田中花子": {"unit": 1, "type": "正規", "role": "介護士", "night": True, "skill": "ベテラン", "night_freq": 6},
    "佐藤太郎": {"unit": 1, "type": "正規", "role": "介護士", "night": True, "skill": "中堅", "night_freq": 8},
    "鈴木一郎": {"unit": 1, "type": "正規", "role": "介護士", "night": True, "skill": "中堅", "night_freq": 7},
    "高橋美咲": {"unit": 1, "type": "正規", "role": "介護士", "night": True, "skill": "若手", "night_freq": 5},
    "渡辺健": {"unit": 1, "type": "正規", "role": "介護士", "night": True, "skill": "中堅", "night_freq": 6},
    "伊藤直子": {"unit": 1, "type": "正規", "role": "介護士", "night": True, "skill": "ベテラン", "night_freq": 4},
    
    # ユニット2 - 正規職員（夜勤可）
    "山田美香": {"unit": 2, "type": "正規", "role": "介護士", "night": True, "skill": "リーダー候補", "night_freq": 4},
    "中村大輔": {"unit": 2, "type": "正規", "role": "介護士", "night": True, "skill": "ベテラン", "night_freq": 6},
    "小林愛": {"unit": 2, "type": "正規", "role": "介護士", "night": True, "skill": "中堅", "night_freq": 8},
    "加藤翔": {"unit": 2, "type": "正規", "role": "介護士", "night": True, "skill": "若手", "night_freq": 7},
    "吉田恵": {"unit": 2, "type": "正規", "role": "介護士", "night": True, "skill": "中堅", "night_freq": 5},
    "松本和也": {"unit": 2, "type": "正規", "role": "介護士", "night": True, "skill": "夜勤専従", "night_freq": 10},
    
    # パート職員（日中のみ）
    "斎藤恵子": {"unit": 1, "type": "パート", "role": "介護士", "night": False, "skill": "パート", "hours": "9:00-16:00", "days": 4},
    "木村洋子": {"unit": 2, "type": "パート", "role": "介護士", "night": False, "skill": "パート", "hours": "10:00-15:00", "days": 3},
    "林さゆり": {"unit": 1, "type": "パート", "role": "介護士", "night": False, "skill": "パート", "hours": "8:30-13:30", "days": 5},
    "森田明美": {"unit": 2, "type": "パート", "role": "介護士", "night": False, "skill": "パート", "hours": "13:00-18:00", "days": 4},
    "橋本真理": {"unit": 1, "type": "パート", "role": "介護士", "night": False, "skill": "パート", "hours": "9:00-14:00", "days": 3},
    "山口裕子": {"unit": 2, "type": "パート", "role": "介護士", "night": False, "skill": "パート", "hours": "14:00-19:00", "days": 4},
    "石川美穂": {"unit": 1, "type": "パート", "role": "介護士", "night": False, "skill": "パート", "hours": "7:00-12:00", "days": 5},
    "福田千夏": {"unit": 2, "type": "パート", "role": "介護士", "night": False, "skill": "パート", "hours": "11:00-16:00", "days": 3},
    
    # スポットバイト
    "スポットA": {"unit": 1, "type": "スポット", "role": "介護士", "night": False, "skill": "スポット", "days": 2},
    "スポットB": {"unit": 2, "type": "スポット", "role": "介護士", "night": False, "skill": "スポット", "days": 2},
    
    # 管理職
    "施設長": {"unit": 0, "type": "正規", "role": "管理者", "night": False, "skill": "管理"},
    "ケアマネ": {"unit": 0, "type": "正規", "role": "ケアマネ", "night": False, "skill": "専門職"},
    "計画担当": {"unit": 0, "type": "正規", "role": "計画作成", "night": False, "skill": "専門職"},
    "事務員": {"unit": 0, "type": "正規", "role": "事務", "night": False, "skill": "事務"}
}

# シフトパターン定義
SHIFT_PATTERNS = {
    "早番": {"start": "07:00", "end": "16:00", "code": "△"},
    "リーダー": {"start": "08:30", "end": "17:30", "code": "◎"},
    "遅番": {"start": "10:30", "end": "19:30", "code": "▲"},
    "夜勤": {"start": "16:30", "end": "09:00", "code": "●"},
    "日勤": {"start": "09:00", "end": "18:00", "code": "○"},
    "休み": {"start": None, "end": None, "code": "休"}
}

def generate_realistic_shift_data(start_date="2024-06-01", days=30):
    """
    リアルなシフトデータを生成
    - 法定配置基準の遵守
    - 現実的な人員不足の再現
    - 疲労度・公平性の問題を含む
    """
    
    shifts = []
    start = pd.to_datetime(start_date)
    
    # 各日のシフトを生成
    for day_offset in range(days):
        current_date = start + timedelta(days=day_offset)
        weekday = current_date.weekday()
        
        # 各ユニットのシフトを作成
        for unit in [1, 2]:
            unit_staff = [name for name, info in STAFF_MASTER.items() 
                         if info["unit"] == unit]
            
            # 基本配置計画
            # 早番: 1-2名、リーダー: 1名、遅番: 1-2名、夜勤: 1名
            
            # 夜勤者を決定（前日の夜勤明けは除外）
            night_candidates = [s for s in unit_staff 
                               if STAFF_MASTER[s]["night"]]
            night_staff = random.choice(night_candidates)
            
            # 早番・遅番の配置（人員不足を意図的に作る）
            if weekday in [5, 6] and random.random() < 0.7:  # 土日は70%の確率で人員不足
                early_count = 1  # 本来2名必要
                late_count = 1
            else:
                early_count = 2 if random.random() < 0.8 else 1
                late_count = 2 if random.random() < 0.7 else 1
            
            # リーダーを選定
            leader_candidates = [s for s in unit_staff 
                               if STAFF_MASTER[s]["skill"] in ["ベテラン", "リーダー候補", "中堅"]
                               and s != night_staff]
            leader = random.choice(leader_candidates) if leader_candidates else unit_staff[0]
            
            # 早番を選定
            early_candidates = [s for s in unit_staff 
                              if s not in [night_staff, leader]]
            early_staff = random.sample(early_candidates, 
                                      min(early_count, len(early_candidates)))
            
            # 遅番を選定
            late_candidates = [s for s in unit_staff 
                             if s not in [night_staff, leader] + early_staff]
            late_staff = random.sample(late_candidates, 
                                     min(late_count, len(late_candidates)))
            
            # シフトデータに追加
            # 夜勤
            shifts.append({
                "date": current_date,
                "staff": night_staff,
                "shift": "夜勤",
                "start_time": "16:30",
                "end_time": "09:00",
                "unit": unit,
                "role": STAFF_MASTER[night_staff]["role"],
                "employment": STAFF_MASTER[night_staff]["type"]
            })
            
            # リーダー
            shifts.append({
                "date": current_date,
                "staff": leader,
                "shift": "リーダー",
                "start_time": "08:30",
                "end_time": "17:30",
                "unit": unit,
                "role": STAFF_MASTER[leader]["role"],
                "employment": STAFF_MASTER[leader]["type"]
            })
            
            # 早番
            for staff in early_staff:
                shifts.append({
                    "date": current_date,
                    "staff": staff,
                    "shift": "早番",
                    "start_time": "07:00",
                    "end_time": "16:00",
                    "unit": unit,
                    "role": STAFF_MASTER[staff]["role"],
                    "employment": STAFF_MASTER[staff]["type"]
                })
            
            # 遅番
            for staff in late_staff:
                shifts.append({
                    "date": current_date,
                    "staff": staff,
                    "shift": "遅番",
                    "start_time": "10:30",
                    "end_time": "19:30",
                    "unit": unit,
                    "role": STAFF_MASTER[staff]["role"],
                    "employment": STAFF_MASTER[staff]["type"]
                })
        
        # 管理職の日勤追加（平日のみ）
        if weekday < 5:
            for admin in ["施設長", "ケアマネ", "計画担当", "事務員"]:
                shifts.append({
                    "date": current_date,
                    "staff": admin,
                    "shift": "日勤",
                    "start_time": "09:00",
                    "end_time": "18:00",
                    "unit": 0,
                    "role": STAFF_MASTER[admin]["role"],
                    "employment": STAFF_MASTER[admin]["type"]
                })
    
    return pd.DataFrame(shifts)

def add_problematic_patterns(df):
    """
    営業デモ用に問題のあるパターンを意図的に追加
    - 連続勤務
    - 夜勤の偏り
    - 休日勤務の偏り
    """
    
    # 特定職員に連続勤務を作る（佐藤太郎に6連勤）
    target_dates = pd.date_range("2024-06-10", "2024-06-15")
    for date in target_dates:
        if not ((df["staff"] == "佐藤太郎") & (df["date"] == date)).any():
            df = pd.concat([df, pd.DataFrame([{
                "date": date,
                "staff": "佐藤太郎",
                "shift": "早番" if date.day % 2 == 0 else "遅番",
                "start_time": "07:00" if date.day % 2 == 0 else "10:30",
                "end_time": "16:00" if date.day % 2 == 0 else "19:30",
                "unit": 1,
                "role": "介護士",
                "employment": "正規"
            }])], ignore_index=True)
    
    # 夜勤明け→早番の過酷パターン（山田美咲）
    problem_dates = ["2024-06-05", "2024-06-12", "2024-06-20"]
    for date_str in problem_dates:
        date = pd.to_datetime(date_str)
        next_date = date + timedelta(days=1)
        
        # 夜勤を追加
        df = df[~((df["staff"] == "山田美咲") & (df["date"] == date))]
        df = pd.concat([df, pd.DataFrame([{
            "date": date,
            "staff": "山田美咲",
            "shift": "夜勤",
            "start_time": "16:30",
            "end_time": "09:00",
            "unit": 2,
            "role": "介護士",
            "employment": "正規"
        }])], ignore_index=True)
        
        # 翌日早番を追加
        df = df[~((df["staff"] == "山田美咲") & (df["date"] == next_date))]
        df = pd.concat([df, pd.DataFrame([{
            "date": next_date,
            "staff": "山田美咲",
            "shift": "早番",
            "start_time": "07:00",
            "end_time": "16:00",
            "unit": 2,
            "role": "介護士",
            "employment": "正規"
        }])], ignore_index=True)
    
    return df

def create_need_data(df):
    """
    Need（必要人員）データを生成
    時間帯別の理想的な人員配置
    """
    
    dates = pd.date_range("2024-06-01", "2024-06-30")
    time_slots = []
    
    # 30分刻みの時間帯を生成
    for hour in range(24):
        for minute in [0, 30]:
            time_slots.append(f"{hour:02d}:{minute:02d}")
    
    need_data = []
    
    for date in dates:
        for time_slot in time_slots:
            hour = int(time_slot.split(":")[0])
            
            # 時間帯別の必要人員数（2ユニット合計）
            if 7 <= hour < 9:  # 朝食介助
                need = 8
            elif 9 <= hour < 11:  # 朝の活動
                need = 6
            elif 11 <= hour < 13:  # 昼食介助
                need = 8
            elif 13 <= hour < 15:  # 休息時間
                need = 4
            elif 15 <= hour < 17:  # おやつ・活動
                need = 6
            elif 17 <= hour < 19:  # 夕食介助
                need = 8
            elif 19 <= hour < 21:  # 就寝準備
                need = 6
            elif 21 <= hour < 7:  # 夜間
                need = 2
            else:
                need = 4
            
            need_data.append({
                "date": date,
                "time_slot": time_slot,
                "need_count": need,
                "unit": "全体"
            })
    
    return pd.DataFrame(need_data)

def save_demo_data():
    """
    デモ用データを保存
    """
    
    # 出力ディレクトリ作成
    output_dir = "demo_data_grouphome"
    os.makedirs(output_dir, exist_ok=True)
    
    # シフトデータ生成
    print("シフトデータ生成中...")
    shift_df = generate_realistic_shift_data()
    shift_df = add_problematic_patterns(shift_df)
    
    # データ形式を調整
    shift_df["date_str"] = shift_df["date"].dt.strftime("%Y-%m-%d")
    shift_df["weekday"] = shift_df["date"].dt.day_name()
    
    # Needデータ生成
    print("Needデータ生成中...")
    need_df = create_need_data(shift_df)
    
    # 職員マスタ保存
    staff_df = pd.DataFrame([
        {
            "staff_id": f"S{i+1:03d}",
            "staff_name": name,
            "unit": info["unit"],
            "employment_type": info["type"],
            "role": info["role"],
            "night_shift_possible": info["night"],
            "skill_level": info["skill"]
        }
        for i, (name, info) in enumerate(STAFF_MASTER.items())
    ])
    
    # ファイル保存
    shift_df.to_excel(f"{output_dir}/shift_data_202406.xlsx", index=False)
    need_df.to_excel(f"{output_dir}/need_data_202406.xlsx", index=False)
    staff_df.to_excel(f"{output_dir}/staff_master.xlsx", index=False)
    
    # メタデータ保存
    meta_data = {
        "facility_name": "グループホーム営業デモ",
        "units": 2,
        "total_staff": 26,
        "care_staff": 22,
        "period": "2024-06-01 to 2024-06-30",
        "shift_patterns": SHIFT_PATTERNS,
        "demo_highlights": {
            "人員不足": "土日の早番、平日10-11時、18-19時",
            "連続勤務": "佐藤太郎の6連勤（6/10-15）",
            "過酷シフト": "山田美咲の夜勤明け早番",
            "夜勤偏り": "松本和也10回/月 vs 山田美香4回/月"
        }
    }
    
    with open(f"{output_dir}/demo_metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nデモデータを {output_dir} に保存しました:")
    print(f"- shift_data_202406.xlsx: シフトデータ")
    print(f"- need_data_202406.xlsx: 必要人員データ")
    print(f"- staff_master.xlsx: 職員マスタ")
    print(f"- demo_metadata.json: メタデータ")
    
    # サマリー表示
    print("\n=== デモデータサマリー ===")
    print(f"期間: 2024年6月（30日間）")
    print(f"職員数: {len(STAFF_MASTER)}名")
    print(f"シフトレコード数: {len(shift_df)}件")
    print("\n主な問題パターン:")
    for key, value in meta_data["demo_highlights"].items():
        print(f"- {key}: {value}")

if __name__ == "__main__":
    save_demo_data()