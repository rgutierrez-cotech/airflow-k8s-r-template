from airflow.models import Variable
from airflow.operators.python_operator import PythonOperator
import copy
import pendulum


def parse_job_args_fn(**kwargs):
    """
    Push job/run args to XCom for use by all tasks
    """
    def _get_conf_or_default(conf, k, t_args):
        v = conf.get(k)
        if v is None:
            if not t_args:
                return ''
            v = t_args[k].get('default_value', '')
        return v
    dag_run_conf = copy.deepcopy(kwargs["dag_run"].conf)
    dag = kwargs["dag"]
    t_args = copy.deepcopy(getattr(dag, 'trigger_arguments', {}))
    instantiator = _get_conf_or_default(dag_run_conf, 'instantiator', t_args)
    kwargs["ti"].xcom_push(key="instantiator", value=instantiator)
    dag_run_conf.pop('instantiator')
    custom_run_id = dag_run_conf.pop('custom_run_id', None)
    if custom_run_id is None:
        trigger_type = 'manual'
        pac_dt = pendulum\
            .utcnow()\
            .astimezone('America/Los_Angeles')\
            .strftime("%Y-%m-%dT%H:%M:%S.%f%z")
        custom_run_id = f"{trigger_type}__{instantiator}_{pac_dt}"
    kwargs["ti"].xcom_push(key="custom_run_id", value=custom_run_id)
    for k in dag_run_conf:
        arg_val = _get_conf_or_default(dag_run_conf, k, t_args)
        kwargs["ti"].xcom_push(key=k, value=arg_val)


def parse_job_args(dag):
    return PythonOperator(  
        task_id="parse_job_args",
        python_callable=parse_job_args_fn,
        provide_context=True,
        dag=dag
    )