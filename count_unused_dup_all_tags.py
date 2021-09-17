import os
import re
from tqdm import tqdm
import helper


def get_repo_tags(path):
    """Find repo tags from `path`"""
    reader = open(path, "r", encoding="utf-8")
    lines = reader.readlines()
    reader.close()

    dict_repo_tags = {}
    for line in lines:
        parts = line.split("\t")
        dict_repo_tags[parts[0]] = []
        tags = parts[1].replace("\n", "").split("|")
        for tag in tags:
            if tag != "":
                dict_repo_tags[parts[0]].append(tag)

    return dict_repo_tags


def count_duplicates(npm_ls_path):
    """Count number of duplicates from `npm_ls_path` file"""
    reader = open(npm_ls_path, "r", encoding="utf-8")
    lines = reader.readlines()
    reader.close()

    cnt = 0
    dict_dups = {}
    duplicates = ""

    for line in lines:
        if "deduped" in line:
            continue

        line = line.replace("\n", "")
        m = re.search("\w.*@\d\.\d.\d", line)
        if m:
            library_version = m.group(0)  # library@version
            library = library_version.split("@")[0]
            if library in dict_dups:
                cnt += 1
                dict_dups[library] += 1
            else:
                dict_dups[library] = 1

            if dict_dups[library] == 2:
                # List the duplicates when it's found the second time
                duplicates += library + "\n"

    if len(duplicates) > 0:
        duplicates = duplicates[0:len(duplicates) - 1]  # Removing last \n
    return cnt, duplicates


def count_unused(path):
    """Count number of unused dependencies in `path`"""
    reader = open(path, "r")
    lines = reader.readlines()
    reader.close()

    unused = False
    cnt = 0
    for line in lines:
        if "* " not in line:
            if "Unused" in line:
                unused = True
            else:
                unused = False
        elif unused:
            cnt += 1

    return cnt


if __name__ == "__main__":
    """Count unused and duplicate dependencies for 5 tags"""

    dict_repo_tags = get_repo_tags(os.path.join(
        ".", "repo_tags.txt"))

    print("Counting Duplicate Dependencies")
    writer_ddp = open(os.path.join(
        "results", "unused_dup_checker_all_tags", "duplicates_all_tags.txt"), "w")
    writer_ddp.write("Repository\tTag\tOriginal Duplicates\n")

    for i in range(0, 5):
        writer_ddp.write(
            "Tag order from latest-to-earliest[1-to-5]: " + str(i + 1))
        writer_ddp.write("\n")
        for repo in tqdm(dict_repo_tags):
            tag = dict_repo_tags[repo][i]
            try:
                tag_loc = os.path.join(
                    "results", "unused_dup_checker_all_tags", repo, tag)
                cnt, duplicates = count_duplicates(
                    os.path.join(tag_loc, "npm_ls.txt"))
                writer_ddp.write("%s\t%s\t%s\n" % (repo, tag, cnt))

                if duplicates != "":
                    helper.record(
                        tag_loc, "duplicates_just_lib.txt", duplicates)

            except Exception as ex:
                print(str(ex))

    writer_ddp.close()

    print("Counting Unused Dependencies")

    writer_ddp = open(os.path.join(
        "results", "unused_dup_checker_all_tags", "unused_all_tags"), "w")
    writer_ddp.write("Repository\tTag\tNo. of Unused\n")

    for i in range(0, 5):
        writer_ddp.write(
            "Tag order from latest-to-earliest[1-to-5]: " + str(i + 1))
        writer_ddp.write("\n")
        for repo in tqdm(dict_repo_tags):
            tag = dict_repo_tags[repo][i]
            try:
                tag_loc = os.path.join(
                    "results", "unused_dup_checker_all_tags", repo, tag)
                cnt = count_unused(os.path.join(tag_loc, "unused.txt"))
                writer_ddp.write("%s\t%s\t%s\n" % (repo, tag, cnt))
            except Exception as ex:
                print(str(ex))

    writer_ddp.close()
