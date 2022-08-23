import os
import helper
import re
from tqdm import tqdm


def count_duplicates(npm_ls_path):
    """Count number of duplicates from `npm_ls_path` file"""
    reader = open(npm_ls_path, "r", encoding="utf-8")
    lines = reader.readlines()
    reader.close()

    cnt = 0
    dict_dups = {}
    duplicates = ""

    for line in lines:
        if "deduped" in line or "UNMET DEPENDENCY" in line or "npm ERR!" in line:
            continue

        line = line.replace("\n", "")
        m = re.search("\w.*@\d\.\d.\d", line)
        if m:
            library_version = m.group(0)  # library@version
            library = library_version.split("@")[0]
            if library in dict_dups:
                cnt += 1
                dict_dups[library] += 1
            else:
                dict_dups[library] = 1

            if dict_dups[library] == 2:
                # List the duplicates when it's found the second time
                duplicates += library + "\n"

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
    """Count unused and dup for the latest version of all packages"""

    repos = helper.get_repos(os.path.join(
        ".", "data", "npm_rank_sorted.txt"))

    """output = ""
    for repo in tqdm(repos):
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
    writer.close()"""

    output = ""
    for repo in tqdm(repos):
        try:
            # repo_path = os.path.join(
            #     "results", "ddp_checker", repo["name"])

            # cnt, duplicates = count_duplicates(
            #     os.path.join(repo_path, "before_ddp.txt"))

            npm_ls_path = os.path.join(
                "results", "camera_ready", "dup_checker")

            cnt, duplicates = count_duplicates(
                os.path.join(npm_ls_path, repo["name"] + ".txt"))

            output += ("%s\t%s\n" %
                       (repo["name"], cnt))

            if duplicates != "":
                helper.record(os.path.join(npm_ls_path, "just_libs"),
                              repo["name"] + ".txt", duplicates)

        except Exception as ex:
            print(str(ex))

    writer = open(os.path.join("results", "paper_data",
                               "dup_all_package_one_tag.txt"), "w", encoding="utf-8")
    writer.write(output)
    writer.close()
