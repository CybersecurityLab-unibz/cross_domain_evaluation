import argparse

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
    parser.add_argument("--path-semgrep", required=True, type=str)
    parser.add_argument("--path-output", required=True, type=str)

    return parser.parse_args()

if __name__ == "__main__":
    args = read_args()
    print(args)

    data = load_data("{}/complete.csv".format(args.path_input))

    data["start_position_line"] = data["start_position"].apply(lambda cell: cell.split(",")[0].replace(" ", ""))
    data["start_position_line"] = data["start_position_line"].astype(int)
    data["start_position_character"] = data["start_position"].apply(lambda cell: cell.split(",")[1].replace(" ", ""))
    data["start_position_character"] = data["start_position_character"].astype(int)
    data["end_position_line"] = data["end_position"].apply(lambda cell: cell.split(",")[0].replace(" ", ""))
    data["end_position_line"] = data["end_position_line"].astype(int)
    data["end_position_character"] = data["end_position"].apply(lambda cell: cell.split(",")[1].replace(" ", ""))
    data["end_position_character"] = data["end_position_character"].astype(int)
    data["semgrep"] = False
    data["semgrep_start_position_line"] = None
    data["semgrep_start_position_character"] = None
    data["semgrep_end_position_line"] = None
    data["semgrep_end_position_character"] = None
    data["semgrep_cwe"] = None
    data["semgrep_owasp"] = None
    data["semgrep_category"] = None
    data["semgrep_severity"] = None
    data["semgrep_likelihood"] = None
    data["semgrep_impact"] = None
    data["semgrep_confidence"] = None

    data.pop("start_position")
    data.pop("end_position")

    print(data)

    # data.keys()
    # ['projectname', 'url', 'filename', 'function', 'leading_comment', 'start_position', 'end_position']

    path_semgrep = "{}/semgrep_runs".format(args.path_semgrep)

    semgrep_repositories = os.listdir(path_semgrep)


    for file in semgrep_repositories:
        path_data = path_semgrep + "/" + file
        project = file.replace(".json", "")
        print(path_data)
        with open(path_data, 'r') as file:
            # Load the contents of the file into a Python dictionary
            data_semgrep = json.load(file)

        data_2 = data[data["projectname"] == project]

        for index in range(len(data_semgrep["results"])):
            row = data_semgrep["results"][index]
            start_line = int(row["start"]["line"]) + 1
            start_character = int(row["start"]["col"])
            end_line = int(row["end"]["line"]) + 1
            end_character = int(row["end"]["col"])
            category = row["extra"]["metadata"]["category"]
            severity = row["extra"]["severity"]
            cwe = ";".join(row["extra"]["metadata"]["cwe"]) if row["extra"]["metadata"].get("cwe", None) is not None else None
            # owasp is not always present
            owasp = ";".join(row["extra"]["metadata"]["owasp"]) if "owasp" in row["extra"]["metadata"].keys() else ""
            likelihood = row["extra"]["metadata"].get("likelihood", None)
            impact = row["extra"]["metadata"].get("impact", None)
            confidence = row["extra"]["metadata"]["confidence"]
            path = os.path.join(args.path_input, row["path"])
            result = data_2[(data_2["filename"] == path) &
                            (data_2["start_position_line"] <= start_line) &
                            (data_2["end_position_line"] >= end_line)]
            for index, row in result.iterrows():
                if data.loc[index, "semgrep"]:
                    data.loc[index, "semgrep_start_position_line"] = data.loc[index, "semgrep_start_position_line"] + ";" + str(start_line)
                    data.loc[index, "semgrep_start_position_character"] = data.loc[index, "semgrep_start_position_character"] + ";" + str(start_character)
                    data.loc[index, "semgrep_end_position_line"] = data.loc[index, "semgrep_end_position_line"] + ";" + str(end_line)
                    data.loc[index, "semgrep_end_position_character"] = data.loc[index, "semgrep_end_position_character"] + ";" + str(end_character)
                    data.loc[index, "semgrep_category"] = data.loc[index, "semgrep_category"] + ";" + category
                    data.loc[index, "semgrep_severity"] = data.loc[index, "semgrep_severity"] + ";" + severity
                    data.loc[index, "semgrep_cwe"] = data.loc[index, "semgrep_cwe"] + ";" + cwe
                    data.loc[index, "semgrep_owasp"] = data.loc[index, "semgrep_owasp"] + ";" + owasp
                    data.loc[index, "semgrep_confidence"] = data.loc[index, "semgrep_confidence"] + ";" + confidence
                    data.loc[index, "semgrep_impact"] = data.loc[index, "semgrep_impact"] + ";" + impact
                    data.loc[index, "semgrep_likelihood"] = data.loc[index, "semgrep_likelihood"] + ";" + likelihood
                else:
                    data.loc[index, "semgrep"] = True
                    data.loc[index, "semgrep_start_position_line"] = str(start_line)
                    data.loc[index, "semgrep_start_position_character"] = str(start_character)
                    data.loc[index, "semgrep_end_position_line"] = str(end_line)
                    data.loc[index, "semgrep_end_position_character"] = str(end_character)
                    data.loc[index, "semgrep_category"] = category
                    data.loc[index, "semgrep_severity"] = severity
                    data.loc[index, "semgrep_cwe"] = cwe
                    data.loc[index, "semgrep_owasp"] = owasp
                    data.loc[index, "semgrep_confidence"] = confidence
                    data.loc[index, "semgrep_impact"] = impact
                    data.loc[index, "semgrep_likelihood"] = likelihood

    data.to_csv("{}/complete_with_semgrep.csv".format(args.path_output), index=False)