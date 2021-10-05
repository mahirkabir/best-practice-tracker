import os


def generate_issue(template, repo, tag, url):
    """Generate user study report for `url` from `template`"""
    template = template.replace("<REPO LINK>", url)
    template = template.replace("<PROJECT>", repo)
    template = template.replace("<TAG>", tag)

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
    reader = open(os.path.join(".", "user_studies", "lock_repos.txt"), "r")
    lines = reader.readlines()
    reader.close()
    for line in lines:
        study_repos.append(line.replace("\n", ""))

    template = ""
    reader = open(os.path.join("user_studies",
                               "lock_files_template.txt"), "r", encoding="utf-8")
    lines = reader.readlines()
    reader.close()
    for line in lines:
        template += line

    cnt = 0
    for repo in study_repos:
        try:
            generated_issue = generate_issue(
                template, repo, dict_repo_latest_tag[repo], dict_repo_url[repo])

            writer = open(os.path.join("user_studies", "lock_issues",
                                       repo + ".txt"), "w", encoding="utf-8")
            writer.write(generated_issue)
            writer.close()

            cnt += 1
            if cnt == 60:
                break

        except Exception as ex:
            print(str(ex))
