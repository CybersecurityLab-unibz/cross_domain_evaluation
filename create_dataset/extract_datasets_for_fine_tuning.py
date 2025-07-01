import argparse
import os.path

import pandas as pd
import tqdm
from sklearn.model_selection import train_test_split

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def read_args():

    parser = argparse.ArgumentParser()

    parser.add_argument("--path-input", required=True)
    parser.add_argument("--path-output", required=False, default=None, help="If not set, it is the same as the input path!")
    parser.add_argument("--include-semgrep", default=False, type=str2bool)
    parser.add_argument("--include-leading-comments", default=False, type=str2bool)
    parser.add_argument("--balance-train", default=False, type=str2bool)
    parser.add_argument("--per-dataset", default=False, type=str2bool)
    parser.add_argument("--threshold", default=4934, type=int)
    parser.add_argument("--folder-name", default="split_dataset")

    return parser.parse_args()


if __name__ == "__main__":
    args = read_args()

    if args.path_output is None:
        args.path_output = "/".join(args.path_input.split("/")[:-1])

    data = pd.read_csv(args.path_input)

    if args.include_leading_comments:
        data["input"] = data.apply(lambda row: row["function"] if pd.isna(row["leading_comment"]) else f"{row["leading_comment"]}\n{row["function"]}", axis=1)
    else:
        data["input"] = data["function"]

    data["class"] = False

    pbar = tqdm.tqdm(total=len(data))

    for index, row in data.iterrows():
        semgrep_severity = row["semgrep_severity"]
        sonarqube_severity = row["sonarqube_severity"]
        if args.include_semgrep:
            data.loc[index, "class"] = True if pd.isna(semgrep_severity) is False and "error" in semgrep_severity.lower() else data.loc[index, "class"]
        data.loc[index, "class"] = True if pd.isna(sonarqube_severity) is False and "major" in sonarqube_severity.lower() else data.loc[index, "class"]
        data.loc[index, "class"] = True if pd.isna(sonarqube_severity) is False and "critical" in sonarqube_severity.lower() else data.loc[index, "class"]
        data.loc[index, "class"] = True if pd.isna(sonarqube_severity) is False and "blocker" in sonarqube_severity.lower() else data.loc[index, "class"]

        pbar.update(1)

    pbar.close()

    columns = ['input', 'class', "sonarqube_severity"]

    if args.include_semgrep:
        columns.append("semgrep_severity")

    data = data[columns]

    train, rest = train_test_split(data, test_size=0.2, random_state=42)

    val, test = train_test_split(rest, test_size=0.5, random_state=42)

    if args.balance_train:
        train_positive = train[train["class"] == True]
        train_negative = train[train["class"] == False]

        if args.per_dataset:
            args.threshold = len(train_positive) if len(train_positive) <= len(train_negative) else len(train_negative)

        train_positive = train_positive.sample(n=args.threshold)
        train_negative = train_negative.sample(n=args.threshold)

        train = pd.concat([train_positive, train_negative])
        train = train.sample(frac=1)

    print(f"Train: {len(train)}, Validation: {len(val)}, Test: {len(test)}")

    if os.path.exists(os.path.join(args.path_output, args.folder_name)) is False:
        os.makedirs(os.path.join(args.path_output, args.folder_name))

    train.to_csv(os.path.join(args.path_output, args.folder_name, "train.csv"), index=True)
    val.to_csv(os.path.join(args.path_output, args.folder_name, "val.csv"), index=True)
    test.to_csv(os.path.join(args.path_output, args.folder_name, "test.csv"), index=True)