from core.temporal import TemporalVerifier

tv = TemporalVerifier(min_observations=3)
d1 = tv.observe(track_id=1, student_id=None, name=None, similarity=0.4)
print("d1:", d1)

d2 = tv.observe(track_id=1, student_id="test", name="Test", similarity=0.46)
print("d2:", d2)

d3 = tv.observe(track_id=1, student_id="test", name="Test", similarity=0.48)
print("d3:", d3)

d4 = tv.observe(track_id=1, student_id="test", name="Test", similarity=0.47)
print("d4:", d4)
