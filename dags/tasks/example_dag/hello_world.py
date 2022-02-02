from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator

from tasks import (
    generate_env_vars,
    verify_env_vars,
    generate_op_vars
)


def hello_world(dag):
    env_vars = generate_env_vars({
        'DAG_ID': dag.dag_id,
        'TASK_ID': 'hello_world',
        'TASK_FILE_NAME': 'hello_world.sh'
    })
    env_vars = verify_env_vars(env_vars)
    return KubernetesPodOperator(**generate_op_vars(dict(
        task_id="hello_world",
        name="hello_world",
        env_vars=env_vars,
        dag=dag)))