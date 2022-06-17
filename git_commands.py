import base64
from dataclasses import dataclass
import datetime
import logging
import requests
import time
from typing import Any, Callable, Dict, Iterable, Optional
from ftplib import FTP_PORT
from multiprocessing import Pool
import subprocess
import os
from json import load, dump
import re


class GitCommands:
    def write_json(self, folder_name, repo_name, msg):
        with open(fr"/apps/git/esmail/script/{folder_name}/{repo_name}.json", 'r+') as file:
            # First we load existing data into a dict.
            file_data = load(file)
            # Join new_data with file_data inside emp_details
            file_data[repo_name] = msg
            # Sets file's current position at offset.
            file.seek(0)
            # convert back to json.
            dump(file_data, file)
            file.truncate()

    def push_tags(self, working_path, repo_name, write_json_file):
        os.chdir(f"{working_path}/{repo_name}")
        try:
            subprocess.check_call(
                ["git", "push", "--tags", "origin"])
        except subprocess.CalledProcessError as e:
            error_msg = str(RuntimeError("command '{}' return with error (code {}): {}".format(
                e.cmd, e.returncode, e.output)))
            self.write_json(write_json_file, repo_name, {"msg": error_msg})

    def run_gc_prune(self, working_path, repo_name):
        os.chdir(f"{working_path}/{repo_name}")
        try:
            subprocess.check_call(
                ["git", "gc", "--prune=now"])
        except subprocess.CalledProcessError as e:
            error_msg = str(RuntimeError("command '{}' return with error (code {}): {}".format(
                e.cmd, e.returncode, e.output)))
            self.write_json("error", repo_name, {"msg": error_msg})

    def run_gc_repack(self, working_path, repo_name):
        os.chdir(f"{working_path}/{repo_name}")
        try:
            subprocess.check_call(
                ["git", "repack", "-a", "-d", "-f"])
        except subprocess.CalledProcessError as e:
            error_msg = str(RuntimeError("command '{}' return with error (code {}): {}".format(
                e.cmd, e.returncode, e.output)))
            self.write_json("error", repo_name, {"msg": error_msg})

    def set_remote_url(self, working_path, repo_name, remote_url, write_json_file):
        os.chdir(f"{working_path}/{repo_name}")
        try:
            subprocess.check_call(
                ["git", "remote", "set-url", "origin", remote_url])
        except subprocess.CalledProcessError as e:
            error_msg = str(RuntimeError("command '{}' return with error (code {}): {}".format(
                e.cmd, e.returncode, e.output)))
            self.write_json(write_json_file, repo_name, {"msg": error_msg})

    def push_all(self, working_path, repo_name, write_json_file):
        os.chdir(f"{working_path}/{repo_name}")
        try:
            subprocess.check_call(
                ["git", "push", "--all", "origin"])
        except subprocess.CalledProcessError as e:
            error_msg = str(RuntimeError("command '{}' return with error (code {}): {}".format(
                e.cmd, e.returncode, e.output)))
            self.write_json(write_json_file, repo_name, {"msg": error_msg})
            return False
        else:
            return True

    def clone_bare(self, working_path, git_server, origin_org, origin_project, origin_repo, target_repo, write_json_file):
        os.chdir(f"{working_path}")
        try:
            subprocess.check_call(
                ["git", "clone", "--bare",
                 fr"{git_server}{origin_org}.visualstudio.com/{origin_project}/_git/{origin_repo}",
                 target_repo])
        except subprocess.CalledProcessError as e:
            error_msg = str(RuntimeError("command '{}' return with error (code {}): {}".format(
                e.cmd, e.returncode, e.output)))
            self.write_json(write_json_file, target_repo, {"msg": error_msg})
            return False
        else:
            return True
            # raise RuntimeError("command '{}' return with error (code {}): {}".format(
            #     e.cmd, e.returncode, e.output))

    def clone_bare_gh(self, working_path,  target_repo, write_json_file):
        os.chdir(f"{working_path}")
        try:
            subprocess.check_call(
                ["git", "clone", "--bare",
                 fr"https://Esmail-BenMoussa_Mobileum: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@github.com/mobmigration/{target_repo}.git",
                 fr"{target_repo}_github"])
        except subprocess.CalledProcessError as e:
            error_msg = str(RuntimeError("command '{}' return with error (code {}): {}".format(
                e.cmd, e.returncode, e.output)))
            self.write_json(write_json_file, target_repo, {"msg": error_msg})
            return False
            # raise RuntimeError("command '{}' return with error (code {}): {}".format(
            #     e.cmd, e.returncode, e.output))
        else:
            return True

    def fetch(self, working_path, repo_name, write_json_file):
        os.chdir(f"{working_path}/{repo_name}")
        try:
            subprocess.check_call(
                ["git", "fetch"])
        except subprocess.CalledProcessError as e:
            error_msg = str(RuntimeError("command '{}' return with error (code {}): {}".format(
                e.cmd, e.returncode, e.output)))
            self.write_json(write_json_file, repo_name, {"msg": error_msg})
