from kubernetes import config as k8s_config, client as k8s_client
from kubernetes.client.rest import ApiException
from smartops.utils import setting_wrapper as setting
import logging


class K8sComponent(object):
    def __init__(self, component, name, namespace):
        k8s_config.load_kube_config(setting.K8S_CONFIG_FILE)
        self.namespace = namespace
        self.api_instance = k8s_client.CoreV1Api()
        self.api_version = component['apiVersion']
        self.kind = component['kind']
        if 'containers' in component.keys():
            self.containers = self._parse_containers(component['containers'])
        if 'nodeSelector' in component.keys():
            self.node_selector = component['nodeSelector']
        if 'restartPolicy' in component.keys():
            self.restart_policy = component['restartPolicy']
        if 'volumes' in component.keys():
            self.volumes = self._parse_volumes(component['volumes'])

    def _parse_containers(self, containers):
        container_objs = []
        for container in containers:
            container_obj = k8s_client.V1Container(
                name=container['name'],
                image=container['image'],
                ports=[
                    k8s_client.V1ContainerPort(
                        container_port=port['containerPort']
                    )
                    for port in container['ports']
                ] if 'ports' in container.keys() else None,
                image_pull_policy='Always',
                volume_mounts=[
                    k8s_client.V1VolumeMount(
                        mount_path=mount['mountPath'],
                        name=mount['name']
                    )
                    for mount in container['volumeMounts']
                ] if 'volumeMounts' in container.keys() else None,
                env=[
                    k8s_client.V1EnvVar(
                        name=env['name'],
                        value=env['value']
                    )
                    for env in container['env']
                ] if 'env' in container.keys() else None,
                args=container['args'] if 'args' in container.keys() else None,
                readiness_probe=k8s_client.V1Probe(
                    _exec=k8s_client.V1ExecAction(
                        command=container['readinessProbe']['exec']['command']
                    ),
                    initial_delay_seconds=(
                        container['readinessProbe']['initialDelaySeconds']
                    ),
                    timeout_seconds=(
                        container['readinessProbe']['timeoutSeconds']
                    ),
                    success_threshold=(
                        container['readinessProbe']['successThreshold']
                    )
                ) if 'readinessProbe' in container.keys() else None,
            )
            container_objs.append(container_obj)
        return container_objs

    def _parse_volumes(self, volumes):
        volume_objs = []
        for volume in volumes:
            volume_obj = k8s_client.V1Volume(
                name=volume['name'],
                host_path=k8s_client.V1HostPathVolumeSource(
                    path=volume['hostPath']['path']
                ) if 'hostPath' in volume.keys() else None,
                empty_dir={} if 'emptyDir' in volume.keys() else None
            )
            volume_objs.append(volume_obj)
        return volume_objs


class K8sPodComponent(K8sComponent):
    def __init__(self, component, name, namespace):
        super(K8sPodComponent, self).__init__(component, name, namespace)
        self.pod_name = name
        self.containers = (
            self._parse_containers(component['spec']['containers'])
        )
        self.node_selector = component['spec']['nodeSelector']
        self.restart_policy = component['spec']['restartPolicy']
        self.volumes = self._parse_volumes(component['spec']['volumes'])
    def run(self):
        pod_body = k8s_client.V1Pod(
            api_version=self.api_version,
            kind=self.kind,
            metadata=k8s_client.V1ObjectMeta(name=self.pod_name),
            spec=k8s_client.V1PodSpec(
                containers=self.containers,
                node_selector=self.node_selector,
                restart_policy=self.restart_policy,
                volumes=self.volumes
            )
        )
        try:
            api_response = self.api_instance.create_namespaced_pod(
                body=pod_body,
                namespace=self.namespace
            )
        except ApiException as e:
            logging.error('Exception caught when creating pod: %s\n', e)
        return api_response


class K8sServiceComponent(K8sComponent):
    def __init__(self, component, name, namespace):
        super(K8sComponent, self).__init__(component, name, namespace)
        self.pod_name = name
        self.selector = component['spec']['selector']
    def run(self):
        service_body = k8s_client.k8s_client.V1Service(
            api_version=self.api_version,
            kind=self.kind,
            metadata=k8s_client.V1ObjectMeta(name=self.pod_name),
            spec=k8s_client.V1ServiceSpec(
                selector=self.selector,
                ports=[
                    k8s_client.V1ServicePort(
                        port=port['port'],
                        target_port=port['target_port'],
                        protocol=port['protocol'],
                        name=port['name']
                    )
                    for port in component['spec']['ports']
                ]
            )
        )
        try:
            api_response = self.api_instance.create_namespaced_service(
                body=service_body,
                namespace=self.namespace
            )
        except ApiException as e:
            logging.error('Exception caught when creating service: %s\n', e)
        return api_response


