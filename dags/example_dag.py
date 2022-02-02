import airflow
from airflow import DAG
from datetime import timedelta

from tasks.common import parse_job_args
from tasks.example_dag import (
    hello_world
)


default_args = {
    'start_date': airflow.utils.dates.days_ago(0),
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}


dag = DAG(
    'example_dag',
    default_args=default_args,
    description='example dag that tests the KubernetesPodOperator',
    schedule_interval=None,
    dagrun_timeout=timedelta(minutes=20))
dag.trigger_arguments = {
    'instantiator': {
        'display_name': 'Instantiator',
        'arg_type': 'enum',
        'plural': 'instantiators',
        'required': True,
        'default_value': 'airflow',
        'help_text': "Denotes who is triggering this DAG run. The results of the run will have this user's name included in the folder name (e.g. 'manual__smith_2022-01-01T00:00:00.00000-0700')."
    },
}


t1 = parse_job_args(dag)
t2 = hello_world(dag)

t1 >> t2