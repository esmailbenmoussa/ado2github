from stats import Analyzor
from migrator import Migrator
import os
from dotenv import load_dotenv

load_dotenv()

gh_handle = os.getenv("GH_HANDLE")  #
gh_token = os.getenv("GH_TOKEN")  #
gh_organization = os.getenv("GH_ORG")
git_server = "https://Esmail.BenMoussa:l45mb43lfrcyunjkeqxz3yja4clexgpqccmxgusdtau7mrk3vkta@"
# MobileumEngineering/AIDA/_git/AIDA
working_path = "/apps/git/esmail/repos"
migrator = Migrator(gh_handle, gh_token, gh_organization,
                    git_server, working_path)
stats = Analyzor(gh_handle, gh_token, gh_organization,
                 git_server, working_path)


if __name__ == '__main__':
    # migrator.initializer(lfs=False)
    # stats.initializer(lfs=False)
    # migrator.initializer(lfs=True)  # Debug
    stats.initializer(lfs=True)
