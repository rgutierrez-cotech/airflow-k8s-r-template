#!/bin/bash

helpFunction()
{
   echo ""
   echo "Usage: $0 staging|production [ version ]"
   echo -e "\t\$1 Environment to deploy to. Can be either staging or production."
   echo -e "\t\$2 Optional. Version specifier. If specified, will deploy a previous version."
   exit 1 # Exit script after printing help
}

# Print helpFunction in case parameters are empty
if [ -z "$1" ] || [ $1 != "staging" -a $1 != "production" ]
then
   echo "Deployment environment is invalid or missing.";
   helpFunction
fi

# vars
if [ $1 = "staging" ]
then
    bucket="<CLOUD_STORAGE_BUCKET_STAGING>"
else
    bucket="<CLOUD_STORAGE_BUCKET_PRODUCTION>"
fi
if [ -n "$2" ]
then
    if [ ! -f "$PWD/deployments/$2.tar" ] 
    then
        echo "Deployment version $2 does not exist! Exiting..."
        exit 1
    fi
    version="$2"
    version_exists="y"
else
    version=$(date +"%Y%m%dt%H%M%S")
    version_exists=""
fi
deployments_dir="$PWD/deployments"
dags_dir="$deployments_dir/dp-$version/dags"
task_files_dir="$deployments_dir/dp-$version/task_files"
common_files_dir="$PWD/common_files"
plugins_dir="$PWD/plugins"
config_dir="$PWD/config/$1"


echo "Deploying version $version of files to $1"
read -p "Would you like to continue? (y/n) " should_continue

if [ $should_continue = "y" ]
then
    echo ""
else
    echo "Cancelling..."
    exit 1
fi

mkdir "$deployments_dir/dp-$version"

# if version was specified, unpack tar
if [ -n "$version_exists" ]
then
    
    echo "Unpacking previous version $version..."
    tar -xvf "$PWD/deployments/$2.tar" -C "$PWD/deployments/dp-$version"
    echo "Done"
    
else

    # zip `dags`, `task_files`, `plugins`, and `config` together into `deployments`, 
    # add version num (datetime)
    echo "Zipping DAGs, tasks, task-relevant files, plugins, and config..."

    mkdir "$dags_dir"
    cp -r "$PWD/dags/." "$dags_dir/"

    mkdir "$task_files_dir"
    cp -r "$PWD/task_files/." "$task_files_dir/"

    mkdir "$deployments_dir/dp-$version/plugins"
    cp -r "$PWD/plugins/." "$deployments_dir/dp-$version/plugins/"

    mkdir "$deployments_dir/dp-$version/config"
    cp -r "$PWD/config/." "$deployments_dir/dp-$version/config/"

    tar -cf "$deployments_dir/$version.tar" "$deployments_dir/dp-$version"
    echo "Done"

fi

# copy contents of `dags` to gs://BUCKET/dags
echo "Copying DAGs and tasks to Cloud Storage..."
gsutil -m rsync -r -x .*\.DS_Store "$dags_dir" "gs://$bucket/dags"
echo "Done"

# copy contents of `task_files` to gs://BUCKET/task_files
echo "Copying task-relevant files to Cloud Storage..."
gsutil -m rsync -r -x .*\.DS_Store "$task_files_dir" "gs://$bucket/task_files"
echo "Done"

# copy contents of `common_files` to gs://BUCKET/common_files
echo "Copying common files to Cloud Storage..."
gsutil -m rsync -r -x .*\.DS_Store "$common_files_dir" "gs://$bucket/common_files"
echo "Done"

# copy Airflow config to the bucket
echo "Copying Airflow config..."
gsutil cp "$config_dir/airflow.cfg" "gs://$bucket"
echo "Done"

# copy contents of `plugins` to gs://BUCKET/plugins
echo "Copying plugins to Cloud Storage..."
gsutil -m rsync -r -x .*\.DS_Store "$plugins_dir" "gs://$bucket/plugins"
echo "Done"

rm -rf "$PWD/deployments/dp-$version"

echo "Deployment complete"