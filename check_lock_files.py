import requests
from bs4 import BeautifulSoup
import json
import os
import constants
import re
from tqdm import tqdm
import helper


def is_totally_fixed(package_json, section):
    """Check if all dependencies in the `section` are fixed"""
    ret = constants.TAG_EMPTY
    if section in package_json:
        for dep in package_json[section]:
            ret = True
            if re.match("\d\.\d\.\d", package_json[section][dep]):
                pass
            else:
                return False

    return ret


def get_lock_file_info(repo_link):
    """Check which lock files the repository have"""

    result = {"package-lock": 0, "npm-shrinkwrap": 0, "yarn": 0}

    try:
        for lockfile in result:
            lock_file_url = repo_link + "/master/" + lockfile + ".json"

            page = requests.get(lock_file_url)

            if(page.status_code != constants.ERROR_CODE_NOT_FOUND):
                result[lockfile] = 1
            else:
                pass

        result["fixed-json"] = 0
        result["no-dependency"] = 0
        config_file_url = repo_link + "/master/package.json"

        page = requests.get(config_file_url)

        if(page.status_code != constants.ERROR_CODE_NOT_FOUND):
            soup = BeautifulSoup(page.content, 'html.parser')
            package_json = json.loads(soup.text)

            if (constants.TAG_DEPENDENCIES not in package_json) and (
                    constants.TAG_DEVDEPENDENCIES not in package_json):
                result["no-dependency"] = 1
            else:
                all_fixed_dep = is_totally_fixed(
                    package_json, constants.TAG_DEPENDENCIES)
                all_fixed_dev_dep = is_totally_fixed(
                    package_json, constants.TAG_DEVDEPENDENCIES)
                if all_fixed_dep == True and all_fixed_dev_dep == True:
                    result["fixed-json"] = 1
                elif all_fixed_dep == constants.TAG_EMPTY and all_fixed_dev_dep == constants.TAG_EMPTY:
                    result["no-dependency"] = 1

    except Exception as ex:
        print(str(ex))

    return result


if __name__ == "__main__OFF":
    """"Check the existence of lock file in repos
    NOTE: Activate this main function to check lock file existence"""
    reader = open(os.path.join("data", "npm_rank_sorted.txt"), "r")

    repos = reader.readlines()
    refined_repos = []  # only the repos having valid build scripts

    writer = open(os.path.join("results", "paper_data", "repo_lock_files.txt"),
                  "w", encoding="utf-8")
    writer.write(
        "Repository\tPackage-Lock\tNpm-ShrinkWrap\tYarn\tAll-Fixed\tNo-Dependency\n")
    writer.close()

    for repo in tqdm(repos):
        repo = repo[:-1]  # to remove the line break at the end
        repo_url = repo.split("\t")[1]
        repo_link = repo_url.replace("github.com", "raw.githubusercontent.com")
        result = get_lock_file_info(repo_link)

        writer = open(os.path.join("results", "paper_data", "repo_lock_files.txt"),
                      "a", encoding="utf-8")
        writer.write(
            "%s\t%s\t%s\t%s\t%s\t%s\n" %
            (repo.split("\t")[0], result["package-lock"], result["npm-shrinkwrap"], result["yarn"],
             result["fixed-json"], result["no-dependency"]))
        writer.close()

    reader.close()


def get_lock_file_repos(org_repos, path):
    """Filter the repos by keeping only the ones with lock file(s)"""
    dict_org_repo_lock_files = {}
    reader = open(path, "r")
    lines = reader.readlines()[1:]
    reader.close()
    for line in lines:
        parts = line.split("\t")
        dict_org_repo_lock_files[parts[0]] = []

        if parts[1] == "1":
            dict_org_repo_lock_files[parts[0]].append("package-lock.json")
        if parts[2] == "1":
            dict_org_repo_lock_files[parts[0]].append("npm-shrinkwrap.json")
        if parts[3] == "1":
            dict_org_repo_lock_files[parts[0]].append("yarn.lock")

    dict_repo_lock_files = {}
    repos = []
    for repo in org_repos:
        if repo["name"] in dict_org_repo_lock_files and len(dict_org_repo_lock_files[repo["name"]]) > 0:
            repos.append(repo)
            dict_repo_lock_files[repo["name"]
                                 ] = dict_org_repo_lock_files[repo["name"]]

    return dict_org_repo_lock_files, repos


