from types import CoroutineType
import helper
import os
from tqdm import tqdm
import constants
import re


def get_audit(repo_loc):
    """Run `npm audit` and return the result. True if no vulnerability detected"""
    result = helper.execute_cmd(repo_loc, "npm audit")
    # ommitting found from regex pattern as it doesn't always appear ***for > 0 vulnerabilities***

    vul_search_res = re.search("\d+ vulnerabilities", result[1])

    if vul_search_res:
        if "found 0 vulnerabilities" in result[1]:
            return {"status": constants.AUDIT_TRUE, "info": result[1]}
        else:
            return {"status": constants.AUDIT_FALSE, "info": result[1]}
    elif ("fix available" in result[1]) or ("Severity" in result[1]):
        return {"status": constants.AUDIT_FALSE, "info": result[1]}
    elif "npm ERR!" in result[1]:
        # If npm audit failed due to some error, we are treating it as ERR
        return {"status": constants.AUDIT_ERROR, "info": result[1]}
    else:
        return {"status": constants.AUDIT_UNKNOWN, "info": result[1]}


def install_package_lock(repo_loc):
    "Install package-lock.json file in repo_loc"
    return helper.execute_cmd(repo_loc, "npm i --package-lock-only")


def fix_audit(repo_loc):
    """Run `npm audit fix` in repo_loc"""
    return helper.execute_cmd(repo_loc, "npm audit fix")


def get_dict_auditable_repos(result_file):
    """Check if audit process can be executed for repos"""
    reader = open(result_file, "r")
    lines = reader.readlines()[1:]
    reader.close()

    dict_is_auditable = {}
    for line in lines:
        parts = line.split("\t")
        if "ERR" in parts[-1]:
            dict_is_auditable[parts[0]] = False
        else:
            dict_is_auditable[parts[0]] = True

    return dict_is_auditable


def get_tag_time(path, tag):
    """Get commit timestamp of `tag` of repository located in `path`"""
    cmd = "git log -1 --format=%ai " + tag
    result = helper.execute_cmd(path, cmd)
    return result[1].strip()


def get_tags(path, count):
    """Find top `count` tags of repository located in `path`"""

    result = helper.execute_cmd(path, "git tag")
    lines = result[1].split("\n")

    sz = len(lines)

    tags = []
    for i in range(0, sz):
        if lines[i].strip() == "":
            continue
        tags.append(
            {"tag": lines[i].strip(), "time": get_tag_time(path, lines[i].strip())})

    tags.sort(key=lambda x: x["time"], reverse=True)

    if sz < count:
        return tags[0: sz]
    else:
        return tags[0: count]


