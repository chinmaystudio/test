from types import SimpleNamespace

from core.matching import MatchState, ThresholdPolicy
from core.temporal import TemporalVerifier
from core.tracker import SimpleTracker
from db.attendance import AttendanceStore


def test_unknown_rejection():
    decision = ThresholdPolicy(0.8, 0.6).decide({"student_id": "S1", "name": "A", "similarity": 0.4})
    assert decision.state is MatchState.UNKNOWN
    assert decision.student_id is None


def test_temporal_confirmation_requires_stability():
    verifier = TemporalVerifier(min_observations=3, window_size=5, stability_delta=0.1)
    result = None
    for score in (0.88, 0.90, 0.89):
        result = verifier.observe(17, "S1", "A", score)
    assert result is not None and result.confirmed is True
    assert result.student_id == "S1"


def test_tracker_assigns_stable_id():
    tracker = SimpleTracker(iou_threshold=0.1)
    first = tracker.update([SimpleNamespace(bbox=[0, 0, 100, 100])])
    second = tracker.update([SimpleNamespace(bbox=[5, 5, 105, 105])])
    assert first[0][0] == second[0][0]


def test_attendance_unique_key(tmp_path):
    store = AttendanceStore(str(tmp_path / "attendance.db"))
    assert store.mark_present("CSE-A", "L1", "S1", 0.9) is True
    assert store.mark_present("CSE-A", "L1", "S1", 0.95) is False
    assert len(store.list_for_lecture("CSE-A", "L1")) == 1
    store.close()
