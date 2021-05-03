import os
import re

if __name__ == "__main__":
    """Find distribution of unused libraries among repositories"""
    folder = os.path.join("results", "unused_checker")
    repos = os.listdir(folder)

    dict_unused = {}
    tot_npm_libs = 0
    tot_local_libs = 0

    for repo in repos:
        unused_info = os.path.join(folder, repo, "unused_pre.txt")
        reader = open(unused_info, "r", encoding="utf-8")
        lines = reader.readlines()
        reader.close()

        for line in lines:
            line = line.strip()
            m = re.search("\* .*", line)

            if m:
                lib = m.group(0).replace("* ", "")
                if ": " in lib:
                    # library_name: location is the format for local libraries. We are ignoring them for now
                    tot_local_libs += 1
                    continue
                else:
                    tot_npm_libs += 1

                if lib in dict_unused:
                    dict_unused[lib] += 1
                else:
                    dict_unused[lib] = 1

    print(dict_unused)
    print(tot_npm_libs)
    print(tot_local_libs)
