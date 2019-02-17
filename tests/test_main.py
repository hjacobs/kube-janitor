import os.path

from unittest.mock import MagicMock

from kube_janitor.main import main


def test_main(tmpdir, monkeypatch):
    p = tmpdir.join("rules.yaml")
    p.write("rules: []")

    kubeconfig = tmpdir.join('kubeconfig')
    kubeconfig.write('''
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
    ''')

    monkeypatch.setattr(os.path, 'expanduser', lambda x: str(kubeconfig))

    mock_clean_up = MagicMock()
    monkeypatch.setattr('kube_janitor.main.clean_up', mock_clean_up)

    main(['--dry-run', '--once', f'--rules-file={p}'])

    mock_clean_up.assert_called_once()
