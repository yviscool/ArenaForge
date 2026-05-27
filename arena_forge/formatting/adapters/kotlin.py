from __future__ import annotations

from arena_forge.formatting.adapters.jvm import JvmJarFormatterAdapter


class KtfmtAdapter(JvmJarFormatterAdapter):
    id = "ktfmt"
    display_name = "ktfmt"
    selectors = ("source.kotlin",)
    supports_range = False
    binary_names = ("ktfmt", "ktfmt.exe")
    project_jar_relpaths = ("tools/ktfmt.jar",)
    docs_url = "https://github.com/facebook/ktfmt"
    default_extension = ".kt"
