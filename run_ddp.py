import re
import helper
import os
from tqdm import tqdm


def get_ddp_ok_repos():
    """Get all the repos for which ddp can be succesfully run"""
    reader = open(os.path.join(
        "results", "unused_dup_checker_all_tags", "duplicates_all_tags.txt"))
    lines = reader.readlines()[2:773]
    reader.close()

    repos = []
    for line in lines:
        repos.append(line.split("\t")[0])
    return repos


if __name__ == "__main__":
    """Run `npm dedupe`. Check duplicates before and after running `npm dedupe`"""
    dataset_path = helper.get_config("PATHS", "DATASET_PATH")
    result_path = helper.get_config("PATHS", "RESULTS_PATH")
    result_path = os.path.join(result_path, "ddp_results")

    ddp_ok_repos = get_ddp_ok_repos()
    for repo in tqdm(ddp_ok_repos):
        """
        1. Check test result
        2. Record npm ls --all output
        3. Run `npm dedupe`
        4. Record npm ls --all output
        5. Check test result
        """
        try:
            repo_path = os.path.join(
                dataset_path, "test_check_after_ddp_fix", repo)

            if not os.path.exists(os.path.join(result_path, repo)):
                if repo == "webpacknodeexternals" or repo == "nib" or repo == "jszip":
                    continue

                # test_result_before = helper.execute_cmd(
                #     repo_path, "npm run test")
                npm_ls_before = helper.execute_cmd(repo_path, "npm ls --all")
                npm_dedupe_result = helper.execute_cmd(repo_path, "npm dedupe")
                npm_ls_after = helper.execute_cmd(repo_path, "npm ls --all")
                # test_result_after = helper.execute_cmd(
                #     repo_path, "npm run test")                                                                                           





















                # helper.record(os.path.join(result_path, repo),
                #               "test_before.txt", test_result_before[1])
                helper.record(os.path.join(result_path, repo),
                              "npm_ls_before.txt", npm_ls_before[1])
                helper.record(os.path.join(result_path, repo),
                              "dedupe_result.txt", npm_dedupe_result[1])
                helper.record(os.path.join(result_path, repo),
                              "npm_ls_after.txt", npm_ls_after[1])
                # helper.record(os.path.join(result_path, repo),
                #               "test_after.txt", test_result_after[1])
        except Exception as ex:
            print(repo + " " + str(ex))
