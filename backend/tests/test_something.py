import pytest


@pytest.mark.slow
def test_big():
    assert 1 + 1 == 2
