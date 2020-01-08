import os.path
from unittest.mock import MagicMock

import pytest

from kube_janitor.main import main


@pytest.fixture
def kubeconfig(tmpdir):
    kubeconfig = tmpdir.join("kubeconfig")
    kubeconfig.write(
        """
apiVersion: v1
clusters:
- cluster: {server: 'https://localhost:9443'}
  name: test
contexts:
- context: {cluster: test, user: test}
  name: test
current-context: test
kind: Config
preferences: {}
users:
- name: test
  user: {token: test}
    """
    )
    return kubeconfig


def test_main_no_rules(kubeconfig, monkeypatch):
    monkeypatch.setattr(os.path, "expanduser", lambda x: str(kubeconfig))

    mock_clean_up = MagicMock()
    monkeypatch.setattr("kube_janitor.main.clean_up", mock_clean_up)

    main(["--dry-run", "--once"])

    mock_clean_up.assert_called_once()


def test_main_with_rules(tmpdir, kubeconfig, monkeypatch):
    p = tmpdir.join("rules.yaml")
    p.write("rules: []")

    monkeypatch.setattr(os.path, "expanduser", lambda x: str(kubeconfig))

    mock_clean_up = MagicMock()
    monkeypatch.setattr("kube_janitor.main.clean_up", mock_clean_up)

    main(["--dry-run", "--once", f"--rules-file={p}"])

    mock_clean_up.assert_called_once()


def test_main_continue_on_failure(kubeconfig, monkeypatch):
    monkeypatch.setattr(os.path, "expanduser", lambda x: str(kubeconfig))

    mock_shutdown = MagicMock()
    mock_handler = MagicMock()
    mock_handler.shutdown_now = False
    mock_shutdown.GracefulShutdown.return_value = mock_handler

    calls = []

    def mock_clean_up(*args, **kwargs):
        calls.append(args)
        if len(calls) == 1:
            raise Exception("clean up fails on first run")
        elif len(calls) == 2:
            mock_handler.shutdown_now = True

    monkeypatch.setattr("kube_janitor.main.clean_up", mock_clean_up)
    monkeypatch.setattr("kube_janitor.main.shutdown", mock_shutdown)

    main(["--dry-run", "--interval=0"])

    assert len(calls) == 2
