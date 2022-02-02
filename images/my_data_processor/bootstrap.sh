#!/bin/bash
set -e

# activate gcloud service acct and set project
gcloud auth activate-service-account --key-file=$CREDENTIALS_FILE --project $PROJECT_ID
gcloud config set project $PROJECT_ID

# add extra dirs dir
mkdir -p /root/exports
mkdir -p /root/imports

# copy task script from gcs and run task script
gsutil cp gs://$TASK_FOLDER/$TASK_FILE_NAME ./$TASK_FILE_NAME

echo "Running $TASK_FILE_NAME..."
chmod +x "./$TASK_FILE_NAME"
source "./$TASK_FILE_NAME"