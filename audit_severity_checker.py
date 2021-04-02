import os


def get_severity(path):
    """Get severity levels of repository located in `path`"""
    dict_severity_count = {"low": 0, "moderate": 0, "high": 0, "critical": 0}

    reader = open(path, "r", encoding="utf-8")
    lines = reader.readlines()
    for line in lines:
        for key in dict_severity_count.keys():
            if "Severity: " + key in line:
                dict_severity_count[key] += 1
    reader.close()
    return dict_severity_count


if __name__ == "__main__":
    """Find out vulnerability severity levels of unfixable & vulnerable repositories"""

    path = os.path.join("results", "audit_checker")
    dirs = os.listdir(path)

    for dir in dirs:
        try:
            init_audit_result = get_severity(
                os.path.join(path, dir, "init_audit.txt"))
            after_i_lock_result = get_severity(
                os.path.join(path, dir, "after_i_lock.txt"))
            after_fix_result = get_severity(
                os.path.join(path, dir, "after_fix.txt"))
            after_fix_force_result = get_severity(
                os.path.join(path, dir, "after_fix_force.txt"))

            print(after_fix_force_result)

        except Exception as ex:
            print(ex)
