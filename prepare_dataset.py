import os
import helper
from tqdm import tqdm
import datetime
import re


def get_tag(output):
    """Get tag name from tag log output"""
    m = re.search("tag: .*[,)]", output)
    try:
        tag = m.group(0).split(",")[0].replace("tag: ", "").replace(")", "")
        return tag
    except Exception as ex:
        pass
    return ""


if __name__ == "__main__DOWNLOAD":
    """Download all dataset repositories and store them in (external) drive"""
    dataset_path = helper.get_config("PATHS", "DATASET_PATH")
    repos = helper.get_repos(os.path.join(
        ".", "data", "npm_rank_sorted.txt"))

    repos_sz = len(repos)

    range_limit = 50
    for i in range(0, repos_sz, range_limit):
        print("Processing repo [%s..%s]:" % (str(i), str(i + range_limit - 1)))

        # First clone the (<= range_limit) repositories in dataset folder
        left_repos = min(i + range_limit, repos_sz)
        if False:
            for j in tqdm(range(i, left_repos)):
                repo = repos[j]

                try:
                    repo["name"] = helper.clone_repo_to_dir(
                        os.path.join(dataset_path, "originals"), repo["url"], repo["name"])

                except Exception as ex:
                    print("Error cloning [%s]: %s" % (repo["name"], str(ex)))

        # Process each one of the cloned repositories
        for j in tqdm(range(i, left_repos)):
            repo = repos[j]

            repo_loc = os.path.join(dataset_path, "originals", repo["name"])

            try:
                result = helper.execute_cmd(
                    repo_loc, 'git log --tags --simplify-by-decoration --pretty="format:%ci %d"')
                lines = result[1].split("\n")

                sz = len(lines)

                tags = []
                for i in range(0, sz):
                    if lines[i].strip() == "":
                        continue

                    # commit_time = get_tag_time(repo_loc, lines[i].strip())
                    # commit_time = lines[i].split(" ")[0]
                    commit_date = lines[i].split(" ")[0]
                    lines[i] = get_tag(lines[i])
                    if lines[i] == "":
                        continue
                    # commit_date = commit_time.split(" ")[0]
                    day = commit_date.split("-")[2]
                    month = commit_date.split("-")[1]
                    year = commit_date.split("-")[0]
                    commit_date = datetime.datetime(
                        int(year), int(month), int(day))
                    threshold_date = datetime.datetime(
                        2021, 8, 4)  # Aug 04, 2021

                    if threshold_date < commit_date:
                        continue

                    tags.append(
                        {"tag": lines[i].strip(), "time": year + "-" + month + "-" + day})

                # if len(tags) < 5:
                #     continue

                tags.sort(key=lambda x: x["time"], reverse=True)
                tags = tags[0:5]
                output = repo["name"] + "\t"
                for tag in tags:
                    output += tag["tag"] + "|"

                output += "\t"
                for tag in tags:
                    output += tag["time"] + "|"

                writer = open(os.path.join(dataset_path, "..",
                                           "results", "repo_tags.txt"), "a", encoding="utf-8")
                writer.write(output)
                writer.write("\n")
                writer.close()
            except Exception as ex:
                print("Error processing [%s]: %s" %
                      (repo["name"], str(ex)))

    """
    1. Download repositories in <DATASET>/originals folder
    2. Collect top 5 tags till Aug 4, 2021 in <RESULTS>/repo_tags.txt file
    3. Create 5 (or less) copies of all repositories in <DATASET>/tags folder. Name them as tag names
    4. Reset the HEADs of <DATASET>/tags folders to the folder-name tags
    """

if __name__ == "__main__":
    """Run npm i on the downloaded repositories"""
    dataset_path = helper.get_config("PATHS", "DATASET_PATH")
    repos = helper.get_repos(os.path.join(
        ".", "data", "npm_rank_sorted.txt"))

    repos_sz = len(repos)

    range_limit = 50
    for i in range(0, repos_sz, range_limit):
        print("Processing repo [%s..%s]:" % (str(i), str(i + range_limit - 1)))

        # First clone the (<= range_limit) repositories in dataset folder
        left_repos = min(i + range_limit, repos_sz)
        # Process each one of the cloned repositories
        for j in tqdm(range(i, left_repos)):
            repo = repos[j]

            repo_loc = os.path.join(dataset_path, "after_npm_i", repo["name"])

            try:
                helper.execute_cmd(repo_loc, 'npm i')
            except Exception as ex:
                print("Error processing [%s]: %s" %
                      (repo["name"], str(ex)))
