def test_equity_pnl_long():
    quantity = 100
    entry = 100
    current = 112
    assert quantity * (current - entry) == 1200


def test_equity_pnl_short():
    quantity = -100
    entry = 100
    current = 88
    assert quantity * (current - entry) == 1200
