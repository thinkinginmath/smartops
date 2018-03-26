from kubernetes import client, config
from smartops.utils import setting_wrapper as setting
import logging
from time import sleep


class DemoComponent(object):
    def __init__(self):
        config.load_kube_config(setting.K8S_CONFIG_FILE)
        self.api_instance = client.CoreV1Api()
        self.pod_name = "capacityplanner"
        self.helper_ns_name = "helper-app7"
        #self.app_ns_name = "app6planner20dryrun0"
        return

    def check_pod_existence(self):
        pod_list = self.api_instance.list_namespaced_pod(self.helper_ns_name)
        return self.pod_name in map(lambda x:x.metadata.name, pod_list.items)

    def check_ns_existence(self, ns_name):
        ns_list = self.api_instance.list_namespace()
        return ns_name in map(lambda x:x.metadata.name, ns_list.items)

    def deploy_capacity_planner(self):
        config.load_kube_config(setting.K8S_CONFIG_FILE)
        delete_pod_body = client.V1DeleteOptions()
        if self.check_pod_existence():
            self.api_instance.delete_namespaced_pod(
                self.pod_name,
                self.helper_ns_name,
                delete_pod_body,
                grace_period_seconds=0
            )
        #for ns_name in [self.helper_ns_name, self.app_ns_name]:
        if not self.check_ns_existence(self.helper_ns_name):
            self.api_instance.create_namespace(
                client.V1Namespace(
                    api_version='v1',
                    metadata=client.V1ObjectMeta(name=self.helper_ns_name)
                )
            )
        pod_body = client.V1Pod(
            api_version="v1",
            kind="Pod",
            metadata=client.V1ObjectMeta(name=self.pod_name),
            spec=client.V1PodSpec(
                containers=[client.V1Container(
                    name="capplanner-demo",
                    image="10.145.88.66:5000/demo/smartops/smartops-capacityplanner",
                    ports=[client.V1ContainerPort(container_port=8086)],
                    image_pull_policy="Always",
                    volume_mounts=[client.V1VolumeMount(mount_path="/autoshift-capacityplanner/log", name="log")],
                    env=[
                        client.V1EnvVar(name="MAX_REPLICA_ADD", value="6"),
                        client.V1EnvVar(
                            name="APPLICATION_TOPOLOGY",
                            value="{\"app_id\":7,\"demand_profile_id\":12,\"capacity_plan_id\":21,\"load_duration\":300,\"is_auto\":true,\"k8s_endpoint_id_candidates\":[1],\"app_sla\":{\"error_rate\":95.0,\"latency\":5000,\"cost\":1000.0,\"currency_type\":\"dollar\"},\"setconfigs\":[{\"id\":1,\"kind\":\"StatefulSet\",\"name\":\"mysql\",\"replicas\":1,\"podConfig\":{\"containersConfig\":{\"mysql\":{\"cpu_quota\":1000000,\"mem_limit\":1073741824}}}},{\"id\":2,\"kind\":\"Deployment\",\"name\":\"webrc\",\"replicas\":1,\"podConfig\":{\"containersConfig\":{\"web\":{\"cpu_quota\":1000000,\"mem_limit\":1073741824}}}}]}"
                        ),
                        client.V1EnvVar(name="INFLUXDB_ENDPOINT", value="influxdb.smartops:8086"),
                        client.V1EnvVar(name="INFLUXDB_DATABASE", value="user_1"),
                        client.V1EnvVar(name="API_ENDPOINT", value="http://api.smartops:9000"),
                        client.V1EnvVar(name="INFLUXDB_USE_SSL", value="false")
                    ]
                )],
                node_selector={"stack": "smartops"},
                restart_policy="OnFailure",
                volumes=[
                    client.V1Volume(
                        name="log",
                        host_path=client.V1HostPathVolumeSource(path="/autoshift-capacityplanner-logs")
                    )
                ]
            )
        )

        # api_instance.create_namespace(namespace_body, pretty='true')
        while True:
            try:
                api_response = self.api_instance.create_namespaced_pod(
                    body=pod_body, namespace=self.helper_ns_name, pretty='true'
                )
            except:
                logging.info("Namespace not ready, sleeping...")
                sleep(1)
                continue
            logging.info("Namespace ready, woke up and successfully created pod")
            break

        return api_response
