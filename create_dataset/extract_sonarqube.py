import argparse
import os
import pandas as pd
import requests
from tqdm import tqdm
import json

def get_total(username, password, host, port, project_key, file):
    url = f"http://{host}:{port}/api/issues/search"

    params = {
        "componentKeys": project_key,
        "pageSize": 1,
        "page": 1,
        "languages": "php",
        "files": file
    }

    response = requests.get(url, auth=(username, password), params=params)

    if response.status_code == 200:
        data = response.json()

        return data.get("total", 0)
    else:
        print(f"Error: {response.status_code} - {response.text}")


def fetch_all_sonarqube_issues(username, password, host, port, project_key, output_path):
    url = f"http://{host}:{port}/api/issues/search"

    data = pd.read_csv(os.path.join(output_path.split("/")[0], "complete.csv"), sep=",")
    data = data[data["projectname"] == project_key]

    paths = ["/".join(path.split("/")[3:]) for path in list(set(data["filename"].tolist()))]

    all_issues = []

    print(len(paths))

    pbar = tqdm(total=len(paths), desc="Loading data...")

    for path in paths:
        total = get_total(username, password, host, port, project_key, path)
        page_size: int = 100
        page = 1
        while True:
            params = {
                "componentKeys": project_key,
                "pageSize": page_size,
                "page": page,
                "languages": "php",
                "files": path
            }

            response = requests.get(url, auth=(username, password), params=params)

            if response.status_code == 200:
                data = response.json()
                issues = data.get("issues", [])

                all_issues.extend(issues)

                if total < page * page_size:
                    break
                page += 1
            else:
                print(f"Error: {response.status_code} - {response.text}")
                break

        pbar.update(1)

    pbar.close()

    all_issues = [issue for issue in tqdm(all_issues, desc="Filtering issues with 'textRange'") if "textRange" in issue]

    with open(output_path+"/"+project_key+'.json', 'w') as outfile:
        json.dump(all_issues, outfile, indent=4)

    print(f"Export completed. Total {len(all_issues)} issues saved to " +"data_oss/sonarqube_runs/"+project_key+'.json')


def read_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True)
    parser.add_argument("--project-key", required=True)
    parser.add_argument("--output-path", default="data_oss/sonarqube_runs")

    return parser.parse_args()

if __name__ == "__main__":
    args = read_args()

    fetch_all_sonarqube_issues(args.username, args.password, args.host, args.port, args.project_key, args.output_path)
