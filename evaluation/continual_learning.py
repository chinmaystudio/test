"""Offline evaluation utilities for baseline vs. adaptive identity profiles."""
from dataclasses import dataclass
from typing import Iterable, List
import numpy as np


@dataclass
class EvaluationRow:
    phase: str
    threshold: float
    true_accepts: int
    false_accepts: int
    true_rejects: int
    false_rejects: int

    @property
    def far(self) -> float:
        return self.false_accepts / (self.false_accepts + self.true_rejects) if self.false_accepts + self.true_rejects else 0.0

    @property
    def frr(self) -> float:
        return self.false_rejects / (self.false_rejects + self.true_accepts) if self.false_rejects + self.true_accepts else 0.0


def evaluate_scores(genuine_scores: Iterable[float], impostor_scores: Iterable[float], threshold: float, phase: str) -> EvaluationRow:
    genuine = np.asarray(list(genuine_scores), dtype=float)
    impostor = np.asarray(list(impostor_scores), dtype=float)
    ta = int(np.sum(genuine >= threshold))
    fr = int(np.sum(genuine < threshold))
    fa = int(np.sum(impostor >= threshold))
    tr = int(np.sum(impostor < threshold))
    return EvaluationRow(phase, threshold, ta, fa, tr, fr)


def compare_baseline_adaptive(baseline_genuine, adaptive_genuine, impostor, thresholds=(0.45, 0.50, 0.55, 0.60, 0.65)) -> List[EvaluationRow]:
    rows = []
    for threshold in thresholds:
        rows.append(evaluate_scores(baseline_genuine, impostor, threshold, "BASELINE"))
        rows.append(evaluate_scores(adaptive_genuine, impostor, threshold, "ADAPTIVE"))
    return rows
