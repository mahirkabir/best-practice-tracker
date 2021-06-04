import helper
import os
from tqdm import tqdm


def get_directory_size(directory):
    """Return the `directory` size in bytes.
    https://www.thepythoncode.com/article/get-directory-size-in-bytes-using-python
    """
    total = 0
    try:
        # print("[+] Getting the size of", directory)
        for entry in os.scandir(directory):
            if entry.is_file():
                # if it's a file, use stat() function
                total += entry.stat().st_size
            elif entry.is_dir():
                # if it's a directory, recursively call this function
                total += get_directory_size(entry.path)
    except NotADirectoryError:
        # if `directory` isn't a directory, get the file size then
        return os.path.getsize(directory)
    except PermissionError:
        # if for whatever reason we can't open the folder, return 0
        return 0
    return total


def get_size_format(b, factor=1024, suffix="B"):
    """
    Scale bytes to its proper byte format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    https://www.thepythoncode.com/article/get-directory-size-in-bytes-using-python
    """
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if b < factor:
            return f"{b:.2f}{unit}{suffix}"
        b /= factor
    return f"{b:.2f}Y{suffix}"


if __name__ == "__main__":
    """Check the node_modules size before and after `npm ddp`"""

    dataset_path = helper.get_config("PATHS", "DATASET_PATH")
    repos = helper.get_repos(os.path.join(".", "data", "npm_rank_sorted.txt"))

    repos_sz = len(repos)

    writer = open(os.path.join("results", "ddp_checker",
                               "ddp_size.txt"), "w", encoding="utf-8")
    writer.write(
        "Repository\tInitial Size\tAfter DDP")
    writer.write("\n")
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
                2. Record fresh node_modules folder size
                3. Run `npm ddp`
                4. Record fresh node_modules folder size again
                """

                result = {"name": repo["name"], "initial": "", "after-ddp": ""}
                writer = open(os.path.join("results", "ddp_checker",
                                           "ddp_size.txt"), "a", encoding="utf-8")

                helper.execute_cmd(repo_loc, "npm i")
                result["initial"] = get_size_format(
                    get_directory_size(os.path.join(repo_loc, "node_modules")))
                os.rename(os.path.join(repo_loc, "node_modules"),
                          os.path.join(repo_loc, "node_modules_v1"))

                helper.execute_cmd(repo_loc, "npm ddp")
                helper.execute_cmd(repo_loc, "npm i")
                result["after-ddp"] = get_size_format(
                    get_directory_size(os.path.join(repo_loc, "node_modules")))

            except Exception as ex:
                print("Error processing [%s]: %s" % (repo["name"], str(ex)))
            finally:
                writer.write(
                    "%s\t%s\t%s" % (
                        str(result["name"]),
                        str(result["initial"]),
                        str(result["after-ddp"])
                    ))
                writer.write("\n")
                writer.close()

        # Delete the (<= range_limit) repositories in dataset folder
        for j in tqdm(range(i, left_repos)):
            repo = repos[j]

            try:
                helper.remove_folder(
                    dataset_path, repo["name"])

            except Exception as ex:
                print("Error deleting [%s]: %s" % (repo["name"], str(ex)))
