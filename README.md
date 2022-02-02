# Carnegie Foundation Data Processing Project

This project contains config files, artifacts, and scripts for use within the data processing pipeline orchestrated with Apache Airflow/Cloud Composer.

## Overview

The pipeline is operated by Google Cloud Composer which is a hosted Apache Airflow service deployed with Google Kubernetes Engine. DAGs, their tasks, and the requisite dockerfiles will be defined here, and a custom deploy script will upload the files to their respective Cloud Storage destinations for use by Airflow and tasks.

Our DAGs will mainly be using the `KubernetesPodOperator` to spin up each task in its own container. The entrypoint of the container will be a small "bootstrap" script that will authenticate with Google Cloud, download the task's requisite shell script, and execute it.

### `dags`

Contains the DAGs and tasks code for Airflow. Task code is separate for maintainability.

### `deployments`

Contains TARs of previous deployments. Nothing in this directory will ever be tracked in the repository. The deploy script will be operating with this directory, creating TARs of the current state of files before copying them to Cloud Storage. Any TAR here can also be used in a deployment, as a sort of "rollback" deployment.

### `images`

Contains the Dockerfiles and relevant files for any container images we'll be using

### `task_files`

This is the meat and potatoes of the project. All files needed for execution in the pod by the task will live here. This will need to include a shell script that will be downloaded and run by the container. Within the shell script, we will execute all code needed for the particular task, so include any relevant R scripts, python scripts, etc here as well.

### `common_files`

Files used by multiple tasks will live here. These will be things like correspondence tables, crosswalks, cut points, codebooks, etc.

### `config`

Contains Airflow config files (`airflow.cfg`) for each version of your Cloud Composer environments.

### `plugins`

Custom plugins for Airflow

### Prerequisites

To handle task creation and interface with Google Cloud, you'll need the following packages/libraries installed on your machine:
```
google-cloud-sdk
git-lfs
virtualbox
kubectl
docker-machine
docker
pyenv
pyenv-virtualenv
```

## Setup

You'll need to first set up a Cloud Composer environment, if you have not done so. Here are the settings we've used:

- Location: us-central1
- Service account: default Compute Engine service account
- Image version: composer-1.17.3-airflow-1.10.15
- Python version: 3
- Web server machine type: composer-n1-webserver-2 (2 vCPU, 1.6 GB memory)
- Cloud SQL machine type: db-n1-standard-2 (2 vCPU, 7.5 GB memory)
- Workers:
    - Nodes: 3
    - Disk size: 50gb
    - Machine type: n1-standard-1
- Number of schedulers: 1
- GKE Cluster
    - Zone: us-central1-c

Once the deployment is finished, make sure you copy the Cloud Storage bucket name to the deploy script in the `bucket` variable.

**Secrets**

For whatever service account you used when creating the Cloud Composer environment, you'll need to make a key. In the cloud console, go to IAM & Admin > Service Accounts, click the three dots on the service account, then select Manage Keys. Add a new JSON key and copy this file to the project root. Do not track it in your repository.

Next, we need to add it as a Kubernetes Secret. On your machine, run the following command, filling in the arguments. You can find the info needed by going to your Cloud Composer environment in the console and clicking the Environment Details tab.
```
$ gcloud container clusters get-credentials CLUSTER_ID \
--zone ZONE \
--project PROJECT
```
This command gives us connection credentials to the cluster.

Add the key file we downloaded a bit ago as a secret:
```
$ kubectl create secret generic KEY_NAME \
--from-file REMOTE_KEY_NAME.json=./LOCAL_KEY_NAME.json
```

Verify the secret's existence by going to Kubernetes Engine > Configuration in the console.

**Environment Variables**

From the console, go to your Cloud Composer environment and open the Airflow UI. Within Airflow, go to Admin > Variables.

We're gonna create three variables here:

- cloud_storage_bucket: BUCKET
- project_id: PROJECT
- valid_instantiators: airflow\r\nuser 1\r\nuser 2

Fill in the name of the bucket created for Cloud Composer, and fill in the project id that you're running Cloud Composer in.

`valid_instantiators` is a newline-separated list of the "instantiators" that will be triggering DAGs. I've added this so that when we manually trigger a DAG, we can specify an instantiator in the `conf` JSON, which will then be checked against this list. The "instantiator" specified will be used when creating a custom run ID, and this custom run ID will be used as the output folder in Cloud Storage for a DAG run.

**Airflow Config**

