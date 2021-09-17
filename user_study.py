import os

if __name__ == "__main__":
    """Find repositories for user study"""

    """Audit Vulnerabilities"""
    reader = open(os.path.join("results", "audit_checker_all_tags",
                               "grouped_vul_count_all_tags.txt"), "r")
    lines = reader.readlines()
    reader.close()

    dict_vuls = {}
    dict_vuls_cnt = {}
    for line in lines:
        if "Tag order" in line:
            pass
        else:
            line = line.replace("\n", "")
            parts = line.split("\t")
            repo_name = parts[0]
            after_i = parts[5]

            if repo_name not in dict_vuls:
                dict_vuls[repo_name] = []
                dict_vuls_cnt[repo_name] = 0

            dict_vuls[repo_name].append(after_i)
            if "Vul Found" in after_i:
                dict_vuls_cnt[repo_name] += 1

    always_vuls = []
    changed_to_vuls = []

    for repo_name in dict_vuls:
        if dict_vuls_cnt[repo_name] == 5:
            always_vuls.append(repo_name)
        elif "Vul Found" in dict_vuls[repo_name][0]:
            changed_to_vuls.append(repo_name)

    print(len(always_vuls))
    print(len(changed_to_vuls))

    writer = open(os.path.join("results", "paper_data",
                               "user_study_audit.txt"), "w", encoding="utf-8")

    writer.write("Always Vulnerable\n")
    for repo_name in always_vuls:
        writer.write(repo_name)
        writer.write("\n")

    writer.write("Changed to Vulnerable\n")
    for repo_name in changed_to_vuls:
        writer.write(repo_name)
        writer.write("\n")

    writer.close()
