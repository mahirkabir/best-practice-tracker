import helper
import os
from tqdm import tqdm
import re


def count_unused(path):
    """Find number of unused dependencies in `path`"""
    try:
        cnt = 0
        reader = open(path, "r")
        lines = reader.readlines()
        reader.close()

        for line in lines:
            if "* " in line:
                cnt += 1

        return cnt
    except:
        return -1


def count_vulnerable(path):
    """Find number of vulnerable dependencies in `path`"""
    try:
        cnt = 0
        reader = open(path, "r")
        lines = reader.readlines()
        reader.close()

        for line in lines:
            if "Severity: " in line:
                cnt += 1

        return cnt
    except:
        return -1


def count_duplicate(path):
    """Find number of vulnerable dependencies in `path`"""
    try:
        cnt = 0
        dict_dups = {}

        reader = open(path, "r")
        lines = reader.readlines()
        reader.close()

        for line in lines:
            if not "deduped" in line:
                line = line.replace("\n", "")
                m = re.search("\w.*@\d\.\d.\d", line)
                if m:
                    library_version = m.group(0)  # library@version
                    if library_version in dict_dups:
                        cnt += 1
                    else:
                        dict_dups[library_version] = 1

        return cnt
    except:
        return -1


if __name__ == "__main__":
    """Check number of projects having at least one unused, duplicate or vulnerable dependencies
    Check number of projects for which the violations could be fixed"""

    repos = helper.get_repos(os.path.join(".", "data", "npm_rank_sorted.txt"))

    repos_sz = len(repos)

    result = {"unused": 0, "duplicate": 0, "vulnerable": 0,
              "duplicate-fixed": 0, "duplicate-part-fixed": 0, "vulnerable-fixed": 0}

    for repo in tqdm(repos):
        unused_cnt = count_unused(os.path.join(
            "results", "unused_checker", repo["name"], "unused_pre.txt"))
        duplicate_cnt = count_duplicate(os.path.join(
            "results", "ddp_checker", repo["name"], "before_ddp.txt"))
        vulnerable_cnt = count_vulnerable(os.path.join(
            "results", "audit_checker", repo["name"], "init_audit.txt"))

        if vulnerable_cnt == 0:
            # In case, npm i needed to be run
            vulnerable_cnt = count_vulnerable(os.path.join(
                "results", "audit_checker", repo["name"], "after_i_lock.txt"))

        fixed_duplicate_cnt = count_duplicate(os.path.join(
            "results", "ddp_checker", repo["name"], "after_ddp.txt"))
        fixed_vulnerable_cnt = count_vulnerable(os.path.join(
            "results", "audit_checker", repo["name"], "after_fix.txt"))

        result["unused"] += int(unused_cnt > 0)
        result["duplicate"] += int(duplicate_cnt > 0)
        result["vulnerable"] += int(vulnerable_cnt > 0)

        # if all duplicates are fixed
        result["duplicate-fixed"] += int(duplicate_cnt >
                                         0 and fixed_duplicate_cnt == 0)
        result["duplicate-part-fixed"] += int(
            duplicate_cnt > 0 and fixed_duplicate_cnt < duplicate_cnt)

        # if all vulnerabilities are fixed
        result["vulnerable-fixed"] += int(vulnerable_cnt >
                                          0 and fixed_vulnerable_cnt == 0)

    print(result)
