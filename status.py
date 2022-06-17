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
from json import load
import re


@dataclass
class SetFieldOperation:
    ado_field: str
    yt_field: str
    set_after_creation: bool


CustomFieldHandler = Callable[[Dict[str, Any]], Iterable[SetFieldOperation]]


class StatusManager:
    def list(self, step, repo_name="", repo_size=""):
        status = ""
        if(step == 0):
            status = f"""
                (0/4) {repo_name}, {repo_size}
                _git_clone_pull      => To do
                _create_gh_repo      => To do
                _push_repo_gh        => To do
                """
        if(step == 1):
            status = f"""
                (1/4) {repo_name}, {repo_size}
                _git_clone_pull      => In progress
                _create_gh_repo      => To do
                _push_repo_gh        => To do
                """
        if(step == 2):
            status = f"""
                (2/4) {repo_name}, {repo_size}
                _git_clone_pull      => Done
                _create_gh_repo      => In progress
                _push_repo_gh        => To do
                """
        if(step == 3):
            status = f"""
                (3/4) {repo_name}, {repo_size}
                _git_clone_pull      => Done
                _create_gh_repo      => Done
                _push_repo_gh        => In progress
                """
        if(step == 4):
            status = f"""
                (4/4) {repo_name}, {repo_size}
                _git_clone_pull      => Done
                _create_gh_repo      => Done
                _push_repo_gh        => Done
                """
        print(status)
