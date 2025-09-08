from __future__ import annotations
from pathlib import Path
import pandas as pd
import logging
from ..logger_config import configure_logging

configure_logging()
log = logging.getLogger(__name__)


def _get_shift_pattern_hours(
    excel_path: Path | None = None, 
    master_sheet_name: str = "勤務区分",
    out_dir: Path | None = None
) -> dict[str, set[str]]:
    """勤務区分シートから、各勤務コードの時間帯セットを読み込む
    
    優先順位:
    1. Excelファイルの勤務区分シート
    2. 実際のシフトデータからの動的抽出
    3. デフォルトパターン
    """
    
    # 1. Excelファイルが指定されていて、存在する場合は読み込みを試みる
    if excel_path and excel_path.exists():
        try:
            from .io_excel import load_shift_patterns
            from .constants import DEFAULT_SLOT_MINUTES

            _, code2slots = load_shift_patterns(
                excel_path, sheet_name=master_sheet_name, slot_minutes=DEFAULT_SLOT_MINUTES
            )
            log.info(f"勤務区分シート '{master_sheet_name}' からパターンを読み込みました")
            return {code: set(slots) for code, slots in code2slots.items()}
        except Exception as e:  # noqa: BLE001
            log.warning(f"勤務区分シート '{master_sheet_name}' の読み込みに失敗しました: {e}")
            log.info("実際のシフトデータからパターン抽出を試みます")
    
    # 2. 実際のシフトデータから動的抽出を試みる
    if out_dir and out_dir.exists():
        try:
            dynamic_patterns = _extract_patterns_from_data(out_dir)
            if dynamic_patterns:
                log.info(f"実際のシフトデータから {len(dynamic_patterns)} 種類のパターンを抽出しました")
                return dynamic_patterns
        except Exception as e:  # noqa: BLE001
            log.warning(f"シフトデータからのパターン抽出に失敗しました: {e}")
    
    # 3. デフォルトパターンを使用
    log.info("デフォルトのシフトパターンを使用します")
    
    DEFAULT_SHIFT_PATTERNS = {
        '日勤': {
            '09:00-09:30', '09:30-10:00', '10:00-10:30', '10:30-11:00',
            '11:00-11:30', '11:30-12:00', '12:00-12:30', '12:30-13:00',
            '13:00-13:30', '13:30-14:00', '14:00-14:30', '14:30-15:00',
            '15:00-15:30', '15:30-16:00', '16:00-16:30', '16:30-17:00',
            '17:00-17:30', '17:30-18:00'
        },
        '早番': {
            '07:00-07:30', '07:30-08:00', '08:00-08:30', '08:30-09:00',
            '09:00-09:30', '09:30-10:00', '10:00-10:30', '10:30-11:00',
            '11:00-11:30', '11:30-12:00', '12:00-12:30', '12:30-13:00',
            '13:00-13:30', '13:30-14:00', '14:00-14:30', '14:30-15:00'
        },
        '遅番': {
            '11:00-11:30', '11:30-12:00', '12:00-12:30', '12:30-13:00',
            '13:00-13:30', '13:30-14:00', '14:00-14:30', '14:30-15:00',
            '15:00-15:30', '15:30-16:00', '16:00-16:30', '16:30-17:00',
            '17:00-17:30', '17:30-18:00', '18:00-18:30', '18:30-19:00',
            '19:00-19:30', '19:30-20:00'
        },
        '夜勤': {
            '18:00-18:30', '18:30-19:00', '19:00-19:30', '19:30-20:00',
            '20:00-20:30', '20:30-21:00', '21:00-21:30', '21:30-22:00',
            '22:00-22:30', '22:30-23:00', '23:00-23:30', '23:30-00:00',
            '00:00-00:30', '00:30-01:00', '01:00-01:30', '01:30-02:00',
            '02:00-02:30', '02:30-03:00', '03:00-03:30', '03:30-04:00',
            '04:00-04:30', '04:30-05:00', '05:00-05:30', '05:30-06:00',
            '06:00-06:30', '06:30-07:00', '07:00-07:30', '07:30-08:00',
            '08:00-08:30', '08:30-09:00'
        }
    }
    
    return DEFAULT_SHIFT_PATTERNS


