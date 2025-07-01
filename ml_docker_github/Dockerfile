# For local development
#FROM ubuntu:22.04
# For production
FROM --platform=linux/amd64 ubuntu:22.04

ENV DEBIAN_FRONTEND noninteractive

RUN apt update
RUN apt install -y software-properties-common
RUN apt install -y wget
RUN apt install -y curl
RUN apt install -y python3-pip
RUN apt install -y vim
RUN apt install -y git

# packages to install
COPY requirements.txt /tmp/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# COPY code
COPY ml_model/ /vulnerability-detection/ml_model/

# overwrite the error of keras
RUN sed -i '39s/^/#/' /usr/local/lib/python3.10/dist-packages/transformers/modeling_tf_utils.py

COPY main.py /vulnerability-detection/main.py
COPY models/ /vulnerability-detection/models
COPY data_encoders.py /vulnerability-detection/data_encoders.py
COPY model_strategy.py /vulnerability-detection/model_strategy.py
COPY scores_calculator.py /vulnerability-detection/scores_calculator.py
COPY utils.py /vulnerability-detection/utils.py
COPY f1.py /vulnerability-detection/f1.py
COPY linear_decay_with_warmup.py /vulnerability-detection/linear_decay_with_warmup.py
COPY codebert_tokenizer.py /vulnerability-detection/codebert_tokenizer.py
COPY language_parser.py /vulnerability-detection/language_parser.py
COPY extract_functions.py /vulnerability-detection/extract_functions.py
COPY vendor/ /vulnerability-detection/vendor

RUN mkdir -p /vulnerability-detection/build