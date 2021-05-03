import os
import re

from requests.sessions import extract_cookies_to_jar
import helper
import requests
from bs4 import BeautifulSoup
import json
import constants


def count_techniques(dict_count_deps, dict_count_repos, package_json, tag):
    """Find occurrences of version relaxation techniques in `tag` section of `package_json`"""
    if tag in package_json:
        dependencies = package_json[tag]

        has_tilde, has_caret, has_hyphen, has_lt_gt, has_others = 0, 0, 0, 0, 0
        for lib in dependencies:
            version = dependencies[lib]

            if "~" in version:
                dict_count_deps[constants.TECH_TILDE] += 1
                has_tilde = 1
            elif "^" in version:
                dict_count_deps[constants.TECH_CARET] += 1
                has_caret = 1
            elif "-" in version:
                dict_count_deps[constants.TECH_HYPHEN] += 1
                has_hyphen = 1
            elif ("<" in version) or (">" in version):
                dict_count_deps[constants.TECH_LT_GT] += 1
                has_lt_gt = 1
            else:
                dict_count_deps[constants.TECH_OTHERS] += 1
                has_others = 1

        dict_count_repos[constants.TECH_TILDE] += has_tilde
        dict_count_repos[constants.TECH_CARET] += has_caret
        dict_count_repos[constants.TECH_HYPHEN] += has_hyphen
        dict_count_repos[constants.TECH_LT_GT] += has_lt_gt
        dict_count_repos[constants.TECH_OTHERS] += has_others

    return dict_count_deps, dict_count_repos


if __name__ == "__main__":
    """Find version relaxation techniques' distribution"""
    dataset_path = helper.get_config("PATHS", "DATASET_PATH")
    repos = helper.get_repos(os.path.join(".", "data", "npm_rank_sorted.txt"))

    repos_sz = len(repos)

    dict_techniques = {constants.TECH_TILDE: 0, constants.TECH_CARET: 0,
                       constants.TECH_HYPHEN: 0, constants.TECH_LT_GT: 0,
                       constants.TECH_OTHERS: 0}

    dict_repos = {constants.TECH_TILDE: 0, constants.TECH_CARET: 0,
                  constants.TECH_HYPHEN: 0, constants.TECH_LT_GT: 0,
                  constants.TECH_OTHERS: 0}

    for repo in repos:
        """
        1. Get the content of package.json file by web scraping
        2. Check all the version relaxation techniques' count for 4 main techniques & others
        3. The techniques are - Tilde, Caret, Hyphen, Less Than Greater Than, Others
        """
        try:
            url = repo["url"].replace(
                "github", "raw.githubusercontent") + "/master/package.json"
            r = requests.get(url)

            soup = BeautifulSoup(r.content, 'html.parser')
            package_json = json.loads(soup.text)

            dict_techniques, dict_repos = count_techniques(
                dict_techniques, dict_repos, package_json, constants.TAG_DEPENDENCIES)
            dict_techniques, dict_repos = count_techniques(
                dict_techniques, dict_repos, package_json, constants.TAG_DEVDEPENDENCIES)

        except Exception as ex:
            print(ex)

    print(dict_techniques)
    print(dict_repos)
