"""
Save Manager - JSON save/load.
"""

from __future__ import annotations

import json
import os
from typing import Optional

from config import Config
from domain.models.game_state import GameState


class SaveManager:
    def __init__(self, save_dir: str | None = None):
        self.save_dir = save_dir or Config.SAVE_DIR
        os.makedirs(self.save_dir, exist_ok=True)

    def _path(self, filename: str) -> str:
        return os.path.join(self.save_dir, filename)

    # =========================================================
    # SAVE
    # =========================================================

    def save(self, state: GameState, filename: str | None = None) -> str:
        filename = filename or Config.SAVE_FILE
        path = self._path(filename)
        data = state.to_dict()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return path

    # =========================================================
    # LOAD
    # =========================================================

    def load(self, filename: str | None = None) -> Optional[GameState]:
        filename = filename or Config.SAVE_FILE
        path = self._path(filename)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return GameState.from_dict(data)

    # =========================================================
    # UTILITIES
    # =========================================================

    def exists(self, filename: str | None = None) -> bool:
        filename = filename or Config.SAVE_FILE
        return os.path.exists(self._path(filename))

    def delete(self, filename: str | None = None) -> bool:
        filename = filename or Config.SAVE_FILE
        path = self._path(filename)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def list_saves(self) -> list[str]:
        if not os.path.isdir(self.save_dir):
            return []
        return [f for f in os.listdir(self.save_dir) if f.endswith(".json")]
