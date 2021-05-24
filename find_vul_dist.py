import os

from semantic_version.base import NpmSpec, SimpleSpec, Version
import helper
import constants
import semantic_version


def get_lib_mappings(libs, dict_lib_count, dict_lib_ver_count,
                     dict_severity_count, filename, repo, dict_repo_of_lib):
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
                    dict_repo_of_lib[lib_info[0]][lib_info[1]].append(repo)
                else:
                    dict_lib_ver_count[lib_info[0]][lib_info[1]] = 1
                    dict_repo_of_lib[lib_info[0]][lib_info[1]] = [repo]
            else:
                libs.append(lib_info[0])
                dict_lib_count[lib_info[0]] = 1
                dict_lib_ver_count[lib_info[0]] = {lib_info[1]: 1}
                dict_repo_of_lib[lib_info[0]] = {lib_info[1]: [repo]}

    return libs, dict_lib_count, dict_lib_ver_count, dict_severity_count, dict_repo_of_lib


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


def get_overlaps(dict_fixed, dict_unfixed):
    """Find library versions which are both in fixable and unfixable list"""
    lib_vers = []

    for lib in dict_fixed:
        if lib in dict_unfixed:
            for ver in dict_fixed[lib]:
                if ver in dict_unfixed[lib]:
                    lib_vers.append({"lib": lib, "ver": ver})

    return lib_vers


def get_levels(npm_ls_file, lib_to_track, ver_range):
    """Find all the unique levels of `lib_to_track` in `ver_range` from `npm_ls_file`'s dependency tree"""
    reader = open(npm_ls_file, "r", encoding="utf-8")
    # No need to process the local directory line
    lines = reader.readlines()[1:]
    reader.close()

    levels = []

    for line in lines:
        line = line.replace("\n", "")
        if lib_to_track in line:
            if constants.DDP_CHECKER_UNMET_DEPENDENCY in line:
                levels.append(constants.DDP_CHECKER_UNMET_DEPENDENCY)
            elif constants.DDP_DEDUPED in line:
                # levels.append(constants.DDP_DEDUPED)
                pass
            else:
                version = line.split("@")[-1].replace("\n", "")
                if Version(version) in NpmSpec(ver_range):
                    # -4 is to get rid of first ├─┬ part
                    # / 2 is because each level has a difference of 2
                    lvl = int((line.index(lib_to_track) - 4) / 2) + 1
                    levels.append(str(lvl))

    levels = list(set(levels))
    return levels


def list_to_str(lst):
    """Converts list to a comma separated string wrapped by []"""
    str_lst = ""
    for elm in lst:
        if str_lst == "":
            str_lst = str(elm)
        else:
            str_lst += ", " + str(elm)

    return "[" + str_lst + "]"


if __name__ == "__main__":
    """Find library distribution for unfixable and fixable audit failure repositories"""

    reader = open(os.path.join(
        "results", "audit_checker", "audit_results.txt"), "r", encoding="utf-8")
    lines = reader.readlines()[1:]
    reader.close()

    dataset_path = helper.get_config("PATHS", "DATASET_PATH")
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
    dict_repo_of_lib_UNFIXED = {}

    fix_failed_repos = []
    for repo in unfixables:
        try:
            if fixing_failed(repo):
                fix_failed_repos.append(repo["name"])
            else:
                unfixable_libs, dict_lib_count_UNFIXED, dict_lib_ver_count_UNFIXED, dict_severity_count_UNFIXED, dict_repo_of_lib_UNFIXED = get_lib_mappings(
                    unfixable_libs, dict_lib_count_UNFIXED,
                    dict_lib_ver_count_UNFIXED, dict_severity_count_UNFIXED,
                    os.path.join("results", "audit_checker",
                                 repo["name"], "after_fix_force.txt"),
                    repo, dict_repo_of_lib_UNFIXED
                )

        except Exception as ex:
            print(ex)

    print("Audit fixing threw errors for %s out of %s unfixable repos: %s\n" % (
        len(fix_failed_repos), len(unfixables), fix_failed_repos
    ))

    """Process Fixable Repos"""
    fixable_libs = []
    dict_lib_count_FIXED = {}
    dict_lib_ver_count_FIXED = {}
    dict_severity_count_FIXED = {}
    dict_repo_of_lib_FIXED = {}

    for repo in fixables:
        try:
            if "Vul Found" in repo["initial"] or "Vul Found" in repo["package-lock"]:
                audit_file_path = os.path.join(
                    "results", "audit_checker", repo["name"])

                if "Vul Found" in repo["initial"]:
                    audit_file_path = os.path.join(
                        audit_file_path, "init_audit.txt")
                elif "Vul Found" in repo["package-lock"]:
                    audit_file_path = os.path.join(
                        audit_file_path, "after_i_lock.txt")

                fixable_libs, dict_lib_count_FIXED, dict_lib_ver_count_FIXED, dict_severity_count_FIXED, dict_repo_of_lib_FIXED = get_lib_mappings(
                    fixable_libs, dict_lib_count_FIXED, dict_lib_ver_count_FIXED, dict_severity_count_FIXED,
                    audit_file_path, repo, dict_repo_of_lib_FIXED
                )

        except Exception as ex:
            print(ex)

    overlapped_lib_vers = get_overlaps(
        dict_repo_of_lib_FIXED, dict_repo_of_lib_UNFIXED)

    print("Total overlaps: %s" % len(overlapped_lib_vers))

    writer = open(os.path.join(".", "results", "audit_checker",
                               "audit_fail_checks.txt"), "w", encoding="utf-8")
    for lib_ver in overlapped_lib_vers:
        output = ""
        # output += "============\n"
        output += "%s\t%s\n" % (lib_ver["lib"], lib_ver["ver"])

        # output += "======\n"
        output += "FIXED\n"
        for repo in dict_repo_of_lib_FIXED[lib_ver["lib"]][lib_ver["ver"]]:
            levels = get_levels(os.path.join(
                dataset_path, "fixed_ls", repo["name"] + ".txt"), lib_ver["lib"], lib_ver["ver"])
            str_levels = list_to_str(levels)
            output += "%s\t%s\t%s\t%s\t%s\t%s\n" % (
                repo["name"], repo["initial"], repo["package-lock"],
                repo["audit-fix"], repo["audit-fix-force"], str_levels)

        # output += "======\n"
        output += "UNFIXED\n"
        for repo in dict_repo_of_lib_UNFIXED[lib_ver["lib"]][lib_ver["ver"]]:
            levels = get_levels(os.path.join(
                dataset_path, "unfixed_ls", repo["name"] + ".txt"), lib_ver["lib"], lib_ver["ver"])
            str_levels = list_to_str(levels)
            output += "%s\t%s\t%s\t%s\t%s\t%s\n" % (
                repo["name"], repo["initial"], repo["package-lock"],
                repo["audit-fix"], repo["audit-fix-force"], str_levels)

        # output += "============\n"

        writer.write(output)

    writer.close()
