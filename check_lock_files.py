import requests
from bs4 import BeautifulSoup
import json
import os
import constants
import re
from tqdm import tqdm


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


if __name__ == "__main__":
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
