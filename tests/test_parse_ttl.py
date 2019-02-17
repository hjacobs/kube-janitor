from kube_janitor.helper import parse_ttl


def test_parse_ttl():
    assert parse_ttl('1s') == 1
    assert parse_ttl('08s') == 8
    assert parse_ttl('5m') == 300
    assert parse_ttl('2h') == 3600*2
    assert parse_ttl('7d') == 3600*24*7
