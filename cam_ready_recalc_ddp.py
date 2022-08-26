import os
import helper
from tqdm import tqdm


if __name__ == "__main__RECALC_DUP":
    """Recalc number of duplicates"""
    repos = helper.get_repos(os.path.join(".", "data", "npm_rank_sorted.txt"))
    repo_tags = helper.get_tags("repo_tags.txt")
    dataset_path = helper.get_config("PATHS", "DATASET_PATH")
    dataset_path = os.path.join(dataset_path, "after_npm_i")

    it = 0
    for repo in tqdm(repos):
        # if it <= 763:
        #     it += 1
        #     continue
        # if repo["name"] != "chaiaspromised":
        #     continue

        try:
            repo_loc = os.path.join(dataset_path, repo["name"])
            reset_result = helper.execute_cmd(repo_loc, "git reset --hard")
            checkout_result = ""
            if repo["name"] in repo_tags and len(repo_tags[repo["name"]]["tags"]) > 0:
                checkout_result = helper.execute_cmd(
                    repo_loc, "git checkout " + repo_tags[repo["name"]]["tags"][0])
            else:
                print("No tag for: " + repo["name"])

            npm_i_result = helper.execute_cmd(
                repo_loc, "npm i --package-lock-only")
            npm_ls_str = helper.execute_cmd(repo_loc, "npm ls --all")[1]
            helper.record(os.path.join("results", "camera_ready", "dup_checker"),
                          repo["name"] + ".txt", npm_ls_str)
        except Exception as ex:
            print(str(ex) + ": " + str(repo["name"]))

        it += 1


def get_repos_with_dups(path, repos):
    """Get repos which have duplicates reported"""
    dict_has_dup = {}
    reader = open(path, "r", encoding="utf-8")
    lines = reader.readlines()
    reader.close()

    for line in lines:
        parts = line.split("\t")
        reponame = parts[0]
        cnt = parts[1]
        if int(cnt) > 0:
            dict_has_dup[reponame] = True

    new_repos = []
    for repo in repos:
        if repo["name"] in dict_has_dup:
            new_repos.append(repo)

    return new_repos

if __name__ == "__main__":
    """Recalc number of duplicates after ddp"""
    repos = helper.get_repos(os.path.join(".", "data", "npm_rank_sorted.txt"))
    repo_tags = helper.get_tags("repo_tags.txt")
    dataset_path = helper.get_config("PATHS", "DATASET_PATH")
    dataset_path = os.path.join(dataset_path, "test_check_after_ddp_fix")
    repos = get_repos_with_dups(os.path.join(
        "results", "paper_data", "dup_all_package_one_tag.txt"), repos)
    print(len(repos))

    it = 0
    for repo in tqdm(repos):
        if it <= 648:
            it += 1
            continue
        
        try:
            repo_loc = os.path.join(dataset_path, repo["name"])
            reset_result = helper.execute_cmd(repo_loc, "git reset --hard")
            checkout_result = ""
            if repo["name"] in repo_tags and len(repo_tags[repo["name"]]["tags"]) > 0:
                checkout_result = helper.execute_cmd(
                    repo_loc, "git checkout " + repo_tags[repo["name"]]["tags"][0])
            else:
                print("No tag for: " + repo["name"])

            npm_i_result = helper.execute_cmd(
                repo_loc, "npm i --package-lock-only")
            ddp_result = helper.execute_cmd(repo_loc, "npm ddp")
            npm_ls_str = helper.execute_cmd(repo_loc, "npm ls --all")[1]
            helper.record(os.path.join("results", "camera_ready", "after_ddp_checker"),
                          repo["name"] + ".txt", npm_ls_str)
        except Exception as ex:
            print(str(ex) + ": " + str(repo["name"]))

        it += 1