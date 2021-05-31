import os
import re
import constants
import helper


def get_packages(path):
    """Gets list of packages and their count"""
    libs = []
    dict_lib_ver_count = {}

    reader = open(path, "r", encoding="utf-8")
    lines = reader.readlines()
    reader.close()

    for line in lines:
        if "deduped" in line:
            continue  # No need to process libs already deduped

        line = line.replace("\n", "")
        m = re.search("\w.*@\d\.\d.\d", line)
        if m:
            library_version = m.group(0)  # library@version
            lib = library_version.split("@")[0]
            ver = library_version.split("@")[1]

            if lib in dict_lib_ver_count:
                if ver in dict_lib_ver_count[lib]:
                    dict_lib_ver_count[lib][ver] += 1
                else:
                    dict_lib_ver_count[lib][ver] = 1
            else:
                dict_lib_ver_count[lib] = {ver: 1}
                libs.append(lib)

    return libs, dict_lib_ver_count


def get_uniques(libs):
    """Get unique libraries and unique library-versions from list of all libraries"""
    dict_lib = {}
    dict_lib_ver = {}
    unique_libs = []
    unique_lib_vers = []

    for lib_info in libs:
        lib = lib_info["lib"]
        ver = lib_info["ver"]

        if lib in dict_lib:
            dict_lib[lib] += 1
        else:
            dict_lib[lib] = 1
            dict_lib_ver[lib] = {}
            unique_libs.append(lib)

        if ver in dict_lib_ver[lib]:
            dict_lib_ver[lib][ver] += 1
        else:
            dict_lib_ver[lib] = {ver: 1}
            unique_lib_vers.append({"lib": lib, "ver": ver})

    return unique_libs, unique_lib_vers


def make_unique(lst):
    """Make `lst` unique"""
    new_lst = []
    for elm in lst:
        if elm not in new_lst:
            new_lst.append(elm)
    return new_lst


def get_levels(npm_ls_file, lib_to_track, ver_cmp):
    """Find all the unique levels of `lib_to_track` of version `ver_cmp` from `npm_ls_file`'s dependency tree"""
    reader = open(npm_ls_file, "r", encoding="utf-8")
    # No need to process the local directory line
    lines = reader.readlines()[1:]
    reader.close()

    levels = []

    for line in lines:
        line = line.replace("\n", "")
        if " " + lib_to_track + "@" in line:
            if constants.DDP_CHECKER_UNMET_DEPENDENCY in line:
                levels.append(constants.DDP_CHECKER_UNMET_DEPENDENCY)
            elif constants.DDP_DEDUPED in line:
                # levels.append(constants.DDP_DEDUPED)
                pass
            else:
                version = line.split("@")[-1].replace("\n", "")
                if ver_cmp == version:
                    lvl = int((line.index(lib_to_track) - 4) / 2) + 1
                    levels.append(lvl)

    levels = list(set(levels))
    levels.sort()
    return levels


