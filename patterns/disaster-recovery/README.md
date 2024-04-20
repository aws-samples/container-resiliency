# Achieving Cross-region DR for EKS stateful workloads using Velero
This project shows the steps involved to implement Disaster recovery for EKS stateful workloads using Velero's built-in data movement feature

# Pre-requisites
* [aws-cli](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
* EKS clusters on 2 different region. One will be primary and the other one will the DR cluster
* [ebs csi controller](https://docs.aws.amazon.com/eks/latest/userguide/managing-ebs-csi.html)
* [EKS Pod Identities](https://docs.aws.amazon.com/eks/latest/userguide/pod-id-agent-setup.html)
* [Storage class](https://github.com/kubernetes-sigs/aws-ebs-csi-driver/blob/master/examples/kubernetes/dynamic-provisioning/manifests/storageclass.yaml) (make sure they are the same name in both the clusters) 
* S3 buckets in source and DR region
* [Velero cli](https://velero.io/docs/v1.3.0/basic-install/#install-the-cli)

# Architecture
![Architecture](/images/velero_architecture.png)
# Solution
## Step 1: Cloning the github repo

```bash
git clone https://github.com/aws-samples/cross-region-dr-eks
cd cross-region-dr-eks
```

## Step 2: Setting up the source cluster

### IAM policy & Pod identities setup
The first step on the source cluster is to deploy the velero controller. Before doing that, we need to ensure the service account used by velero has necessary permission to access the S3 buckets

Use the [IAM policy](file://config_files/iam.json) and create the IAM role which will be used by the velero's service account. 

```bash
aws iam create-policy --policy-name velero-policy --policy-document file://config_files/iam.json

aws iam create-role --role-name velero-source-role --assume-role-policy-document file://trust-relationship.json --description "my-role-description"

aws iam attach-role-policy --role-name velero-source-role --policy-arn=arn:aws:iam::<Account_ID>:policy/velero-policy


```
### Associating IAM role with the service account for velero
Next step is associating the role we created in the previous step to the service account used by velero controller. Velero runs in the `velero` namespace and the service account will be `velero-server`

```bash
aws eks create-pod-identity-association --cluster-name <Your EKS Cluster> --role-arn arn:aws:iam::<ACCOUNT_ID>:role/velero-source-role --namespace velero --service-account velero-server

```
### Deploying Velero controller with CSI features enabled

We will leverage the values-source.yaml in the `config_files` directory and deploy the controller

```bash
helm repo add vmware-tanzu https://vmware-tanzu.github.io/helm-charts 
helm repo update
helm install velero vmware-tanzu/velero  --namespace velero     -f values-source.yaml --version 5.2.2
```
The above command also deploys a velero node agent daemonset. Velero Node Agent is a Kubernetes daemonset that hosts Velero data movement modules, i.e., data mover controller, uploader & repository. If you are using Velero built-in data mover, Node Agent must be installed.

Your output should look like below :
![Velero Output](/images/veleroout.png)

## Step 3: Deploy a statefulset and create a backup

We will now deploy a sample nginx application that is backed by the persistent volume. 

```bash
kubectl apply -f config_files/nginx-stateful.yaml
```
We will be using velero's built in data mover(kopia) to upload the persistent volume to S3 bucket.While triggering the backup, it is important to specify the `--snapshot-move-data` flag to ensure the volume's snapshot gets copied to the S3 bucket.

CSI Snapshot Data Movement is built according to the Volume Snapshot Data Movement design and is specifically designed to move CSI snapshot data to a backup storage location.
CSI Snapshot Data Movement takes CSI snapshots through the CSI plugin in nearly the same way as CSI snapshot backup. However, it doesn’t stop after a snapshot is taken. Instead, it tries to access the snapshot data through various data movers and back up the data to a backup storage connected to the data movers.
Consequently, the volume data is backed up to a pre-defined backup storage in a consistent manner.
After the backup completes, the CSI snapshot will be removed by Velero and the snapshot data space will be released on the storage side.


```bash
velero create backup jhbackup --snapshot-move-data --include-namespaces default
```
Your output should look like below:
![backup](/images/backup.png)
### Enabling cross region replication on the source region S3 bucket (optional)

You can enable [cross region replication on the source S3](https://aws.amazon.com/blogs/aws/new-replicate-existing-objects-with-amazon-s3-batch-replication/) bucket to the desired bucket in the DR region which will be used while setting up the velero controller in the DR region

## Step 4: Setting the DR cluster
You can follow the IAM role creation process in step 2 to create the service account for the DR EKS cluster. Make sure the bucket name is updated correctly in the `iam.json` to point to the right bucket in the DR region

### Deploy the velero controller

We will leverage the `velero-restore.yaml` to deploy the velero controller in the DR EKS cluster

```bash
helm repo add vmware-tanzu https://vmware-tanzu.github.io/helm-charts
helm repo update
helm install velero vmware-tanzu/velero --version 5.2.2         --namespace velero     -f values-restore.yaml

```

## Step 5: Create the restore job

We will again leverage velero's built-in datadownloader to download the persistent volume from the S3 bucket and restore it on the destination EKS cluster

```bash
velero create restore jhrestore --from-backup jhbackup --namespace-mappings default:restore

```
Your output should look like below:
```bash
nht-admin:~/environment $ velero get restore
NAME        BACKUP     STATUS            STARTED                         COMPLETED                       ERRORS   WARNINGS   CREATED                         SELECTOR
jhrestore   jhbackup   Completed   2024-01-26 03:08:13 +0000 UTC   2024-01-26 03:18:36 +0000 UTC   0        13         2024-01-26 03:08:13 +0000 UTC   <none>
```

## Using Resource Modifiers

Velero provides a generic ability to modify the resources during restore by specifying json patches. The json patches are applied to the resources before they are restored. The json patches are specified in a configmap and the configmap is referenced in the restore command.

In this example, we're going to use Velero Restore Resource Modifiers to update an external service endpoint before restoring from a backup.

### Deploy a sample workload on source cluster

First, let's deploy the example workload in the source EKS cluster using `kubectl apply` command.

```bash
kubectl apply -f resource_modifier/nginx-deployment.yaml
```

Check the status of the resources created in the namespace `demo`.

```bash
$ kubectl -n demo get all
NAME                                   READY   STATUS    RESTARTS   AGE
pod/nginx-deployment-78cff7984-hf4h8   1/1     Running   0          23s
pod/nginx-deployment-78cff7984-n6bmf   1/1     Running   0          23s

NAME                               READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/nginx-deployment   2/2     2            2           23s

NAME                                         DESIRED   CURRENT   READY   AGE
replicaset.apps/nginx-deployment-78cff7984   2         2         2       23s
```

Notice, that there's an env variable named `DB_ENDPOINT` that points to an Aurora DB cluster endpoint `mycluster.cluster-1.<source_region>.rds.amazonaws.com:3306`. When restoring the EKS cluster and its workload to a different AWS region, you can use the Velero Restore Resource Modifiers to patch the value of the endpoint at the time of restoring from the backup.

### BackUp the source cluster 

Using the velero cli, take the backup of the source EKS cluster.

```bash
velero create backup eks-backup-demo  --include-namespaces demo
```

Check the status of the backup

```bash
velero get backup

NAME              STATUS      ERRORS   WARNINGS   CREATED                         EXPIRES   STORAGE LOCATION   SELECTOR
eks-backup-demo    Completed   0        0          2024-03-04 21:09:01 +0000 UTC   29d       default            <none>
```

### Create Restore Resource Modifer

Now, in your destination or recovery EKS cluster on the other AWS region, create a `ConfigMap` in `velero` namespace to patch the value of the `DB_ENDPOINT` env variable to point to the Aurora cluster on that region.

```bash

kubectl create cm nginx-deploy-cm --from-file resource_modifier/resource_modifer.yaml -n velero
```

Then, restore the cluster from the backup `eks-backup-demo` taken avove.

```bash
velero create restore eks-restore-demo --resource-modifier-configmap nginx-deploy-cm --from-backup eks-backup-demo
```

Check the `velero restore` status

```bash
velero get restore
```

Verify that the resources on the `demo` namespace are in `Running` state.

```bash
kubectl -n demo get all
```

Now, check the value of the DB_ENDPOINT env variable by execing into a Pod.

```bash
kubectl -n demo exec nginx-deployment-849d985c48-xyzhh -- env | grep -i DB_ENDPOINT

DB_ENDPOINT=mycluster.cluster-2.us-east-2.rds.amazonaws.com:3306
```

This way, you can patch any configuration parameter or specific values that your workload uses while restoring from the backup.



# Clean up
* Delete both the clusters
* Delete the S3 buckets
