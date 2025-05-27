# EKS Cluster Setup with PostgreSQL Deployment

This guide walks you through the process of creating an Amazon EKS cluster and deploying a PostgreSQL database using Helm. The instructions aim to be clear and descriptive, providing not only commands but also context, caveats, and example outputs for better understanding.

---

## 1. Create the EKS Cluster

We use `eksctl` to create our EKS cluster using a predefined configuration file.

```bash
eksctl create cluster -f ./eks/cluster-config.yaml
```

> 💡 **Tip:** To optimize for cost, we use spot instances.

### Troubleshooting:

If you encounter errors, navigate to the AWS CloudFormation console to investigate. For example, setting the EBS volume size to 8Gi will fail (the minimum must be 20Gi by default).

📸 *\[Insert screenshots here]*

```bash
kubectl config current-context
```

✅ **Sample Output:**

```
devops-master@coworking.us-east-1.eksctl.io
```

---

## 2. Install Helm

Install Helm v3 using the official installation script:

```bash
curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash
```

Add the Bitnami chart repository:

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

---

## 3. Create Namespace for PostgreSQL

```bash
kubectl create namespace postgres
```

---

## 4. Configure StorageClass

By default, the EBS-backed `gp2` storage class has a `Delete` reclaim policy, which deletes volumes even on instance restart. We'll create a new StorageClass with a `Retain` policy.

```bash
kubectl get storageclass
```

✅ **Sample Output:**

```
NAME   PROVISIONER             RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
gp2    kubernetes.io/aws-ebs   Delete          WaitForFirstConsumer   false                  14m
```

```bash
kubectl apply -f ./db/gp2-retain.yaml
```

```bash
kubectl get storageclass
```

✅ **Sample Output:**

```
NAME         PROVISIONER             RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
gp2          kubernetes.io/aws-ebs   Delete          WaitForFirstConsumer   false                  16m
gp2-retain   kubernetes.io/aws-ebs   Retain          WaitForFirstConsumer   false                  17s
```

---

## 5. Enable EBS CSI Driver

```bash
kubectl get csidrivers
```

✅ **Sample Output (initial):**

```
NAME              ATTACHREQUIRED   PODINFOONMOUNT   STORAGECAPACITY   TOKENREQUESTS   REQUIRESREPUBLISH   MODES        AGE
efs.csi.aws.com   false            false            false             <unset>         false               Persistent   14m
```

If `ebs.csi.aws.com` is missing, follow these steps:

### Associate IAM OIDC Provider:

```bash
eksctl utils associate-iam-oidc-provider \
  --region=us-east-1 \
  --cluster=coworking \
  --approve
```

### Create IAM Service Account:

```bash
eksctl create iamserviceaccount \
  --name ebs-csi-controller-sa \
  --namespace kube-system \
  --cluster coworking \
  --region us-east-1 \
  --attach-policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy \
  --approve \
  --role-only
```

### Retrieve IAM Role ARN:

```bash
aws cloudformation describe-stacks \
  --stack-name eksctl-coworking-addon-iamserviceaccount-kube-system-ebs-csi-controller-sa \
  --query "Stacks[0].Outputs[?OutputKey=='Role1'].OutputValue" \
  --output text
```

### Create the Addon:

```bash
eksctl create addon \
  --name aws-ebs-csi-driver \
  --cluster coworking \
  --region us-east-1 \
  --service-account-role-arn <role-arn-from-above> \
  --force
```

```bash
kubectl get csidrivers
```

✅ **Sample Output (after install):**

```
NAME              ATTACHREQUIRED   PODINFOONMOUNT   STORAGECAPACITY   TOKENREQUESTS   REQUIRESREPUBLISH   MODES        AGE
ebs.csi.aws.com   true             false            false             <unset>         false               Persistent   33s
efs.csi.aws.com   false            false            false             <unset>         false               Persistent   23m
```

---

## 6. Deploy PostgreSQL

### Create Secret:

```bash
kubectl create secret generic postgres-secret \
  --from-literal=postgres-password='changeme' \
  --from-literal=postgres-user='cw-user' \
  --from-literal=postgres-db='coworking-db' \
  -n postgres
```

### Configure Helm Values (`postgres-values.yaml`):

```yaml
auth:
  existingSecret: postgres-secret
  username: cw-user
  database: coworking-db

primary:
  persistence:
    enabled: true
    storageClass: gp2-retain
    size: 8Gi
```

> 📝 We're using the `gp2-retain` storage class created earlier.

### Install PostgreSQL using Helm:

```bash
helm install my-postgres bitnami/postgresql -n postgres -f ./db/postgres-values.yaml
```

---

## 7. Verify the Deployment

```bash
kubectl get pods -n postgres -w
```

✅ **Sample Output:**

```
NAME                       READY   STATUS              RESTARTS   AGE
my-postgres-postgresql-0   0/1     ContainerCreating   0          4s
my-postgres-postgresql-0   0/1     Running             0          5s
my-postgres-postgresql-0   1/1     Running             0          17s
```

```bash
kubectl get pvc -n postgres
```

```bash
kubectl get pv
```

PVC status should be `Bound`.

---

## 8. Connect to PostgreSQL

### Option 1: Local Port Forwarding

```bash
kubectl port-forward svc/my-postgres-postgresql 5432:5432 -n postgres
```

In another terminal (from EC2 instance or your machine):

```bash
PGPASSWORD=changeme psql -h 127.0.0.1 -U cw-user -d coworking-db
```

### Option 2: Temporary Pod

```bash
kubectl run psql-client --rm -it --restart=Never --image=bitnami/postgresql \
  --env="PGPASSWORD=changeme" \
  --command -- psql -h my-postgres-postgresql.postgres.svc.cluster.local -U cw-user -d coworking-db
```

Once inside:

```bash
psql -h my-postgres-postgresql -U cw-user -d coworking-db
```

✅ **Prompt:**

```
coworking-db=>
```

You can run commands like `\l` to list databases.

---

## ✅ You're all set!

You now have a fully operational EKS cluster with a PostgreSQL instance running inside it, leveraging spot instances, persistent storage, and Helm deployment best practices.
