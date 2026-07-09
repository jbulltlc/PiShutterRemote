import json
from pathlib import Path


DEFAULT_STATE_PATH = Path.home() / ".pishutter" / "state.json"


DEFAULT_BLIND_STATE = {
    "position": 0,
    "open_time_seconds": 20.0,
    "close_time_seconds": 20.0,
    "safety_buffer_seconds": 2.0,
}


class StateStore:
    def __init__(self, path: Path = DEFAULT_STATE_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> dict:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text())

    def save(self) -> None:
        self.path.write_text(json.dumps(self.data, indent=2, sort_keys=True))

    def get_blind_state(self, key: str) -> dict:
        if key not in self.data:
            self.data[key] = dict(DEFAULT_BLIND_STATE)
            self.save()
        return self.data[key]

    def update_blind_state(self, key: str, **values) -> None:
        state = self.get_blind_state(key)
        state.update(values)
        self.save()