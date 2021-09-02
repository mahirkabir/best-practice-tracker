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
    reader = open(os.path.join(
        "results", "audit_checker_all_tags", "vul_count_all_tags.txt"), "r")
    lines = reader.readlines()
    reader.close()

    repos_cnt = int(len(lines) / 5)

    writer = open(os.path.join(
        "results", "audit_checker_all_tags", "grouped_vul_count_all_tags.txt"), "w")
    for i in range(0, 5):
        writer.write(
            "Tag order from latest-to-earliest[1-to-5]: " + str(i + 1) + "\n")
        for j in range(i, repos_cnt * 5, 5):
            writer.write(lines[j])
    writer.close()
