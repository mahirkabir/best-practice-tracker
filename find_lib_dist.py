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
    for repo in unfixables:
        try:
            unfixable_libs, dict_lib_count_UNFIXED, dict_lib_ver_count_UNFIXED, dict_severity_count_UNFIXED = get_lib_mappings(
                unfixable_libs, dict_lib_count_UNFIXED, dict_lib_ver_count_UNFIXED, dict_severity_count_UNFIXED,
                os.path.join("results", "audit_checker", repo["name"], "after_fix_force.txt"))

        except Exception as ex:
            print(ex)

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

    print(fixable_libs)