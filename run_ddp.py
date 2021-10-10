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


if __name__ == "__main__RUN_DEDUPE":
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

            # if not os.path.exists(os.path.join(result_path, repo)):
            if True:
                # if not repo in ["webpacknodeexternals", "nib", "jszip"]:
                #     continue

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


def count_duplicates(npm_ls_path):
    """Count number of duplicates from `npm_ls_path` file"""
    reader = open(npm_ls_path, "r", encoding="utf-8")
    lines = reader.readlines()
    reader.close()

    cnt = 0
    dict_dups = {}
    duplicates = ""

    for line in lines:
        if "deduped" in line:
            continue

        line = line.replace("\n", "")
        m = re.search("\w.*@\d\.\d.\d", line)
        if m:
            library_version = m.group(0)  # library@version
            library = library_version.split("@")[0]
            if library in dict_dups:
                cnt += 1
                dict_dups[library] += 1
            else:
                dict_dups[library] = 1

            if dict_dups[library] == 2:
                # List the duplicates when it's found the second time
                duplicates += library + "\n"

    if len(duplicates) > 0:
        duplicates = duplicates[0:len(duplicates) - 1]  # Removing last \n
    return cnt, duplicates


if __name__ == "__main__":
    """Check the duplicate count before and after running `npm dedupe`"""
    result_path = helper.get_config("PATHS", "RESULTS_PATH")
    result_path = os.path.join(result_path, "ddp_results")

    dirs = os.listdir(result_path)

    writer = open(os.path.join("results", "ddp_checker",
                               "ddp_count_after.txt"), "w", encoding="utf-8")
    for dir in tqdm(dirs):
        before_cnt, _ = count_duplicates(os.path.join(
            result_path, dir, "npm_ls_before.txt"))
        after_cnt, _ = count_duplicates(os.path.join(
            result_path, dir, "npm_ls_after.txt"))
        writer.write(dir + "\t" + str(before_cnt) +
                     "\t" + str(after_cnt))

        if after_cnt > before_cnt:
            writer.write("\t^^^\n")
        elif after_cnt < before_cnt:
            writer.write("\t---\n")
        else:
            writer.write("\t***\n")

    writer.close()
