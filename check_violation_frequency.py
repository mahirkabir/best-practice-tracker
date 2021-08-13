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

    ddp_writer = open(os.path.join("results", "ddp_checker",
                                   "ddp_count.txt"), "w", encoding="utf-8")
    ddp_writer.write("Repository\tOriginal Duplicates\n")
    ddp_writer.close()

    ddp_err_repos = []

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

        ddp_writer = open(os.path.join("results", "ddp_checker",
                                       "ddp_count.txt"), "a", encoding="utf-8")
        ddp_writer.write("%s\t%s\n" % (repo["name"], duplicate_cnt))
        ddp_writer.close()
        if duplicate_cnt == -1:
            ddp_err_repos.append(repo)

    print(result)

    # dataset_path = helper.get_config("PATHS", "DATASET_PATH")
    # repos = ddp_err_repos
    # repos_sz = len(repos)

    # range_limit = 50
    # for i in range(0, repos_sz, range_limit):
    #     print("Processing repo [%s..%s]:" % (str(i), str(i + range_limit - 1)))

    #     # First clone the (<= range_limit) repositories in dataset folder
    #     left_repos = min(i + range_limit, repos_sz)
    #     for j in tqdm(range(i, left_repos)):
    #         repo = repos[j]

    #         try:
    #             repo["name"] = helper.clone_repo_to_dir(
    #                 dataset_path, repo["url"], repo["name"])

    #         except Exception as ex:
    #             print("Error cloning [%s]: %s" % (repo["name"], str(ex)))

    #     # Process each one of the cloned repositories
    #     for j in tqdm(range(i, left_repos)):
    #         repo = repos[j]

    #         repo_loc = os.path.join(dataset_path, repo["name"])

    #         try:
    #             helper.execute_cmd(repo_loc, "npm i")
    #             result = helper.execute_cmd(repo_loc, "npm ls --all")
    #             helper.record(os.path.join("results", "ddp_checker",
    #                                        repo["name"]), "before_ddp.txt", result[1])
    #         except Exception as ex:
    #             print("Error processing [%s]: %s" % (repo["name"], str(ex)))

    #     # Delete the (<= range_limit) repositories in dataset folder
    #     for j in tqdm(range(i, left_repos)):
    #         repo = repos[j]

    #         try:
    #             helper.remove_folder(
    #                 dataset_path, repo["name"])

    #         except Exception as ex:
    #             print("Error deleting [%s]: %s" % (repo["name"], str(ex)))
