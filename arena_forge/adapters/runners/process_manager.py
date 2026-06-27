from __future__ import annotations

import os
import signal
import subprocess
from collections import OrderedDict
from os import path
from typing import Iterable

from arena_forge.adapters.i18n.catalog import translate_catalog as translate
from arena_forge.core.domain import LanguageProfile
from arena_forge.core.services import select_language_profile

from .subprocess_runner import (
    build_command_argv,
    build_process_spawn_options,
    build_process_text_options,
    render_command,
)

_COMPILE_CACHE_MAX_SIZE = 64
_COMPILE_CACHE: OrderedDict = OrderedDict()


def _build_compile_cache_key(source_file, command):
    try:
        source_stat = os.stat(source_file)
    except OSError:
        return None
    return (path.abspath(source_file), source_stat.st_mtime_ns, command)


def _get_cached_compile_result(cache_key):
    if cache_key is None:
        return None
    result = _COMPILE_CACHE.get(cache_key)
    if result is not None:
        _COMPILE_CACHE.move_to_end(cache_key)
    return result


def _store_cached_compile_result(cache_key, compile_result):
    if cache_key is None:
        return
    if compile_result[0] == 0:
        _COMPILE_CACHE[cache_key] = compile_result
        _COMPILE_CACHE.move_to_end(cache_key)
        while len(_COMPILE_CACHE) > _COMPILE_CACHE_MAX_SIZE:
            _COMPILE_CACHE.popitem(last=False)
    else:
        _COMPILE_CACHE.pop(cache_key, None)


class ProcessManager:
    def __init__(self, file, syntax, profiles: Iterable[LanguageProfile] | None = None):
        self.syntax = syntax
        self.file = file
        self.is_run = False
        self.test_counter = 0
        self.profiles = tuple(profiles or ())

    def format_command(self, cmd, args=""):
        return render_command(cmd, self.file, args=args)

    def has_var_view_api(self):
        return False

    def _find_profile_setting(self, key):
        try:
            profile = select_language_profile(self.file, self.profiles)
        except ValueError:
            return -1
        return getattr(profile, key, -1)

    def get_compile_cmd(self):
        value = self._find_profile_setting("compile_cmd")
        if value is None:
            return None
        if value == -1:
            return -1
        return self.format_command(value)

    def get_run_cmd(self, args):
        value = self._find_profile_setting("run_cmd")
        if value is None:
            return None
        if value == -1:
            return -1
        return self.format_command(value, args=args)

    def compile(self, wait_close=True):
        cmd = self.get_compile_cmd()
        if cmd not in {None, -1}:
            cache_key = _build_compile_cache_key(self.file, cmd)
            cached_result = _get_cached_compile_result(cache_key)
            if cached_result is not None:
                return cached_result
            argv = build_command_argv(cmd)
            spawn_options = build_process_spawn_options()
            text_options = build_process_text_options()
            process = subprocess.Popen(
                argv,
                shell=False,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=os.path.split(self.file)[0],
                startupinfo=spawn_options["startupinfo"],
                creationflags=spawn_options["creationflags"],
                **text_options,
            )
            compile_result = process.communicate()[0]
            result = (process.returncode, compile_result)
            _store_cached_compile_result(cache_key, result)
            return result

    def run(self, args=None):
        cmd = self.get_run_cmd(" ".join(args or ()))
        if cmd in {None, -1}:
            raise ValueError(translate("error.no_runnable_command_configured", file=self.file))

        argv = build_command_argv(cmd)
        spawn_options = build_process_spawn_options()
        text_options = build_process_text_options()

        self.process = subprocess.Popen(
            argv,
            shell=False,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
            cwd=os.path.split(self.file)[0],
            startupinfo=spawn_options["startupinfo"],
            creationflags=spawn_options["creationflags"],
            preexec_fn=spawn_options["preexec_fn"],
            **text_options,
        )

    def write(self, s):
        if self.process.poll() is None:
            self.process.stdin.write(s)
            self.process.stdin.flush()

    def communicate(self, s, timeout=None):
        return self.process.communicate(input=s, timeout=timeout)

    def is_stopped(self):
        return self.process.poll()

    def read(self, bfsize=None):
        if bfsize is None:
            return self.process.stdout.read()
        return self.process.stdout.read(bfsize)

    def new_test(self, input_data=None):
        self.test_counter += 1
        self.run()
        if input_data is not None:
            self.write(input_data)

    def terminate(self):
        if os.name != "nt":
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
        else:
            self.process.kill()
