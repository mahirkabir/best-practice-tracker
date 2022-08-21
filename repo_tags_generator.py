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
    dataset_path = os.path.join(dataset_path, "originals")
    repos = helper.get_repos(os.path.join(
        ".", "data", "npm_rank_sorted.txt"))

    repos_sz = len(repos)
    outputs = []

    range_limit = 50
    for i in range(0, repos_sz, range_limit):
        print("Processing repo [%s..%s]:" % (str(i), str(i + range_limit - 1)))
        left_repos = min(i + range_limit, repos_sz)

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
                    if commit_time == "":
                        # Privacy of the tag is no longer public
                        continue

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

                tags.sort(key=lambda x: x["time"], reverse=True)
                tag_cnt = min(5, len(tags))
                tags = tags[0:tag_cnt]
                output = repo["name"] + "\t"
                for tag in tags:
                    output += tag["tag"] + "|"

                output += "\t"
                for tag in tags:
                    output += tag["time"] + "|"

                outputs.append({"res": output, "cnt": tag_cnt})

            except Exception as ex:
                print("Error processing [%s]: %s" % (repo["name"], str(ex)))

    outputs.sort(key=lambda x: x["cnt"], reverse=True)
    writer = open("repo_tags.txt", "w", encoding="utf-8")
    for output in outputs:
        writer.write(output["res"] + "\n")
    writer.write("\n")
    writer.close()
