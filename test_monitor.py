import numpy as np
import pandas as pd
from api import app
from fastapi.testclient import TestClient
from monitor import features, point_metrics


def test_features_are_causal():
    source = pd.DataFrame({"value": np.arange(30, dtype=float)})
    changed = source.copy()
    changed.loc[20:, "value"] = 999
    pd.testing.assert_frame_equal(features(source).iloc[:9], features(changed).iloc[:9])


def test_false_positive_count_and_validation():
    report = point_metrics(np.array([0, 0, 1, 1]), np.array([True, False, True, False]))
    assert report["false_positives"] == 1
    assert report["precision"] == 0.5
    assert report["recall"] == 0.5
    assert TestClient(app).post("/score", json={"values": [1, 2]}).status_code == 422
