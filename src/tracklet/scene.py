"""scene — single source of truth for scene parameters (S1).

Contract: build_scene(config_path) -> SceneConfig (frozen dataclass; pure). Reads no truth.
"""
from __future__ import annotations


def build_scene(config_path: str) -> "SceneConfig":  # noqa: F821
    raise NotImplementedError("scene.build_scene lands in Sprint 1")
