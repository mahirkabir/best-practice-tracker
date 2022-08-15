from datetime import datetime
import os
import helper
from tqdm import tqdm


def repos_with_lock(repos, repo_names_with_lock):
    """Filter to get repos that have package.lock file"""
    reader = open(repo_names_with_lock, "r")
    lines = reader.readlines()
    reader.close()

    dict = {}
    for line in lines:
        repo = line.strip()
        dict[repo] = True

    ret_repos = []
    for repo in repos:
        if repo["name"] in dict:
            ret_repos.append(repo)
    return ret_repos


def get_month_num_from_name(month):
    """Get the month number from the month name"""
    dict = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
            "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
            }
    return dict[month]


def get_commit_info(repo_loc, lock_file):
    """Find first commit no. for `lock_file`"""
    commit = ""
    time = ""
    det_time = ""
    result = helper.execute_cmd(
        repo_loc, "git log --diff-filter=A -- " + lock_file)
    commit = result[1].split("\n")[0].split(" ")[1]

    parts = result[1].split("\n")
    for part in parts:
        const_str = "Date:   "
        if const_str in part:
            part = part.replace(const_str, "")
            date_parts = part.split(" ")
            month = date_parts[1]
            year = date_parts[-2]
            time = month + "||" + year

            day = date_parts[2]
            month_num = get_month_num_from_name(month)
            strdatetime = "%s-%s-%s %s" % (day, month_num, year, date_parts[3])
            det_time = datetime.strptime(strdatetime, "%d-%m-%Y %H:%M:%S")
            break

    return commit, time, det_time


def get_first_commit_time(repo_loc):
    """Get time of the first ever commit for the repo"""
    commit = ""
    time = ""
    det_time = ""
    result = helper.execute_cmd(
        repo_loc, "git log --reverse")
    commit = result[1].split("\n")[0].split(" ")[1]

    parts = result[1].split("\n")
    for part in parts:
        const_str = "Date:   "
        if const_str in part:
            part = part.replace(const_str, "")
            date_parts = part.split(" ")
            month = date_parts[1]
            year = date_parts[-2]
            time = month + "||" + year

            day = date_parts[2]
            month_num = get_month_num_from_name(month)
            strdatetime = "%s-%s-%s %s" % (day, month_num, year, date_parts[3])
            det_time = datetime.strptime(strdatetime, "%d-%m-%Y %H:%M:%S")
            break

    return commit, time, det_time


if __name__ == "__main__":
    """Check if package lock files are committed after the initial commit"""
    dataset_path = helper.get_config("PATHS", "DATASET_PATH")
    repos = helper.get_repos(os.path.join(".", "data", "npm_rank_sorted.txt"))
    repo_names_with_lock = os.path.join(
        "results", "camera_ready", "has_lock_repos.txt")
    repos = repos_with_lock(repos, repo_names_with_lock)

    writer = open(os.path.join("results", "camera_ready", "lock_info.txt"),
                  "w", encoding="utf-8")
    writer.write(
        "Repository\tLock-Commit\tLock-Period\tLock-Time\tFirst-Commit-Time\tLock-Committed-After\n")

    for repo in tqdm(repos):
        try:
            repo_loc = os.path.join(dataset_path, "originals", repo["name"])
            lock_commit, lock_time, lock_detailed_time = get_commit_info(
                repo_loc, "package-lock.json")

            _, _, first_commit_time = get_first_commit_time(repo_loc)

            is_lock_file_committed_after = False
            if lock_detailed_time > first_commit_time:
                is_lock_file_committed_after = True

            writer.write(
                "%s\t%s\t%s\t%s\t%s\t%s\n" % (
                    repo["name"],
                    lock_commit, lock_time,
                    str(lock_detailed_time), str(first_commit_time),
                    str(is_lock_file_committed_after)
                ))
        except Exception as ex:
            print(repo["name"] + ": " + str(ex))

    writer.close()
