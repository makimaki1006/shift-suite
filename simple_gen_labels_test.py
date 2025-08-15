#!/usr/bin/env python3
"""
gen_labels関数の単純テスト（依存関係なし）
"""

from datetime import datetime, timedelta

def gen_labels(slot: int, extended_hours: bool = True) -> list[str]:
    """時間ラベルを生成
    
    Parameters
    ----------
    slot : int
        時間間隔（分）
    extended_hours : bool, default True
        明け番シフト対応のため、翌日早朝まで含む時間ラベルを生成するか
        Falseの場合は従来の24時間（00:00-23:59）のみ
    
    Returns
    -------
    list[str]
        時間ラベルのリスト（重複なし、時系列順）
    """
    labels: list[str] = []
    
    if extended_hours:
        # 明け番シフト対応：00:00-23:59 + 翌日の00:00-11:59
        # 1日目の全時間帯
        t = datetime(2000, 1, 1)
        while t.day == 1:  # 1日目の24時間
            labels.append(t.strftime("%H:%M"))
            t += timedelta(minutes=slot)
        
        # 2日目の朝（00:00-11:59）を追加
        t = datetime(2000, 1, 2)  # 翌日の00:00から
        end_time = datetime(2000, 1, 2, 12, 0)  # 翌日の12:00まで
        while t < end_time:
            # 翌日分であることを示すため "+" プレフィックスを付ける
            labels.append("+" + t.strftime("%H:%M"))
            t += timedelta(minutes=slot)
    else:
        # 従来の24時間（00:00-23:59）
        t = datetime(2000, 1, 1)
        while t.day == 1:  # 24h
            labels.append(t.strftime("%H:%M"))
            t += timedelta(minutes=slot)
    
    return labels

def test_gen_labels():
    """gen_labels関数のテスト"""
    print("=== gen_labels関数テスト ===")
    
    # 標準24時間
    standard_labels = gen_labels(30, extended_hours=False)
    print(f"標準24時間ラベル数: {len(standard_labels)}")
    print(f"最初の5個: {standard_labels[:5]}")
    print(f"最後の5個: {standard_labels[-5:]}")
    
    # 拡張32時間（明け番対応）
    extended_labels = gen_labels(30, extended_hours=True)
    print(f"\n拡張32時間ラベル数: {len(extended_labels)}")
    print(f"最初の5個: {extended_labels[:5]}")
    print(f"最後の5個: {extended_labels[-5:]}")
    
    # 1日目の0:00台の確認
    midnight_labels = [label for label in extended_labels if label.startswith("0") and not label.startswith("+")]
    print(f"\n1日目 0:xx時間帯ラベル数: {len(midnight_labels)}")
    print(f"1日目 0:xx時間帯: {midnight_labels}")
    
    # 2日目の早朝（+プレフィックス）の確認
    next_day_labels = [label for label in extended_labels if label.startswith("+")]
    print(f"\n2日目早朝（明け番継続）ラベル数: {len(next_day_labels)}")
    print(f"2日目早朝: {next_day_labels[:10]}...")  # 最初の10個のみ表示
    
    # 23:xx台の確認（24時間境界）
    twentythree_labels = [label for label in extended_labels if label.startswith("23")]
    print(f"\n23:xx時間帯ラベル数: {len(twentythree_labels)}")
    print(f"23:xx時間帯: {twentythree_labels}")
    
    print(f"\n修正前vs修正後の差分:")
    print(f"標準：{len(standard_labels)}個 vs 拡張：{len(extended_labels)}個")
    print(f"追加された時間帯数: {len(extended_labels) - len(standard_labels)}")

if __name__ == "__main__":
    test_gen_labels()
    print("\n=== テスト完了 ===")