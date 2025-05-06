"""shift_suite.skill_nmf – 潜在スキル推定 (NMF)  v0.2"""
from __future__ import annotations
import pandas as pd
from pathlib import Path
from sklearn.decomposition import NMF
from .utils import save_df_xlsx, log


def build_skill_matrix(long_df: pd.DataFrame, out_dir: Path):
    mat = (
        long_df.groupby(["name", "code"]).size().unstack(fill_value=0)
    )
    model = NMF(
        n_components=1, random_state=0, init="nndsvd", max_iter=500   # ← 500
    )
    W = model.fit_transform(mat.values)
    skill = pd.Series(W[:, 0], index=mat.index, name="skill_score")
    skill = (skill / skill.max() * 5).round(2)
    save_df_xlsx(skill.to_frame(), out_dir / "skill_matrix.xlsx", sheet="skill")
    log.info("skill_nmf: matrix written")
    return skill
