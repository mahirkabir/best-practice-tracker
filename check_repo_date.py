import datetime
import os
import helper
from tqdm import tqdm


def get_month_num_from_name(month):
    """Get the month number from the month name"""
    dict = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
            "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
            }
    return dict[month]


def get_current_cloned_date(repo_path):
    """Get current cloned date of the repo in `repo_path`"""
    result = helper.execute_cmd(repo_path, "git log -1")
    lines = result[1].split("\n")
    curr_date = datetime.datetime(3000, 1, 1)
    for line in lines:
        if "Date: " in line:
            parts = line.split(" ")
            month = get_month_num_from_name(parts[4])
            day = parts[5]
            year = parts[7]
            curr_date = datetime.datetime(
                int(year), int(month), int(day))
            break

    return curr_date


def get_last_date_before_threshold(repo_loc, threshold_date):
    """Get the last tag date for the repo in `repo_path` before `threshold_date`"""
    result = helper.execute_cmd(repo_loc, "git tag")
    lines = result[1].split("\n")

    sz = len(lines)

    tags = []
    for i in range(0, sz):
        if lines[i].strip() == "":
            continue

        commit_time = helper.get_tag_time(repo_loc, lines[i].strip())
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
    last_date = tags[0]["time"]

    return datetime.datetime(int(last_date.split("-")[0]),
                             int(last_date.split("-")[1]),
                             int(last_date.split("-")[2]))


if __name__ == "__main__":
    """Check commit dates of cloned repositories"""
    dataset_path = helper.get_config("PATHS", "DATASET_PATH")
    root_folder = os.path.join(dataset_path, "originals")
    dirs = os.listdir(root_folder)

    dict_repo_date = {}
    err_repos = []
    for dir in tqdm(dirs):
        try:
            repo_path = os.path.join(root_folder, dir)
            current_cloned_date = get_current_cloned_date(repo_path)
            threshold_date = datetime.datetime(
                2021, 8, 4)  # Aug 04, 2021
            last_date_before_threshold = get_last_date_before_threshold(
                repo_path, threshold_date)

            if current_cloned_date != last_date_before_threshold:
                err_repos.append(dir)
                dict_repo_date[dir] = {
                    "current": current_cloned_date, "last_date": last_date_before_threshold}
        except Exception as ex:
            print(dir + " " + str(ex))

    print(len(err_repos))

    writer = open("err_repos_date_threshold.txt", "w", encoding="utf-8")
    for repo in err_repos:
        curr = dict_repo_date[repo]["current"]
        last = dict_repo_date[repo]["last_date"]
        writer.write(
            repo + "\t" + curr.strftime("%Y-%m-%d") + "\t" + last.strftime("%Y-%m-%d"))
        writer.write("\n")
    writer.close()
