from types import CoroutineType
import helper
import os
from tqdm import tqdm
import re


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


def count_unused(content):
    """Find number of unused dependencies in `content`"""
    try:
        cnt = 0
        lines = content.split("\n")

        for line in lines:
            if "* " in line and not ": " in line:
                cnt += 1
            if "Path . does not contain a package.json file" in line:
                cnt = -2
                break

        return cnt
    except:
        return -1


def count_duplicate(content):
    """Find number of vulnerable dependencies in `content`"""
    try:
        cnt = 0
        dict_dups = {}

        lines = content.split("\n")
        duplicates = ""

        for line in lines:
            if not "deduped" in line:
                line = line.replace("\n", "")
                m = re.search("\w.*@\d\.\d.\d", line)
                if m:
                    library_version = m.group(0)  # library@version
                    if library_version in dict_dups:
                        cnt += 1
                        dict_dups[library_version] += 1
                    else:
                        dict_dups[library_version] = 1

                    if dict_dups[library_version] == 2:
                        # List the duplicates when it's found the second time
                        duplicates += library_version + "\n"

        if len(duplicates) > 0:
            duplicates = duplicates[0:len(duplicates) - 1]  # Removing last \n
        return cnt, duplicates
    except:
        return -1, ""


if __name__ == "__main__":
    """Check if best practices are used in package.json files"""

    reader = open(os.path.join(".", "repo_tags.txt"), "r", encoding="utf-8")
    lines = reader.readlines()[1:]
    reader.close()
    dict_tags = {}
    for line in lines:
        line = line.strip()
        parts = line.split("\t")
        dict_tags[parts[0]] = parts[1][0: len(parts[1]) - 1].split("|")

    dataset_path = helper.get_config("PATHS", "DATASET_PATH")
    org_repos = helper.get_repos(os.path.join(
        ".", "data", "npm_rank_sorted.txt"))

    repos = []
    for repo in org_repos:
        if repo["name"] in dict_tags:
            repos.append(repo)

    repos_sz = len(repos)

    unused_writer = open(os.path.join("results", "unused_dup_checker_all_tags",
                                      "unused_results_all_tags.txt"), "w", encoding="utf-8")
    unused_writer.write(
        "Repository\tTag\tNo. Of. Unused")
    unused_writer.write("\n")
    unused_writer.close()

    dup_writer = open(os.path.join("results", "unused_dup_checker_all_tags",
                                   "dup_results_all_tags.txt"), "w", encoding="utf-8")
    dup_writer.write(
        "Repository\tTag\tNo. Of. Duplicates")
    dup_writer.write("\n")
    dup_writer.close()

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

            for tag in dict_tags[repo["name"]]:
                helper.execute_cmd(repo_loc, "git checkout tags/" + tag)

                try:
                    """
                    1. Record number of unused dependencies for each tag
                    2. Record number of duplicate dependencies for each tag
                    """
                    unused_result = helper.execute_cmd(
                        repo_loc, "npx depcheck")
                    npm_i_result = helper.execute_cmd(repo_loc, "npm i")
                    duplicate_result = helper.execute_cmd(
                        repo_loc, "npm ls --all")

                    cnt_unused = count_unused(unused_result[1])
                    cnt_duplicate, duplicates = count_duplicate(
                        duplicate_result[1])

                    unused_writer = open(os.path.join("results", "unused_dup_checker_all_tags",
                                                      "unused_results_all_tags.txt"), "a", encoding="utf-8")
                    unused_writer.write(
                        "%s\t%s\t%s" % (repo["name"], tag, cnt_unused))
                    unused_writer.write("\n")
                    unused_writer.close()

                    dup_writer = open(os.path.join("results", "unused_dup_checker_all_tags",
                                                   "dup_results_all_tags.txt"), "a", encoding="utf-8")
                    dup_writer.write(
                        "%s\t%s\t%s" % (repo["name"], tag, cnt_duplicate))
                    dup_writer.write("\n")
                    dup_writer.close()

                    foldername = os.path.join(
                        "results", "unused_dup_checker_all_tags", repo["name"], tag)

                    helper.record(foldername, "unused.txt",
                                  unused_result[1])
                    helper.record(foldername, "npm_i.txt",
                                  npm_i_result[1])
                    helper.record(foldername, "npm_ls.txt",
                                  duplicate_result[1])
                    helper.record(foldername, "duplicates.txt",
                                  duplicates)

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

# TODO: Group the results based on the tags like audit results
