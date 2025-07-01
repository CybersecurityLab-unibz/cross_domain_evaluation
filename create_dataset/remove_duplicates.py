import argparse
import os
import pandas as pd
from tqdm import tqdm
import re
from add_information_sonarqube import load_data


def read_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--path-company", required=False)
    parser.add_argument("--path-oss", required=False)
    parser.add_argument("--path", default=None, required=False)
    parser.add_argument("--path-pmd-cpd", required=True)

    return parser.parse_args()


def load_data_custom(path):

    # You can also create a DataFrame with columns if needed
    columns = ['lines', 'tokens', 'start', 'file', 'id']
    df = pd.DataFrame(columns=columns)

    pbar = tqdm(desc="Loading data..."+path)

    with open("{}".format(path), 'r') as file:
        # Iterate over each line in the file
        idx = 0
        for line in file:
            if idx != 0:
                pbar.update(1)
                # Do something with each line, for example, print it
                split_line = line.strip().split(",")
                lines = int(split_line[0])
                tokens = int(split_line[1])
                occurrences = int(split_line[2])
                for idx_occurrences in range(occurrences):
                    start = int(split_line[3+idx_occurrences*2])
                    file = split_line[4+idx_occurrences*2]

                    df.loc[len(df)] = {
                        "lines": lines,
                        "tokens": tokens,
                        "start": start,
                        "file": file,
                        "id": idx
                    }

            idx += 1

    return df


def add_percentage(df):
    df['Project_Count'] = df.groupby('id')['project'].transform('nunique')

    df = df[df['Project_Count'] == 1].drop(columns='Project_Count')

    pbar = tqdm(total=len(df), desc="Calculating length of files...")

    # Display the result
    df["LOC"] = 0
    df["percentage"] = 0.0
    df["JACCARD"] = 0.0
    for idx, row in df.iterrows():
        file = row["file"]
        if "extracted_projects" not in file:
            file = file.replace("dataset", "dataset/extracted_projects")

        with open(file, 'r') as file:
            # Read the entire content
            content = file.read()
            LOC = len(content.split("\n"))
            df.loc[idx, "LOC"] = LOC
        pbar.update(1)

    pbar.close()

    pbar = tqdm(total=len(df), desc="Calculating percentage...")

    for idx, row in df.iterrows():
        id = row["id"]
        LOC = row["LOC"]
        tokens = row["tokens"]
        lines = row["lines"] if LOC > max(df[(df["id"] == id) & (df["tokens"] == tokens)]["lines"].tolist()) else LOC
        start_a = row["start"]
        lines_a = row["lines"]
        start_b = df[(df["id"] == id) & (df.index != idx)].sort_values(by='lines', ascending=False)["start"].tolist()[0]
        lines_b = df[(df["id"] == id) & (df.index != idx)].sort_values(by='lines', ascending=False)["lines"].tolist()[0]
        LOC_b = df[(df["id"] == id) & (df.index != idx)].sort_values(by='lines', ascending=False)["LOC"].tolist()[0]

        # Lines of code for each row
        range_A = set(range(start_a, lines_a))
        range_B = set(range(start_b, lines_b))
        range_A_1 = set(range(1, LOC))
        range_B_1 = set(range(1, LOC_b))
        intersection = len(range_A.intersection(range_B))
        union = len(range_A_1.union(range_B_1))

        # Calculate Jaccard index
        jaccard_index = intersection / union * 100 if union != 0 else 0

        df.loc[idx, "JACCARD"] = jaccard_index

        if row["project"] == "devign":
            percentage = lines/(LOC/2) * 100
            #print(LOC, lines)
            #print(LOC, row["lines"])
            #print(percentage)
            if percentage > 100:
                percentage = lines/(LOC/1) * 100
            #print(percentage)
            #print(len(content.split("\n")))
            #print("-------------" + str(row["id"]))
            df.loc[idx, "percentage"] = percentage
        else:
            df.loc[idx, "percentage"] = lines/LOC * 100
        pbar.update(1)

    pbar.close()

    return df

def get_relevant_files(df):
    df = df[df["JACCARD"] > 99]
    df.drop_duplicates(subset=['id'], keep='first', inplace=True)
    df['project_id'] = df['file'].str.extract(r'(\d+)\.php$', flags=re.IGNORECASE)
    return df


def remove_by_ID(data, JACCARD):
    for idx, row in JACCARD.iterrows():
        id = int(row["project_id"])
        if id in data.index:
            data.drop([id], inplace=True)
    return data


if __name__ == "__main__":
    args = read_args()
    print(args)
    data = None

    if args.path is None and args.path_company is not None and args.path_oss is not None:
        data = pd.concat([load_data(args.path_company), load_data(args.path_oss)], ignore_index=True)
    elif args.path is not None and args.path_company is None and  args.path_oss is None:
        data = load_data(args.path)
    else:
        print("Issue in the configuration of the paths!")
        print("Only path or path-company and path-oss are allowed to be set...")
        print("Exiting...")
        quit()

    names = os.listdir(args.path_pmd_cpd)
    names = [file for file in names if not re.search(r'\d{2}\.csv$', file)]
    total_removed = 0

    names = list(set([name for name in names for project in data["projectname"].unique() if project in name]))

    assert len(names) == len(data["projectname"].unique()), "Error - not all projects are included!"

    for name in names:
        print("----------------------------")
        filepath = "{}/{}".format(args.path_pmd_cpd, name)
        if not os.path.exists(filepath):
            print("skipped...", filepath)
            continue
        data_pmd = None
        if name != "duplicated_code_report_dolibarr.csv" and name != "duplicated_code_report_splashSyncDolibar.csv":
            data_pmd = load_data_custom(filepath)
        else:
            data_1 = load_data_custom(filepath.replace(".csv", "_12.csv"))
            data_2 = load_data_custom(filepath.replace(".csv", "_13.csv"))
            data_3 = load_data_custom(filepath.replace(".csv", "_14.csv"))
            data_4 = load_data_custom(filepath.replace(".csv", "_23.csv"))
            data_5 = load_data_custom(filepath.replace(".csv", "_24.csv"))
            data_6 = load_data_custom(filepath.replace(".csv", "_34.csv"))

            data_pmd = pd.concat([data_1, data_2, data_3, data_4, data_5, data_6], ignore_index=False)

        project = name.split("_")[-1].split(".csv")[0]
        data_pmd["project"] = project
        data_pmd = add_percentage(data_pmd)
        data_pmd = get_relevant_files(data_pmd)
        total_removed = total_removed + len(data_pmd)
        print(f"Total removed: {total_removed}")
        if len(data_pmd) != 0:
            data = remove_by_ID(data, data_pmd)

    print("total instances removed", total_removed)
    if args.path is None:
        data.to_csv("complete.csv", index=False)
    if args.path is not None:
        data.to_csv(re.sub(".csv", "_without_duplicates.csv", args.path), index=False)