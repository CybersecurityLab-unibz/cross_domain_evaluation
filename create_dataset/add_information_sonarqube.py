import argparse
import re

import pandas as pd
from tqdm import tqdm
import os
import json

#pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

def load_data(path, nrows=None):
    return pd.concat(
        [chunk for chunk in
         tqdm(pd.read_csv(path, chunksize=1000, lineterminator="\n", nrows=nrows), desc="Load csv...")])


def read_args():

    parser = argparse.ArgumentParser()

    parser.add_argument("--path-input", required=True, type=str)
    parser.add_argument("--path-sonarqube", required=True, type=str)
    parser.add_argument("--path-output", required=True, type=str)

    return parser.parse_args()

if __name__ == "__main__":
    args = read_args()

    data = load_data("{}/complete_with_semgrep.csv".format(args.path_input))

    data["sonarqube"] = False
    data["sonarqube_start_position_line"] = None
    data["sonarqube_start_position_character"] = None
    data["sonarqube_end_position_line"] = None
    data["sonarqube_end_position_character"] = None
    data["sonarqube_rule"] = None
    data["sonarqube_cwe"] = None
    data["sonarqube_owasp"] = None
    data["sonarqube_category"] = None
    data["sonarqube_severity"] = None
    data["sonarqube_likelihood"] = None
    data["sonarqube_impact"] = None
    data["sonarqube_confidence"] = None

    print(data)

    # data.keys()
    # ['projectname', 'url', 'filename', 'function', 'leading_comment', 'start_position', 'end_position']

    path_sonarqube = "{}/sonarqube_runs".format(args.path_sonarqube)

    sonarqube_repositories = os.listdir(path_sonarqube)


    for file in sonarqube_repositories:
        path_data = path_sonarqube + "/" + file
        project = file.replace(".json", "")
        print(path_data)
        with open(path_data, 'r') as file:
            # Load the contents of the file into a Python dictionary
            data_sonarqube = json.load(file)

        data_2 = data[data["projectname"] == project]

        pbar = tqdm(total=len(data_sonarqube), desc="extracting information")

        for index in range(len(data_sonarqube)):
            row = data_sonarqube[index]
            start_line = int(row["textRange"]["startLine"])
            start_character = int(row["textRange"]["startOffset"])
            end_line = int(row["textRange"]["endLine"])
            end_character = int(row["textRange"]["endOffset"])
            rule = row["rule"]
            category = row["type"]
            severity = row["severity"]
            print(row["tags"])
            cwe = ";".join([tag for tag in row["tags"] if "cwe" in tag])
            owasp = ";".join([tag for tag in row["tags"] if "owasp" in tag])
            likelihood = ""
            impact = row["impacts"][0]["softwareQuality"]
            confidence = ""
            path = os.path.join(args.path_input, "repositories", re.sub(":", "/", row["component"]))

            result = data_2[(data_2["filename"] == path) &
                            (data_2["start_position_line"] <= start_line) &
                            (data_2["end_position_line"] >= end_line)]

            for index, row in result.iterrows():
                if data.loc[index, "sonarqube"]:
                    data.loc[index, "sonarqube_start_position_line"] = data.loc[index, "sonarqube_start_position_line"] + ";" + str(start_line)
                    data.loc[index, "sonarqube_start_position_character"] = data.loc[index, "sonarqube_start_position_character"] + ";" + str(start_character)
                    data.loc[index, "sonarqube_end_position_line"] = data.loc[index, "sonarqube_end_position_line"] + ";" + str(end_line)
                    data.loc[index, "sonarqube_end_position_character"] = data.loc[index, "sonarqube_end_position_character"] + ";" + str(end_character)
                    data.loc[index, "sonarqube_rule"] = data.loc[index, "sonarqube_rule"] + ";" + rule
                    data.loc[index, "sonarqube_category"] = data.loc[index, "sonarqube_category"] + ";" + category
                    data.loc[index, "sonarqube_severity"] = data.loc[index, "sonarqube_severity"] + ";" + severity
                    data.loc[index, "sonarqube_cwe"] = data.loc[index, "sonarqube_cwe"] + ";" + cwe
                    data.loc[index, "sonarqube_owasp"] = data.loc[index, "sonarqube_owasp"] + ";" + owasp
                    #data.loc[index, "sonarqube_confidence"] = data.loc[index, "sonarqube_confidence"] + ";" + confidence
                    data.loc[index, "sonarqube_impact"] = data.loc[index, "sonarqube_impact"] + ";" + impact
                    #data.loc[index, "sonarqube_likelihood"] = data.loc[index, "sonarqube_likelihood"] + ";" + likelihood
                else:
                    data.loc[index, "sonarqube"] = True
                    data.loc[index, "sonarqube_start_position_line"] = str(start_line)
                    data.loc[index, "sonarqube_start_position_character"] = str(start_character)
                    data.loc[index, "sonarqube_end_position_line"] = str(end_line)
                    data.loc[index, "sonarqube_end_position_character"] = str(end_character)
                    data.loc[index, "sonarqube_rule"] = rule
                    data.loc[index, "sonarqube_category"] = category
                    data.loc[index, "sonarqube_severity"] = severity
                    data.loc[index, "sonarqube_cwe"] = cwe
                    data.loc[index, "sonarqube_owasp"] = owasp
                    data.loc[index, "sonarqube_confidence"] = confidence
                    data.loc[index, "sonarqube_impact"] = impact
                    data.loc[index, "sonarqube_likelihood"] = likelihood

            pbar.update(1)
        pbar.close()
    print(data[data["sonarqube"] == True])

    #data.to_csv("{}/complete_with_semgrep_and_sonarqube.csv".format(args.path_output), index=False)