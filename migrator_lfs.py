import base64
import requests
from multiprocessing import Pool
import subprocess
import os
from json import load, dump
from status import StatusManager
from git_commands import GitCommands
status = StatusManager()
git = GitCommands()


class Migrator_LFS:
    def __init__(self, gh_handle, gh_token, gh_organization, git_server, working_path):
        self.gh_base = f"{gh_organization}/"
        self.auth_header_gh = self._authorization_header_gh(gh_token)
        self.repo_list = self.load_json_file(
            "/apps/git/esmail/script/", "git_repo_list_lfs.json")
        self.git_server = git_server
        self.working_path = working_path

    @staticmethod
    def _authorization_header_gh(pat: str) -> str:
        return "Basic " + base64.b64encode(f":{pat}".encode("ascii")).decode("ascii")

    @staticmethod
    def _authorization_header_ado(pat: str) -> str:
        return "Basic " + base64.b64encode(f":{pat}".encode("ascii")).decode("ascii")

    @staticmethod
    def _authorization_header_gitlab(token: str) -> str:
        return "Bearer " + token

    def _git_clone_pull(self, origin_org, origin_project, origin_repo, target_repo):
        working_path = self.working_path
        git_server = self.git_server
        os.chdir(f"{working_path}")
        if(os.path.isdir(f"{working_path}/{target_repo}")):
            os.chdir(f"{working_path}/{target_repo}")
            status.list(1, target_repo)
            git.set_remote_url(self.working_path, target_repo,
                               fr"{git_server}{origin_org}.visualstudio.com/{origin_project}/_git/{origin_repo}", "error_lfs")
            git.fetch(self.working_path, target_repo, "error_lfs")
        else:
            status.list(1, target_repo)
            git.clone_bare(self.working_path, git_server, origin_org,
                           origin_project, origin_repo, target_repo, "error_lfs")
        self.append_json("status_lfs",
                         target_repo, {"level": 1, "check": True})
        self.amount_tags_branches_source(
            fr"{working_path}/{target_repo}", target_repo)
        self.checking_repo_size(
            fr"{working_path}/{target_repo}", target_repo, "source")

    def _git_clone_gh(self,  target_repo):
        working_path = self.working_path
        os.chdir(f"{working_path}")
        res = True
        if(os.path.isdir(f"{working_path}/{target_repo}")):
            os.chdir(f"{working_path}/{target_repo}")
            git.fetch(self.working_path, target_repo, "error_lfs")
        else:
            res = git.clone_bare_gh(
                self.working_path, target_repo, "error_lfs")
        if res is True:
            self.checking_repo_size(
                fr"{working_path}/{target_repo}", target_repo, "github")

    def _push_repo_gh(self, gh_repo, target_repo):
        status.list(3, target_repo)
        working_path = self.working_path
        os.chdir(f"{working_path}/{target_repo}")
        if "errors" in gh_repo:
            remote_url = fr"https://Esmail-BenMoussa_Mobileum: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@github.com/mobmigration/{target_repo}.git"
        else:
            remote_url = gh_repo["clone_url"]

        git.set_remote_url(self.working_path, target_repo,
                           remote_url, "error_lfs")
        git.run_gc_prune(self.working_path, target_repo)
        git.run_gc_repack(self.working_path, target_repo)
        try:
            subprocess.check_call(
                ["git", "lfs", "migrate", "import", "--everything", "--above=100Mb"])
            push_repo = git.push_all(
                self.working_path, target_repo, "error_lfs")
            if push_repo == True:
                git.push_tags(self.working_path, target_repo, "error_lfs")
        except subprocess.CalledProcessError as e:
            error_msg = str(RuntimeError("command '{}' return with error (code {}): {}".format(
                e.cmd, e.returncode, e.output)))
            self.append_json("error_lfs",
                             target_repo, {"msg": error_msg})
        self.append_json("status_lfs", target_repo, {
            "level": 3, "check": True})

    def _create_gh_repo(self, repo_name):
        status.list(2, repo_name)
        repo_details = {
            "name": f"{repo_name}",
            "description": "",
            "homepage": "",
            "visibility": "internal"
        }
        res = requests.post(
            f"{self.gh_base}repos",
            headers={
                "Authorization": self.auth_header_gh,
                "Content-Type": "application/json",
            },
            json=repo_details,
        ).json()
        self.append_json("status_lfs", repo_name, {
            "level": 2, "check": True})
        return res

    def _delete_gh_repo(self, repo):
        # repo_name = repo[0]
        repo_name = repo["Target-repo"]
        print(f"Deleting {repo_name}")
        requests.delete(
            f"https://api.github.com/repos/mobmigration/{repo_name}",
            headers={
                "Authorization": self.auth_header_gh,
                "Content-Type": "application/json",
            },
        )

    def _get_gh_repo(self):
        print("Getting gh repo")
        res = requests.get(
            f"{self.gh_base}repos?per_page=100",
            headers={
                "Authorization": self.auth_header_gh,
                "Content-Type": "application/json",
            },
        ).json()
        list = {}
        for item in res:
            list[item["name"]] = item["size"]
        response = {"res": res, "list": list}
        return response

    def _delete_local_repo(self, repo_name):
        os.chdir(self.working_path)
        subprocess.check_call(["rm", "-r", repo_name])

    def load_json_file(self, working_path, file_name: str):
        f = open(fr"{working_path}/{file_name}")
        data = load(f)
        return data

    def create_json(self, folder_name, repo_name, key, attr):
        with open(fr"/apps/git/esmail/script/{folder_name}/{repo_name}.json", 'w+') as file:
            content = {fr"{repo_name}": {fr"{key}": attr}}
            dump(content, file)
            print("file created")

    def append_json(self, folder_name, repo_name, msg):
        with open(fr"/apps/git/esmail/script/{folder_name}/{repo_name}.json", 'r+') as file:
            # First we load existing data into a dict.
            file_data = load(file)
            # Join new_data with file_data inside emp_details
            file_data[fr"{repo_name}"].update(msg)
            # Sets file's current position at offset.
            file.seek(0)
            # convert back to json.
            dump(file_data, file)
            file.truncate()

    def find(self, name, path):
        for root, dirs, files in os.walk(path):
            if name in files:
                return True
            else:
                return False

    def _error_manager(self, repo_name):
        path = "/apps/git/esmail/script/error_lfs"
        find_file = self.find(fr"{repo_name}.json", path)
        if find_file is True:
            # error_file = self.load_json_file(
            #     fr"/apps/git/esmail/script/error_lfs/{repo_name}.json")
            # if "msg" in error_file[repo_name]:
            #     exit(1)
            # else:
            return True
        else:
            self.create_json("error_lfs",
                             repo_name, "Initialize", "error_lfs")
            return True

    def _status_manager(self, repo_name):
        path = "/apps/git/esmail/script/status_lfs"
        find_file = self.find(fr"{repo_name}.json", path)
        if find_file is True:
            status_file = self.load_json_file(
                fr"/apps/git/esmail/script/status_lfs/", fr"{repo_name}.json")
            if "level" in status_file[repo_name]:
                progress_level = status_file[repo_name]["level"]
                print("Level:", progress_level)
                res = {"level": progress_level, "check": True}
                return res
            else:
                res = {"level": progress_level, "check": True}
                return res
        else:
            self.create_json(
                "status_lfs", repo_name, "level", 0)
            res = {"level": 0, "check": True}
            return res

    def checking_repo_size(self, working_path, target_repo, source):
        if(os.path.isdir(f"{working_path}")):
            os.chdir(f"{working_path}")
            size = subprocess.Popen(
                "du -skh", shell=True, stdout=subprocess.PIPE).communicate()[0].decode('utf-8').strip()
            size = size.replace('\t.', '')
            self.append_json("status_lfs", target_repo, {
                fr"size_{source}": size})

    def checking_repo_size_github(self, target_repo):
        size = 0
        res = requests.get(
            f"https://api.github.com/repos/mobmigration/{target_repo}",
            headers={
                "Authorization": self.auth_header_gh,
                "Content-Type": "application/json",
            },
        ).json()
        size = res["size"]
        self.append_json("status_lfs", target_repo, {
            "size_github": size})

    def amount_tags_branches_source(self, working_path, target_repo):
        if(os.path.isdir(f"{working_path}")):
            os.chdir(f"{working_path}")
            tags = subprocess.Popen(
                "git tag |wc -l", shell=True, stdout=subprocess.PIPE).communicate()[0].decode('utf-8').strip()
            branches = subprocess.Popen(
                "git branch |wc -l", shell=True, stdout=subprocess.PIPE).communicate()[0].decode('utf-8').strip()
            if branches is '':
                branches = 0
            else:
                branches = int(branches)
            if tags is '':
                tags = 0
            else:
                tags = int(tags)
            self.append_json("status_lfs", target_repo, {
                "branches_source": branches})
            self.append_json("status_lfs", target_repo, {
                "tags_source": tags})
            return True

    def amount_tags_github(self, target_repo):
        page = 0
        loop = True
        count = 0
        while loop is True:
            res = requests.get(
                f"https://api.github.com/repos/mobmigration/{target_repo}/tags?per_page=100&page={page}",
                headers={
                    "Authorization": self.auth_header_gh,
                    "Content-Type": "application/json",
                },
            ).json()
            length = len(res)
            count = count + length
            if length < 100:
                loop = False
                self.append_json("status_lfs", target_repo, {
                    "tags_github": count})

    def amount_branches_github(self, target_repo):
        page = 0
        loop = True
        count = 0
        while loop is True:
            res = requests.get(
                f"https://api.github.com/repos/mobmigration/{target_repo}/branches?per_page=100&page={page}",
                headers={
                    "Authorization": self.auth_header_gh,
                    "Content-Type": "application/json",
                },
            ).json()
            length = len(res)
            count = count + length
            if length < 100:
                loop = False
                self.append_json("status_lfs", target_repo, {
                    "branches_github": count})

    def _runner(self, repo, gh_repo=""):
        origin_org = repo["Origin-Org"]
        origin_project = repo["Origin-Project"]
        origin_repo = repo["Origin-repo"]
        target_repo = repo["Target-repo"]
        _error_manager = self._error_manager(target_repo)
        _status_manager = self._status_manager(target_repo)
        if _error_manager is True and _status_manager["check"] is True:
            if _status_manager["level"] < 4:
                if _status_manager["level"] == 0:
                    status.list(0, target_repo, 0)
                    self._git_clone_pull(
                        origin_org, origin_project, origin_repo, target_repo)
                    self._runner(repo, gh_repo)
                if _status_manager["level"] == 1:
                    gh_repo = self._create_gh_repo(target_repo)
                    self._runner(repo, gh_repo)
                if _status_manager["level"] == 2:
                    if isinstance(gh_repo, dict):
                        self._push_repo_gh(gh_repo, target_repo)
                        self._runner(repo, gh_repo)
                    else:
                        gh_repo = {"errors": "errors"}
                        self._push_repo_gh(gh_repo, target_repo)
                        self._runner(repo, gh_repo)
                if _status_manager["level"] == 3:
                    status.list(4, target_repo, 0)
                    status_report = {
                        "level": 4,
                    }
                    self.append_json("status_lfs", target_repo, status_report)
                    self.amount_tags_github(target_repo)
                    self.amount_branches_github(target_repo)
                    self._git_clone_gh(target_repo)
                    self._runner(repo, gh_repo)
            else:
                # self.amount_tags_github(target_repo)
                # self.amount_branches_github(target_repo)
                # self._git_clone_gh(target_repo)
                print(target_repo, " Already migrated!")
        else:
            print(target_repo, "Other serius issue related to error/status report")

    def initializer(self):
        # delete_flag = False
        # gh_repos_names_size = self.gh_repos["list"]
        # # Deletes all repos in GitHub
        # if delete_flag:
        #     pool = Pool()
        #     pool.map(self._delete_gh_repo, gh_repos_names_size.items())
        # else:
        pool = Pool()
        pool.map(self._runner, self.repo_list)
