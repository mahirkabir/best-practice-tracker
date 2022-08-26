import os
from tqdm import tqdm


def get_duplicate_deps(repo, tag):
    """Get duplicate dependencies for `tag` of `repo`"""
    reader = open(os.path.join("results", "camera_ready", "dup_checker",
                               "just_libs", repo + ".txt"), "r", encoding="utf-8")
    lines = reader.readlines()
    reader.close()

    report = ""
    for line in lines:
        report += line

    return report


def generate_issue(template, repo, tag, url, report):
    """Generate user study report for `url` from `template`"""
    template = template.replace("<REPO LINK>", url)
    template = template.replace("<PROJECT>", repo)
    template = template.replace("<TAG>", tag)
    template = template.replace("<DUPLICATE DEPENDENCIES>", report)

    return template


if __name__ == "__main__":
    """Generate user study issues for repos"""
    reader = open(os.path.join(
        ".", "data", "npm_rank_sorted.txt"), "r")
    lines = reader.readlines()
    reader.close()

    dict_repo_url = {}
    for line in lines:
        parts = line.split("\t")
        dict_repo_url[parts[0]] = parts[1]

    dict_repo_latest_tag = {}
    reader = open("repo_tags.txt", "r")
    lines = reader.readlines()

    for line in lines:
        parts = line.split("\t")
        tags = parts[1].split("|")
        if len(tags) == 6:  # last dummy one is "\n"
            dict_repo_latest_tag[parts[0]] = tags[0]

    study_repos = []
    reader = open(os.path.join(".", "user_studies",
                               "duplicate_repos.txt"), "r")
    lines = reader.readlines()
    reader.close()
    for line in lines:
        study_repos.append(line.replace("\n", ""))

    template = ""
    reader = open(os.path.join("user_studies",
                               "duplicate_deps_template.txt"), "r", encoding="utf-8")
    lines = reader.readlines()
    reader.close()
    for line in lines:
        template += line

    for repo in tqdm(study_repos):
        try:
            if repo not in dict_repo_latest_tag:
                # Only generating issues for repos with 5 tags
                continue
            report = get_duplicate_deps(repo, dict_repo_latest_tag[repo])
            generated_issue = generate_issue(
                template, repo, dict_repo_latest_tag[repo], dict_repo_url[repo], report)

            writer = open(os.path.join("user_studies", "duplicate_issues",
                                       repo + ".txt"), "w", encoding="utf-8")
            writer.write(generated_issue)
            writer.close()

        except Exception as ex:
            print(str(ex))
