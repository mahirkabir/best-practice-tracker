import os
import helper


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
    """Count audit vulnerabilities for the latest version of all packages"""

    repos = helper.get_repos(os.path.join(
        ".", "data", "npm_rank_sorted.txt"))

    root_folder = os.path.join("results", "audit_checker")

    output = ""
    for repo in repos:
        try:
            repo_path = os.path.join(
                "results", "audit_checker", repo["name"])

            init = ""
            after_i = ""
            after_fix = ""

            cnt_pre = get_vul_count(
                os.path.join(repo_path, "init_audit.txt"))
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
                        os.path.join(repo_path, "after_fix.txt"))
                    if cnt_post == 0:
                        after_fix = "No Vul (Changed)"
                    else:
                        after_fix = "Vul Found"

            elif cnt_pre == "-":
                init = "ERR"
                cnt_pre = get_vul_count(
                    os.path.join(repo_path, "after_i_lock.txt"))

                if cnt_pre == "-":
                    after_i = "ERR"
                    after_fix = "ERR"
                elif cnt_pre == 0:
                    after_i = "No Vul (Changed)"
                    after_fix = "No Vul"
                elif cnt_pre > 0:
                    after_i = "Vul Found (Changed)"

                    cnt_post = get_vul_count(
                        os.path.join(repo_path, "after_fix.txt"))
                    if cnt_post == 0:
                        after_fix = "No Vul (Changed)"
                    else:
                        after_fix = "Vul Found"

            if cnt_post == "":
                cnt_post = cnt_pre

            output += ("%s\t%s\t%s\t%s\t%s\t%s\n" %
                       (repo["name"], cnt_pre, cnt_post, init, after_i, after_fix))

        except Exception as ex:
            print(str(ex))

    writer = open(os.path.join("results", "paper_data",
                               "audit_vuls_all_package_one_tag.txt"), "w", encoding="utf-8")
    writer.write(output)
    writer.close()
