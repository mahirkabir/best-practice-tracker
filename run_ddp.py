import os
import constants
import helper
from tqdm import tqdm
from functools import reduce


def get_repo_step(lines):
    """Get the first step in which `npm audit` found no vulnerability"""
    dict_repo_step = {}
    dict_needs_install = {}

    for line in lines:
        parts = line.split("\t")
        parts[-1] = parts[-1].strip()

        repo_name = parts[0]
        if constants.AUDIT_TRUE in parts[1]:
            dict_repo_step[repo_name] = constants.AUDIT_STEP_INIT
        elif constants.AUDIT_TRUE in parts[2]:
            dict_repo_step[repo_name] = constants.AUDIT_STEP_INSTALL
        elif constants.AUDIT_TRUE in parts[3]:
            dict_repo_step[repo_name] = constants.AUDIT_STEP_FIX
        elif constants.AUDIT_TRUE in parts[4]:
            dict_repo_step[repo_name] = constants.AUDIT_STEP_FORCE_FIX
        else:
            dict_repo_step[repo_name] = constants.AUDIT_STEP_FAIL

        dict_needs_install[repo_name] = (
            dict_repo_step[repo_name] != constants.AUDIT_STEP_FAIL) and (
            constants.AUDIT_STEP_CHANGED in parts[2])

    return dict_repo_step, dict_needs_install


def get_fixable_repos(org_repos, dict_repo_step):
    """Keep repos that already have no vulnerability or can be fixed"""
    repos = []
    for repo in org_repos:
        if dict_repo_step[repo["name"]] != constants.AUDIT_STEP_FAIL:
            repos.append(repo)
    return repos


def get_npm_ls(repo_loc):
    """Run `npm ls --all` and return the result"""
    helper.execute_cmd(repo_loc, "npm ls --all >> tmp.txt")
    reader = open(os.path.join(repo_loc, "tmp.txt"), "r", encoding="utf-8")
    lines = reader.readlines()
    result = reduce(lambda a, b: a.strip() + "\n" + b.strip(), lines)
    reader.close()
    helper.execute_cmd(repo_loc, "del tmp.txt")
    return result


def install_package_lock(repo_lock):
    "Install package-lock.json file in repo_loc"
    return helper.execute_cmd(repo_loc, "npm i --package-lock-only")


def fix_audit(repo_loc):
    """Run `npm audit fix` in repo_loc"""
    return helper.execute_cmd(repo_loc, "npm audit fix")


def fix_audit_force(repo_loc):
    """Run `npm audit fix --force` in repo_loc"""
    return helper.execute_cmd(repo_loc, "npm audit fix --force")


def deduplicate(repo_loc, cmd, audit_step, needs_install):
    """Deduplicate the repository using `cmd`"""
    if audit_step == constants.AUDIT_STEP_INIT:
        ddp_result = helper.execute_cmd(repo_loc, cmd)
    elif audit_step == constants.AUDIT_STEP_INSTALL:
        install_package_lock(repo_loc)
        ddp_result = helper.execute_cmd(repo_loc, cmd)
    elif audit_step == constants.AUDIT_STEP_FIX:
        if needs_install:
            install_package_lock(repo_loc)
        fix_audit(repo_loc)
        ddp_result = helper.execute_cmd(repo_loc, cmd)
    elif audit_step == constants.AUDIT_STEP_FORCE_FIX:
        if needs_install:
            install_package_lock(repo_loc)
        fix_audit(repo_loc)
        fix_audit_force(repo_loc)
        ddp_result = helper.execute_cmd(repo_loc, cmd)
    else:
        ddp_result = ["", ""]

    return ddp_result


def get_package_lock_json(repo_loc):
    """Get content of package-lock.json file from the repository"""
    if not os.path.exists(os.path.join(repo_loc, "package-lock.json")):
        return ""

    reader = open(os.path.join(repo_loc, "package-lock.json"),
                  "r", encoding="utf-8")
    lines = reader.readlines()
    result = reduce(lambda a, b: a.strip() + "\n" + b.strip(), lines)
    reader.close()
    return result