if __name__ == "__main__":
    """Find duplicate library distribution for unfixable and fixable ddp repositories"""

    root_ddp_folder = os.path.join("results", "ddp_checker")
    repos = os.listdir(root_ddp_folder)

    final_fixables = []
    final_unfixables = []
    final_partially_fixables = []
    final_removed_libs = []
    dict_lib_ver_repo = {}

    for repo in repos:
        """List out the list of packages before and after running npm ddp to see the difference"""
        try:
            if not os.path.isdir(os.path.join(root_ddp_folder, repo)):
                continue

            libs_pre, dict_lib_ver_count_pre = get_packages(
                os.path.join(root_ddp_folder, repo, "before_ddp.txt"))

            libs_post, dict_lib_ver_count_post = get_packages(
                os.path.join(root_ddp_folder, repo, "after_ddp.txt"))

            fixables = []
            unfixables = []
            partially_fixables = []
            removed_libs = []

            for lib in dict_lib_ver_count_pre:
                for ver in dict_lib_ver_count_pre[lib]:
                    if lib not in dict_lib_ver_repo:
                        dict_lib_ver_repo[lib] = {}
                    if ver not in dict_lib_ver_repo[lib]:
                        dict_lib_ver_repo[lib][ver] = {}

                    if not lib in dict_lib_ver_count_post:
                        removed_libs.append(lib)
                        continue

                    if ver in dict_lib_ver_count_post[lib]:
                        lib_item = {"lib": lib, "ver": ver, "count-pre": dict_lib_ver_count_pre[lib][ver],
                                    "count-post": dict_lib_ver_count_post[lib][ver]}

                        if dict_lib_ver_count_pre[lib][ver] >= 2 and dict_lib_ver_count_post[lib][ver] <= 1:
                            # if count for a library version is changed from >= 2 to <= 1 then it's fixable
                            fixables.append(lib_item)
                            dict_lib_ver_repo[lib][ver][repo] = "FIXABLE"
                        elif dict_lib_ver_count_pre[lib][ver] >= 2 and dict_lib_ver_count_post[lib][ver] >= 2:
                            unfixables.append(lib_item)
                            dict_lib_ver_repo[lib][ver][repo] = "UNFIXABLE"
                            if dict_lib_ver_count_pre[lib][ver] > dict_lib_ver_count_post[lib][ver]:
                                partially_fixables.append(lib_item)
                        else:
                            # If previously the count was <= 1 then it wasn't duplicate in the first place
                            pass
                    else:
                        # if the version is completely removed, then it's also fixable
                        fixables.append(
                            {"lib": lib, "ver": ver, "count-pre": dict_lib_ver_count_pre[lib][ver],
                             "count-post": 0})
                        dict_lib_ver_repo[lib][ver][repo] = "FIXABLE"

            final_fixables += fixables
            final_unfixables += unfixables
            final_partially_fixables += partially_fixables
            final_removed_libs += removed_libs
        except Exception as ex:
            print(str(ex))

    # print(len(final_fixables))
    # print(len(final_unfixables))
    # print(len(final_partially_fixables))
    # print(len(final_removed_libs))

    fixable_libs, fixable_lib_vers = get_uniques(final_fixables)
    unfixable_libs, unfixable_lib_vers = get_uniques(final_unfixables)
    partially_fixable_libs, partially_fixable_lib_vers = get_uniques(
        final_partially_fixables)

    # print(len(fixable_libs))
    # print(len(fixable_lib_vers))
    # print(len(unfixable_libs))
    # print(len(unfixable_lib_vers))
    # print(len(partially_fixable_libs))
    # print(len(partially_fixable_lib_vers))
    # print(len(final_removed_libs))

    overlapped_lib_vers = []
    for lib_ver in fixable_lib_vers:
        if lib_ver in unfixable_lib_vers:
            overlapped_lib_vers.append(lib_ver)

    overlapped_lib_vers = make_unique(overlapped_lib_vers)

    dataset_path = helper.get_config("PATHS", "DATASET_PATH")

    writer = open(os.path.join("results", "ddp_checker",
                               "ddp_fail_checks.txt"), "w", encoding="utf-8")

    writer.write("Total # of overlapped libraries: " +
                 str(len(overlapped_lib_vers)))
    writer.write("\n")
    cnt = len(overlapped_lib_vers)
    for lib_ver in overlapped_lib_vers:
        output = str(lib_ver["lib"] + "\t" + lib_ver["ver"] + "\n")

        try:
            for repo in dict_lib_ver_repo[lib_ver["lib"]][lib_ver["ver"]]:
                if dict_lib_ver_repo[lib_ver["lib"]][lib_ver["ver"]][repo] == "FIXABLE":
                    levels = get_levels(os.path.join(
                        dataset_path, "all_ls", repo + ".txt"), lib_ver["lib"], lib_ver["ver"])

                    output += ("%s\tFIXABLE\t%s\n" % (repo, levels))

                elif dict_lib_ver_repo[lib_ver["lib"]][lib_ver["ver"]][repo] == "UNFIXABLE":
                    levels = get_levels(os.path.join(
                        dataset_path, "all_ls", repo + ".txt"), lib_ver["lib"], lib_ver["ver"])

                    output += ("%s\tUNFIXABLE\t%s\n" % (repo, levels))

            writer.write(output)
        except Exception as ex:
            # print(ex)
            cnt -= 1

    writer.close()

    print("Checked ddp-fail reason for: " + str(cnt))
