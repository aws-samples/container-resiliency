# EKS Topology Aware Routing (TAR)🚀

## What is Topology Aware Routing

Topology Aware Routing (TAR) plays a crucial role in enhancing container resiliency within Kubernetes clusters, especially in multi-zone environments. By intelligently distributing Pods across different failure domains (nodes, zones, or regions), TAR minimizes the risk of an entire application being impacted by a single point of failure. This failure domain isolation ensures that if a failure occurs in one domain, replicated Pods in other domains can quickly take over, minimizing downtime and ensuring application availability. you can read more [Topology Aware Routing](https://kubernetes.io/docs/concepts/services-networking/topology-aware-routing/)

Additionally, TAR promotes efficient resource utilization by evenly distributing Pods across available resources, preventing resource contention and improving overall cluster stability. By adjusting routing behavior to prefer keeping traffic within the zone it originated from, TAR can potentially reduce costs and improve network performance, further contributing to the overall resiliency and efficiency of the Kubernetes cluster. For more information [Topology Aware Routing on Amazon EKS](https://aws.amazon.com/blogs/containers/exploring-the-effect-of-topology-aware-hints-on-network-traffic-in-amazon-elastic-kubernetes-service/)

In summary, Topology-aware Routing is a valuable feature in Kubernetes that enhances container resiliency by providing failure domain isolation, efficient resource utilization, faster recovery from failures, and potential cost and performance benefits through optimized traffic routing within zones.

### Topology Aware Routing Caveats

Topology Aware Routing (TAR) offers an excellent approach for reducing traffic costs and enhancing network performance. However, there are certain scenarios where TAR might not perform as expected, and these scenarios are referred to as caveats.

In this example, we will explore below four different scenarios involving Topology Aware Routing, including the first happy path scenario where Topology Aware Routing functions as expected, as well as the failure scenarios involving the Fault Injection Tool (FIS), Horizontal Pod Autoscaling (HPA), and Karpenter Cluster Autoscaler where TAR operations may be influenced by other factors. For a comprehensive list of these caveats, please refer to the following repository [Topology Aware Routing Caveats](https://github.com/aws-samples/aws-eks-se-samples/tree/main/examples/kubernetes/how-to-topology-awareness-hints#caveats)

* [Normal Behavior with Topology Aware Routing](#normal-topology-aware-routing-behavior)
* [Failure use case 1 with Topology Aware Routing and FIS](#topology-aware-routing-with-az-failures-using-aws-fault-injection-simulator-fis)
* [Failure use case 2 with Topology Aware Routing and HPA](#topology-aware-routing-with-horizontal-pod-autoscaling-hpa)
* [Failure use case 3 with Topology Aware Routing and Karpenter](#topology-aware-routing-with-karpenter)

## Prerequisite

For the following examples we will ned to have an EKS cluster, for information on how to setup, please refer to [Setup EKS Cluster](https://github.com/terraform-aws-modules/terraform-aws-eks/tree/master/examples/karpenter)

The cluster should look like below, with one node in each Availability Zone (AZ):

```bash
kubectl get nodes -L topology.kubernetes.io/zone
```

![EKS Cluster status](images/EKS_cluster_status.png)

Apply the manifests in config-files directory, this will create the namespace, deployment using the Busybox image and a service exposing that deployment

```bash
kubectl apply -f config-files/namespace.yaml
kubectl apply -f config-files/busybox-deployment.yaml
kubectl apply -f config-files/service-busybox.yaml
```

Note that the service "service-demo-Busybox" is deployed as service type ClusterIP adding the annotation:

```bash
kubectl -n demo get svc demo-service
```

![demo-service](images/EKS_demo-service.png)

Let's Verify if the Hints are being populated inside the endpoint slice:

```bash
kubectl -n demo get endpointslices
```

![endpoint-slice](images/EKS_endpoint_slice.png)

Replace the endpoint-name below with your endpoint name from the above command:

```bash
kubectl -n demo get endpointslices.discovery.k8s.io <endpoint-name> -oyaml
```

![hints](images/EKS_hints.png)

Checking the deployed application and the distribution on the EKS cluster, Keep in mind that each EKS node is deployed in a different AZ:

```bash
kubectl -n demo get pods -o wide
```

![Application Deployment status](images/EKS_application_deployment.png)

## Normal Topology Aware Routing Behavior

In a working scenario, where the Hints are populated inside ```endpointSlice```. We will Deploy a test pod in one of EKS nodes in one availability zone to curl the service and see to which pod the traffic is being directed to.

```bash
kubectl get nodes
```

![Nodes](images/EKS_nodes.png)

Also, get the service cluster-IP as we will need it in the next step

```bash
kubectl -n demo get svc demo-service
```

![demo-svc](images/EKS_svc_cluster_ip.png)

You can use "nicolaka/netshoot" image in test pod to curl the service. Replace the ```node-name``` in below command.

```bash
kubectl run tmp-shell --rm -i --tty --image nicolaka/netshoot --overrides='{"spec": { "nodeSelector": {"kubernetes.io/hostname": "<node-name>"}}}‘
```

Once you are inside the pod use curl command to hit the service ClusterIP

```bash
curl <service-ClusterIP>:80
```

As you can see every time we curl the service ClusterIP we are getting the reply from the pod deployed on the same node we are connected to.

![curl_svc_w_hints](images/EKS_curl_svc_w_hints.png)

![pod_ip_node_ip](images/EKS_pods_ip_nodes_ip.png)

Cleanup

Now, Lets cleanup the service, deployment and namespace

```bash
kubectl delete -f config-files/service-busybox.yaml
kubectl delete -f config-files/busybox-deployment-karpenter.yaml
```

## Topology Aware Routing with AZ failures using AWS Fault Injection Simulator (FIS)

In this example we will simulate AZ failure and check the behavior of Topology Aware Routing. we will use the EKS cluster setup in the [Prerequisite](#prerequisite). For more infomration on FIS , please refer to this Blog [Simulating Kubernetes-workload AZ failures with AWS Fault Injection Simulator](https://aws.amazon.com/blogs/architecture/simulating-kubernetes-workload-az-failures-with-aws-fault-injection-simulator/)

Okay, Now we are going to create create an IAM Role for AWS FIS.

```bash
aws iam create-role --role-name my-fis-role --assume-role-policy-document file://config-files/fis-trust-policy.json
```

![FIS-Policy](images/fis-policy.png)

Now, Let's attach the created policy

```bash
aws iam attach-role-policy --role-name my-fis-role --policy-arn  arn:aws:iam::aws:policy/service-role/AWSFaultInjectionSimulatorNetworkAccess
aws iam attach-role-policy --role-name my-fis-role --policy-arn  arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy
aws iam attach-role-policy --role-name my-fis-role --policy-arn  arn:aws:iam::aws:policy/service-role/AWSFaultInjectionSimulatorEKSAccess
aws iam attach-role-policy --role-name my-fis-role --policy-arn  arn:aws:iam::aws:policy/service-role/AWSFaultInjectionSimulatorEC2Access
aws iam attach-role-policy --role-name my-fis-role --policy-arn  arn:aws:iam::aws:policy/service-role/AWSFaultInjectionSimulatorSSMAccess
```

![FIS-Attach](images/fis-attach.png)

The EKS nodes should be distributed across two or more AZs:

```bash
kubectl get nodes -L topology.kubernetes.io/zone
```

![FIS-EKS-nodes](FIS-EKS-nodes.png)

Let's apply the deployment where we will tell the provisioner to have pods spread across availability zones to limit the blast radius of an outage, the below command:

```bash
kubectl apply -f config-files/busybox-deployment-fis.yaml
kubectl apply -f config-files/service-busybox.yaml
kubectl apply -f config-files/fis-ingress-class.yaml
kubectl apply -f config-files/fis-ingress.yaml
```

Also, Chekcing the deployed topology aware routing hints, :

```bash
kubectl -n demo get endpointslices.discovery.k8s.io
kubectl -n demo get pods -owide
```

![fis-pods-ips](images/fis-pods-ips.png)

So, we should have one pod deployed on each EKS node in each AZ:

```bash
kubectl -n demo get pods -owide
kubectl get nodes -L topology.kubernetes.io/zone
```

![FIS-Deployment-pods](images/fis-deployment-pods.png)

Also, Checking on the deployed ingress:

```bash
kubectl -n demo get ingress
```

![fis-ingress](images/fis-ingress.png)

Let's prepare for our testing of the application (busy-box deployment), we will use [Grafana k6](https://grafana.com/docs/k6/latest/) to simulate browser accessing our application via ingress URL:

```bash
export MYSITE=$(kubectl -n demo get ing -o=json | jq '.items[].status.loadBalancer.ingress[].hostname' -r)
sed -i "s/URI/$MYSITE/g" config-files/fis-k6-site.js
```

Also we would need to download seccomp profile to use along with K6 :

```bash
curl -o chrome.json https://raw.githubusercontent.com/jfrazelle/dotfiles/master/etc/docker/seccomp/chrome.json
```

Now, we are ready to generate some load to our application, for that we will run a docker container:

```bash
docker run --rm -i --security-opt seccomp=$(pwd)/chrome.json grafana/k6:latest-with-browser run - <config-files/fis-k6-site.js
```

The output should be like below, notice that the reply is coming from both service endpoints:

![fis-k6-normal](images/fis-k6-normal.png)

Also, from AWS FIS the expermint should look like below,

![fis-experiment](images/fis-experiment.png)

Let's now introduce the network disruption to the AZ where the above EKS node deployed:

Go to ```AWS console > AWS FIS > Start experiment``` , give it a minute or two until you see it moved from "Intiating" to "Running" .. then go back to monitor our load generation , you will see that we are still getting reply from the affected node inside AZ!

![fis-k6-abnormal](images/fis-k6-abnormal.png)

Comparing to the normal behavior, the load generation was getting a reply from both endpoints which are deployed on two nodes on different AZ while the affected AZ is suffering from a network disruption, Topoology Aware Routing was still not able to forward the traffic only into one endpoint instead of both endpoints.

## Topology Aware routing with Horizontal Pod Autoscaling (HPA)

In this section we will see the impact of replicas scaling within a deployment using HPA on the Topology Aware Routing.
Let's first enable metric-server for EKS cluster, as we will need to report out metrics like CPU utilization.

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
 ```

```bash
kubectl top nodes
```

![EKS metric server](images/EKS_metric_server.png)

Now, Let's set up the HPA for deployment busybox-demo

```bash
kubectl -n demo autoscale deployment busybox-demo —cpu-percent=10 —min=3 —max=4
```

![EKS deployment HPA](images/EKS_HPA_1.png)

```bash
kubectl -n demo get hpa
```

![HPA](images/EKS_HPA_2.png)

Now Let's introduce some load, replace the node-name with actual EKS node name:

```bash
kubectl run tmp-shell --rm -i --tty --image nicolaka/netshoot --overrides='{"spec": { "nodeSelector": {"kubernetes.io/hostname": "<node-name>"}}}‘
```

Then do curl to the service cluster-IP, replace ```svc-cluster-ip``` with the actual Service ClusterIP
see [Normal Behavior](#normal-topology-aware-routing-behaviour) for how to replace ```svc-cluster-ip```

```bash
while sleep 0.01; do curl <svc-cluster-ip>:80; done
```

Give it a minute or so, and you will see load being generated and HPA is kicking in and adding more pods:

![HPA kick-in adding more pods](images/EKS_HPA_3.png)

![HPA pods](images/EKS_HPA_4.png)

Now Let's see the test of curl on which pod IP will reply, you will see different answer from different pods

![hpa_test](images/EKS_hpa_test_pods_ip.png)

Let's verify the pods IPs,

```bash
kubectl -n demo get pods -o wide
```

![testing_hpa_hints](images/EKA_hpa_hints_test.png)

As you can see the curl command was executed from a specific EKS node that exists in a specific AZ, however the reply are coming from the different pods that are deployed on a different node outside this AZ where the curl command is executed.

Comparing to the normal behavior, the curl command is not getting the same reply from the same AZ where the test pod was deployed, and the curl command was executed, Instead other pods replied to the curl from other nodes with the impact of HPA on the Topology aware hints.

Cleanup

Let's get back the deployment "busybox-demo" back to 3 replicas as before:

Kill the tmp-shell pod by using ```ctrl+c``` and delete the hpa

```bash
kubectl -n demo delete hpa busybox-demo
```

![delete-hpa](images/EKS_HPA_delete.png)

Now, Lets cleanup the service, deployment and namespace

```bash
kubectl delete -f config-files/service-busybox.yaml
kubectl delete -f config-files/busybox-deployment-karpenter.yaml
kubectl delete -f config-files/namespace.yaml
```

![deployment-scaling-back](images/EKS_deployment_scale_3_replicas.png)

## Topology Aware routing with Karpenter

In this section we will see the impact of cluster autoscaling through Karpenter and the impact on the Topology Aware Routing. To know more about Karpenter: <https://aws.amazon.com/blogs/aws/introducing-karpenter-an-open-source-high-performance-kubernetes-cluster-autoscaler/>

Assuming the creation of the EKS cluster from the [Prerequisite](#prerequisite), Karpenter should already be installed, Let's verify that:

```bash
kubectl get pods —namespace karpenter
```

![karpenter-installation](images/karpenter_installation.png)

```bash
kubectl apply -f config-files/namespace.yaml
kubectl apply -f config-files/busybox-deployment-karpenter.yaml
kubectl apply -f config-files/service-busybox.yaml
```

Now. Let's test the Topology Aware routing, we will use "nicolaka/netshoot" image in test pod to curl the service. Replace the ```node-name``` in below command

```bash
kubectl run tmp-shell --rm -i --tty --image nicolaka/netshoot --overrides='{"spec": { "nodeSelector": {"kubernetes.io/hostname": "<node-name>"}}}‘
```

Once you are inside the pod use curl command to hit the service

```bash
while sleep 0.01; do curl <svc-cluster-ip>:80; done
```

On another terminal, Let's scale the deployment to 5 replicas:

```bash
kubectl -n demo scale deployment busybox-demo —replicas=5
```

![karpenter-scale-deployment](images/karpneter-deployment-scale.png)

You will see the new pods is not yet schedule as Karpenter is still forking new nodes to deploy the new pods on top:

```bash
kubectl -n demo get pods -owide
```

![karpenter-deployment-nodes](images/karpenter-deployment-nodes.png)

But after a minute or so, you will see that karpenter provisioned a new node and deployed the pod on top:

```bash
kubectl get nodes
kubectl -n demo get pods -owide
```

![karpenter-nodes-scalling](images/karpenter-scalled-nodes.png)
![karpenter-pods-nodes-scalling](images/karpenter-pods-nodes-scalling.png)

Now, Let's get back and Monitor the curl output from the temp pod:

![karpenter-pods-ips-scalling](images/karpenter-hints-pods-ip.png)

```bash
kubectl get nodes -L topology.kubernetes.io/zone
kubectl -n demo get pods -owide
```

![karpenter-nodes-pods-ips](images/karpenter-hints-nodes-pods-ips.png)

As we can see that the reply from the curl above returned multiple reply from different pods IP's and by comparing those IPs we can see the reply came from different nodes in other availability zones.

## Conclusion

As we have seen The Topology Aware routing can be impacted in many scenarios Avalability zone failure, the Horizontal Pod Autoscaling and Cluster Autoscaling activities and won't be respecting the zone configuration and will route the traffic to other Endpoints. Very soon we will be releasing a new section for an approach on how to mitigate those Caveats … Stay turned!
