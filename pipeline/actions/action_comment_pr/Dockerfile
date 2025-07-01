FROM python:3.11.6-alpine

# Install git
RUN apk add --no-cache \
    git \
    curl \
    vim

# COPY scripts
COPY main.py /main.py
#COPY requirements.txt /tmp/requirements.txt

# Install dependencies
#RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Make the script executable
RUN chmod +x /main.py

# Set the entrypoint to the action script
ENTRYPOINT ["python", "/main.py"]
