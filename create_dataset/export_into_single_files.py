import argparse
import os
import pandas as pd
from tqdm import tqdm
from add_information_sonarqube import load_data
from sklearn.model_selection import train_test_split


def read_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--path-company", required=False)
    parser.add_argument("--path-oss", required=True)
    parser.add_argument("--path-output", required=True)

    return parser.parse_args()


def write_to_file(file_path, content):
    try:
        with open(file_path, "w") as file:
            file.write(content)
    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")



def export_files(data, suffix):
    pbar = tqdm(total=len(data), desc="Writing files")

    for index, row in data.iterrows():
        leading_comment = row["leading_comment"] + "\n" if pd.notna(row["leading_comment"]) else ""
        function_with_leading_comment = leading_comment + row["function"]
        if not os.path.exists(os.path.join(args.path_output, row["projectname"] + suffix)):
            os.makedirs(os.path.join(args.path_output, row["projectname"] + suffix))
        path = os.path.join(args.path_output, row["projectname"] + suffix, str(index) + ".php")
        write_to_file(path, function_with_leading_comment)

        pbar.update(1)

    pbar.close()

if __name__ == "__main__":
    args = read_args()
    print(args)

    #data = pd.concat([load_data(args.path_company), load_data(args.path_oss)], ignore_index=True)
    data = pd.concat([load_data(args.path_oss)], ignore_index=True)


    pbar = tqdm(total=len(data), desc="Writing files")

    for index, row in data.iterrows():
        leading_comment = row["leading_comment"] + "\n" if pd.notna(row["leading_comment"]) else ""
        function_with_leading_comment = leading_comment + row["function"]
        if not os.path.exists(os.path.join(args.path_output, row["projectname"])):
            os.makedirs(os.path.join(args.path_output, row["projectname"]))
        path = os.path.join(args.path_output, row["projectname"], str(index) + ".php")
        write_to_file(path, function_with_leading_comment)

        pbar.update(1)

    pbar.close()
    
    '''

    project = "dolibarr"
    data = data[data["projectname"] == project]

    data__1, data__2 = train_test_split(data, random_state=42, test_size=0.5)
    data_1, data_2 = train_test_split(data__1, random_state=42, test_size=0.5)
    data_3, data_4 = train_test_split(data__2, random_state=42, test_size=0.5)

    export_files(pd.concat([data_1, data_2]), "_12")
    export_files(pd.concat([data_1, data_3]), "_13")
    export_files(pd.concat([data_1, data_4]), "_14")
    export_files(pd.concat([data_2, data_3]), "_23")
    export_files(pd.concat([data_2, data_4]), "_24")
    export_files(pd.concat([data_3, data_4]), "_34")
    '''

