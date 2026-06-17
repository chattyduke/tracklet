"""render — synthetic scene renderer (S2). The ONLY writer of truth.

Contract: render_scene(scene, catalogue, tle) -> RenderResult. Writes image.fits (NO WCS header)
+ truth.json (SEALED). The sealed-truth Poka-Yoke depends on this being the sole truth writer.
"""
from __future__ import annotations


def render_scene(scene: "SceneConfig", catalogue, tle) -> "RenderResult":  # noqa: F821
    raise NotImplementedError("render.render_scene lands in Sprint 2")
