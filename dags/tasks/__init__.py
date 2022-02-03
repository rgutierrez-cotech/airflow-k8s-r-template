import copy

from airflow.models import Variable

from .secrets import secret_svc_acct


# Refer to Airflow templating guide for more info
DEFAULT_ENV_VARS = {
    'INSTANTIATOR': '{{ task_instance.xcom_pull(key="instantiator") }}',
    'RUN_ID': '{{ run_id }}',
    # add these three variables
    'SURVEY_ADMINISTRATION_NAME': '{{ task_instance.xcom_pull(key="survey_administration_name") }}',
    'NETWORK_ID': '{{ task_instance.xcom_pull(key="network_id") }}',
    'CUSTOM_RUN_ID': '{{ task_instance.xcom_pull(key="custom_run_id") }}',
    #
    'DAG_ID': '',
    'TASK_ID': '',
    'CREDENTIALS_FILE': '/var/secrets/google/client_secrets_svc_google.json',
    'PROJECT_ID': '{{ var.value.project_id }}',
    'CLOUD_STORAGE_BUCKET': '{{ var.value.cloud_storage_bucket }}',
    'TASK_FILE_NAME': ''
}


REQUIRED_ENV_VARS = (
    'DAG_ID',
    'TASK_ID',
    'TASK_FILE_NAME'
)


# Refer to KubernetesPodOperator documentation for more info
DEFAULT_OP_VARS = {
    'namespace': 'default',
    'image': 'us.gcr.io/{}/cf_data_processor'.format(Variable.get('project_id')),
    'image_pull_policy': 'Always',
    'secrets': [secret_svc_acct]
}


class TaskVariableException(Exception):
    """
    To be raised when a required environment variable is not 
    found in the dictionary
    """
    def __init__(self, k, *args, **kwargs):
        super().init(*args, **kwargs)
        self.missing_key = k
        self.message = f"The following key was not found in the env_vars dictionary: {self.missing_key}. Required keys are: {REQUIRED_ENV_VARS}"


def generate_env_vars(ev):
    """
    Copy default env vars and update with our own
    """
    new_ev = copy.copy(DEFAULT_ENV_VARS)
    new_ev.update(ev)
    return new_ev


def generate_op_vars(ov):
    """
    Copy default operator vars and update with our own
    """
    new_ov = copy.copy(DEFAULT_OP_VARS)
    new_ov.update(ov)
    return new_ov


def verify_env_vars(ev):
    """
    Verify that we have all the expected environment variables 
    in the dictionary. Additionally, add any dynamic variables 
    that require values from other variables.
    """
    def _check_k(k, d):
        return k == '' or k not in d
    for k in REQUIRED_ENV_VARS:
        if _check_k(k, ev):
            raise TaskVariableException(k)
    ev['TASK_FOLDER'] = f"{ev['CLOUD_STORAGE_BUCKET']}/task_files/{ev['DAG_ID']}/{ev['TASK_ID']}"
    ev['TASK_RESULTS_FOLDER'] = f"{ev['CLOUD_STORAGE_BUCKET']}/runs/{ev['DAG_ID']}/{ev['CUSTOM_RUN_ID']}/{ev['TASK_ID']}"
    return ev