def get_commit_info(repo_loc, lock_file):
    """Find first commit no. and order for `lock_file`"""
    commit = ""
    order = -1

    # total_commits = order = helper.execute_cmd(
    #     repo_loc, "git rev-list --count HEAD")[1].replace("\n", "")
    result = helper.execute_cmd(
        repo_loc, "git log --diff-filter=A -- " + lock_file)
    commit = result[1].split("\n")[0].split(" ")[1]

    # NOTE: Was used to find the order of the commit
    # helper.execute_cmd(repo_loc, "git checkout " + commit)
    # order = helper.execute_cmd(
    #     repo_loc, "git rev-list --count HEAD")[1].replace("\n", "")

    parts = result[1].split("\n")
    for part in parts:
        const_str = "Date:   "
        if const_str in part:
            part = part.replace(const_str, "")
            date_parts = part.split(" ")
            month = date_parts[1]
            year = date_parts[-2]           
            time = month + "||" + year


    # return commit, order,  total_commits
    return commit, time


if __name__ == "__main__":
    """Check when the lock file was introduced first
    NOTE: Activate this main function to check the inital commit of lock file"""

    dataset_path = helper.get_config("PATHS", "DATASET_PATH")
    org_repos = helper.get_repos(os.path.join(
        ".", "data", "npm_rank_sorted.txt"))

    dict_repo_lock_files, repos = get_lock_file_repos(org_repos, os.path.join(
        "results", "paper_data", "repo_lock_files.txt"
    ))

    repos_sz = len(repos)

    writer = open(os.path.join("results", "paper_data",
                               "lock_file_init_commit.txt"), "w", encoding="utf-8")
    writer.write(
        "Repository\tLock File\tCommit No.\tCommit Time\n")
    writer.close()

    range_limit = 50
    for i in range(0, repos_sz, range_limit):
        print("Processing repo [%s..%s]:" % (str(i), str(i + range_limit - 1)))

        # First clone the (<= range_limit) repositories in dataset folder
        left_repos = min(i + range_limit, repos_sz)
        for j in tqdm(range(i, left_repos)):
            repo = repos[j]

            try:
                repo["name"] = helper.clone_repo_to_dir(
                    dataset_path, repo["url"], repo["name"])

            except Exception as ex:
                print("Error cloning [%s]: %s" % (repo["name"], str(ex)))

        # Process each one of the cloned repositories
        for j in tqdm(range(i, left_repos)):
            repo = repos[j]

            repo_loc = os.path.join(dataset_path, repo["name"])
            try:
                """
                1. For each lock file, find the initial commit of the lock file
                2. Checkout the commit
                3. Check the commit count till that commit
                4. Record the info
                """

                lock_files = dict_repo_lock_files[repo["name"]]

                for lock_file in lock_files:
                    result = {"name": repo["name"], "lock-type": lock_file, "first-commit": "",
                              "commit-time": ""}

                    result["first-commit"], result["commit-time"] = get_commit_info(
                        repo_loc, lock_file)

                    writer = open(os.path.join("results", "paper_data",
                                               "lock_file_init_commit.txt"), "a", encoding="utf-8")
                    writer.write(
                        "%s\t%s\t%s\t%s\n" % (result["name"], result["lock-type"],
                                                  result["first-commit"], result["commit-time"]))
                    writer.close()

            except Exception as ex:
                print("Error processing [%s]: %s" % (repo["name"], str(ex)))

        # Delete the (<= range_limit) repositories in dataset folder
        for j in tqdm(range(i, left_repos)):
            repo = repos[j]

            try:
                helper.remove_folder(
                    dataset_path, repo["name"])

            except Exception as ex:
                print("Error deleting [%s]: %s" % (repo["name"], str(ex)))
