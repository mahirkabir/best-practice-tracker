import os
import helper


def get_sorted_tags(repo_tags_path):
    """Return top 5 tags that were previously sorted in descending order based on commit time"""
    reader = open(repo_tags_path, "r")
    lines = reader.readlines()[1:]
    reader.close()

    dict_sorted_tags = {}

    for line in lines:
        parts = line.split("\t")
        repo_name = parts[0]
        if len(parts) > 1:
            tags = parts[1].split("|")
            while "\n" in tags:
                tags.remove("\n")
            if len(tags) >= 5:
                dict_sorted_tags[repo_name] = tags[0:5]

    return dict_sorted_tags


def get_five_tag_results(all_five_tag_results_path):
    """Get top 5 tags' vulnerability count"""
    reader = open(all_five_tag_results_path, "r")
    lines = reader.readlines()[1:]
    reader.close()

    dict_five_tag_results = {}

    for line in lines:
        parts = line.split("\t")
        repo_name = parts[0]

        if repo_name in dict_five_tag_results:
            if dict_five_tag_results[repo_name] == "ERR":
                continue
        else:
            dict_five_tag_results[repo_name] = {}

        tag = parts[1]

        row = []
        if "ERR" in parts[-2]:
            dict_five_tag_results[repo_name] = "ERR"
            print("Error for at least one tag in:\t" + repo_name)
        else:
            for part in parts[2:]:
                part = part.replace("\n", "")
                row.append(part)

        if dict_five_tag_results[repo_name] == "ERR":
            continue
        else:
            dict_five_tag_results[repo_name][tag] = row

    to_be_deleted_keys = []
    for key in dict_five_tag_results:
        if dict_five_tag_results[key] == {} or dict_five_tag_results[key] == "ERR":
            to_be_deleted_keys.append(key)

    for key in to_be_deleted_keys:
        dict_five_tag_results.pop(key)

    return dict_five_tag_results


if __name__ == "__main__":
    repo_tags_path = os.path.join(
        "results", "audit_checker_all_tags", "repo_tags.txt")
    dict_sorted_tags = get_sorted_tags(repo_tags_path)

    all_five_tag_results_path = os.path.join(
        "results", "audit_checker_all_tags", "audit_results_five_tags.txt")
    dict_five_tag_results = get_five_tag_results(all_five_tag_results_path)

    repos = dict_five_tag_results.keys()

    writer = open(os.path.join("results", "audit_checker_all_tags",
                               "grouped_vul_count_all_tags.txt"), "w")

    dict_no_tag = {}
    for i in range(0, 5):
        writer.write(
            "Tag order from latest-to-earliest[1-to-5]: %s\n" % str(i + 1))
        for repo in repos:
            if repo in dict_no_tag:
                continue
            if repo not in dict_sorted_tags:
                print("No sorted tags found for:\t" + repo)
                dict_no_tag[repo] = True
                continue
            tag = dict_sorted_tags[repo][i]

            if tag not in dict_five_tag_results[repo]:
                print("%s not in dict_five_tag_results[%s]" % (tag, repo))
                continue
            row = dict_five_tag_results[repo][tag]

            output = repo + "\t" + tag
            for col in row:
                output += "\t" + col
            writer.write(output)
            writer.write("\n")

    writer.close()
