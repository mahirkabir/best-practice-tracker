import os


def get_current_repos(path):
    """Get current dataset repositories"""
    reader = open(path, "r", encoding="utf-8")
    lines = reader.readlines()
    reader.close()

    dict_current_repos = {}
    for line in lines:
        parts = line.split("\t")
        dict_current_repos[parts[0]] = True

    return dict_current_repos


def get_repo_tag_repos(path):
    """Get repos for which repo tags were generated in `path`"""
    reader = open(path, "r", encoding="utf-8")
    lines = reader.readlines()
    reader.close()

    dict_repo_tag_repos = {}
    for line in lines:
        parts = line.split("\t")
        dict_repo_tag_repos[parts[0]] = True

    return dict_repo_tag_repos


def get_unused_dup_repos(path):
    """Get repos for which unused/duplicate count was generated`path`"""
    reader = open(path, "r", encoding="utf-8")
    lines = reader.readlines()[2:]
    reader.close()

    i = 0
    dict_repos = {}
    for line in lines:
        parts = line.split("\t")
        if len(parts) < 3:
            break

        dict_repos[parts[0]] = i
        i += 1

    return dict_repos

def clean_repos(path, dict_repos):
    """Clean all entries of repos not in `dict_repos`"""
    output = "Repository\tPackage-Lock\tNpm-ShrinkWrap\tYarn\tAll-Fixed\tNo-Dependency"

    reader = open(path, "r")
    lines = reader.readlines()
    reader.close()

    for line in lines:
        parts = line.split("\t")
        if parts[0] in dict_repos:
            output += "\n" + line.replace("\n", "")

    writer = open(path, "w")
    writer.write(output)
    writer.close()

if __name__ == "__main__":
    """Cleans out repositories from results that no longer exist in dataset"""
    dict_current_repos = get_current_repos(
        os.path.join("data", "npm_rank_sorted.txt"))

    dict_repo_tag_repos = get_repo_tag_repos("repo_tags.txt")

    dict_unused_repos = get_unused_dup_repos(os.path.join(
        "results", "unused_dup_checker_all_tags", "unused_all_tags"))

    dict_duplicate_repos = get_unused_dup_repos(os.path.join(
        "results", "unused_dup_checker_all_tags", "duplicates_all_tags"))

    # for repo in dict_unused_repos:
    #     if repo not in dict_repo_tag_repos:
    #         print(repo + " " + str(dict_unused_repos[repo]))

    clean_repos(os.path.join("results", "paper_data",
                             "repo_lock_files.txt"), dict_current_repos)
