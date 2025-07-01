import time
from utils import load_model, load_data
from model_strategy import ModelStrategy
from argparse import ArgumentParser
from extract_functions import extract_functions, write2environment
import os
import subprocess

ENV_VARIABLE = "FILES"

def test_saved_model(model_name, model_file, separate_comments, truncation_side, test_data, limit):
    print('Testing saved model {}'.format(model_name))

    model = load_model(model_file)

    model_factory = ModelStrategy(model_name)
    encoder = model_factory.create_encoder(separate_comments, truncation_side)

    ds_test_encoded = encoder.encode_examples(test_data, limit)
    predictions = model.predict(ds_test_encoded)

    return predictions


def str2bool(v):
    parser = ArgumentParser()
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise parser.error('Boolean value expected.')

def read_args():

    parser = ArgumentParser()

    parser.add_argument('--model', choices=['satdonly', 'vulonly', 'vulsatd', 'multitask'], required=False, default="vulonly")
    parser.add_argument('--mode', choices=['hyper-analysis', 'train', 'test', 'test-combination'], required=False, default="test")
    parser.add_argument('--dataset', type=str, required=False)
    parser.add_argument('--original-parameter', type=str, required=False)
    parser.add_argument('--dataset-code-column', type=str, required=False, default="Code")
    parser.add_argument('--separate-comments', type=str2bool, default=False)
    parser.add_argument('--truncation-side', choices=['left', 'right'], default='right')
    parser.add_argument('--shared-layer', type=str2bool, default=True)
    parser.add_argument('--model-file', type=str, default="/vulnerability-detection/ml_model",
                        help='In test mode, the file to load the weights from.')
    parser.add_argument('--store-weights', type=bool, default=False,
                        help='If the weights should be saved in a file.')
    parser.add_argument('--output-dir', type=str, default='stored_models',
                        help='The output directory to save weights if store-weights is enabled.')

    parser.add_argument('--epochs', type=int, default=10)
    parser.add_argument('--learning-rate', type=float, default=5e-5)
    parser.add_argument('--batch-size', type=int, default=32)
    parser.add_argument('--dropout-prob', type=float, default=0.2)
    parser.add_argument('--l2-reg-lambda', type=float, default=0)
    parser.add_argument('--limit', type=int, default=-1)
    parser.add_argument('--gamma', type=float, required=False)

    # Arguments needed for openshift
    #parser.add_argument("--path", type=str, required=True)
    #parser.add_argument("--base-branch", type=str, required=True)
    #parser.add_argument("--result-path-comment", type=str, required=True)
    #parser.add_argument("--result-path-comment-per-file", type=str, required=True)

    return parser.parse_args()

def convert_seconds_to_hhmmss(seconds):
    hours = seconds // 3600
    seconds_remaining = seconds % 3600
    minutes = seconds_remaining // 60
    seconds_remaining = seconds_remaining % 60
    return f"{hours:02d}:{minutes:02d}:{seconds_remaining:02d}"


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


def write2environment(variable, data):
    env_file = os.getenv('GITHUB_OUTPUT')

    with open(env_file, "a") as file:
        file.write("{}='{}'".format(variable, data))

if __name__ == "__main__":

    base_branch = os.getenv('INPUT_BASE-BRANCH')
    branch = os.getenv('INPUT_BRANCH')

    run_git_command("git fetch")
    run_git_command("git checkout {}".format(base_branch))
    run_git_command("git checkout {}".format(branch))

    args = read_args()
    print(args)

    start_time = time.time()

    data2BeTested = extract_functions(base_branch, ENV_VARIABLE)

    if len(data2BeTested) == 0:
        print("No Functions detected!")
        print("Exiting...")
        quit()

    paths, data2BeTested, starts, ends = load_data(data2BeTested)

    if args.mode == "test":
        predictions = test_saved_model(args.model,
                                       args.model_file,
                                       args.separate_comments,
                                       args.truncation_side,
                                       data2BeTested,
                                       args.limit)

        # Convert the two-dimensional array to a one-dimensional array
        array_1d = [item for sublist in predictions for item in sublist]

        # Round the numbers to 0 or 1
        rounded_array = [1 if num >= 0.5 else 0 for num in array_1d]

        # Concatenate the array into a string with ";" as the separator
        result = []
        for index in range(0, len(rounded_array)):
            if rounded_array[index] == 1:
                result.append(str(starts[index]))
                result.append(str(starts[index]))
                # Since we want to have at the header of a function the comment,
                # otherwise uncomment the line below and comment the line above
                #result.append(str(ends[index]))
                result.append(paths[index])
                result.append("In the following function a vulnerability was detected.")

        print(result)

        result = ';'.join(result) if len(result) > 0 else "NOTHING FOUND!"
        result = '"' + result + '"'

        print("------")
        print("result")
        print(result)
        print("------")

        write2environment(ENV_VARIABLE, result)


    else:
        print("The selected mode ({}) is not supported, only 'test' is available.".format(args.mode))

    print("--- %s seconds taken to run ---" % convert_seconds_to_hhmmss(int(time.time() - start_time)))

## Commands to trigger the python scripts

# To test the extraction of functions from a repository
# /workspace/output/test-security-miner-pipeline-6n24mt/icingaweb2-module-slm
# cd /vulnerability-detection && python3 extract_functions.py

# To execute the ML
# cd /vulnerability-detection && python3 main.py --result-path-comment-per-file /output.txt --path /test --base-branch main && cd / && ls -l && vim output.txt