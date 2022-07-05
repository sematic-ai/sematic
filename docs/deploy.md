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
$ sudo docker run -d -p 80:80 -e DATABASE_URL=<DATABASE_URL> \
    -v /home/ubuntu/.sematic:/root/.sematic \
    sematicai/sematic-server:latest
```

where `DATABASE_URL` is the fully-qualified URL of your Postgres database. It
should be of the form:

```
postgresql://<username>:<password>@<hostname>:<port>/<database>
```

Now you should be able to visit http://my-remote-server.dev and see the landing page.

### Run pipelines against the deployed API

At this time Sematic still runs your pipelines on your local machine (cloud
execution coming soon). In order to write metadata to the deployed API, simply do:

```shell
$ sematic settings set SEMATIC_API_ADDRESS http://my-remote-server.dev
```