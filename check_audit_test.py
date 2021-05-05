import helper
import os
from tqdm import tqdm
import constants
import re


def run_npm_i(repo_loc):
    "Run `npm i` in repo_loc"
    return helper.execute_cmd(repo_loc, "npm i")


def deduplicate(repo_loc):
    """Run `npm ddp` in repo_loc"""
    return helper.execute_cmd(repo_loc, "npm ddp")


def get_fixable_repos_dict(result_filename):
    """Find dictionary of all the repos that are fixable by audit fixings and show the steps to fix"""
    reader = open(result_filename, "r", encoding="utf-8")
    lines = reader.readlines()[1:]
    reader.close()

    dict_repos = {}
    for line in lines:
        parts = line.split("\t")
        if constants.AUDIT_TRUE in parts[-1]:
            dict_repos[parts[0]] = []
            if constants.AUDIT_TRUE in parts[1]:
                # Had no vulnerability in the first place
                pass
            elif constants.AUDIT_TRUE in parts[2]:
                # "npm i" is added as prerequisite for ddp. So no need to install package-lock here
                pass
            elif constants.AUDIT_TRUE in parts[3]:
                # Need to run `npm audit fix` to make the repo fixable
                dict_repos[parts[0]].append("npm audit fix")
            elif constants.AUDIT_TRUE in parts[4]:
                # Need to run `npm audit fix --force` to make the repo fixable
                dict_repos[parts[0]].append("npm audit fix")
                dict_repos[parts[0]].append("npm audit fix --force")

    return dict_repos


def run_audit_fixings(repo_loc, commands):
    """Run all the `commands` in the `repo_loc` step by step"""
    for command in commands:
        helper.execute_cmd(repo_loc, command)


if __name__ == "__main__":
    """Check run status after audit fixes and deduplication"""

    dataset_path = helper.get_config("PATHS", "DATASET_PATH")
    dict_fixable_repos = get_fixable_repos_dict(
        os.path.join("results", "audit_checker", "audit_results.txt"))

    org_repos = helper.get_repos(os.path.join(
        ".", "data", "npm_rank_sorted.txt"))
    repos = []
    dict_tmp = {}
    for repo in org_repos:
        if repo["name"] in dict_fixable_repos:
            repos.append(repo)

            if repo["name"] in dict_tmp:
                print(repo)
            dict_tmp[repo["name"]] = 1

    repos.reverse()
    repos = repos[0:1]
    repos_sz = len(repos)

    main_folder = "audit_test_checker"
    writer = open(os.path.join("results", main_folder,
                               "audit_test_results.txt"), "w", encoding="utf-8")

    writer.write(
        "Repository\tInitial Test\tTest After Audit Fix\tTest After Deduplication\tNotes")
    writer.write("\n")
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
                1. Check Test Result Initially
                2. Check Test Result after fixing audit vulneralibities
                3. Check Test Result after running deduplication
                """

                result = {"name": repo["name"], "initial": "", "after-audit-fix": "",
                          "after-ddp": "", "note": ""}

                run_npm_i(repo_loc)  # Prerequisite
                initial_test = helper.test(repo_loc)

                if "Missing script: \"test\"" in initial_test[1]:
                    after_audit_fix_test = initial_test
                    after_ddp_test = initial_test
                    ddp_result = [
                        "", "Didn't execute `npm ddp` since \"Test\" script was missing"]
                    result["note"] = "Missing Test Script"
                else:
                    after_audit_fix_test = ["-", ""]
                    if len(dict_fixable_repos[repo["name"]]) > 0:
                        # This repo needs audit fixing
                        run_audit_fixings(
                            repo_loc, dict_fixable_repos[repo["name"]])
                        after_audit_fix_test = helper.test(repo_loc)

                        if after_audit_fix_test[0] != initial_test[0]:
                            after_audit_fix_test[0] += " (Changed)"
                    else:
                        # This repo did not need audit fixing. So no need to check test status again
                        result["after-audit-fix"] = "-"

                    ddp_result = deduplicate(repo_loc)
                    after_ddp_test = helper.test(repo_loc)
                    if after_ddp_test[0] != initial_test[0]:
                        after_ddp_test[0] += " (Changed)"

                result["initial"] = initial_test[0]
                result["after-audit-fix"] = after_audit_fix_test[0]
                result["after-ddp"] = after_ddp_test[0]
                writer = open(os.path.join("results", main_folder,
                                           "audit_test_results.txt"), "a", encoding="utf-8")

                writer.write("%s\t%s\t%s\t%s\t%s\n" % (
                    repo["name"], result["initial"], result["after-audit-fix"],
                    result["after-ddp"], result["note"]))
                writer.close()

                foldername = os.path.join(
                    "results", main_folder, repo["name"])

                helper.record(foldername, "initial_test.txt", initial_test[1])
                helper.record(foldername, "after_audit_fix_test.txt",
                              after_audit_fix_test[1])
                helper.record(foldername, "after_ddp_test.txt",
                              after_ddp_test[1])
                helper.record(foldername, "ddp_result.txt", ddp_result[1])

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
