import os
import re
from sys import call_tracing


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


if __name__ == "__main__":
    """Find duplicate library distribution for unfixable and fixable ddp repositories"""

    root_ddp_folder = os.path.join("results", "ddp_checker")
    repos = os.listdir(root_ddp_folder)

    final_fixables = []
    final_unfixables = []
    final_partially_fixables = []
    final_removed_libs = []

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
                    if not lib in dict_lib_ver_count_post:
                        removed_libs.append(lib)
                        continue

                    if ver in dict_lib_ver_count_post[lib]:
                        lib_item = {"lib": lib, "ver": ver, "count-pre": dict_lib_ver_count_pre[lib][ver],
                                    "count-post": dict_lib_ver_count_post[lib][ver]}

                        if dict_lib_ver_count_pre[lib][ver] >= 2 and dict_lib_ver_count_post[lib][ver] <= 1:
                            # if count for a library version is changed from >= 2 to <= 1 then it's fixable
                            fixables.append(lib_item)
                        elif dict_lib_ver_count_pre[lib][ver] >= 2 and dict_lib_ver_count_post[lib][ver] >= 2:
                            unfixables.append(lib_item)
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

    print(len(fixable_libs))
    print(len(fixable_lib_vers))
    print(len(unfixable_libs))
    print(len(unfixable_lib_vers))
    print(len(partially_fixable_libs))
    print(len(partially_fixable_lib_vers))
    print(len(final_removed_libs))