if __name__ == "__main__":
    """Run `npm ddp` on repositories having no vulnerabilities"""

    reader = open(os.path.join(
        "results", "audit_checker", "audit_results.txt"), "r", encoding="utf-8")
    lines = reader.readlines()[1:]
    reader.close()
    dict_repo_step, dict_needs_install = get_repo_step(lines)

    dataset_path = helper.get_config("PATHS", "DATASET_PATH")
    repos = helper.get_repos(os.path.join(".", "data", "npm_rank_sorted.txt"))

    # Keep only repos that are fixable by npm audit or already fixed
    repos = get_fixable_repos(repos, dict_repo_step)

    repos_sz = len(repos)

    writer = open(os.path.join("results", "ddp_checker",
                               "ddp_results.txt"), "w", encoding="utf-8")
    writer.write(
        "Repository\tStatus After Deduplication\tPackage-Lock Status\tNote")
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
                1. Record `npm ls` result before deduplication
                2. Run `npm ddp` and `npm dedupe`
                3. Record `npm ls --all` result before deduplication
                4. If 1. & 3. gave different result, report it
                """

                result = {"name": repo["name"],
                          "duplicates": "Same", "package-lock": "Same", "note": ""}

                before_ddp = get_npm_ls(repo_loc)
                package_lock_before_ddp = get_package_lock_json(repo_loc)
                ddp_result = deduplicate(
                    repo_loc, "npm ddp", dict_repo_step[repo["name"]], dict_needs_install[repo["name"]])
                # TODO: Uncomment if npm dedupe is different
                # dedupe_result = deduplicate(
                #     repo_loc, "npm dedupe", dict_repo_step[repo["name"]], dict_needs_install[repo["name"]])
                after_ddp = get_npm_ls(repo_loc)
                package_lock_after_ddp = get_package_lock_json(repo_loc)

                if before_ddp.strip() != after_ddp.strip():
                    result["duplicates"] = "Changed"

                if package_lock_before_ddp.strip() != package_lock_after_ddp.strip():
                    result["package-lock"] = "Changed"

                if constants.DDP_CHECKER_EMPTY in before_ddp.upper():
                    result["note"] += "*Empty Before*"
                if constants.DDP_CHECKER_UNMET_DEPENDENCY in before_ddp.upper():
                    result["note"] += "*Has %s Unmet Dependency Before*" % int(
                        before_ddp.count(constants.DDP_CHECKER_UNMET_DEPENDENCY))

                if constants.DDP_CHECKER_EMPTY in after_ddp.upper():
                    result["note"] += "*Empty After*"
                if constants.DDP_CHECKER_UNMET_DEPENDENCY in after_ddp.upper():
                    result["note"] += "*Has %s Unmet Dependency After*" % int(
                        after_ddp.count(constants.DDP_CHECKER_UNMET_DEPENDENCY))

                writer = open(os.path.join("results", "ddp_checker",
                                           "ddp_results.txt"), "a", encoding="utf-8")
                writer.write(
                    "%s\t%s\t%s\t%s" % (
                        str(result["name"]),
                        str(result["duplicates"]),
                        str(result["package-lock"]),
                        str(result["note"])
                    ))
                writer.write("\n")
                writer.close()

                foldername = os.path.join(
                    "results", "ddp_checker", repo["name"])

                helper.record(foldername, "before_ddp.txt",
                              before_ddp)
                helper.record(foldername, "package_lock_before.txt",
                              package_lock_before_ddp)
                helper.record(foldername, "ddp_result.txt",
                              ddp_result[1])
                # TODO: Uncomment if npm dedupe is different
                # helper.record(foldername, "dedupe_result.txt",
                #               dedupe_result[1])
                helper.record(foldername, "after_ddp.txt",
                              after_ddp)
                helper.record(
                    foldername, "package_lock_after_ddp.txt", package_lock_after_ddp)

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
