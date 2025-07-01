import argparse
import pandas as pd
from datasets import Dataset
from torch.utils.hipify.hipify_python import str2bool
from transformers import RobertaTokenizer, RobertaForSequenceClassification, Trainer, TrainingArguments
import numpy as np
import os
import re
import torch
from transformers.training_args import trainer_log_levels


def tokenize_function(examples, tokenizer):
    return tokenizer(examples["input"], padding="max_length", truncation=True)


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)

    TP = FP = TN = FN = 0

    for pred, label in zip(predictions, labels):
        if pred == 1 and label == 1:
            TP += 1
        elif pred == 1 and label == 0:
            FP += 1
        elif pred == 0 and label == 0:
            TN += 1
        elif pred == 0 and label == 1:
            FN += 1

    accuracy = (TP + TN) / (TP + FP + TN + FN) if (TP + FP + TN + FN) > 0 else 0
    precision = TP / (TP + FP) if (TP + FP) > 0 else 0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "TP": TP,
        "FP": FP,
        "TN": TN,
        "FN": FN
    }


def load_data(path, filename):
    df = pd.read_csv(os.path.join(path, filename))
    df["label"] = df["class"].astype(int)
    return Dataset.from_pandas(df)


def evaluate_model(df, model_path, tokenizer, data):
    model = RobertaForSequenceClassification.from_pretrained(model_path)
    df = df.map(lambda x: tokenize_function(x, tokenizer), batched=True)

    trainer = Trainer(
        model=model,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
    )

    results = trainer.evaluate(eval_dataset=df)
    print("Test set evaluation results:", results)

    new_row = [
        model_path.split("/")[-1],
        results.get("eval_loss"),
        results.get("eval_accuracy"),
        results.get("eval_precision"),
        results.get("eval_recall"),
        results.get("eval_f1"),
        results.get("eval_TP"),
        results.get("eval_FP"),
        results.get("eval_TN"),
        results.get("eval_FN")
    ]

    if len(new_row) < len(data.columns):
        new_row += [""] * (len(data.columns) - len(new_row))

    data.loc[len(data)] = new_row
    return data

