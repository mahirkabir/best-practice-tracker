import os
import subprocess
import configparser
from shutil import copy2


def execute_cmd(path, cmd):
    """Execute windows command in input path directory"""

    working_dir = os.getcwd()
    os.chdir(path)

    out = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)

    stdout, stderr = out.communicate()
    # utf-8 encoding is reverse compatible with ASCII
    str_stdout = stdout.decode("utf-8")

    os.chdir(working_dir)

    if "ERR" in str_stdout or "err" in str_stdout:
        return [False, str_stdout]
    else:
        return [True, str_stdout]


def get_repos(path):
    """Get list of all repos that are going to be processed. Returns: [{name, url}]"""

    reader = open(path, "r")

    repo_lines = reader.readlines()
    npm_rank_repos = []

    for repo_line in repo_lines:
        repo_info = repo_line.split("\t")
        repo = {"name": repo_info[0].strip(), "url": repo_info[1].strip()}
        npm_rank_repos.append(repo)

    reader.close()

    return npm_rank_repos


def get_config(section, key):
    """Get config value from config.ini"""

    config = configparser.ConfigParser()
    config.read("config.ini")
    value = config.get(section, key)
    return value


def get_file_safe_name(name):
    """Remove invalid characters from filename"""
    return "".join([c for c in name if c.isalpha() or c.isdigit() or c == ' ']).rstrip()


def clone_repo_to_dir(directory, git_url, repo_name):
    """Clone GitHub repository in input directory with repo_name as folder name"""

    repo_safe_name = get_file_safe_name(repo_name)
    suffix = 0
    while os.path.exists(os.path.join(directory, repo_safe_name)):
        suffix += 1
        repo_safe_name = repo_name + "_" + str(suffix)

    cmd = "git clone {git_url} {repo_name}".format(
        git_url=git_url, repo_name=repo_safe_name)
    clone_result = execute_cmd(directory, cmd)

    if(clone_result[0] == False):
        raise Exception(clone_result[1])
    else:
        return repo_safe_name


def remove_folder(root, folder):
    """Remove folder in root directory"""

    folder_to_delete = os.path.join(root, folder)

    if(os.path.isdir(folder_to_delete)):
        if not (execute_cmd(folder_to_delete, "DEL /F/Q/S *.* > NUL")[0] and execute_cmd(root, "RMDIR /Q/S " + folder_to_delete)[0]):
            raise Exception("Error removing: " + folder)


def clean_info(info):
    """Clean extra characters from build info"""
    lines = info.split("</ BR>")
    result = ""
    for line in lines:
        result += line.strip()
    return result


def record(foldername, filename, content):
    """Record content in filename located in foldername"""
    if not os.path.isdir(foldername):
        os.makedirs(foldername)

    writer = open(os.path.join(foldername, filename), "w", encoding="utf-8")
    writer.write(content)
    writer.close()


def IFF(statement, true_val, false_val):
    "Return `true_val` if statement is `True`, else return `false_val`"
    if statement == True:
        return true_val
    else:
        return false_val