def _extract_patterns_from_data(out_dir: Path) -> dict[str, set[str]] | None:
    """実際のシフトデータから勤務パターンを動的に抽出する
    
    intermediate_data.parquetから実際に使われている勤務パターンを分析し、
    時間帯の組み合わせから勤務区分を推定する
    """
    try:
        # intermediate_data.parquetから実際のシフトデータを読み込み
        intermediate_path = out_dir / "intermediate_data.parquet"
        if not intermediate_path.exists():
            return None
        
        df = pd.read_parquet(intermediate_path)
        
        # 必須カラムの確認
        required_columns = ['task', 'start_time', 'end_time']
        if not all(col in df.columns for col in required_columns):
            log.debug("動的パターン抽出に必要なカラムが不足しています")
            return None
        
        # task(勤務区分)ごとに時間帯を集計
        patterns = {}
        
        for task in df['task'].unique():
            if pd.isna(task) or str(task).strip() == '':
                continue
                
            task_data = df[df['task'] == task]
            
            # 時間帯のセットを構築
            time_slots = set()
            for _, row in task_data.iterrows():
                start_time = str(row['start_time']).strip()
                end_time = str(row['end_time']).strip()
                
                # "HH:MM-HH:MM"形式の時間帯を生成
                if start_time and end_time:
                    time_slot = f"{start_time}-{end_time}"
                    time_slots.add(time_slot)
            
            # 最低2つの時間帯があるパターンのみ採用（実用的な閾値）
            if len(time_slots) >= 2:
                patterns[str(task)] = time_slots
                log.debug(f"パターン抽出: {task} → {len(time_slots)}時間帯")
        
        return patterns if patterns else None
        
    except Exception as e:  # noqa: BLE001
        log.debug(f"データからのパターン抽出でエラー: {e}")
        return None


def create_optimal_hire_plan(
    out_dir: Path,
    original_excel_path: Path | None = None,
    top_n_shortages: int = 5,
) -> Path | None:
    """不足分析の結果と勤務区分マスターを突き合わせ、最適な採用計画を生成する。"""
    log.info("最適採用計画の生成を開始します。")
    shortage_summary_fp = out_dir / "shortage_weekday_timeslot_summary.parquet"
    shortage_role_fp = out_dir / "shortage_role_summary.parquet"

    if not shortage_summary_fp.exists() or not shortage_role_fp.exists():
        log.warning(
            "不足分析のサマリーファイルが見つからないため、最適採用計画を生成できません。"
        )
        return None

    role_shortage = pd.read_parquet(shortage_role_fp)
    if (
        role_shortage.empty
        or "role" not in role_shortage.columns
        or "lack_h" not in role_shortage.columns
    ):
        log.warning("職種別の不足データが不正です。")
        return None
    most_lacking_role = role_shortage.loc[role_shortage["lack_h"].idxmax()]["role"]

    df = pd.read_parquet(shortage_summary_fp)
    top_shortages = df.nlargest(top_n_shortages, "avg_count")

    shift_patterns = _get_shift_pattern_hours(original_excel_path, out_dir=out_dir)
    if not shift_patterns:
        log.warning("勤務区分の定義が読み込めませんでした。")
        return None

    recommendations = []
    for _, row in top_shortages.iterrows():
        shortage_slot = row["timeslot"]
        best_pattern_name = None
        for pattern_name, pattern_slots in shift_patterns.items():
            if shortage_slot in pattern_slots:
                best_pattern_name = pattern_name
                break
        if best_pattern_name:
            recommendations.append(
                {
                    "推奨職種": most_lacking_role,
                    "推奨勤務区分": best_pattern_name,
                    "主な不足曜日": row["weekday"],
                    "主な不足時間帯": shortage_slot,
                    "平均不足人数": round(row["avg_count"], 1),
                    "推奨採用人数": int(-(-row["avg_count"] // 1)),
                }
            )

    if not recommendations:
        log.info("具体的な採用推奨事項は見つかりませんでした。")
        return None

    result_df = pd.DataFrame(recommendations).drop_duplicates().reset_index(drop=True)
    out_fp = out_dir / "optimal_hire_plan.parquet"
    result_df.to_parquet(out_fp, index=False)
    log.info(f"最適採用計画を {out_fp} に保存しました。")

    return out_fp
