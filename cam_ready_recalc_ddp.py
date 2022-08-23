import os
import helper
from tqdm import tqdm


if __name__ == "__main__":
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
