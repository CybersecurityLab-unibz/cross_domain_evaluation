import os
import re
from utils import detect_security_indicator, \
    write2environment

import subprocess


INDEX_LINE = 0
INDEX_CODE = 1
INDEX_NUMBER_OF_LINES = 2
MESSAGE_REMOVED = "Removed"
MESSAGE_INTRODUCED = "Introduced"


def find_multiline_comment_start(lines):
    in_comment = False
    comment_start_line = None

    result = []
    for i, line in enumerate(lines):
        if re.search(r'\/\*.*\*\/', line) is not None:
            # Handle comments that start and end on the same line
            result.append(i)
        elif re.search(r'\/\*.*', line) and not in_comment:
            in_comment = True
            comment_start_line = i
        elif re.search(r'.*\*\/', line) and in_comment:
            in_comment = False
            result.append(comment_start_line)

    return result

def extract_comments_with_line_numbers(code):
    comments = []

    # for single line comments starting with // or #
    for i, line in enumerate(code.split('\n'), start=0):
        # Match PHP comments
        matches = re.findall(r'((((?<!:)\/\/.*))|(#.*))', line)
        if matches:
            for match in matches:
                comments.append((i, match[0].strip(), 1))

    # for multi line comments
    pattern = r'(/\*(.*?)\*/)'
    multiline_comments = re.finditer(pattern, code, re.DOTALL)
    start_lines = find_multiline_comment_start(code.split('\n'))
    for index, match in enumerate(multiline_comments):
        start_line = start_lines[index]
        comment_content = match.group(1).strip()
        num_lines = comment_content.count('\n') if comment_content.count('\n') != 0 else 1
        comments.append((start_line, comment_content, num_lines))
    return comments


def convert_tuple_to_list(tuple):
    return [elem for elem in tuple]

def extract_information_from_altered_file(code, filename, message=MESSAGE_INTRODUCED, apply_filter=True):
    result = []

    if apply_filter:
        code = "\n".join([line[1:] for line in code.split("\n")])

    comments_with_code = extract_comments_with_line_numbers(code)

    for elem in comments_with_code:
        elem = convert_tuple_to_list(elem)

        security_indicator = detect_security_indicator(elem[INDEX_CODE])
        if len(security_indicator) > 0:
            elem.append(filename)
            elem.append(message)
            elem.append(", ".join(security_indicator))
            result.append(elem)

    return result


def extract_information_from_modified_file(code, filename):
    original = "\n".join([line[1:] for line in code.split("\n") if not line.startswith("+")])
    new = "\n".join([line[1:] for line in code.split("\n") if not line.startswith("-")])

    result = \
        extract_information_from_altered_file(original, filename, MESSAGE_REMOVED, False) + \
        extract_information_from_altered_file(new, filename, MESSAGE_INTRODUCED, False)

    relevant_lines = [index for index, line in enumerate(code.split("\n")) if
                      line.startswith("+") or line.startswith("-")]

    # take only those which have been removed or introduced and were not present before
    relevant_comments = [elem for elem in result if any(int(elem[INDEX_LINE]) <= x <= int(elem[INDEX_LINE])+int(elem[INDEX_NUMBER_OF_LINES]) for x in relevant_lines)]

    return sorted(relevant_comments, key=lambda x: int(x[0]))


def run_git_command(command, return_value = False):
    process = subprocess.Popen(
        "git config --global --add safe.directory /github/workspace && {}".format(command),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        encoding="latin-1"
    )

    stdout, stderr = process.communicate()

    if process.returncode != 0:
        raise RuntimeError(f"Error: {stderr.strip()}")

    if return_value == True:
        return stdout, stderr, process.returncode



if __name__ == '__main__':
    base_branch = "main"#os.getenv('INPUT_BASE-BRANCH')
    branch = "show"#os.getenv('INPUT_BRANCH')

    print(base_branch, branch)

    run_git_command("git fetch")
    run_git_command("git checkout {}".format(base_branch))
    run_git_command("git checkout {}".format(branch))
    stdout, stderr, returnCode = run_git_command("git show-branch --merge-base {}".format(base_branch), True)

    if returnCode != 0:
        raise RuntimeError(f"2Error: {stderr.strip()}")

    hash = stdout.strip()

    print("Hash which the PR is compared too:")
    print(hash)

    diff = subprocess.check_output(
        "git diff {} -U9999 -- '*.php'".format(hash),
        shell=True,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=".",
        encoding="latin-1"
    )

    pattern = r'(diff --git a/.* b/.*|@@.*@@)'

    parts = re.split(pattern, diff)[1:]  # the first element can be removed as it is always an empty line
    print(parts)
    security_indicators = []
    print(len(parts))
    factor = 0
    for index, elem in enumerate(parts):
        print(index, elem)
        if index % 4 == 0:
            filename = parts[index+factor].split(" b/")[-1]
            filetype = filename.split(".")[-1]
            print("hier", filetype, filename)
            print(filename, filetype, filetype == "*@@)'")
            if filetype == "*@@)'":
                factor = factor - 2
            print(factor)

            if filetype == "php":
                git_diff = parts[index +3+factor]
                print(git_diff)
                # new file
                if 'index 0000000' in parts[index +1+factor]:
                    print("new file")
                    [security_indicators.append(elem) for elem in
                     extract_information_from_altered_file(git_diff, filename, MESSAGE_INTRODUCED)]
                # deleted file
                elif re.search(r'(index\s[0-9a-f]{7}\.\.[0]{7})', parts[index +1+factor]):
                    print("deleted file")
                    [security_indicators.append(elem) for elem in
                     extract_information_from_altered_file(git_diff, filename, MESSAGE_REMOVED)]
                # modified file
                else:
                    print("modified file")
                    [security_indicators.append(elem) for elem in
                     extract_information_from_modified_file(git_diff, filename)]

    sentences = ['']
    sentences_per_file = []

    for elem in security_indicators:
        line_number_start, comment, line_number_end, file_name, action, patterns = elem
        # remove duplicates
        patterns = ", ".join(list(set(patterns.split(", "))))

        # Determine if it was introduced or removed
        action_str = "introduced" if action.lower() == "introduced" else "removed"
        #sentence = f"The comment '{comment.strip()}' on line {line_number_start} of file '{file_name}' was {action_str}."
        sentence = f"On line {line_number_start} of file '{file_name}' a security indicator was {action_str} ({patterns})." if line_number_end == 1 else f"Between the lines {line_number_start} to {line_number_start+line_number_end} of file '{file_name}' a security indicator was {action_str} ({patterns})."
        sentences_per_file.append('{};{};{};{}'.format(line_number_start,line_number_start,file_name, "In the following line there was a security indicator "+action_str+" ("+patterns+")"))
        sentences.append(sentence)

    #result = " \\n\\n ".join(sentences)
    #result = '"' + result + '"'
    #print(result)

    result = ";".join(sentences_per_file)

    #core.warning("Moritz This is a warning message from the Python script.")
    #core.info("This is an informational message from the Python script.")
    #core.error("This is an error message from the Python script.")

    #core.set_error('SSL certificates installation failed.')
    print("result")
    print(result)
    write2environment("FILES", result)
    #print("::set-output name=test::{}".format(result))
