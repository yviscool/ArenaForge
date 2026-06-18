from __future__ import annotations

import os
import signal
import subprocess
from os import path

from arena_forge.adapters.i18n.catalog import translate_catalog as translate

from .subprocess_runner import build_command_argv, build_process_spawn_options, build_process_text_options

_COMPILE_CACHE = {}


def _build_compile_cache_key(source_file, command):
    try:
        source_stat = os.stat(source_file)
    except OSError:
        return None
    return (path.abspath(source_file), source_stat.st_mtime_ns, command)


def _get_cached_compile_result(cache_key):
    if cache_key is None:
        return None
    return _COMPILE_CACHE.get(cache_key)


def _store_cached_compile_result(cache_key, compile_result):
    if cache_key is None:
        return
    if compile_result[0] == 0:
        _COMPILE_CACHE[cache_key] = compile_result
    else:
        _COMPILE_CACHE.pop(cache_key, None)


class ProcessManager(object):
    def __init__(self, file, syntax, run_settings=None):
        super(ProcessManager, self).__init__()
        self.syntax = syntax
        self.file = file
        self.is_run = False
        self.test_counter = 0
        self.write = self.insert
        self.run = self.run_file
        self.run_settings = run_settings
        self.file_name = path.splitext(path.split(file)[1])[0]

    def format_command(self, cmd, args=""):
        file = path.split(self.file)[1]
        return cmd.format(
            file=file,
            source_file=self.file,
            source_file_dir=path.dirname(self.file),
            file_name=self.file_name,
            args=args,
        )

    def has_var_view_api(self):
        return False

    def get_compile_cmd(self):
        opt = self.run_settings
        file_ext = path.splitext(self.file)[1][1:]
        for x in opt:
            if file_ext in x["extensions"]:
                if x["compile_cmd"] is None:
                    return None
                return self.format_command(x["compile_cmd"])
        return -1

    def get_run_cmd(self, args):
        opt = self.run_settings
        file_ext = path.splitext(self.file)[1][1:]
        for x in opt:
            if file_ext in x["extensions"]:
                if x["run_cmd"] is None:
                    return None
                return self.format_command(x["run_cmd"], args=args)
        return -1

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

    def run_file(self, args=[]):
        cmd = self.get_run_cmd(" ".join(args))
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

    def insert(self, s):
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
        self.run_file()
        if input_data is not None:
            self.insert(input_data)

    def terminate(self):
        if os.name != "nt":
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
        else:
            self.process.kill()
