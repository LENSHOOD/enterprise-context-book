# 退款积压处置手册

当 refund-worker 队列积压超过 500 时，先检查 payment-service 的 provider_error_rate，
再检查 order.cancelled 消费延迟。禁止在未获得值班负责人批准时重放消息。
