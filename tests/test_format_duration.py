from kube_janitor.helper import format_duration


def test_format_duration():
    assert format_duration(-1) == "-1s"
    assert format_duration(0) == "0s"
    assert format_duration(1) == "1s"
    assert format_duration(61) == "1m1s"
    assert format_duration(3600) == "1h"
    assert format_duration(3900) == "1h5m"
    assert format_duration(3600 * 25) == "1d1h"
    assert format_duration(3600 * 24 * 14) == "2w"
