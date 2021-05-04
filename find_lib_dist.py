import os


def get_lib_mappings(libs, dict_lib_count, dict_lib_ver_count, dict_severity_count, filename):
    """Evaluate `filename` and find out updated library version frequency and audit severity frequency"""

    reader = open(filename, "r", encoding="utf-8")
    lines = reader.readlines()
    reader.close()

    for i in range(len(lines)):
        line = lines[i]
        if "Severity: " in line:
            line = line.replace("\n", "").strip()
            severity = line.split(" ")[1]  # e.g. - Severity: high => high
            if severity in dict_severity_count:
                dict_severity_count[severity] += 1
            else:
                dict_severity_count[severity] = 1

            # e.g. - cookie-signature  <=1.0.5 => [cookie-signature, <=1.0.5]
            prev_line = lines[i - 1].replace("\n", "").strip()
            lib_info = prev_line.split("  ")

            # if lib_info[0] == "prismjs" and lib_info[1] == "<1.23.0":
            #     print("")

            if lib_info[0] in dict_lib_count:
                dict_lib_count[lib_info[0]] += 1
                if lib_info[1] in dict_lib_ver_count[lib_info[0]]:
                    dict_lib_ver_count[lib_info[0]][lib_info[1]] += 1
                else:
                    dict_lib_ver_count[lib_info[0]][lib_info[1]] = 1
            else:
                libs.append(lib_info[0])
                dict_lib_count[lib_info[0]] = 1
                dict_lib_ver_count[lib_info[0]] = {lib_info[1]: 1}

    return libs, dict_lib_count, dict_lib_ver_count, dict_severity_count


def has_error_in_file(filename):
    """Check if filename has `npm ERR!` in it"""
    reader = open(filename, "r", encoding="utf-8")
    lines = reader.readlines()
    reader.close()
    for line in lines:
        if "npm ERR!" in line:
            return True
    return False


def fixing_failed(repo):
    """Return `True` if the `audit fix` or `audit fix --force` operation had `npm ERR!`"""
    if has_error_in_file(os.path.join("results", "audit_checker",
                                      repo["name"], "fix_audit_output.txt")):
        return True
    else:
        return has_error_in_file(os.path.join("results", "audit_checker",
                                              repo["name"], "force_fix_audit_output.txt"))


if __name__ == "__main__":
    """Find library distribution for unfixable and fixable audit failure repositories"""

    reader = open(os.path.join(
        "results", "audit_checker", "audit_results.txt"), "r", encoding="utf-8")
    lines = reader.readlines()[1:]
    reader.close()

    unfixables = []
    fixables = []

    for line in lines:
        parts = line.split("\t")
        repo = {"name": parts[0], "initial": parts[1], "package-lock": parts[2],
                "audit-fix": parts[3], "audit-fix-force": parts[4].replace("\n", "")}
        if "Vul Found" in repo["audit-fix-force"]:
            unfixables.append(repo)
        elif "No Vul" in repo["audit-fix-force"]:
            fixables.append(repo)

    """Process Unfixable Repos"""
    unfixable_libs = []
    dict_lib_count_UNFIXED = {}
    dict_lib_ver_count_UNFIXED = {}
    dict_severity_count_UNFIXED = {}

    fix_failed_repos = []
    for repo in unfixables:
        try:
            if fixing_failed(repo):
                fix_failed_repos.append(repo["name"])
            else:
                unfixable_libs, dict_lib_count_UNFIXED, dict_lib_ver_count_UNFIXED, dict_severity_count_UNFIXED = get_lib_mappings(
                    unfixable_libs, dict_lib_count_UNFIXED, dict_lib_ver_count_UNFIXED, dict_severity_count_UNFIXED,
                    os.path.join("results", "audit_checker", repo["name"], "after_fix_force.txt"))

        except Exception as ex:
            print(ex)

    print("Audit fixing threw errors for %s out of %s unfixable repos: %s\n" % (
          str(len(fix_failed_repos)), str(len(unfixables)), fix_failed_repos))

    """Process Fixable Repos"""
    fixable_libs = []
    dict_lib_count_FIXED = {}
    dict_lib_ver_count_FIXED = {}
    dict_severity_count_FIXED = {}
    for repo in fixables:
        try:
            if "Vul Found" in repo["initial"]:
                fixable_libs, dict_lib_count_FIXED, dict_lib_ver_count_FIXED, dict_severity_count_FIXED = get_lib_mappings(
                    fixable_libs, dict_lib_count_FIXED, dict_lib_ver_count_FIXED, dict_severity_count_FIXED,
                    os.path.join("results", "audit_checker", repo["name"], "init_audit.txt"))
            elif "Vul Found" in repo["package-lock"]:
                fixable_libs, dict_lib_count_FIXED, dict_lib_ver_count_FIXED, dict_severity_count_FIXED = get_lib_mappings(
                    fixable_libs, dict_lib_count_FIXED, dict_lib_ver_count_FIXED, dict_severity_count_FIXED,
                    os.path.join("results", "audit_checker", repo["name"], "after_i_lock.txt"))
            else:
                pass

        except Exception as ex:
            print(ex)

    overlapped_cnt = 0
    nonoverlapped_cnt = 0
    for lib in dict_lib_ver_count_FIXED:
        if lib in dict_lib_ver_count_UNFIXED:
            cnt = 0
            str = ""
            for ver in dict_lib_ver_count_FIXED[lib]:
                if ver in dict_lib_ver_count_UNFIXED[lib]:
                    cnt += 1
                    str += ver + ",,, "
                    overlapped_cnt += 1
                else:
                    nonoverlapped_cnt += 1

            if str != "":
                str = lib + ": " + str
                print(str)
                print("%s out of %s version of %s had overlap\n" %
                      (cnt, len(dict_lib_ver_count_FIXED[lib]), lib))
        else:
            nonoverlapped_cnt += len(dict_lib_ver_count_FIXED[lib])

    print("%s library versions were both in unfixable and fixable vulneraility list" %
          overlapped_cnt)

    print("%s library versions were either in unfixable or fixable vulneraility list" %
          nonoverlapped_cnt)
