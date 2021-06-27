import requests
from bs4 import BeautifulSoup
import json
import os
import constants


def has_build_scripts(repo_link):
    """Check if repo has valid build scripts"""
    # For some repos, the raw package.json file location is in different position than expected
    # They are filtered out as well

    config_file_url = repo_link + "/master/package.json"

    page = requests.get(config_file_url)

    if(page.status_code == constants.ERROR_CODE_NOT_FOUND):
        return False

    try:

        soup = BeautifulSoup(page.content, 'html.parser')
        package_json = json.loads(soup.text)

        # only processing repos with build scripts (i.e. => "build": ...)
        has_proper_build_scripts = False
        if constants.TAG_SCRIPTS in package_json:  # checking further if the scripts are okay
            scripts = package_json[constants.TAG_SCRIPTS]
            if(len(scripts) > 0 and constants.TAG_BUILD_SCRIPTS in scripts):
                has_proper_build_scripts = True

        return has_proper_build_scripts
    except Exception as ex:
        return False


if __name__ == "__main__":
    reader = open(os.path.join("data", "npm_rank_sorted.txt"), "r")

    repos = reader.readlines()
    refined_repos = []  # only the repos having valid build scripts

    clean_cnt = 0
    for repo in repos:
        repo = repo[:-1]  # to remove the line break at the end
        repo_url = repo.split("\t")[1]
        repo_link = repo_url.replace("github.com", "raw.githubusercontent.com")

        if has_build_scripts(repo_link):
            refined_repos.append(repo)
        else:
            clean_cnt += 1

    reader.close()

    writer = open(os.path.join("data", "repo_with_build_scripts.txt"),
                  "w", encoding="utf-8")

    for repo in refined_repos:
        writer.write(repo.split("\t")[0] + "\t" + repo.split("\t")[1])
        writer.write("\n")

    writer.close()

    print("Filtered out %s repositories" % (str(clean_cnt)))
