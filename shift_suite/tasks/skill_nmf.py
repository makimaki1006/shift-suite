"""shift_suite.skill_nmf – 潜在スキル推定 (NMF)  v0.2"""
from __future__ import annotations
import pandas as pd
from pathlib import Path
# sklearn import removed - using simple implementation
# from sklearn.decomposition import NMF
from .utils import save_df_xlsx, log
import numpy as np

# Simple NMF implementation to replace sklearn
class SimpleNMF:
    """Simple Non-negative Matrix Factorization implementation"""
    
    def __init__(self, n_components=2, random_state=None, init='random', max_iter=200):
        self.n_components = n_components
        self.random_state = random_state
        self.init = init
        self.max_iter = max_iter
        self.components_ = None
        
    def fit_transform(self, X):
        """Fit NMF model and return transformed data"""
        if self.random_state:
            np.random.seed(self.random_state)
            
        X = np.array(X)
        n_samples, n_features = X.shape
        
        # Initialize W and H matrices
        if self.init == 'nndsvd':
            # Simple SVD-based initialization (simplified)
            W = np.random.uniform(0.1, 1.0, (n_samples, self.n_components))
            H = np.random.uniform(0.1, 1.0, (self.n_components, n_features))
        else:
            W = np.random.uniform(0.1, 1.0, (n_samples, self.n_components))
            H = np.random.uniform(0.1, 1.0, (self.n_components, n_features))
        
        # Multiplicative update rules for NMF
        for iteration in range(self.max_iter):
            # Update H
            numerator_H = np.dot(W.T, X)
            denominator_H = np.dot(np.dot(W.T, W), H) + 1e-10
            H = H * numerator_H / denominator_H
            
            # Update W
            numerator_W = np.dot(X, H.T)
            denominator_W = np.dot(W, np.dot(H, H.T)) + 1e-10
            W = W * numerator_W / denominator_W
            
            # Optional: check for convergence (simplified)
            if iteration % 50 == 0:
                reconstruction_error = np.linalg.norm(X - np.dot(W, H))
                if reconstruction_error < 1e-6:
                    break
        
        self.components_ = H
        return W


def build_skill_matrix(long_df: pd.DataFrame, out_dir: Path):
    mat = (
        long_df.groupby(["name", "code"]).size().unstack(fill_value=0)
    )
    model = SimpleNMF(
        n_components=1, random_state=0, init="nndsvd", max_iter=500   # ← 500
    )
    W = model.fit_transform(mat.values)
    skill = pd.Series(W[:, 0], index=mat.index, name="skill_score")
    skill = (skill / skill.max() * 5).round(2)
    save_df_xlsx(skill.to_frame(), out_dir / "skill_matrix.xlsx", sheet_name="skill")
    log.info("skill_nmf: matrix written")
    return skill
