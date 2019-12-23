from unittest.mock import MagicMock

from kube_janitor.shutdown import GracefulShutdown


def test_graceful_shutdown(monkeypatch):
    handler = GracefulShutdown()
    assert not handler.safe_to_exit
    with handler.safe_exit():
        assert handler.safe_to_exit

    assert not handler.shutdown_now
    # this would be called by SIGINT or SIGTERM
    handler.exit_gracefully(None, None)
    assert handler.shutdown_now

    mock_exit = MagicMock()
    monkeypatch.setattr("sys.exit", mock_exit)
    with handler.safe_exit():
        handler.exit_gracefully(None, None)

    mock_exit.assert_called_once_with(0)
