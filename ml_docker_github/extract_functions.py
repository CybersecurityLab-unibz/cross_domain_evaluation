from tree_sitter import Language, Parser
from typing import List, Dict, Any
from language_parser import LanguageParser
import subprocess
import re
import os


def write2environment(variable, data):
    env_file = os.getenv('GITHUB_OUTPUT')

    with open(env_file, "a") as file:
        file.write("{}='{}'".format(variable, data))


class PHPParser(LanguageParser):
    relevantTypes = ["method_declaration", "function_definition"]
    relevantTypesAndComments = ["method_declaration", "function_definition", "comment"]

    @staticmethod
    def get_definition(tree, blob: str) -> List[Dict[str, Any]]:
        definitions = []
        PHPParser.traverse_node(tree.root_node, definitions)
        return definitions

    @staticmethod
    def traverse_node(node, result, depth_counter=0):
        if not isinstance(node, list):
            type = node.type
            start = node.start_point
            end = node.end_point
            text = node.text.decode()  # any content in a node
            result.append({
                "type": type,
                "start": start,
                "end": end,
                "text": text
            })
            if type in PHPParser.relevantTypesAndComments:
                return

        # for safety measures, else python might crash
        if depth_counter == 100:
            return

        for sub_node in node.children:
            PHPParser.traverse_node(sub_node, result, depth_counter + 1)


def readFile(path):
    with open(path, 'r', encoding='latin_1') as file:
        # Read all lines at once and store them in a variable
        fileContent = file.read()
        return fileContent
    return None


def extract_relevant_files(base_branch):

    process = subprocess.Popen(
        "git show-branch --merge-base {}".format(base_branch),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        encoding="latin-1"
    )

    print("git show-branch --merge-base {}".format(base_branch))

    stdout, stderr = process.communicate()

    if process.returncode != 0:
        raise RuntimeError(f"Error: {stderr.strip()}")

    hash = stdout.strip()

    print("Hash which the PR is compared too:")
    print(hash)

    diff = subprocess.check_output(
        "git diff {} -U9999 -- '*.php'".format(hash),
        shell=True,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="latin-1"
    )

    print("----------------------------------")
    print(diff)
    print("----------------------------------")

    pattern = r'(diff --git a/.* b/.*|@@.*@@)'

    parts = re.split(pattern, diff)[1:]  # the first element can be removed as it is always an empty line
    print(parts)
    print(parts)

    affected_files = []

    for index, elem in enumerate(parts):
        if index % 4 == 0:
            if index >=4 :
                quit()
            filepath = parts[index].split(" b/")[-1]
            filetype = filepath.split(".")[-1]
            print(filetype, filepath)

            if filetype == "php":
                git_diff = parts[index + 3]
                print(git_diff)

                count = -1
                lines_added = []

                for line in re.split(r'\n|\r\n?', git_diff):
                    change_indicator = ""
                    if len(line) > 0:
                        change_indicator = line[0]
                        line = line[1:]
                        #print(count+1, ":", change_indicator, ":", line)

                    if change_indicator != "-":
                        count += 1

                    if change_indicator == "+":
                        lines_added.append(count)

                if len(lines_added) != 0:
                    affected_files.append(
                        (filepath, lines_added)
                    )

    return affected_files


def extract_functions(base_branch, variable):
    Language.build_library(
        # Store the library in the `build` directory
        "build/parser_php.so",
        # Include one or more languages
        ["/vulnerability-detection/vendor/tree-sitter-php/php"]
    )


    PHP_LANGUAGE = Language("build/parser_php.so", "php")

    parser = Parser()
    parser.set_language(PHP_LANGUAGE)

    files_affected = extract_relevant_files(base_branch)
    print(files_affected)

    if len(files_affected) == 0:
        print("No files affected!")
        write2environment(variable, "NO FILES AFFECTED")
        quit()

    relevant_functions = []

    #files_affected = [file for file in files_affected if "ml_docker_" not in file[0]] # todo remove

    for file_affected in files_affected:
        filepath, lines_added = file_affected

        fileContent = readFile("{}".format(filepath))

        tree = parser.parse(
            bytes(fileContent, "utf8", )
        )

        result = PHPParser.get_definition(tree, fileContent)

        for index in [index for index, elem in enumerate(result) if elem["type"] in PHPParser.relevantTypes]:
            start = result[index]["start"][0]+1
            end = result[index]["end"][0]+1
            for index_line in range(start, end+1, 1):
                if index_line in lines_added:
                    relevant_functions.append(
                        (filepath, result[index]["text"],start,end)
                    )
                    break

    print(relevant_functions)

    return relevant_functions


if __name__ == "__main__":
    variable = "FILE"
    base_branch = "main"
    extract_functions(base_branch, variable)
