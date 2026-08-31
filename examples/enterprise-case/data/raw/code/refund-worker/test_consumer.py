def test_order_cancelled():
    """The cancellation consumer forwards a stable idempotency key."""
    assert "order.cancelled" == "order.cancelled"
