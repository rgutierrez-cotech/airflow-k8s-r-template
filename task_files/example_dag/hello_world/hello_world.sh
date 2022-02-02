#!/bin/bash
set -e
source /root/.bashrc
cd /root

# copy task files
gsutil -m -q cp -r -n gs://$CLOUD_STORAGE_BUCKET/task_files/example_dag/hello_world/** .
chmod +x ./hello_world.R
chmod +x ./hello_world.Rmd

# copy common files
gsutil -m -q cp -r gs://$CLOUD_STORAGE_BUCKET/common_files/* .
ls -al .

# task code
Rscript ./hello_world.R
Rscript -e "options(tinytex.verbose = TRUE); rmarkdown::render('hello_world.Rmd')"

touch ./hello_world.csv
echo "Name,Message" >> hello_world.csv
echo "$INSTANTIATOR,Hello world" >> hello_world.csv
gsutil cp hello_world.csv gs://$CLOUD_STORAGE_BUCKET/runs/example_dag/$CF_RUN_ID/hello_world/
gsutil cp hello_world.pdf gs://$CLOUD_STORAGE_BUCKET/runs/example_dag/$CF_RUN_ID/hello_world/