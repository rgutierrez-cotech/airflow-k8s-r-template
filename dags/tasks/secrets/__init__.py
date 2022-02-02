from airflow.contrib.kubernetes import secret


secret_svc_acct = secret.Secret(
    deploy_type='volume',
    deploy_target='/var/secrets/google',
    secret='service-account',
    key='client_secrets_svc_google.json')