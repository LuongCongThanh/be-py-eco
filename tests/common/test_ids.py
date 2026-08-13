import uuid

from common.ids import uuid7


def test_uuid7_returns_valid_uuid():
    value = uuid7()
    assert isinstance(value, uuid.UUID)
    assert value.version == 7


def test_uuid7_timestamps_are_non_decreasing():
    # The random suffix isn't ordered, so compare the embedded timestamps
    # (the leading 48 bits) rather than the raw UUID bytes.
    timestamps = [uuid7().int >> 80 for _ in range(1000)]
    assert timestamps == sorted(timestamps)


def test_uuid7_values_are_unique():
    values = [uuid7() for _ in range(1000)]
    assert len(set(values)) == len(values)
