"""shift_suite.skill_nmf – 潜在スキル推定 (NMF)  v0.2"""

from __future__ import annotations
import pandas as pd
from pathlib import Path
from sklearn.decomposition import NMF
from .utils import save_df_xlsx, log


def build_skill_matrix(long_df: pd.DataFrame, out_dir: Path):
    if "staff" not in long_df.columns or "code" not in long_df.columns:
        log.error(
            "[skill_nmf] long_dfに 'staff' または 'code' 列が見つかりません。処理をスキップします。"
        )
        empty_skill_df = pd.DataFrame(columns=["skill_score"])
        save_df_xlsx(empty_skill_df, out_dir / "skill_matrix.xlsx", sheet_name="skill")
        log.info(
            "skill_nmf: 'staff'または'code'列がなかったため、空のskill_matrix.xlsxを作成しました。"
        )
        return empty_skill_df  # または None

    # スタッフ識別列を "name" から "staff" に変更
    mat = long_df.groupby(["staff", "code"]).size().unstack(fill_value=0)

    if mat.empty or mat.shape[0] == 0 or mat.shape[1] == 0:
        log.warning(
            "[skill_nmf] NMFの入力となる行列が空または次元が0です。スキルスコアは計算されません。"
        )
        empty_skill_df = pd.DataFrame(columns=["skill_score"])
        save_df_xlsx(empty_skill_df, out_dir / "skill_matrix.xlsx", sheet_name="skill")
        return empty_skill_df

    # n_components はサンプル数または特徴量の数の小さい方以下である必要がある
    n_components = min(1, mat.shape[0], mat.shape[1])
    if n_components < 1:  # NMFが実行できない場合
        log.warning(
            f"[skill_nmf] NMFのn_componentsが1未満 ({n_components}) のため実行できません。スキルスコアは計算されません。"
        )
        skill = pd.Series(index=mat.index, name="skill_score", dtype=float).fillna(
            0.0
        )  # 全て0など
    else:
        try:
            model = NMF(
                n_components=n_components, random_state=0, init="nndsvd", max_iter=500
            )
            W = model.fit_transform(mat.values)
            skill_scores = (
                W[:, 0] if W.shape[1] > 0 else pd.Series(0.0, index=mat.index)
            )  # Wが空でないかチェック
            skill = pd.Series(skill_scores, index=mat.index, name="skill_score")
            # スキルスコアの最大値が0の場合のZeroDivisionErrorを避ける
            max_skill = skill.max()
            if max_skill > 0:
                skill = (skill / max_skill * 5).round(2)
            else:
                skill = skill.round(2)  # 全て0のまま
        except Exception as e:
            log.error(
                f"[skill_nmf] NMFの計算中にエラーが発生しました: {e}。スキルスコアは0として記録します。"
            )
            skill = pd.Series(0.0, index=mat.index, name="skill_score")

    save_df_xlsx(skill.to_frame(), out_dir / "skill_matrix.xlsx", sheet_name="skill")
    log.info(f"skill_nmf: matrix written to {out_dir / 'skill_matrix.xlsx'}")
    return skill.to_frame()  # DataFrameを返す方が一貫性があるかも
