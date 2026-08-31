def handle_order_cancelled(event, payment_client):
    """Create a refund after a paid, unfulfilled order is cancelled."""
    if not event["order_id"]:
        raise ValueError("order_id is required")
    return payment_client.create_refund(event["order_id"])
