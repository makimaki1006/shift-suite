from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from .utils import log, safe_read_excel


def _read_excel(fp: Path, sheet: str) -> pd.DataFrame:
    """Return ``pd.DataFrame`` from *fp* ``sheet`` or an empty frame on error."""
    try:
        return safe_read_excel(fp, sheet_name=sheet)
    except FileNotFoundError:
        log.warning("Excel file not found: %s", fp)
    except Exception as e:  # noqa: BLE001
        log.warning("Failed reading %s [%s]: %s", fp, sheet, e)
    return pd.DataFrame()


def generate_summary_report(out_dir: Path | str) -> Path:
    """Generate Markdown shortage summary report under *out_dir*.

    Parameters
    ----------
    out_dir : Path | str
        Directory containing analysis Excel outputs.

    Returns
    -------
    Path
        Path to the created Markdown report.
    """
    out_dir_path = Path(out_dir)
    out_dir_path.mkdir(parents=True, exist_ok=True)

    role_fp = out_dir_path / "shortage_role.xlsx"
    stats_fp = out_dir_path / "stats.xlsx"
    weekday_fp = out_dir_path / "shortage_weekday_timeslot_summary.xlsx"
    heat_fp = out_dir_path / "heat_ALL.xlsx"

    role_df = _read_excel(role_fp, "role_summary")

    if stats_fp.exists():
        try:
            xls = pd.ExcelFile(stats_fp)
            _ = (
                xls.parse("Overall_Summary")
                if "Overall_Summary" in xls.sheet_names
                else pd.DataFrame()
            )
            monthly_df = (
                xls.parse("Monthly_Summary")
                if "Monthly_Summary" in xls.sheet_names
                else pd.DataFrame()
            )
            alerts_df = (
                xls.parse("alerts") if "alerts" in xls.sheet_names else pd.DataFrame()
            )
        except Exception:
            monthly_df = alerts_df = pd.DataFrame()
    else:
        monthly_df = alerts_df = pd.DataFrame()

    weekday_df = pd.DataFrame()
    if weekday_fp.exists():
        try:
            weekday_df = pd.read_excel(weekday_fp)
        except Exception:
            weekday_df = pd.DataFrame()

    min_date = max_date = ""
    if heat_fp.exists():
        try:
            heat_df = pd.read_excel(heat_fp, index_col=0)
            date_cols = pd.to_datetime(heat_df.columns, errors="coerce").dropna()
            if not date_cols.empty:
                min_date = date_cols.min().date().isoformat()
                max_date = date_cols.max().date().isoformat()
        except Exception as e:
            log.warning("Failed to load heat map '%s': %s", heat_fp, e)

    lack_h_total = float(role_df.get("lack_h", pd.Series()).sum())
    excess_h_total = float(role_df.get("excess_h", pd.Series()).sum())
    lack_cost_total = float(
        role_df.get("estimated_lack_cost_if_temporary_staff", pd.Series()).sum()
    )
    penalty_cost_total = float(
        role_df.get("estimated_lack_penalty_cost", pd.Series()).sum()
    )
    excess_cost_total = float(role_df.get("estimated_excess_cost", pd.Series()).sum())

    top_lack_roles = []
    if {"role", "lack_h"}.issubset(role_df.columns):
        top_lack_roles = role_df.nlargest(3, "lack_h")[["role", "lack_h"]]

    top_excess_roles = []
    if {"role", "excess_h"}.issubset(role_df.columns):
        top_excess_roles = role_df.nlargest(3, "excess_h")[["role", "excess_h"]]

    trend_txt = ""
    if not monthly_df.empty and {"month", "summary_item"}.issubset(monthly_df.columns):
        hour_col = next((c for c in monthly_df.columns if "(hours)" in c), None)
        if hour_col:
            df_lack = monthly_df[monthly_df["summary_item"] == "lack"].copy()
            if not df_lack.empty:
                df_lack["month_dt"] = pd.to_datetime(df_lack["month"], errors="coerce")
                df_lack = df_lack.dropna(subset=["month_dt"]).sort_values("month_dt")
                if len(df_lack) >= 2:
                    first = float(df_lack.iloc[0][hour_col])
                    last = float(df_lack.iloc[-1][hour_col])
                    if first:
                        pct = (last - first) / first * 100
                        trend_txt = f"過去{len(df_lack)}ヶ月で不足時間は{pct:+.1f}%変化しています"

    timeslot_lines = []
    if not weekday_df.empty:
        num_col = next(
            (
                c
                for c in weekday_df.columns
                if pd.api.types.is_numeric_dtype(weekday_df[c])
            ),
            None,
        )
        if num_col and {"weekday", "timeslot"}.issubset(weekday_df.columns):
            top_ts = weekday_df.nlargest(3, num_col)
            for _, row in top_ts.iterrows():
                timeslot_lines.append(
                    f"{row['weekday']}{row['timeslot']} 平均{row[num_col]:.1f}人不足"
                )

    alert_lines = []
    if not alerts_df.empty:
        col = alerts_df.columns[0]
        alert_lines = [f"- {v}" for v in alerts_df[col].astype(str).head(5)]

    today = datetime.now().strftime("%Y年%m月%d日")
    title = f"### 過不足分析サマリーレポート ({today}作成)"

    md_lines = [title]
    if min_date and max_date:
        md_lines.append(f"**分析期間**: {min_date} ～ {max_date}")
    md_lines.append("\n#### 総括")
    md_lines.append(
        f"- 総不足時間: {lack_h_total:.1f}h (派遣補填想定 {lack_cost_total:,.0f}円, ペナルティ {penalty_cost_total:,.0f}円)"
    )
    md_lines.append(
        f"- 総過剰時間: {excess_h_total:.1f}h (コスト {excess_cost_total:,.0f}円)"
    )

    if len(top_lack_roles) > 0:
        md_lines.append("- 最も不足の多い職種トップ3:")
        for _, r in top_lack_roles.iterrows():
            md_lines.append(f"  - {r['role']}: {r['lack_h']:.1f}h")
    if len(top_excess_roles) > 0:
        md_lines.append("- 最も過剰の多い職種トップ3:")
        for _, r in top_excess_roles.iterrows():
            md_lines.append(f"  - {r['role']}: {r['excess_h']:.1f}h")

    if trend_txt or timeslot_lines:
        md_lines.append("\n#### 傾向分析")
        if trend_txt:
            md_lines.append(f"- {trend_txt}")
        if timeslot_lines:
            md_lines.append("- 不足が集中している曜日・時間帯トップ3:")
            md_lines.extend([f"  - {t}" for t in timeslot_lines])

    if alert_lines:
        md_lines.append("\n#### 主要アラート")
        md_lines.extend(alert_lines)

    md_lines.append("\n#### 推奨アクションのヒント")
    if not top_lack_roles.empty:
        md_lines.append(
            "- 特定職種の不足が顕著です。採用強化や配置見直しをご検討ください。"
        )
    if timeslot_lines:
        md_lines.append(
            "- 特定の曜日・時間帯で不足が多発しています。シフト調整をご検討ください。"
        )

    markdown_text = "\n".join(md_lines) + "\n"

    out_fp = (
        out_dir_path
        / f"OverShortage_SummaryReport_{datetime.now().strftime('%Y%m%d')}.md"
    )
    out_fp.write_text(markdown_text, encoding="utf-8")
    return out_fp
