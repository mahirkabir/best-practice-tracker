import os
import re
import helper
from tqdm import tqdm


def check_unused_dependencies(repo_loc):
    """Check if any unused dependency is used in repository located in repo_loc. True if no unused is used"""
    result = helper.execute_cmd(repo_loc, "npx depcheck")
    outputs = result[1].split("\n")
    outputs_sz = len(outputs)

    for i in range(0, outputs_sz - 1):
        if "Unused" in outputs[i] and "* " in outputs[i + 1]:
            return [False, result[1]]

    return [True, result[1]]


if __name__ == "__main__":
    """Generate unused library list for repositories"""
    dataset_path = helper.get_config("PATHS", "DATASET_PATH")
    repos = helper.get_repos(os.path.join(".", "data", "npm_rank_sorted.txt"))

    repos_sz = len(repos)

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
            try:
                """
                1. Record unused dependencies of repositories
                """
                ununsed_dependecies_result = check_unused_dependencies(
                    repo_loc)

                foldername = os.path.join(
                    "results", "unused_checker", repo["name"])

                helper.record(foldername, "unused_pre.txt",
                              ununsed_dependecies_result[1])

            except Exception as ex:
                print("Error processing [%s]: %s" % (repo["name"], str(ex)))

        # Delete the (<= range_limit) repositories in dataset folder
        for j in tqdm(range(i, left_repos)):
            repo = repos[j]

            try:
                helper.remove_folder(
                    dataset_path, repo["name"])

            except Exception as ex:
                print("Error deleting [%s]: %s" % (repo["name"], str(ex)))


if __name__ == "__main__org":
    """Find distribution of unused libraries among repositories"""
    folder = os.path.join("results", "unused_checker")
    repos = os.listdir(folder)

    dict_unused = {}
    tot_npm_libs = 0
    tot_local_libs = 0

    for repo in repos:
        unused_info = os.path.join(folder, repo, "unused_pre.txt")
        reader = open(unused_info, "r", encoding="utf-8")
        lines = reader.readlines()
        reader.close()

        for line in lines:
            line = line.strip()
            m = re.search("\* .*", line)

            if m:
                lib = m.group(0).replace("* ", "")
                if ": " in lib:
                    # library_name: location is the format for local libraries. We are ignoring them for now
                    tot_local_libs += 1
                    continue
                else:
                    tot_npm_libs += 1

                if lib in dict_unused:
                    dict_unused[lib] += 1
                else:
                    dict_unused[lib] = 1

    print(dict_unused)
    print(tot_npm_libs)
    print(tot_local_libs)
