# Grafana integration

Sematic lets you display a Grafana panel on in the Logs tab of the [Run
Panel](./sematic-ui.md#run-panel).

## Parametrize your Grafana panel

In order for Sematic to be able to display logs specifically for a particular
function, your Grafana panel needs to be parametrized with a `container`
variable.

To achieve this:

* Open the Grafana dashboard, click the cog button in the top right
* Select **Variables** in the left menu
* Add a variable named **container** of type "Text box".
* Edit your panel to use the variable `$container` in the log query

For example, if you are using AWS CloudWatch logs, the log query can look like:

```
filter @logStream like "$container" | fields log
```

## Set the Grafana embed URL

In your Grafana dashboard, select the panel you want to embed in Sematic, click
on its header and select **Share**. Select the **Embed** tab and extract the
iframe src URL that is displayed. Do not worry about the URL parameters.

Then pass the `GRAFANA_PANEL_URL` environment variable to the Sematic server
either by passing it explicitly to the `docker` command:

```shell
$ docker run ... -e GRAFANA_PANEL_URL="<url>" ...
```

or by adding it to `~/.sematic/settings.yaml`:

```yaml
# ~/.sematic/settings.yaml

default:
  # ...
  GRAFANA_PANEL_URL: <url>
  # ...
```

then restart the server.

## Authentication

Make sure embeddings are allowed in your Grafana instance:

```ini
# grafana.ini

[security]
allow_embedding = true
```

The, in order for the embed to function, there are two options.

### Option 1: Anonymous access

You can enable anonymous access to your Grafana instance by setting
```ini
# grafana.ini

[auth.anonymous]
enabled = true
```
in `grafana.ini`. This is obviously not the safest option but if your Grafana
instance is behind a VPN it's ok.

### Option 2: TLS and SameSite=None

If both your Sematic and Grafana instances are protected with TLS certificates,
you can set the following settings to ensure Grafana cookies can be sent while
visiting your Sematic instance:

```ini
# grafana.ini

[security]
cookie_samesite = none
cookie_secure = true
```