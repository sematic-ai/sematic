# Deploy Sematic

When you install Sematic the first time, everything runs locally. The web app
and your pipelines run locally.

Here is how to deploy Sematic to take full advantage of your cloud resources.

## Deploy the web app

In order to collaborate and share results with your team, it is best to deploy
the Sematic web app to a remote server.

Prerequisites:

* A remote instance into which you can SSH
* A Postgres database
* [Install Docker](https://docs.docker.com/engine/install/) onto your remote instance

Then, SSH into your remote server:

```shell
$ ssh my-remote-server.dev
```

Pull the latest server image

```shell
$ sudo docker pull sematicai/sematic-server:latest
```

launch the server

```shell
$ sudo docker run -d -p 80:80 \
    -e DATABASE_URL=<DATABASE_URL> \
    -v /home/ubuntu/.sematic:/root/.sematic \
    [-e SEMATIC_AUTHENTICATE=1 -e GOOGLE_OAUTH_CLIENT_ID=123456789.apps.googleusercontent.com \]
    [-e SEMATIC_AUTHORIZED_EMAIL_DOMAIN=yourdomain.com \]
    [-p 443:443 -e CERTIFICATE=/path/to/certificate.pem -e PRIVATE_KEY=/path/to/private.key \]
    sematicai/sematic-server:latest
```

where `DATABASE_URL` is the fully-qualified URL of your Postgres database. It
should be of the form:

```
postgresql://<username>:<password>@<hostname>:<port>/<database>
```

Now you should be able to visit http://my-remote-server.dev and see the landing page.

### Authentication

In the `docker run` command above, three optional environment variables dictate
authentication behavior for your deployed app.

If you don't pass any of them, your app will be available publicly and users
will not need to authenticate to use it. Everyone will be the "Anonymous" user.

* `SEMATIC_AUTHENTICATE` activates authentication. Users will need to sign in to
  user the web app, and will need to set an API key in their local settings in
  order to submit jobs.

* `GOOGLE_OAUTH_CLIENT_ID` is the client ID of your Google OAuth App. We will
  support more OAuth providers int he future.

* `SEMATIC_AUTHORIZED_EMAIL_DOMAIN` denies access to users whose email is not of
  said domain.

### SSL

If you have an SLL certificate for the domain on which you are deploying
Sematic, you can pass it to the server container with the `CERTIFICATE` and
`PRIVATE_KEY` environment variables when calling `docker run`.

Make sure that the certificate and private key files are accessible within the
container (e.g. place them in the `~/.sematic` directory).

Also make sure to add `-p 443:443` to the forwarded ports.

### Run pipelines against the deployed API

At this time Sematic still runs your pipelines on your local machine (cloud
execution coming soon). In order to write metadata to the deployed API, simply do:

```shell
$ sematic settings set SEMATIC_API_ADDRESS http://my-remote-server.dev
```

## Run pipelines in your cloud

In order to benefit from cloud resources (e.g. GPUs, high memory, etc.), Sematic
lets you run pipelines in a Kubernetes cluster.

{% hint style="warning" %}

In theory Sematic can run in any cloud provider. However at this time, Sematic
focuses support on **Amazon Web Services**. Other providers to follow soon.

{% endhint %}

In order to do so, the following must be true:

* The Sematic web app is deployed. See [Deploy the web app](#deploy-the-web-app).

* You have a Kubernetes cluster and have permissions to submit jobs to it.

* You have an S3 bucket and you and nodes in your Kubernetes cluster have read
  and write permissions to it.

* You have a container registry (e.g. AWS Elastic Container Registry) and you
  have write access, and nodes in yout Kubernetes cluster have read access to
  it.

When you are set, the following settings should be visible to Sematic

```
$ sematic settings show
Active settings:

AWS_S3_BUCKET: <bucket-name>
KUBERNETES_NAMESPACE: <namespace>
SEMATIC_API_ADDRESS: <web-app-server-address>
```

{% hint style="warning" %}

If you have chosen to deploy Sematic in such a way that users of Sematic
will use a different URL for the server from what should be used for
jobs on your Kubernetes cluster (e.g. users access via a reverse proxy
that's not needed on Kubernetes), you may also need to set 
`SEMATIC_WORKER_API_ADDRESS`. That will set the URL to be used from
Kubernetes, while `SEMATIC_API_ADDRESS` will be used from your machine.
{% endhint %}


### Kubernetes setup

Assuming you have

* a Kubernetes cluster instantiated in your cloud,

* have the [AWS CLI
  installed](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
  on your machine,

* have [`kubectl`
installed](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/) on
your machine,

you can generate the Kube config for your cluster with

```
$ aws eks update-kubeconfig --region <region> --name <cluster-name>
```

then verify that everything is set up correctly with

```
$ kubectl get svc
NAME         TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
kubernetes   ClusterIP   172.20.0.1   <none>        443/TCP   14d
```

Select the relevant namespace with
```
$ kubectl config set-context --current --namespace=<namespace>
```

then set this namespace in Sematic settings with
```
$ sematic settings set KUBERNETES_NAMESPACE <namespace>
```

### Cloud storage bucket

Once you have created an S3 bucket, make sure your Kubernetes cluster's node
groups' IAM role has the following policy:

```
arn:aws:iam::aws:policy/AmazonS3FullAccess
```

then set the name of your bucket in your Sematic settings:

```
$ sematic settings set AWS_S3_BUCKET <bucket-name>
```

### Container registry

Make sure you have [Docker installed](https://docs.docker.com/engine/install/)
on your machine, then authenticate with your container registry with

```
$ aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.<region>.amazonaws.com
```

You will likely need to issue this command every day.