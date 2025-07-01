import pandas as pd
import tensorflow as tf
from f1 import F1
from linear_decay_with_warmup import LinearDecayWithWarmup
import os

def load_model(path):
    model = tf.keras.models.load_model(path, custom_objects={'F1': F1, 'LinearDecayWithWarmup': LinearDecayWithWarmup})
    return model


def calculate_scores(predictions, label):

    if hasattr(label, "ndim") and label.ndim > 1:
        label = label.squeeze()

    tp = 0
    tn = 0
    fp = 0
    fn = 0

    for index in range(len(predictions)):
        prediction = predictions[index] if isinstance(predictions[index], bool) else predictions[index][0] > 0.5

        if(label[index] == True):
            if(prediction == True):
                tp = tp + 1
            else:
                fn = fn + 1
        else:
            if(prediction == False):
                tn = tn + 1
            else:
                fp = fp + 1

    print("tp -> ", tp)
    print("tn -> ", tn)
    print("fp -> ", fp)
    print("fn -> ", fn)

    precision = tp / (tp + fp) if tp + fp > 0 else -1
    recall = tp / (tp + fn) if tp + fn > 0 else -1
    accuracy = (tp + tn) / (tp + tn + fp + fn)
    f1 = 2 * ((precision * recall) / (precision + recall)) if precision + recall > 0 else -1

    print("\nprecision -> ", precision)
    print("recall -> ", recall)
    print("accuracy -> ", accuracy)
    print("f1 -> ", f1)

def read_file(file_path):
    with open(file_path, 'r') as file:
        file_content = file.read()
    return file_content


def load_data(data):

    paths = [elem[0] for elem in data]
    functions = [elem[1] for elem in data]
    starts = [elem[2] for elem in data]
    ends = [elem[3] for elem in data]

    df = pd.DataFrame(functions, columns=["Code"])

    data = tf.data.Dataset.from_tensor_slices((df["Code"]))

    return paths, data, starts, ends