# Custom Trainer with weighted loss
class WeightedLossTrainer(Trainer):
    def __init__(self, weights=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.weights = weights

    def compute_loss(self, model, inputs, return_outputs=False):
        labels = inputs.get("labels")
        outputs = model(**inputs)
        logits = outputs.get("logits")
        loss_fct = torch.nn.CrossEntropyLoss(weight=self.weights.to(model.device) if self.weights is not None else None)
        loss = loss_fct(logits, labels)
        return (loss, outputs) if return_outputs else loss


def train_model(train, val, tokenizer, output_dir, weighted_loss=False):
    # Tokenize datasets
    train = train.map(lambda x: tokenize_function(x, tokenizer), batched=True)
    val = val.map(lambda x: tokenize_function(x, tokenizer), batched=True)

    model = RobertaForSequenceClassification.from_pretrained("microsoft/codebert-base", num_labels=2)

    weights = None
    TrainerClass = Trainer

    if weighted_loss:
        # Calculate class weights based on inverse frequency
        labels = train["label"]
        labels = [int(label) for label in labels]
        class_counts = np.bincount(labels)
        total_count = sum(class_counts)
        class_weights = [1 - (count / total_count) for count in class_counts]
        weights = torch.tensor(class_weights, dtype=torch.float)
        TrainerClass = WeightedLossTrainer

    training_args = TrainingArguments(
        output_dir=output_dir,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=None,
        learning_rate=2e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=10,
        logging_dir=f"{output_dir}/logs",
        logging_steps=10,
        load_best_model_at_end=True,
    )

    trainer = TrainerClass(
        model=model,
        args=training_args,
        train_dataset=train,
        eval_dataset=val,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
        weights=weights  # Only used by WeightedLossTrainer
    )

    trainer.train()
    trainer.save_model(f"{output_dir}/final_model")
    tokenizer.save_pretrained(f"{output_dir}/final_model")


def read_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path-data", required=True)
    parser.add_argument("--path-results", required=True)
    parser.add_argument("--file-name-train", default="train.csv")
    parser.add_argument("--file-name-val", default="val.csv")
    parser.add_argument("--file-name-test", default="test.csv")
    parser.add_argument("--model", default="microsoft/codebert-base")
    parser.add_argument("--mode", default="train", choices=["train", "test", "cross-val"])
    parser.add_argument("--weighted-loss", type=str2bool)
    return parser.parse_args()


def check_files(path):
    assert os.path.isfile(os.path.join(path, "val_eval.csv")), f"File 'val_eval.csv' does not exist under the path {path}"
    assert os.path.isfile(os.path.join(path, "test_eval.csv")), f"File 'test_eval.csv' does not exist under the path {path}"


def find_best_checkpoint(data):
    data['checkpoint_num'] = data['epoch'].str.extract(r'(\d+)')
    data['checkpoint_num'] = pd.to_numeric(data['checkpoint_num'], errors='coerce')
    data['checkpoint_num'] = data['checkpoint_num'].fillna(np.inf)
    data = data.sort_values(by='checkpoint_num')
    data = data.drop(columns='checkpoint_num')

    best_epoch = 0
    best_f1 = 0
    count = 0

    for index, row in data.iterrows():
        f1 = row["f1"]
        epoch = row["epoch"]

        count += 1
        if f1 - best_f1 > 0.001:
            best_f1 = f1
            best_epoch = epoch
            count = 0
        elif count == 5:
            break

    return best_epoch


def test_model_against_other_parts(data, model: str, path_data: str, testAgainst: str, type: str):
    val = load_data(os.path.join(path_data, testAgainst), f"{type}.csv")
    data = evaluate_model(val, model, tokenizer, data)
    index = len(data) - 1
    data.loc[index, "model"] = model.split("/")[-2]
    data.loc[index, "dataset"] = testAgainst
    data.loc[index, "type"] = type
    return data


if __name__ == "__main__":
    args = read_args()
    print(args)

    tokenizer = RobertaTokenizer.from_pretrained("microsoft/codebert-base")

    if args.mode == "train":
        train_dataset = load_data(args.path_data, args.file_name_train)
        val_dataset = load_data(args.path_data, args.file_name_val)
        train_model(train_dataset, val_dataset, tokenizer, args.path_results, weighted_loss=args.weighted_loss)

    elif args.mode == "test":
        test_dataset = load_data(args.path_data, args.file_name_test)

        checkpoints = []
        for item in os.listdir(args.path_results):
            full_path = os.path.join(args.path_results, item)
            if os.path.isdir(full_path) and (item.startswith('check') or item.startswith('final')):
                checkpoints.append(full_path)

        data = pd.DataFrame(columns=["epoch", "loss", "accuracy", "precision", "recall", "f1", "TP", "FP", "TN", "FN"])

        for checkpoint in checkpoints:
            data = evaluate_model(test_dataset, checkpoint, tokenizer, data)

        data.to_csv(os.path.join(args.path_results, re.sub(".csv", "_eval.csv", args.file_name_test)), index=False)

    elif args.mode == "cross-val":
        path_data = os.path.dirname(args.path_data)
        path_results = os.path.dirname(args.path_results)

        assert os.path.isdir(os.path.join(path_results, "industry")), f"Folder 'industry' does not exist under the path {path_results}"
        assert os.path.isdir(os.path.join(path_results, "oss_large")), f"Folder 'oss_large' does not exist under the path {path_results}"
        assert os.path.isdir(os.path.join(path_results, "oss_similar")), f"Folder 'oss_similar' does not exist under the path {path_results}"

        check_files(os.path.join(path_results, "industry"))
        check_files(os.path.join(path_results, "oss_large"))
        check_files(os.path.join(path_results, "oss_similar"))

        datasets = ["industry", "oss_large", "oss_similar"]

        data = pd.DataFrame(columns=["epoch", "loss", "accuracy", "precision", "recall", "f1", "TP", "FP", "TN", "FN", "model", "dataset", "type"])

        for dataset in datasets:
            data_val = pd.read_csv(os.path.join(path_results, dataset, "val_eval.csv"))
            best_checkpoint = find_best_checkpoint(data_val)
            datasets2validateAgainst = [x for x in datasets if dataset != x]

            data = test_model_against_other_parts(data, os.path.join(path_results, dataset, best_checkpoint), path_data, datasets2validateAgainst[0], "val")
            data = test_model_against_other_parts(data, os.path.join(path_results, dataset, best_checkpoint), path_data, datasets2validateAgainst[0], "test")
            data = test_model_against_other_parts(data, os.path.join(path_results, dataset, best_checkpoint), path_data, datasets2validateAgainst[1], "val")
            data = test_model_against_other_parts(data, os.path.join(path_results, dataset, best_checkpoint), path_data, datasets2validateAgainst[1], "test")

        data.to_csv(os.path.join(path_results, "cross_val.csv"), index=False)
