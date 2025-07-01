import argparse

from tree_sitter import Language, Parser
import pandas as pd
from php_parser import PHPParser
import os
from tqdm import tqdm
import subprocess


def get_repository_link(project_path):
    try:
        # Change directory to the project path
        cmd = ['git', '-C', project_path, 'config', '--get', 'remote.origin.url']
        # Run the command
        result = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode().strip()
        return result
    except subprocess.CalledProcessError:
        return "Error: Not a Git repository or remote URL not found"


def get_files(directory):
    all_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".php"):
                # Append the full path of each file to the list
                all_files.append(os.path.join(root, file))

    return all_files


def readFile(path):
    with open(path, 'r', encoding='latin_1') as file:
        # Read all lines at once and store them in a variable
        fileContent = file.read()
        return fileContent
    return None


def read_args():

    parser = argparse.ArgumentParser()

    parser.add_argument("--path-repos", type=str, required=True)
    parser.add_argument("--path-output", type=str, required=True)

    return parser.parse_args()


if __name__ == "__main__":

    args = read_args()

    PHP_LANGUAGE = Language("build/parser_php.so", "php")

    parser = Parser()
    parser.set_language(PHP_LANGUAGE)

    data = pd.DataFrame()
    data["projectname"] = ""
    data["url"] = ""
    data["filename"] = ""
    data["function"] = ""
    data["leading_comment"] = ""
    data["start_position"] = ""
    data["end_position"] = ""

    directory = args.path_repos
    projects = [folder for folder in os.listdir(directory) if os.path.isdir(os.path.join(directory, folder))]
    projects = [folder for folder in projects if folder != '.scannerwork']

    print(projects)

    for p_idx in tqdm(range(len(projects)), desc='Projects', leave=False):

        projectname = projects[p_idx]
        projectPath = "{}/{}".format(directory, projectname)
        git_url = get_repository_link(projectPath)
        allFiles = get_files(projectPath)

        for f_idx in tqdm(range(len(allFiles)), desc='Files of the project -> {}'.format(projects[p_idx]), leave=False):

            filename = allFiles[f_idx]
            fileContent = readFile(filename)

            if fileContent is None:
                print("ERROR")
                quit()

            tree = parser.parse(
                bytes(fileContent, "utf8", )
            )

            result = PHPParser.get_definition(tree, fileContent)

            for index in [index for index, elem in enumerate(result) if elem["type"] in PHPParser.relevantTypes]:

                data_length = len(data)
                leading_comment = []
                code = result[index]["text"]
                code_start = result[index]["start"]
                code_end = result[index]["end"]

                for i in range(index-1, -1, -1):
                    if result[i]["type"] == "comment":
                        leading_comment.append(result[i]["text"])
                    else:
                        break

                data.loc[data_length, "projectname"] = projectname
                data.loc[data_length, "url"] = git_url
                data.loc[data_length, "filename"] = filename
                data.loc[data_length, "function"] = code
                data.loc[data_length, "leading_comment"] = "\n".join(leading_comment)
                data.loc[data_length, "start_position"] = ', '.join(map(str, code_start))
                data.loc[data_length, "end_position"] = ', '.join(map(str, code_end))

    data.to_csv("{}/complete.csv".format(args.path_output), index=False)


