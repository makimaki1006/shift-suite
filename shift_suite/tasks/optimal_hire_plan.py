from __future__ import annotations
from pathlib import Path
import pandas as pd
import logging
from ..logger_config import configure_logging

configure_logging()
log = logging.getLogger(__name__)


def _get_shift_pattern_hours(
    excel_path: Path, master_sheet_name: str = "勤務区分"
) -> dict[str, set[str]]:
    """勤務区分シートから、各勤務コードの時間帯セットを読み込む"""
    try:
        from .io_excel import load_shift_patterns

        _, code2slots = load_shift_patterns(
            excel_path, sheet_name=master_sheet_name, slot_minutes=30
        )
        return {code: set(slots) for code, slots in code2slots.items()}
    except Exception as e:  # noqa: BLE001
        log.error(f"勤務区分シート '{master_sheet_name}' の読み込みに失敗しました: {e}")
        return {}


def create_optimal_hire_plan(
    out_dir: Path,
    original_excel_path: Path,
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

    shift_patterns = _get_shift_pattern_hours(original_excel_path)
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