class K8sReplicationControllerComponent(K8sComponent):
    def __init__(self, component, name, namespace):
        super(K8sReplicationControllerComponent, self).__init__(
            component, name, namespace
        )
        self.replication_controller_name = name
        self.replicas = component['spec']['replicas']
        self.template_meta = component['spec']['template']['metadata']
        self.restart_policy = (
            component['spec']['template']['spec']['restartPolicy']
        ) if 'restartPolicy' in component['spec']['template']['spec'].keys() else None
        self.node_selector = (
            component['spec']['template']['spec']['nodeSelector']
        )
        contianer_component = (
            component['spec']['template']['spec']['containers']
        )
        volume_component = (
            component['spec']['template']['spec']['volumes']
        )
        self.containers = self._parse_containers(container_component)
        self.volumes = self._parse_volumes(volume_component)
    def run(self):
        replication_controller_body = k8s_client.V1ReplicationController(
            api_version=self.api_version,
            kind=self.kind,
            metadata=k8s_client.V1ObjectMeta(
                name=self.replication_controller_name
            ),
            spec=k8s_client.V1ReplicationControllerSpec(
                replicas=self.replicas,
                template=k8s_client.V1PodTemplateSpec(
                    metadata=k8s_client.V1ObjectMeta(
                        labels=self.template_meta['labels']
                    ),
                    spec=k8s_client.V1PodSpec(
                        restart_policy=self.restart_policy,
                        node_selector=self.node_selector,
                        containers=self.containers,
                        volumes=self.volumes
                    )
                )
            )
        )
        try:
            api_response = (
                self.api_instance
                .create_namespaced_replication_controller(
                    body=replication_controller_body,
                    namespace=self.namespace
                )
            )
        except ApiException as e:
            logging.error(
                'Exception caught when creating replication controller: %s\n',
                e
            )
        return api_response


class K8sStatefulSetComponent(K8sReplicationControllerComponent):
    def __init__(self, component, name, namespace):
        super(K8sStatefulSetComponent, self).__init__(
            component, name, namespace
        )
        self.stateful_set_name = name
        self.api_instance = k8s_client.AppsV1beta1Api()
    def run(self):
        stateful_set_body = k8s_client.V1betaStatefulSet(
            api_version=self.api_version,
            kind=self.kind,
            metadata=k8s_client.V1ObjectMeta(
                name=self.stateful_set_name,
                namespace=self.namesace
            ),
            spec=k8s_client.V1beta1StatefulSetSpec(
                service_name=self.service_name,
                replicas=self.replicas,
                template=k8s_client.V1PodTemplateSpec(
                    metadata=k8s_client.V1ObjectMeta(
                        labels=self.template_meta['labels'],
                        annotations=self.template_meta['annotations']
                    ),
                    spec=k8s_client.V1PodSpec(
                        node_selector=self.node_selector,
                        containers=self.containers,
                        volumes=self.volumes
                    )
                )
            )
        )
        try:
            api_response = (
                self.api_instance.create_namespaced_stateful_set(
                    body=stateful_set_body,
                    namespace=self.namespace
                )
            )
        except ApiException as e:
            logging.error(
                'Exception caught when creating stateful set: %s\n',
                e
            )
        return api_response


class K8sNamespaceComponent(object):
    def __init__(self, namespace):
        k8s_config.load_kube_config(setting.K8S_CONFIG_FILE)
        self.namespace = namespace
        self.api_instance = k8s_client.CoreV1Api()
        self.api_version = 'v1'

    def check_existence(self):
        namespace_list = self.api_instance.list_namespace().items
        return self.namespace in map(
            lambda x:x.metadata.name,
            namespace_list
        )

    def create_namespace(self):
        namespace_body = k8s_client.V1Namespace(
            api_version=self.api_version,
            metadata=k8s_client.V1ObjectMeta(
                name=self.namespace
            )
        )
        try:
            api_response = self.api_instance.create_namespace(namespace_body)
        except ApiException as e:
            logging.error(
                'Exception caught when creating namespace: %s\n',
                e
            )
        return api_response
