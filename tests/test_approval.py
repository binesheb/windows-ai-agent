from agent.core.approval import ApprovalManager


def test_approval_lifecycle() -> None:
    manager = ApprovalManager()
    request = manager.create("process_stop", "Stop a test process", action={"pid": 123})

    assert request.status == "pending"
    assert manager.get(request.request_id) == request
    assert manager.list_pending() == [request]

    decided = manager.decide(request.request_id, "approved", decided_by="tester")

    assert decided is not None
    assert decided.status == "approved"
    assert decided.decided_by == "tester"
    assert decided.decided_at is not None
    assert manager.list_pending() == []


def test_approval_cannot_be_decided_twice() -> None:
    manager = ApprovalManager()
    request = manager.create("process_stop", "Stop a test process")
    manager.decide(request.request_id, "denied")

    try:
        manager.decide(request.request_id, "approved")
    except ValueError as exc:
        assert "already been decided" in str(exc)
    else:
        raise AssertionError("Expected a second decision to be rejected")