if __name__ == "__main__":
    """Check if best practices are used in package.json files"""

    dict_auditable_repos = get_dict_auditable_repos(os.path.join(
        "results", "audit_checker_all_tags", "audit_results_one_tag.txt"))

    dataset_path = helper.get_config("PATHS", "DATASET_PATH")
    org_repos = helper.get_repos(os.path.join(
        ".", "data", "npm_rank_sorted.txt"))

    repos = []
    for repo in org_repos:
        if dict_auditable_repos[repo["name"]]:
            if not os.path.isdir(os.path.join("results", "audit_checker_all_tags", repo["name"])):
                repos.append(repo)

    repos_sz = len(repos)

    dict_tags = {}

    writer = open(os.path.join("results", "audit_checker_all_tags",
                               "audit_results_all_tags.txt"), "w", encoding="utf-8")
    writer.write(
        "Repository\tTag\tInitial Audit\tAfter i package-lock\tAfter audit fix")
    writer.write("\n")
    writer.close()

    writer = open(os.path.join("results", "audit_checker_all_tags",
                               "repo_tags.txt"), "w", encoding="utf-8")
    writer.write("Repository\tTags")
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

                dict_tags[repo["name"]] = get_tags(
                    os.path.join(dataset_path, repo["name"]), 5)

                tag_writer = open(os.path.join("results", "audit_checker_all_tags",
                                               "repo_tags.txt"), "a", encoding="utf-8")
                output = repo["name"] + "\t"
                for tag in dict_tags[repo["name"]]:
                    output += tag["tag"] + "|"
                tag_writer.write(output)
                tag_writer.write("\n")

                tag_writer.close()
            except Exception as ex:
                print("Error cloning [%s]: %s" % (repo["name"], str(ex)))

        # Process each one of the cloned repositories
        for j in tqdm(range(i, left_repos)):
            repo = repos[j]

            repo_loc = os.path.join(dataset_path, repo["name"])

            if not repo["name"] in dict_tags:
                print(repo["name"] + " does not exist in dictionary")
                continue

            for tag in dict_tags[repo["name"]]:
                repo_name = repo["name"] + "-" + tag["tag"]
                helper.execute_cmd(repo_loc, "git checkout tags/" + tag["tag"])

                try:
                    """
                    1. Record `npm audit` result
                    2. If 1 gives ERR instead of vulnerabilities, install package-lock.json file
                    3. Run `npm audit fix`
                    4. Record `npm audit` result (to check if Step 3 fixed anything)
                    """

                    result = {"name": repo["name"], "tag": tag["tag"], "initial": "", "package-lock": "",
                              "audit-fix": "", "audit-fix-force": ""}
                    install_lock_output = ["", ""]
                    fix_audit_output = ["", ""]

                    init_audit_result = get_audit(repo_loc)

                    if init_audit_result["status"] == constants.AUDIT_ERROR:
                        install_lock_output = install_package_lock(repo_loc)
                        after_i_lock_result = get_audit(repo_loc)
                    else:
                        # If initial result was not an ERR, we don't do anything for after_i_lock
                        after_i_lock_result = {
                            "status": init_audit_result["status"], "info": ""}

                    if after_i_lock_result["status"] == constants.AUDIT_FALSE:
                        fix_audit_output = fix_audit(repo_loc)
                        after_fix_result = get_audit(repo_loc)
                    elif after_i_lock_result["status"] == constants.AUDIT_ERROR:
                        # If error is still there, then fixing won't solve it
                        after_fix_result = {
                            "status": constants.AUDIT_ERROR, "info": ""}
                    else:
                        # If previous result was already vulnerability-free, no need to fix anything
                        after_fix_result = {
                            "status": constants.AUDIT_TRUE, "info": ""}

                    result["initial"] = init_audit_result["status"]
                    result["package-lock"] = helper.IFF(
                        init_audit_result["status"] == after_i_lock_result["status"],
                        after_i_lock_result["status"], str(after_i_lock_result["status"]) + " " + constants.AUDIT_STEP_CHANGED)
                    result["audit-fix"] = helper.IFF(
                        after_i_lock_result["status"] == after_fix_result["status"],
                        after_fix_result["status"], str(after_fix_result["status"]) + " " + constants.AUDIT_STEP_CHANGED)

                    writer = open(os.path.join("results", "audit_checker_all_tags",
                                               "audit_results_all_tags.txt"), "a", encoding="utf-8")
                    writer.write(
                        "%s\t%s\t%s\t%s\t%s" % (
                            str(result["name"]),
                            str(result["tag"]),
                            str(result["initial"]),
                            str(result["package-lock"]),
                            str(result["audit-fix"])
                        ))
                    writer.write("\n")
                    writer.close()

                    foldername = os.path.join(
                        "results", "audit_checker_all_tags", repo["name"], tag["tag"])

                    helper.record(foldername, "init_audit.txt",
                                  init_audit_result["info"])
                    helper.record(foldername, "after_i_lock.txt",
                                  after_i_lock_result["info"])
                    helper.record(foldername, "after_fix.txt",
                                  after_fix_result["info"])

                    helper.record(
                        foldername, "install_lock_output.txt", install_lock_output[1])
                    helper.record(foldername, "fix_audit_output.txt",
                                  fix_audit_output[1])

                except Exception as ex:
                    print("Error processing [%s]: %s" %
                          (repo["name"], str(ex)))

        # Delete the (<= range_limit) repositories in dataset folder
        for j in tqdm(range(i, left_repos)):
            repo = repos[j]

            try:
                helper.remove_folder(
                    dataset_path, repo["name"])

            except Exception as ex:
                print("Error deleting [%s]: %s" % (repo["name"], str(ex)))
