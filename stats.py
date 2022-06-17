import base64
import requests
import os
from json import load, dump
from status import StatusManager
status = StatusManager()


class Analyzor:
    def __init__(self, gh_handle, gh_token, gh_organization, git_server, working_path):
        self.gh_base = f"{gh_organization}/"
        self.auth_header_gh = self._authorization_header_gh(gh_token)
        # self.repo_list = self.load_json_file("roaming_git_repo_list.json")
        # self.gh_repos = self._get_gh_repo()
        self.git_server = git_server
        self.working_path = working_path
        self.globalProps = {}
        self.list = {}

    @staticmethod
    def _authorization_header_gh(pat: str) -> str:
        return "Basic " + base64.b64encode(f":{pat}".encode("ascii")).decode("ascii")

    @staticmethod
    def _authorization_header_ado(pat: str) -> str:
        return "Basic " + base64.b64encode(f":{pat}".encode("ascii")).decode("ascii")

    @staticmethod
    def _authorization_header_gitlab(token: str) -> str:
        return "Bearer " + token

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

    def load_json_file(self, file_name: str):
        f = open(file_name)
        data = load(f)
        return data
        # with open(file_name, "a+") as f:
        #     try:
        #         data = load(f)
        #         return data
        #     except:
        #         obj = {}
        #         return obj

    def create_json(self, folder_name, repo_name, key, attr):
        with open(fr"/apps/git/esmail/script/{folder_name}/{repo_name}.json", 'w+') as file:
            content = {fr"{repo_name}": {fr"{key}": attr}}
            dump(content, file)
            print("file created")

    def append_json(self, folder_name, repo_name, msg):
        with open(folder_name, 'r+') as file:
            # First we load existing data into a dict.
            file_data = load(file)
            # Join new_data with file_data inside emp_details
            if type(file_data) is dict:
                file_data[repo_name] = msg
            else:
                file_data.append(msg)
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

    def initializer(self, lfs=False):
        path = "/apps/git/esmail/script/"
        result_migrated = "result_migrated"
        result_failed = "result_failed"
        status_ = "status"
        repo_list = "git_repo_list_lfs"
        if lfs is True:
            result_migrated = "result_migrated_lfs"
            result_failed = "result_failed_lfs"
            status_ = "status_lfs"
            repo_list = "git_repo_list_lfs_leftovers"
        find_file = self.find(fr"{result_migrated}.json", fr"{path}/result")
        if find_file is True:
            files = []
            for root, dirs, files in os.walk(fr"{path}/{status_}"):
                files = files
            for file in files:
                status_file = self.load_json_file(
                    fr"{path}/{status_}/{file}")
                name = file[0: -5]
                print("Status on: ", name)
                if "level" in status_file[name]:
                    progress_level = status_file[name]["level"]
                    print("Level:", progress_level)
                    if progress_level < 4:
                        result = {"level": progress_level}
                        self.append_json(
                            fr"/apps/git/esmail/script/result/{result_failed}.json", name, result)
                        if progress_level == 2:
                            lfs_result = {
                                "Origin-Org": status_file[name]["Origin-Org"],
                                "Origin-Project": status_file[name]["Origin-Project"],
                                "Origin-repo": status_file[name]["Origin-repo"],
                                "Target-repo": status_file[name]["Target-repo"]
                            }
                            self.append_json(
                                fr"/apps/git/esmail/script/{repo_list}.json", name, lfs_result)

                    else:
                        result = "Migrated"
                        # Branch and tags check
                        branches_source = status_file[name]["branches_source"]
                        branches_github = status_file[name]["branches_github"]
                        tags_source = status_file[name]["tags_source"]
                        tags_github = status_file[name]["tags_github"]
                        size_source = status_file[name]["size_source"]
                        size_github = status_file[name]["size_github"]
                        # branch_result = False
                        # tag_result = False
                        # size_result = ""
                        # if branches_source == branches_github:
                        #     branch_result = True
                        # if tags_source == tags_github:
                        #     tag_result = True
                        # if size_github == size_source:
                        #     size_result = "Match"
                        # else:
                        #     size_result = fr"GH:{size_github}, SC:{size_source}"
                        # res = {
                        #     "branch_result": branch_result,
                        #        "tag_result": tag_result, "size_result": size_result}
                        res = {"branches_source": branches_source, "branches_github": branches_github, "tags_source": tags_source,
                               "tags_github": tags_github, "size_source": size_source, "size_github": size_github}
                        self.append_json(
                            fr"/apps/git/esmail/script/result/{result_migrated}.json", name, res)

        else:
            self.create_json("result", result_migrated, "Initialize", "result")
            self.create_json("result", result_failed,
                             "Initialize", "result")
            self.initializer(lfs)
