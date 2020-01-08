import datetime

import pytest

from kube_janitor.helper import parse_expiry


def test_parse_expiry_validate_input_string():
    with pytest.raises(ValueError):
        parse_expiry("99-06-02T12:12:59")
    with pytest.raises(ValueError):
        parse_expiry("2010-12-12 09:26:11")


def test_parse_expiry_output_type():
    assert type(parse_expiry("2019-02-25T09:26:14Z")).__name__ == "datetime"


def test_parse_expiry_output_value_is_correct():
    assert parse_expiry("2008-09-26T01:51:42Z") == datetime.datetime(
        2008, 9, 26, 1, 51, 42
    )
    assert parse_expiry("2008-09-26T01:51") == datetime.datetime(2008, 9, 26, 1, 51, 0)
    assert parse_expiry("2008-09-26") == datetime.datetime(2008, 9, 26, 0, 0, 0)
