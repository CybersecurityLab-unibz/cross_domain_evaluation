import subprocess
import os
import json

token = os.getenv('INPUT_GITHUB-TOKEN')
body = os.getenv('INPUT_BODY') if os.getenv('INPUT_BODY') != "" else None
file = os.getenv('INPUT_FILE').replace("'", "") if os.getenv('INPUT_FILE').replace("'", "") != "" else None
owner_repository = os.getenv('INPUT_OWNER-REPOSITORY')
pr_number = os.getenv('INPUT_PR-NUMBER')
commit_id = os.getenv('INPUT_COMMIT-ID')
logs = os.getenv('INPUT_LOGS')

LOGGING = True if logs.lower() == "true" else False

def run_command(command, return_value):
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        encoding="latin-1"
    )

    stdout, stderr = process.communicate()

    if process.returncode != 0:
        raise RuntimeError(f"Error: {stderr.strip()}")

    if LOGGING:
        print(stdout)
        print(stderr)
        print(process.returncode)

    if return_value == True:
        return stdout, stderr, process.returncode


def get_current_comments(token, owner_repository, pr_number):
    command = "curl -L " \
              "-H \"Accept: application/vnd.github+json\" " \
              "-H \"Authorization: Bearer "+token+"\" " \
              "-H \"X-GitHub-Api-Version: 2022-11-28\" " \
              "https://api.github.com/repos/"+owner_repository+"/pulls/"+pr_number+"/comments"

    stdout, stderr, code = run_command(command, True)

    return json.loads(stdout)


def write_comment(body, file, token, owner_repository, pr_number, current_file_level_comments, return_value = False):

    if body is not None:
        json = {
            "event": "COMMENT",
            "body": body
        }

        command = "curl -L " \
                  "-X POST " \
                  "-H \"Accept: application/vnd.github+json\" " \
                  "-H \"Authorization: Bearer " + token + "\" " \
                  "-H \"X-GitHub-Api-Version: 2022-11-28\" https://api.github.com/repos/" + owner_repository + "/pulls/" + pr_number + "/reviews " \
                  "-d '" + str(json).replace("'", '\"') + "'"

        run_command(command, return_value)

    added_file_comment = False

    if file is not None:
        file = file.split(";")
        for i in range(0, len(file), 4):
            start_line, line, path, message = file[i:i+4]

            if not any(
                    obj.get('body') == message and
                    obj.get('line') == int(line) and
                    obj.get('path') == path
                    for obj in current_file_level_comments
            ):
                inner_json = {
                    "path": path,
                    "line": int(line),
                    "body": message,
                    "side": "LEFT" if "removed" in message else "RIGHT",
                    "commit_id": commit_id
                }

                if int(start_line) < int(line):
                    inner_json["start_line"] = int(start_line)

                command = "curl -X POST " \
                          "-H \"Authorization: token " + token + "\" " \
                          "-H \"Accept: application/vnd.github.v3+json\" " \
                          "https://api.github.com/repos/" + owner_repository + "/pulls/" + pr_number + "/comments " \
                          "-d '" + str(inner_json).replace("'", '\"') + "'"

                run_command(command, return_value)
                added_file_comment = True

    if body is None and added_file_comment is False:
        print("All comments at file level are already present!")
        print("No information was passed regarding a comment on the main conversation page of the pull request.")
        print("The action did not perform anything.")
        quit()


if __name__ == "__main__":
    if file is not None:
        file = file.replace('"', "")

    if file == "NOTHING FOUND!" or body == "NOTHING FOUND!":
        print("Nothing was detected, the action will shut down now!")
        quit()

    if LOGGING:
        print("file ->:{}:".format(file))
        print("body ->:{}:".format(body))

    if file is None and body is None:
        print("No values are passed!")
        print("Nothing was done, pass a value either to 'body' or 'file'")
        quit()

    if file is not None and len(file.split(";")) % 4 != 0:
        print("The shape of the variable 'file' is wrong!")
        print("It is expected to be the following: 'start_line;line;file_path;message'")
        print("If multiple comments should be placed, concatenate the schema with a ';'")
        quit()

    current_file_level_comments = get_current_comments(token, owner_repository, pr_number)

    write_comment(body, file, token, owner_repository, pr_number, current_file_level_comments)