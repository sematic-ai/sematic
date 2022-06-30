Sematic aims to make your development workflow faster and more efficient.

It is quite typical to start iterating on a pipeline locally, e.g. on 1% of the
data, and then run it at scale in the cloud.

Sematic enables this seamlessly by aiming to guarantee a local-to-cloud parity.
This means that if your pipeline runs succesfully locally, it should run
succesfully at scale on the cloud.

Of course there are many reasons why a cloud pipeline could fail that are not
forseeable locally. For example: network failures, Out-of-memory issues,
differences in underlying hardware (CPU, GPU, etc.), invalid data not present in
your local 1%, rare corner cases, etc.

But when it comes to building your code, correctness of your type hints and
syntax, and dependency packaging, Sematic can do a great deal to save you from a lot
of wasted time.

Sematic provides the following execution stragegies:

### Silent execution

Silent execution runs your code locally (i.e. on your machine) and does not
write anything to the (local) database. Your pipeline will not show up in the UI.

This is useful for quick debugging in a Python console, or writing tests.

To use this mode, simply do:

```
>>> pipeline(...).resolve(tracking=False)
```

### Local execution

This is the default mode. Your pipeline still runs on your local machine, but
tracks execution in Sematic's database. Your pipeline's runs and artifacts are
visualizable in the UI.

To use this mode, simply do:

```
>>> pipeline(...).resolve()
```

{% hint style="info" %}

Out of the box, Sematic writes to a local database sitting on your local machine,
and the UI also runs in a local server.

To be able to share results with your team, it is best to deploy Sematic in your
cloud infrastructure. See [Deploy Sematic](./coming-soon.md).


{% endhint %}

### Cloud execution

{% hint style="warning" %}

Cloud execution is currently under development, check our [public roadmap]().

{% endhint %}

Cloud execution will let you execute your pipeline remotely in your cloud. Each
individual Sematic function can have its own resource requirements (e.g. GPUs
for your training function).