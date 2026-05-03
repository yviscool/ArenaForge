import sys
import types
import unittest

from tests.helpers import local_test_workspace


class _FakeView:
    def __init__(self, theme_name: str = "Default.sublime-theme") -> None:
        self._settings = {"theme": theme_name}

    def settings(self):
        return types.SimpleNamespace(get=lambda key, default=None: self._settings.get(key, default))


class RenderAssetsTests(unittest.TestCase):
    def test_render_template_injects_translated_labels(self) -> None:
        sys.modules["sublime"] = types.SimpleNamespace(platform=lambda: "windows")
        from arena_forge.adapters.sublime import render_assets

        original_root = render_assets.ASSET_ROOT
        with local_test_workspace("render-assets-template") as root:
            (root / "test_styles.css").write_text("html{}", encoding="utf-8")
            (root / "test_config.html").write_text(
                "{test_label}|{edit_label}|{run_label}|{time_label}",
                encoding="utf-8",
            )
            render_assets.ASSET_ROOT = root
            render_assets._read_asset.cache_clear()
            render_assets._base_styles.cache_clear()
            text = render_assets.render_template("test_config.html")
            self.assertIn("test", text)
            self.assertIn("edit", text)
        render_assets.ASSET_ROOT = original_root
        render_assets._read_asset.cache_clear()
        render_assets._base_styles.cache_clear()

    def test_build_styles_appends_variant_css(self) -> None:
        sys.modules["sublime"] = types.SimpleNamespace(platform=lambda: "windows")
        from arena_forge.adapters.sublime import render_assets

        original_settings = render_assets.get_settings
        original_root = render_assets.ASSET_ROOT
        with local_test_workspace("render-assets-styles") as root:
            (root / "test_styles.css").write_text("html{color:red;}", encoding="utf-8")
            render_assets.ASSET_ROOT = root
            render_assets.get_settings = lambda: {"ui_variant": "refined", "ui_density": "compact"}
            render_assets._read_asset.cache_clear()
            render_assets._base_styles.cache_clear()
            styles = render_assets.build_styles(_FakeView())
            self.assertIn("--af-gap", styles)
            self.assertIn("color:red", styles)
        render_assets.ASSET_ROOT = original_root
        render_assets.get_settings = original_settings
        render_assets._read_asset.cache_clear()
        render_assets._base_styles.cache_clear()

    def test_terminal_variant_adds_monospace_and_zero_radius(self) -> None:
        sys.modules["sublime"] = types.SimpleNamespace(platform=lambda: "windows")
        from arena_forge.adapters.sublime import render_assets

        original_settings = render_assets.get_settings
        render_assets.get_settings = lambda: {"ui_variant": "terminal", "ui_density": "compact"}
        styles = render_assets.build_styles(_FakeView())
        self.assertIn("--af-font-family: monospace", styles)
        self.assertIn("--af-chip-radius: 0px", styles)
        render_assets.get_settings = original_settings
