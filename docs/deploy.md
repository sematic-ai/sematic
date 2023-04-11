# Deploy Sematic

When you install Sematic the first time, according to the instructions from the
[Get started](get-started.md#installation) section, everything runs locally. The web app
and your pipelines run locally.

Here is how to deploy Sematic to take full advantage of your cloud resources.
Before you start, you will need to decide how you wish to use Sematic.

- Option 1 is to use Sematic to track and share your pipeline executions, but
  still have the pipelines execute locally. This setup is simpler, but less
  powerful.
- Option 2 is to deploy Sematic on Kubernetes, where the pipelines
  can have access to more powerful compute by executing in the cloud. This
  setup is a little more complex and has more pre-requisites.

## Deployment Option 1: Shared Metadata Server

You can deploy the Sematic server so that you and others
can share results of Sematic pipelines. With this
option, you get all the experiment tracking functionality of the Sematic UI –
including input/output visualization, chat, and more.
Your pipelines will still execute locally.

### Deploy the web app

Prerequisites:

- A remote instance into which you can SSH
- A Postgres database
- [Install Docker](https://docs.docker.com/engine/install/) onto your remote instance

Then, SSH into your remote server:

```shell
$ ssh my-remote-server.dev
```

Pull the server image for the release of Sematic you want to deploy

```shell
$ DEPLOY_VERSION=v<MAJOR.MINOR.PATCH>  # use the actual version numbers here
$ sudo docker pull sematic/sematic-server:$DEPLOY_VERSION
```

launch the server

```shell
$ sudo docker run -d -p 80:80 \
    -e DATABASE_URL=<DATABASE_URL> \
    -v /home/ubuntu/.sematic:/root/.sematic \
    [-e SEMATIC_AUTHENTICATE=1 -e GOOGLE_OAUTH_CLIENT_ID=123456789.apps.googleusercontent.com \]
    [-e SEMATIC_AUTHORIZED_EMAIL_DOMAIN=yourdomain.com \]
    [-p 443:443 -e CERTIFICATE=/path/to/certificate.pem -e PRIVATE_KEY=/path/to/private.key \]
    sematic/sematic-server:$DEPLOY_VERSION
```

where DATABASE_URL is the fully-qualified URL of your Postgres database. It should be of the form:

```
postgresql://<username>:<password>@<hostname>:<port>/<database>
```

Now you should be able to visit http://my-remote-server.dev and see the landing page.

#### Configuration

##### Authentication

In the `docker run` command above, three optional environment variables dictate authentication
behavior for your deployed app.

If you don't pass any of them, your app will be available publicly and users will not need to
authenticate to use it. Everyone will be the "Anonymous" user.

- `SEMATIC_AUTHENTICATE` activates authentication. Users will need to sign in to user the web app,
  and will need to set an API key in their local settings in order to submit jobs.
- `GOOGLE_OAUTH_CLIENT_ID` is the client ID of your Google OAuth App. We will support more OAuth
  providers in the future.
- `SEMATIC_AUTHORIZED_EMAIL_DOMAIN` denies access to users whose email is not of said domain.

##### SSL

If you have an SSL certificate for the domain on which you are deploying Sematic,
you can pass it to the server container with the `CERTIFICATE` and `PRIVATE_KEY`
environment variables when calling docker run. Make sure that the certificate and
private key files are accessible within the container (e.g. place them in the
`~/.sematic` directory). Also make sure to add `-p 443:443` to the forwarded ports.

## Deployment Option 2: Sematic with Cloud Execution

If you wish to not only use your Sematic deployment to share the results
of pipeline executions, but also to actually execute the pipelines, you
will need to deploy it on Kubernetes.

### Deploy the web app

Prerequisites:

- A Kubernetes cluster running Kubernetes >=1.23.  1.24 recommended as officially supported.
- A Postgres database
- [Helm](https://helm.sh/docs/intro/install/#helm) &
  [kubectl](https://kubernetes.io/docs/tasks/tools/) installed and
  able to access your Kubernetes cluster
- Ingress configured on your cluster that allows accessing services deployed on it

Add the Sematic Helm repository to your cluster:

```shell
$ helm repo add sematic-ai https://sematic-ai.github.io/helm-charts
```

Configure the contents of `helm/sematic/values.yaml` (see the sections below).
Once you have set all the values, deploy the Sematic Helm chart to your cluster:

```
$ helm install sematic-server sematic-ai/sematic-server \
        -n <NAMESPACE FOR DEPLOYING> \
        -f <PATH TO YOUR CONFIGURED VALUES YAML FILE>
```

Once the command above completes, it can take a few minutes for all of the Sematic
resources to be created in your Kubernetes cluster.  You should see the Sematic
Dashboard landing page when you open the Ingress host path in your browser when
deployment is complete.

#### Configuration

##### Database

You should create a separate database and an owner user, in order to ensure the service can perform
required database schema migrations.

In the `values.yaml` file above, the setting `database.url` can be set to the fully-qualified URL
of your Postgres database, using the credentials of the owner user.  It should look similar to the
following:

```
postgresql://<username>:<password>@<hostname>:<port>/<database>
```

If the `database.url` setting is valid, you can set the `secret.create` setting
to `true`, and the Helm chart will automatically create a secret named `sematic-server`
for you.

Alternatively, you can set `secret.create` to `false`, and create the secret
yourself:

```shell
$ kubectl create secret generic sematic-server \
    --namespace=<NAMESPACE FOR DEPLOYING> \
    --from-literal=DATABASE_URL=<YOUR DATABASE URL>
```

For example:

```shell
$ kubectl create secret generic sematic-server \
    --namespace=default
    --from-literal=DATABASE_URL=postgresql://postgres:mYdBpA55worD@my.db.url.com:5432/my-database-name
```

##### Cloud storage bucket

When deployed in the cloud, Sematic artifacts need to be stored in an AWS S3
bucket.  You'll need to set the `aws.enabled` setting to `true`, as well as set
the `aws.storage_bucket` value to the name of your AWS S3 bucket.

##### Authentication

In the `values.yaml` file above, three settings dictate the
authentication behavior for your deployed app.

- `auth.enabled` activates authentication. Users will need to sign in to
  user the web app, and will need to set an API key in their local settings in
  order to submit jobs.

- `auth.google_oauth_client_id` is the client ID of your Google OAuth App.
  We will support more OAuth providers in the future.

- `auth.authorized_email_domain` denies access to users whose email is not of
  said domain.

##### Ingress

The Helm chart can create an ingress for you by setting `ingress.create` to `true`, and by
specifying the ingress domain information like so in the `ingress.hosts` setting:

```
  hosts:
    - host: chart-example.local
      paths:
        - path: /
          pathType: ImplementationSpecific
```

##### SSL

If you wish to put your Kubernetes Sematic deployment behind SSL, the recommended way to do
this is to set up an [ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)
that points to the service (named `sematic-server`) deployed by the Helm chart,
and set up your ingress to use SSL.

##### Additional configuration options

There are several other configuration options that can be used to customize the
Sematic Helm installation to your specific needs.  While we've chosen reasonable
default values for these, you can explore them further in the [Helm chart docs](https://sematic-ai.github.io/helm-charts/).

## Using your deployment

### Run pipelines against the deployed API

At this point you should be able to run pipelines that are tracked by Sematic.
In order to write metadata to the deployed API, simply do:

```shell
$ sematic settings set SEMATIC_API_ADDRESS http://my-remote-server.dev
```

This is required regardless of whether you deployed using Option 1 or Option 2.

### Run pipelines in your cloud

In order to benefit from cloud resources (e.g. GPUs, high memory, etc.), Sematic
lets you run pipelines in a Kubernetes cluster. This requires that you set up
Sematic using deployment Option 2.

{% hint style="warning" %}

In theory Sematic can run in any cloud provider. However, at this time, Sematic
focuses support on **Amazon Web Services**. Other providers to follow soon.

{% endhint %}

Before you proceed, the following must be true:

- The Sematic web app is deployed. See
  [Deploy the web app](#deployment-option-2-sematic-with-cloud-execution).

- You have an S3 bucket and you and nodes in your Kubernetes cluster have read
  and write permissions to it.

- You have a container registry (e.g. AWS Elastic Container Registry) and you
  have write access, and nodes in your Kubernetes cluster have read access to
  it.

- You have `sematic_pipeline` bazel targets defined as described in
  [Container Images](./container-images.md). This will enable `bazel run` commands
  to execute the launch script to start your cloud jobs.

{% hint style="warning" %}

Sematic plans to support other ways to produce container images besides
bazel, but for now it is required for cloud execution.

{% endhint %}

When you are set, the following settings should be visible to Sematic

```
$ sematic settings show
Active user settings:

SEMATIC_API_ADDRESS: <web-app-server-address>
```

{% hint style="warning" %}

If you have chosen to deploy Sematic in such a way that users of Sematic
will use a different URL for the server from what should be used for
jobs on your Kubernetes cluster (e.g. users access via a reverse proxy
that's not needed on Kubernetes), you may also need to set the
`SEMATIC_WORKER_API_ADDRESS` server setting. That will set the URL to be used
from Kubernetes, while `SEMATIC_API_ADDRESS` will be used from your machine.
{% endhint %}

#### Cloud storage bucket

Once you have created an S3 bucket, make sure your Kubernetes cluster's node
groups' IAM role has the following policy:

```
arn:aws:iam::aws:policy/AmazonS3FullAccess
```

then set the name of your bucket in your Sematic user settings:

```
$ sematic settings set AWS_S3_BUCKET <bucket-name>
```

#### Container registry

Make sure you have [Docker installed](https://docs.docker.com/engine/install/)
on your machine, then authenticate with your container registry with

```bash
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.<region>.amazonaws.com
```

You will likely need to issue this command every day.

## Upgrading and enhancing your deployments

Eventually, you will want to access the latest features Sematic has
to offer! You might also want to get set up with some of the
advanced integrations we provide. When you're ready to do this,
check out our [upgrades guide](./upgrades.md) for help.
