"""Read-only synthetic perturbations with frozen models and thresholds."""
import numpy as np
from monitor import FEATURES, features


def perturb_window(readings, saved, kind, amplitude, position, baseline_threshold):
    if kind not in ("spike", "shift"):
        raise ValueError("Unknown perturbation.")
    if not np.isfinite(amplitude) or abs(amplitude) > 50:
        raise ValueError("Amplitude must be finite and in [-50,50].")
    if not np.isfinite(baseline_threshold) or baseline_threshold < 0:
        raise ValueError("Invalid baseline threshold.")
    if len(readings) < 12 or position != int(position) or not 11 <= position < len(readings):
        raise ValueError("Provide 11 preceding observations and a valid change position.")
    if not np.isfinite(readings.value.to_numpy()).all():
        raise ValueError("Readings must be finite.")
    original = readings.copy(deep=True)
    modified = readings.copy(deep=True)
    column = modified.columns.get_loc("value")
    if kind == "spike":
        modified.iloc[position, column] += amplitude
    else:
        modified.iloc[position:, column] += amplitude
    before, after = features(original), features(modified)
    scores_before = -saved["model"].score_samples(saved["scaler"].transform(before[FEATURES]))
    scores_after = -saved["model"].score_samples(saved["scaler"].transform(after[FEATURES]))
    baseline_before = np.abs((before.value.to_numpy() - saved["center"]) / saved["spread"])
    baseline_after = np.abs((after.value.to_numpy() - saved["center"]) / saved["spread"])
    return before[["timestamp", "value"]].assign(
        original_value=before.value.to_numpy(), scenario_value=after.value.to_numpy(),
        original_score=scores_before, scenario_score=scores_after,
        original_alert=scores_before > saved["threshold"], scenario_alert=scores_after > saved["threshold"],
        baseline_original_score=baseline_before, baseline_scenario_score=baseline_after,
        baseline_original_alert=baseline_before > baseline_threshold,
        baseline_scenario_alert=baseline_after > baseline_threshold)
