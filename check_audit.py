import helper
import os
from tqdm import tqdm
import constants
import re


def get_audit(repo_loc):
    """Run `npm audit` and return the result. True if no vulnerability detected"""
    result = helper.execute_cmd(repo_loc, "npm audit")
    # ommitting found from regex pattern as it doesn't always appear ***for > 0 vulnerabilities***

    # TODO:
    """
    "Severity: ", "fix available" - look for these strings in result[1]
    """

    vul_search_res = re.search("\d+ vulnerabilities", result[1])

    if vul_search_res:
        if "found 0 vulnerabilities" in result[1]:
            return {"status": constants.AUDIT_TRUE, "info": result[1]}
        else:
            return {"status": constants.AUDIT_FALSE, "info": result[1]}
    elif "npm ERR!" in result[1]:
        # If npm audit failed due to some error, we are treating it as ERR
        return {"status": constants.AUDIT_ERROR, "info": result[1]}
    else:
        return {"status": constants.AUDIT_UNKNOWN, "info": result[1]}


def install_package_lock(repo_lock):
    "Install package-lock.json file in repo_loc"
    return helper.execute_cmd(repo_loc, "npm i --package-lock-only")


def fix_audit(repo_loc):
    """Run `npm audit fix` in repo_loc"""
    return helper.execute_cmd(repo_loc, "npm audit fix")


def fix_audit_force(repo_loc):
    """Run `npm audit fix --force` in repo_loc"""
    return helper.execute_cmd(repo_loc, "npm audit fix --force")


if __name__ == "__main__":
    """Check if best practices are used in package.json files"""

    dataset_path = helper.get_config("PATHS", "DATASET_PATH")
    repos = helper.get_repos(os.path.join(".", "data", "npm_rank_sorted.txt"))

    repos_sz = len(repos)

    writer = open(os.path.join("results", "audit_checker",
                               "audit_results.txt"), "w", encoding="utf-8")
    writer.write(
        "Repository\tInitial Audit\tBuild-1\tAfter i package-lock\tBuild-2\tAfter audit fix\tBuild-3" +
        "\tAfter audit fix --force\tBuild-4")
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
                1. Record `npm audit` result 
                2. If 1 gives ERR instead of vulnerabilities, install package-lock.json file
                3. Run `npm audit fix`
                4. Record `npm audit` result (to check if Step 3 fixed anything)
                5. Run `npm audit fix --force`
                6. Record `npm audit` result (to check if Step 5 fixed anything)
                """

                result = {"name": repo["name"], "initial": "", "package-lock": "",
                          "audit-fix": "", "audit-fix-force": ""}
                install_lock_output = ["", ""]
                fix_audit_output = ["", ""]
                force_fix_audit_output = ["", ""]

                init_build_result = helper.build(repo_loc)
                after_install_build_result = ["-", ""]
                after_fix_build_result = ["-", ""]
                after_force_fix_build_result = ["-", ""]

                init_audit_result = get_audit(repo_loc)

                if init_audit_result["status"] == constants.AUDIT_ERROR:
                    install_lock_output = install_package_lock(repo_loc)
                    after_i_lock_result = get_audit(repo_loc)
                    after_install_build_result = helper.build(repo_loc)
                else:
                    # If initial result was not an ERR, we don't do anything for after_i_lock
                    after_i_lock_result = {
                        "status": init_audit_result["status"], "info": ""}

                if after_i_lock_result["status"] == constants.AUDIT_FALSE:
                    fix_audit_output = fix_audit(repo_loc)
                    after_fix_result = get_audit(repo_loc)
                    after_fix_build_result = helper.build(repo_loc)
                elif after_i_lock_result["status"] == constants.AUDIT_ERROR:
                    # If error is still there, then fixing won't solve it
                    after_fix_result = {
                        "status": constants.AUDIT_ERROR, "info": ""}
                else:
                    # If previous result was already vulnerability-free, no need to fix anything
                    after_fix_result = {
                        "status": constants.AUDIT_TRUE, "info": ""}

                if after_fix_result["status"] == constants.AUDIT_FALSE:
                    force_fix_audit_output = fix_audit_force(repo_loc)
                    after_fix_force_result = get_audit(repo_loc)
                    after_force_fix_build_result = helper.build(repo_loc)
                elif after_fix_result["status"] == constants.AUDIT_ERROR:
                    # If error is still there, then force fixing won't solve it
                    after_fix_force_result = {
                        "status": constants.AUDIT_ERROR, "info": ""}
                else:
                    # If previous result was already vulnerability-free, no need to fix anything
                    after_fix_force_result = {
                        "status": constants.AUDIT_TRUE, "info": ""}

                result["initial"] = init_audit_result["status"]
                result["package-lock"] = helper.IFF(
                    init_audit_result["status"] == after_i_lock_result["status"],
                    after_i_lock_result["status"], str(after_i_lock_result["status"]) + " " + constants.AUDIT_STEP_CHANGED)
                result["audit-fix"] = helper.IFF(
                    after_i_lock_result["status"] == after_fix_result["status"],
                    after_fix_result["status"], str(after_fix_result["status"]) + " " + constants.AUDIT_STEP_CHANGED)
                result["audit-fix-force"] = helper.IFF(
                    after_fix_result["status"] == after_fix_force_result["status"],
                    after_fix_force_result["status"], str(after_fix_force_result["status"]) + " " + constants.AUDIT_STEP_CHANGED)

                writer = open(os.path.join("results", "audit_checker",
                                           "audit_results.txt"), "a", encoding="utf-8")
                writer.write(
                    "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (
                        str(result["name"]),
                        str(result["initial"]),
                        str(init_build_result[0]),
                        str(result["package-lock"]),
                        str(after_install_build_result[0]),
                        str(result["audit-fix"]),
                        str(after_fix_build_result[0]),
                        str(result["audit-fix-force"]),
                        str(after_force_fix_build_result[0]),
                    ))
                writer.write("\n")
                writer.close()

                foldername = os.path.join(
                    "results", "audit_checker", repo["name"])

                helper.record(foldername, "init_audit.txt",
                              init_audit_result["info"])
                helper.record(foldername, "after_i_lock.txt",
                              after_i_lock_result["info"])
                helper.record(foldername, "after_fix.txt",
                              after_fix_result["info"])
                helper.record(foldername, "after_fix_force.txt",
                              after_fix_force_result["info"])

                helper.record(
                    foldername, "install_lock_output.txt", install_lock_output[1])
                helper.record(foldername, "fix_audit_output.txt",
                              fix_audit_output[1])
                helper.record(
                    foldername, "force_fix_audit_output.txt", force_fix_audit_output[1])

                helper.record(foldername, "init_build_result.txt",
                              init_build_result[1])
                helper.record(foldername, "after_install_build_result.txt",
                              after_install_build_result[1])
                helper.record(foldername, "after_fix_build_result.txt",
                              after_fix_build_result[1])
                helper.record(foldername, "after_force_fix_build_result.txt",
                              after_force_fix_build_result[1])

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
