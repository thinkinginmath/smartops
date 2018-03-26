import jinja2
import logging
import os

from smartops.deployment import k8s_components
from smartops.utils import setting_wrapper as setting


class DeployManager(object):
    """Deployment manager module."""
    def __init__(self, app_id, blueprint, test_plan, entrypoint):
        self.app_id = app_id
        self.blueprint = blueprint
        self.test_plan = test_plan
        self.entrypoint = entrypoint
        self.namespace = 'smartops:app_' + str(app_id)

    @staticmethod
    def render_jmeter_config(app_id, test_plan):
        tmpl_path = setting.TMPL_PATH
        path, filename = os.path.split(tmpl_path)
        jmeter_config = jinja2.Environment(
            loader=jinja2.FileSystemLoader(path or './')
        ).get_template(filename).render(test_plan)
        with open(
            os.path.join(setting.JMETER_DIR, str(app_id)),
            'wb'
        ) as jmeter_file:
            jmeter_file.write(jmeter_config)
        return jmeter_config

    def get_app_details():
        return

    def deploy(self):
        deploy_messages = []
        for component in self.blueprint:
            if component['kind'] == 'Secret':
                pass
            name = self.app_id + component['metadata']['name']
            component_class_ = getattr(
                k8s_components,
                'K8s' + component['kind'] + 'Component'
            )
            component_obj = component_class_(
                component, name, self.namespace
            )
            deploy_messages.append(component_obj.run())
        return deploy_messages


class CapacityPlannerDeployManager(DeployManager):
    """Capacity planner deployment manager module."""
    def __init__(self, app_id, blueprint):
        self.app_id = app_id
        self.blueprint = blueprint
        self.name = 'capplanner-app-' + str(app_id)
        self.namespace = 'smartops-app-' + str(app_id)

    def deploy(self):
        namespace_component = k8s_components.K8sNamespaceComponent(
            self.namespace
        )
        if not namespace_component.check_existence():
            logging.info('creating namespace..')
            namespace_component.create_namespace()
        logging.info('namespace available, creating pod..')
        component = self.blueprint[0]
        k8s_pod_component = k8s_components.K8sPodComponent(
            component,
            self.name,
            self.namespace
        )
        return k8s_pod_component.run()

    """
        def deploy(self):
            from demo_k8s_components import DemoComponent
            component = DemoComponent()
            return component.deploy_capacity_planner()
    """
