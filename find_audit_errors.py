import os
import constants
from shutil import copyfile

if __name__ == "__main__":
    """Find out why audit failed for some repositories"""

    reader = open(os.path.join(
        "results", "audit_checker", "audit_results.txt"), "r")
    lines = reader.readlines()
    reader.close()

    err_repos = []  # Repos for which `npm i` could not fix the audit error
    for line in lines:
        line = line.strip()
        parts = line.split("\t")

        if constants.AUDIT_ERROR in parts[2]:
            err_repos.append(parts)

    not_found_cnt = 0
    for repo in err_repos:
        init_audit_file_loc = os.path.join(
            "results", "audit_checker", repo[0], "init_audit.txt")
        init_dest_loc = os.path.join(
            "results", "find_audit_errors", "init", repo[0] + ".txt")

        after_i_audit_file_loc = os.path.join(
            "results", "audit_checker", repo[0], "after_i_lock.txt")

        after_i_dest_loc = os.path.join(
            "results", "find_audit_errors", "after_i", repo[0] + ".txt")

        npm_i_output_loc = os.path.join(
            "results", "audit_checker", repo[0], "install_lock_output.txt")

        npm_i_output_dest_loc = os.path.join(
            "results", "find_audit_errors", "install_lock", repo[0] + ".txt")

        try:
            copyfile(init_audit_file_loc, init_dest_loc)
            copyfile(after_i_audit_file_loc, after_i_dest_loc)
            copyfile(npm_i_output_loc, npm_i_output_dest_loc)
        except Exception as ex:
            print(ex)
            not_found_cnt += 1

    print("Missing: " + str(not_found_cnt))

    keywords = ["is not recognized as an internal or external command",
                "resolve dependency", "no such file or directory", "Unsupported URL Type",
                "git dep preparation failed", "Cannot destructure property", "up to date",
                "Cannot convert undefined or null to object", "a package version that doesn't exist", 
                "Unsupported platform", "Could not read from remote repository"]

    dict_keyword_frequency = {}
    for keyword in keywords:
        dict_keyword_frequency[keyword] = 0

    for repo in err_repos:
        install_output_loc = os.path.join(
            "results", "find_audit_errors", "install_lock", repo[0] + ".txt")

        try:
            reader = open(install_output_loc, "r")
            lines = reader.readlines()
            reader.close()

            match_found = 0
            for line in lines:
                for keyword in keywords:
                    if keyword in line:
                        dict_keyword_frequency[keyword] += 1
                        match_found = True
                        break
                if match_found:
                    break

            if not match_found:
                print("No match found for: " + repo[0])
        except Exception as ex:
            print(ex)

    print(dict_keyword_frequency)
