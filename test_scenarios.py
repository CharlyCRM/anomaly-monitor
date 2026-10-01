import numpy as np
import pandas as pd
import pytest
from scenarios import perturb_window


class Identity:
    def transform(self, data):
        return data.to_numpy()


class Detector:
    def score_samples(self, data):
        return -data[:, 0]


def inputs():
    data = pd.DataFrame({"timestamp": pd.date_range("2024-01-01", periods=40, freq="h"),
                         "value": np.ones(40) * 10})
    saved = {"model": Detector(), "scaler": Identity(), "threshold": 15, "center": 10, "spread": 2}
    return data, saved


@pytest.mark.parametrize("kind,count", [("spike", 1), ("shift", 20)])
def test_changes_use_frozen_detectors_and_preserve_context(kind, count):
    data, saved = inputs()
    untouched = data.copy(deep=True)
    result = perturb_window(data, saved, kind, 10, 20, 3)
    pd.testing.assert_frame_equal(data, untouched)
    assert len(result) == 29
    assert result.scenario_alert.sum() == count
    assert result.baseline_scenario_alert.sum() == count
    assert result.original_alert.sum() == 0
    assert saved["threshold"] == 15
    assert result.iloc[:9].scenario_score.equals(result.iloc[:9].original_score)


@pytest.mark.parametrize("kind,amplitude,position", [("unknown", 1, 20), ("spike", float("nan"), 20),
                                                  ("shift", 51, 20), ("spike", 1, 10)])
def test_invalid_scenarios_are_rejected(kind, amplitude, position):
    data, saved = inputs()
    with pytest.raises(ValueError):
        perturb_window(data, saved, kind, amplitude, position, 3)


def test_zero_amplitude_reproduces_original():
    data, saved = inputs()
    result = perturb_window(data, saved, "spike", 0, 20, 3)
    assert result.scenario_score.equals(result.original_score)
    assert result.scenario_alert.equals(result.original_alert)


def test_missing_artifacts_render_instructions_without_training(monkeypatch, tmp_path):
    from streamlit.testing.v1 import AppTest
    import monitor
    monkeypatch.setattr(monitor, "ROOT", tmp_path)
    app = AppTest.from_file("app.py").run(timeout=20)
    assert not app.exception
    assert "artefactos" in app.warning[0].value


def test_language_preserves_detector_and_scenario():
    from streamlit.testing.v1 import AppTest
    from monitor import ROOT
    if not (ROOT / "artifacts/model.joblib").exists():
        pytest.skip("Local prepared demo artifacts are required.")
    app = AppTest.from_file("app.py").run(timeout=30)
    assert not app.exception
    app.radio(key="detector").set_value("statistical_baseline").run(timeout=30)
    app.radio(key="kind").set_value("shift").run(timeout=30)
    app.slider(key="amplitude").set_value(20.0).run(timeout=30)
    app.radio(key="language").set_value("en").run(timeout=30)
    assert not app.exception
    assert app.radio(key="detector").value == "statistical_baseline"
    assert app.radio(key="kind").value == "shift"
    assert app.slider(key="amplitude").value == 20.0
