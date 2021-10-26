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
        if "deduped" in line:
            continue

        line = line.replace("\n", "")
        m = re.search("\w.*@\d\.\d.\d", line)
        if m:
            library_version = m.group(0)  # library@version
            library = library_version.split("@")[0]
            # library = library_version
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


if __name__ == "__main__":
    """Count number of duplicates before and after running npm dedupe"""

    repos = helper.get_repos(os.path.join(
        ".", "data", "npm_rank_sorted.txt"))

    results_path = helper.get_config("PATHS", "RESULTS_PATH")

    output = ""
    for repo in tqdm(repos):
        try:
            repo_path = os.path.join(
                results_path, "ddp_results", repo["name"])

            cnt_before, _ = count_duplicates(
                os.path.join(repo_path, "npm_ls_before.txt"))

            cnt_after, _ = count_duplicates(
                os.path.join(repo_path, "npm_ls_after.txt"))

            suffix = ""
            if cnt_before != cnt_after:
                suffix = "***"
            elif cnt_before == 0:
                suffix = "^^^"
            elif cnt_before == cnt_after:
                suffix = "---"

            output += ("%s\t%s\t%s\t%s\n" %
                       (repo["name"], cnt_before, cnt_after, suffix))

        except Exception as ex:
            print(str(ex))
            output += ("%s\t%s\t%s\t%s\n" %
                       (repo["name"], 0, 0, "~~~"))

    writer = open(os.path.join("results", "paper_data",
                               "dup_before_and_after.txt"), "w", encoding="utf-8")
    writer.write(output)
    writer.close()