You can define a custom Airflow configuration by including an `airflow.cfg` file in the relevant folders in the `config` folder. I recommend waiting until your Cloud Composer environment is fully instantiated, then copying the .cfg file from Cloud Storage into the relevant folder in this repository (`config/staging` for your staging environment, `config/production` for your production environment).

Settings you can add/modify can be found on the [Airflow configuration page](https://airflow.apache.org/docs/apache-airflow/stable/configurations-ref.html).

**Airflow Plugins**

If you wish to write plugins for Airflow, place them within the `plugins` folder. Follow the instructions and examples on the [Airflow plugins page](https://airflow.apache.org/docs/apache-airflow/stable/plugins.html) when creating a plugin.

Plugins are supported in all Cloud Composer and Airflow versions, with the exception of UI/web server plugins being unavailable with Cloud Composer 1 and Airflow 2.

***IMPORTANT:*** If you are using the Cloud Composer 1 environment with Airflow 1 and are writing a UI/web server plugin (to be loaded/used within the Airflow UI), *you need to disable DAG Serialization in order for it to work.* Based on [this page](https://cloud.google.com/composer/docs/concepts/versioning/composer-versioning-overview), DAG Serialization disables UI plugins, *and it is turned on by default.* To do this, you'll need to disable two core config settings in your airflow.cfg file. Visit [this page](https://cloud.google.com/composer/docs/dag-serialization#disable) for more information.

### Docker Images

If you are creating any additional Docker images, you'll need to follow the instructions below.

Create a new directory within `images` with the name of your image, then create your dockerfile and any additional files there.

In a terminal window or tab, navigate to that directory and build the image:
```
$ docker build -t IMAGE_NAME .
```

Tag the image and push it to a container registry (e.g. Google Container Registry)
```
$ docker tag IMAGE_NAME HOSTNAME/PROJECT-ID/IMAGE_NAME
$ gcloud auth configure-docker
$ docker push HOSTNAME/PROJECT-ID/IMAGE_NAME
```

`HOSTNAME` is the hostname of the container registry you're pushing to (in our case, `us.gcr.io`)

**Updating an image**

When you need to update the Docker image, just rebuild and push it:
```
$ docker build -t IMAGE_NAME .
$ docker push HOSTNAME/PROJECT-ID/IMAGE_NAME
```

If you want to completely rebuild the image, you can pass `--no-cache` to the `docker build` command. Then push the image to the registry.

Alternatively, for a more thorough solution, you can delete the old image and build it again. Then push.
```
$ docker rmi --force IMAGE_NAME
$ docker build -t IMAGE_NAME .
$ docker tag IMAGE_NAME HOSTNAME/PROJECT-ID/IMAGE_NAME
$ docker push HOSTNAME/PROJECT-ID/IMAGE_NAME
```

This can help if you've modified your Dockerfile but `docker push` results in all "Layer already exists" messages.

**Testing the image locally**

If you are testing the `cf_data_processor` image or another similar image _locally_, pay attention to the `ENTRYPOINT` directive in the dockerfile. If you are running a shell script as the entrypoint, every container spun up will start up and instantly shut down. To get around this, we need to override the `ENTRYPOINT` directive to keep the container alive. Then, once it's running, we can connect to it.

We'll need to run two commands here. First, start up a container and override the entrypoint:
```
$ docker run --name CONTAINER_NAME -dit --entrypoint=/bin/bash IMAGE_NAME
```

For CONTAINER_NAME use something unique and/or related to IMAGE_NAME.

Once it's running, we can initialize a shell session and connect to it:
```
$ docker exec -it CONTAINER_NAME /bin/bash
```

Once you're done testing, to stop the container and delete it, run:
```
$ docker stop CONTAINER_NAME && docker rm CONTAINER_NAME
```

## Misc

Below are some assorted tips and tricks for working with Cloud Composer and assets in this repo.

**Refreshing Cloud Composer environment/Airflow**

If you want to redeploy your Cloud Composer environment, you can do so by adding a "bogus" environment variable and modifying the value.

Navigate to the Cloud Composer section in the Google Cloud Console and click on your environment. Then go to the Environment Variables tab. Now add a bogus key and value and save. Or, if you already have a bogus variable, just edit the value and save. This will redeploy the Cloud Composer environment. This may take up to 15 minutes to complete.

If you have made changes to your Airflow config file, or are debugging DAG/plugin loading errors, you may need to restart your Airflow web server to see any changes take effect. To restart the Airflow web server (Cloud Composer 1 only), you can run the following command from a shell:
```
$ gcloud composer environments restart-web-server ENVIRONMENT --location=LOCATION
```
This may take up to 15 minutes to complete.