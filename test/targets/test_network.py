from wafp.targets.network import is_available


def test_is_available():
    assert not is_available("http://127.0.0.1:1")
