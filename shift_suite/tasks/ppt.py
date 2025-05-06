"""
ppt.py – PowerPoint 自動レポート (stub)
python‑pptx を用いて heatmap / shortage / risk_pay などを
1 枚にまとめた経営報告資料にする予定。
"""
from __future__ import annotations
import logging
from pathlib import Path

log = logging.getLogger(__name__)

def build_ppt(out_dir: Path):
    log.info("build_ppt: stub – 実装は後続フェーズで追加")
