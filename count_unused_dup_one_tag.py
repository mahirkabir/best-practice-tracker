import os
import helper
import re


def count_duplicates(npm_ls_path):
    """Count number of duplicates from `npm_ls_path` file"""
    reader = open(npm_ls_path, "r", encoding="utf-8")
    lines = reader.readlines()
    reader.close()

    cnt = 0
    dict_dups = {}
    duplicates = ""

    for line in lines:
        if "deduped" in line:
            continue

        line = line.replace("\n", "")
        m = re.search("\w.*@\d\.\d.\d", line)
        if m:
            library_version = m.group(0)  # library@version
            if library_version in dict_dups:
                cnt += 1
                dict_dups[library_version] += 1
            else:
                dict_dups[library_version] = 1

            if dict_dups[library_version] == 2:
                # List the duplicates when it's found the second time
                duplicates += library_version + "\n"

    if len(duplicates) > 0:
        duplicates = duplicates[0:len(duplicates) - 1]  # Removing last \n
    return cnt, duplicates


def count_unused(path):
    """Count number of unused dependencies in `path`"""
    reader = open(path, "r")
    lines = reader.readlines()
    reader.close()

    unused = False
    cnt = 0
    for line in lines:
        if "* " not in line:
            if "Unused" in line:
                unused = True
            else:
                unused = False
        elif unused:
            cnt += 1

    return cnt


if __name__ == "__main__":
    """Count audit vulnerabilities for the latest version of all packages"""

    repos = helper.get_repos(os.path.join(
        ".", "data", "npm_rank_sorted.txt"))

    output = ""
    for repo in repos:
        try:
            repo_path = os.path.join(
                "results", "unused_checker", repo["name"])

            cnt = count_unused(os.path.join(repo_path, "unused_pre.txt"))

            output += ("%s\t%s\n" %
                       (repo["name"], cnt))

        except Exception as ex:
            print(str(ex))

    writer = open(os.path.join("results", "paper_data",
                               "unused_all_package_one_tag.txt"), "w", encoding="utf-8")
    writer.write(output)
    writer.close()

    output = ""
    for repo in repos:
        try:
            repo_path = os.path.join(
                "results", "ddp_checker", repo["name"])

            cnt, _ = count_duplicates(
                os.path.join(repo_path, "before_ddp.txt"))

            output += ("%s\t%s\n" %
                       (repo["name"], cnt))

        except Exception as ex:
            print(str(ex))

    writer = open(os.path.join("results", "paper_data",
                               "dup_all_package_one_tag.txt"), "w", encoding="utf-8")
    writer.write(output)
    writer.close()
