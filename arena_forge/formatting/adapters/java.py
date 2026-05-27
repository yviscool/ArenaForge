from __future__ import annotations

from arena_forge.formatting.adapters.jvm import JvmJarFormatterAdapter


class GoogleJavaFormatAdapter(JvmJarFormatterAdapter):
    id = "google-java-format"
    display_name = "google-java-format"
    selectors = ("source.java",)
    supports_range = False
    binary_names = ("google-java-format", "google-java-format.exe")
    project_jar_relpaths = ("tools/google-java-format.jar",)
    docs_url = "https://github.com/google/google-java-format"
    default_extension = ".java"
