from tqdm import tqdm, tqdm_notebook
import helper
import os


if __name__ == "__main__":
    dataset_path = helper.get_config("PATHS", "DATASET_PATH")

    if False:
        src = os.path.join(dataset_path, "originals")
        dest = os.path.join(dataset_path, "test_check_after_ddp")

        dirs = os.listdir(src)

    if False:
        for dir in tqdm(dirs):
            try:
                if not os.path.isdir(os.path.join(dest, dir)):
                    helper.copy_folder(os.path.join(src, dir),
                                       os.path.join(dest, dir))
            except Exception as ex:
                print(str(dir) + " " + str(ex))

    if False:
        reader = open("test.txt", "r")
        lines = reader.readlines()[1:]
        reader.close()

        cnt_dups = 0

        dict_repos = {}

        for line in lines:
            parts = line.split("\t")

            if int(parts[1]) > 0:
                cnt_dups += 1
                dict_repos[parts[0]] = True

        print(cnt_dups)

        src = os.path.join(dataset_path, "test_check_after_ddp")
        for dir in tqdm(dirs):
            try:
                if not dir in dict_repos:
                    helper.remove_folder(root=src, folder=dir)
            except Exception as ex:
                print(str(dir) + " " + str(ex))

    if False:
        """Activate when necessary"""
        for dir in tqdm(dirs):
            helper.remove_folder(dest, dir)

    if True:
        src = os.path.join(dataset_path, "test_check_after_ddp")
        result = os.path.join(dataset_path, "..", "results",
                              "ddp_results", "latest_tag")

        dirs = os.listdir(src)

        for dir in tqdm(dirs):
            path = os.path.join(src, dir)
            result_path = os.path.join(result, dir)
            # MOST IMPORTANT: How many dedupe removes
            result_npm_i = helper.execute_cmd(path, "npm i")
            # result_ls_init = helper.execute_cmd(path, "npm ls --all")
            result_test_init = helper.execute_cmd(path, "npm run test")
            result_ddp = helper.execute_cmd(path, "npm dedupe")
            result_ls_after = helper.execute_cmd(path, "npm ls --all")
            result_test_after = helper.execute_cmd(path, "npm run test")

            helper.record(result_path, "npm_i.txt", result_npm_i[1])
            # helper.record(result_path, "npm_ls_init.txt", result_ls_init[1])
            helper.record(result_path, "npm_test_init.txt",
                          result_test_init[1])
            helper.record(result_path, "npm_ddp.txt", result_ddp[1])
            helper.record(result_path, "npm_ls_after.txt", result_ls_after[1])
            helper.record(result_path, "npm_test_after.txt",
                          result_test_after[1])

    if False:
        src = os.path.join(dataset_path, "test_check_after_audit_fix")
        result = os.path.join(dataset_path, "..", "results",
                              "audit_results", "latest_tag")

        dirs = os.listdir(src)

        for dir in tqdm(dirs):
            path = os.path.join(src, dir)
            result_path = os.path.join(result, dir)

            result_npm_i = helper.execute_cmd(
                path, "npm i --package-lock-only")
            result_test_init = helper.execute_cmd(path, "npm run test")
            result_audit_fix = helper.execute_cmd(path, "npm audit fix")
            result_test_after = helper.execute_cmd(path, "npm run test")

            helper.record(result_path, "npm_i.txt", result_npm_i[1])
            helper.record(result_path, "npm_test_init.txt",
                          result_test_init[1])
            helper.record(result_path, "npm_audit_fix.txt",
                          result_audit_fix[1])
            helper.record(result_path, "npm_test_after.txt",
                          result_test_after[1])
