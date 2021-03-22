
import os
import constants


def get_repo_step(lines):
    """Get the first step in which `npm audit` found no vulnerability"""
    dict_repo_step = {}

    for line in lines:
        parts = line.split("\t")
        parts[-1] = parts[-1].strip()

        repo_name = parts[0]
        if constants.AUDIT_TRUE in parts[1]:
            dict_repo_step[repo_name] = constants.AUDIT_STEP_INIT
        elif constants.AUDIT_TRUE in parts[2]:
            dict_repo_step[repo_name] = constants.AUDIT_STEP_INSTALL
        elif constants.AUDIT_TRUE in parts[3]:
            dict_repo_step[repo_name] = constants.AUDIT_STEP_FIX
        elif constants.AUDIT_TRUE in parts[4]:
            dict_repo_step[repo_name] = constants.AUDIT_STEP_FORCE_FIX
        else:
            dict_repo_step[repo_name] = constants.AUDIT_STEP_FAIL

    return dict_repo_step


if __name__ == "__main__":
    """Run `npm ddp` on repositories having no vulnerabilities"""

    reader = open(os.path.join(
        "results", "audit_checker", "audit_results.txt"), "r")
    lines = reader.readlines()[1:]
    reader.close()
    dict_repo_step = get_repo_step(lines)

    print(dict_repo_step)
