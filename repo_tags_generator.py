import os
import helper
from tqdm import tqdm
import datetime


def get_tag_time(path, tag):
    """Get commit timestamp of `tag` of repository located in `path`"""
    cmd = "git log -1 --format=%ai " + tag
    result = helper.execute_cmd(path, cmd)
    return result[1].strip()


if __name__ == "__main__":
    """Generate repo tags and sort them based on commit time"""
    dataset_path = helper.get_config("PATHS", "DATASET_PATH")
    org_repos = helper.get_repos(os.path.join(
        ".", "data", "npm_rank_sorted.txt"))

    reader = open(os.path.join(
        "results", "audit_checker_all_tags", "repo_tags.txt"), "r", encoding="utf-8")
    lines = reader.readlines()
    reader.close()

    dict_already_generated = {}
    for line in lines:
        parts = line.split("\t")
        dict_already_generated[parts[0]] = True

    dataset_path = helper.get_config("PATHS", "DATASET_PATH")
    org_repos = helper.get_repos(os.path.join(
        ".", "data", "npm_rank_sorted.txt"))

    repos = []
    for repo in org_repos:
        if not repo["name"] in dict_already_generated:
            repos.append(repo)

    repos_sz = len(repos)

    writer = open("repo_tags.txt", "w", encoding="utf-8")
    writer.write("Repo\tTags\tTimes\n")
    writer.close()

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
                1. Generate tags for the repo
                2. Keep only tags committed till August 04, 2021
                3. Sort them based on commit time (desc)
                4. Record top 5 tags
                """
                result = helper.execute_cmd(repo_loc, "git tag")
                lines = result[1].split("\n")

                sz = len(lines)

                tags = []
                for i in range(0, sz):
                    if lines[i].strip() == "":
                        continue

                    commit_time = get_tag_time(repo_loc, lines[i].strip())
                    commit_date = commit_time.split(" ")[0]
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

                if len(tags) < 5:
                    continue

                tags.sort(key=lambda x: x["time"], reverse=True)
                tags = tags[0:5]
                output = repo["name"] + "\t"
                for tag in tags:
                    output += tag["tag"] + "|"

                output += "\t"
                for tag in tags:
                    output += tag["time"] + "|"

                writer = open("repo_tags.txt", "a", encoding="utf-8")
                writer.write(output)
                writer.write("\n")
                writer.close()

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
