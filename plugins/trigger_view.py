import logging
import urllib.parse
from airflow.api.common.experimental.trigger_dag import trigger_dag
from airflow.plugins_manager import AirflowPlugin
from airflow.models import DagBag, Variable
from flask import request, Markup, Blueprint
from flask_admin import BaseView, expose
from flask_admin.base import MenuLink
from flask_appbuilder import BaseView as AppBuilderBaseView, expose as ab_expose
from airflow.utils import timezone
import pendulum


DAG_RUN_URL_TMPL = '/admin/airflow/graph?dag_id={dag_id}&run_id={run_id}&execution_date={execution_date}'
CLOUD_STORAGE_RUN_FOLDER_TMPL = 'https://console.cloud.google.com/storage/browser/{bucket}/runs/{dag_id}'


def trigger(dag_id, trigger_dag_conf):
    """
    Function that triggers the dag with the custom conf.

    We will keep Airflow's standard run_id and supply our own 
    within `conf`.
    """
    execution_date = timezone.utcnow()

    dagrun_job = {
        "dag_id": dag_id,
        "run_id": f"manual__{execution_date.isoformat()}",
        "execution_date": execution_date,
        "replace_microseconds": False,
        "conf": trigger_dag_conf
    }
    r = trigger_dag(**dagrun_job)
    return r


def get_custom_run_id(instantiator):
    trigger_type = 'manual'
    pac_dt = pendulum\
        .utcnow()\
        .astimezone('America/Los_Angeles')\
        .strftime("%Y-%m-%dT%H:%M:%S.%f%z")
    return f"{trigger_type}__{instantiator}_{pac_dt}"


class FlaskAdminTriggerView(BaseView):
    @expose("/", methods=["GET", "POST"])
    def list(self):
        messages = []
        default_dag = Variable.get("default_dag", None)
        dag_data = { dag.dag_id: getattr(dag, "trigger_arguments", {}) for dag in DagBag().dags.values() \
                if dag.dag_id != 'airflow_monitoring' }
        choices = {}
        for dag_id, args in dag_data.items():
            for arg_name, arg_config in args.items():
                if arg_config['arg_type'] == 'enum':
                    choices[arg_name] = Variable.get(f"valid_{arg_config['plural']}", "").splitlines()
        if request.method == "POST":
            trigger_dag_id = request.form["dag"]
            trigger_dag_conf = {k.replace(trigger_dag_id, "").lstrip("-"): v for k, v in request.form.items() if k.startswith(trigger_dag_id)}
            # ensure there is ALWAYS an instantiator, and set it on trigger_dag_conf if not
            try:
                default_instantiator = dag_data[trigger_dag_id]['instantiator']['default_value']
            except KeyError:
                default_instantiator = Variable.get('default_instantiator', 'airflow')
            instantiator = trigger_dag_conf.get('instantiator', default_instantiator)
            trigger_dag_conf.setdefault('instantiator', instantiator)
            #
            custom_run_id = get_custom_run_id(instantiator)
            trigger_dag_conf['custom_run_id'] = custom_run_id
            dag_run = trigger(trigger_dag_id, trigger_dag_conf)
            dag_run_url = DAG_RUN_URL_TMPL.format(
                dag_id=dag_run.dag_id, 
                run_id=urllib.parse.quote(dag_run.run_id), 
                execution_date=urllib.parse.quote_plus(dag_run.execution_date.strftime("%Y-%m-%d %H:%M:%S.%f%z")))
            dag_run_main_folder = CLOUD_STORAGE_RUN_FOLDER_TMPL.format(
                bucket=Variable.get('cloud_storage_bucket'), 
                dag_id=dag_run.dag_id)
            dag_run_folder = f'{dag_run_main_folder}/{custom_run_id}'
            tdc_list = ['<ul>'] + [ f'<li><strong>{k}:</strong> {v}</li>' for k,v in trigger_dag_conf.items() ] + ['</ul>']
            msg = Markup(f"<h4>Success!</h4><p>DAG {trigger_dag_id} triggered with configuration: {''.join(tdc_list)}</p>")
            msg += Markup(f'<p>[<a href="{dag_run_url}" target="_blank">View current run</a>]&nbsp;&nbsp;')
            msg += Markup(f'[<a href="{dag_run_main_folder}" target="_blank">View all run outputs</a>]&nbsp;&nbsp;')
            msg += Markup(f'[<a href="{dag_run_folder}" target="_blank">View current run output</a>] (wait a few minutes before visiting)</p>')
            messages.append(msg)
        return self.render("trigger_view/trigger_view.html", 
                default_dag=default_dag,
                dag_data=dag_data, 
                choices=choices, 
                messages=messages)
v = FlaskAdminTriggerView(
    category="Custom Actions", 
    name="Manual Trigger",
    endpoint="manual_trigger")


bp = Blueprint(
    "trigger_view", __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static/trigger_view')


ml = MenuLink(
    category='Docs',
    name='My Data Processing Repo',
    url='https://www.example.com')


# Defining the plugin class
class TriggerViewPlugin(AirflowPlugin):  
    name = "trigger_view"
    admin_views = [v]
    menu_links = [ml]
    flask_blueprints = [bp]

    @classmethod
    def on_load(cls, *args, **kwargs):
        msg = 'Loading plugin TriggerViewPlugin'
        logging.info(msg)
        print(msg)
        super().on_load(args, kwargs)