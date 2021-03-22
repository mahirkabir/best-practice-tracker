
import os
import constants


def get_repo_step(lines):
    """Get the first step in which `npm audit` found no vulnerability"""
    dict_repo_step = {}
    dict_needs_install = {}

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

        dict_needs_install[repo_name] = (
            dict_repo_step[repo_name] != constants.AUDIT_STEP_FAIL) and (
            constants.AUDIT_STEP_CHANGED in parts[2])

    return dict_repo_step, dict_needs_install


if __name__ == "__main__":
    """Run `npm ddp` on repositories having no vulnerabilities"""

    reader = open(os.path.join(
        "results", "audit_checker", "audit_results.txt"), "r")
    lines = reader.readlines()[1:]
    reader.close()
    dict_repo_step, dict_needs_install = get_repo_step(lines)

    