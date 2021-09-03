import helper
import os
from tqdm import tqdm
import constants
import re


def get_dict_auditable_repos(result_file):
    """Check if audit process can be executed for repos"""
    reader = open(result_file, "r", encoding="utf-8")
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


def get_vul_count(path):
    """Count vulnerabilities from audit report"""
    reader = open(path, "r", encoding="utf-8")
    lines = reader.readlines()
    reader.close()

    cnt_severity = 0
    cnt_fix_available = 0
    has_err = False
    for line in lines:
        if "Severity" in line:
            cnt_severity += 1
        if "fix available" in line:
            cnt_fix_available += 1
        if "npm ERR!" in line:
            has_err = True

    if cnt_severity > cnt_fix_available:
        cnt = cnt_severity
    else:
        cnt = cnt_fix_available

    if has_err == True:
        cnt = "-"

    return cnt


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
            repos.append(repo)

    repos_sz = len(repos)

    reader = open(os.path.join(".", "repo_tags.txt"), "r", encoding="utf-8")
    lines = reader.readlines()
    reader.close()
    dict_tags = {}
    for line in lines:
        line = line.strip()
        parts = line.split("\t")
        dict_tags[parts[0]] = parts[1][0: len(parts[1]) - 1].split("|")

    err_cnt = 0
    dict_below_five_tags_repos = {}
    dict_atleast_one_err_repos = {}
    output = ""
    for repo in repos:
        repo_path = os.path.join(
            "results", "audit_checker_all_tags", repo["name"])
        if repo["name"] in dict_tags:
            tags = dict_tags[repo["name"]]
            tags_cnt = len(tags)
            if tags_cnt < 5:
                dict_below_five_tags_repos[repo["name"]] = {
                    "name": repo["name"], "tag_cnt": len(tags)}
                continue
            for tag in tags:
                tag_path = os.path.join(repo_path, tag)
                try:
                    init = ""
                    after_i = ""
                    after_fix = ""

                    cnt_pre = get_vul_count(
                        os.path.join(tag_path, "init_audit.txt"))
                    cnt_post = ""

                    if cnt_pre != "-":
                        if cnt_pre == 0:
                            init = "No Vul"
                            after_i = "No Vul"
                            after_fix = "No Vul"
                        elif cnt_pre > 0:
                            init = "Vul Found"
                            after_i = "Vul Found"

                            cnt_post = get_vul_count(
                                os.path.join(tag_path, "after_fix.txt"))
                            if cnt_post == 0:
                                after_fix = "No Vul (Changed)"
                            else:
                                after_fix = "Vul Found"

                    elif cnt_pre == "-":
                        init = "ERR"
                        cnt_pre = get_vul_count(
                            os.path.join(tag_path, "after_i_lock.txt"))

                        if cnt_pre == "-":
                            after_i = "ERR"
                            after_fix = "ERR"
                        elif cnt_pre == 0:
                            after_i = "No Vul (Changed)"
                            after_fix = "No Vul"
                        elif cnt_pre > 0:
                            after_i = "Vul Found (Changed)"

                            cnt_post = get_vul_count(
                                os.path.join(tag_path, "after_fix.txt"))
                            if cnt_post == 0:
                                after_fix = "No Vul (Changed)"
                            else:
                                after_fix = "Vul Found"

                    if cnt_post == "":
                        cnt_post = cnt_pre

                    if "ERR" in after_fix:
                        if repo["name"] not in dict_atleast_one_err_repos:
                            dict_atleast_one_err_repos[repo["name"]] = 0

                        dict_atleast_one_err_repos[repo["name"]] += 1
                        continue

                    output += ("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" %
                               (repo["name"], tag, cnt_pre, cnt_post, init, after_i, after_fix))
                except Exception as ex:
                    print(str(ex))

        else:
            # print(repo["name"] + " does not exist")
            err_cnt += 1
            dict_below_five_tags_repos[repo["name"]] = {
                "name": repo["name"], "tag_cnt": 0}

    writer = open(os.path.join(
        "results", "audit_checker_all_tags", "below_five_tags_repos.txt"), "w", encoding="utf-8")

    for repo_name in dict_below_five_tags_repos:
        repo = dict_below_five_tags_repos[repo_name]
        writer.write(repo["name"] + "\t" + str(repo["tag_cnt"]))
        writer.write("\n")

    writer.close()

    writer = open(os.path.join(
        "results", "audit_checker_all_tags", "atleast_one_err_repos.txt"), "w", encoding="utf-8")

    for repo in dict_atleast_one_err_repos:
        writer.write(repo)
        writer.write("\n")

    writer.close()

    writer = open(os.path.join(
        "results", "audit_checker_all_tags", "vul_count_all_tags.txt"), "w", encoding="utf-8")

    for line in output.split("\n"):
        parts = line.split("\t")
        if not (parts[0] in dict_below_five_tags_repos or parts[0] in dict_atleast_one_err_repos):
            writer.write(line)
            writer.write("\n")

    writer.close()
