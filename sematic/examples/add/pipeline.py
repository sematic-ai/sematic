from typing import List

# Standard Library
import time

# Sematic
import sematic
from sematic.types import PromptResponse


@sematic.func
def add(a: float, b: float) -> float:
    """
    Adds two numbers.
    """
    time.sleep(5)
    return a + b


@sematic.func
def add3(a: float, b: float, c: float) -> float:
    """
    Adds three numbers.
    """
    return add(add(a, b), c)


ARTICLE = """

Cloud platforms such as Amazon Web Services (AWS), Google Cloud Platform (GCP), or Azure offer a plethora of very practical and scalable managed services (storage, compute, databases, etc.), and do not necessarily require infrastructure skills to use, but they can infamously run up your costs if not managed correctly.

Here are five tips to ensure your Machine Learning (ML) workloads do not overwhelm your cloud bill.

Prerequisite: track and measure costs

The AWS billing dashboard
As the old adage says: what is not measured cannot be optimized. So the first step before implementing any cost optimization is to know where you stand: how much are you spending and how?

All cloud platforms provide at least minimal cost tracking, e.g. per-service, per-region, etc. Work with your cloud administrator to access these reports.

You can go one step further and implement coarse database-level tracking: what models, teams, datasets spend/cost the most. As a first pass, this can be implemented by running SQL queries on your metadata databases (e.g. what training jobs take the longest, use the most compute, data, fail the most, etc.). Of course, this means that your ML platform must be tracking those things in the first place. These queries can be implemented and automated in usual analytics tools such as Tableau or Looker.

If you use an ML platform maintained by a platform team, you can work with them to implement specific app-level tracking to automatically populate certain cost leaderboards. You can also enforce quotas per user, team, project, model, time period, etc.

1. Caching
Compute caching

Caching expensive compute functions.
As you iterate on your ML model, you likely re-execute the same workload over and over again with different inputs and configurations. You experiment with different hyper-parameters, different model architectures, and so on. However, some parts of your training code may not change all that much or at all between successive executions.

For example, if your training pipeline includes data processing tasks that prepare input data for training, and you are currently iterating on your model architecture, you may want to make sure the training dataset is cached so that it is not regenerated each time. This can help you save money on data transfers and compute time.

To enable caching, make sure your successive transformation stages are implemented as distinct code units (e.g. functions) with well defined data contracts. Then make sure to persist the output of each stage with a storage key that can be explicit (a user-specified string) or implicit (automatically generated from input arguments). You can then ensure that when the same key is passed, the transformation workload will not be executed again, but instead the stored cache value is used.

Data caching
Even if you change input configurations at each execution of your training code and cannot cache compute tasks, it is likely that you will be accessing the same data repeatedly. Depending on where your workloads are running, it may be possible to cache this data on or near the compute resources.

For example, if your workload is running on a cloud Virtual Machine (VM, e.g. EC2 in AWS), you may be able to store part of your training data on the VM itself for much faster and cheaper access. Of course, the entire dataset will likely not fit on disk so you will have to implement some form of Least Recently Used (LRU) garbage collection. Alternatively, certain commercial solutions provide ways to mount a local S3 cache directly on your VMs (e.g. Alluxio).

2. Checkpoints

Checkpointing. Source: ML design patterns #2.
Warm restarts
The longer the training job, the more likely it is to fail before completion. This can be for various reasons: a bug in your code, transient failures (e.g. network blip), out-of-memory issues, etc. Who has not raged at a training job failing at the penultimate epoch, after hours or even days of training?

To remedy this, it is critical to implement "warm restarts". That means restarting training not from scratch, but from where the last job left it. For this to work, two things are necessary:

Save model checkpoints to persistent storage (e.g. a cloud bucket) on a regular basis (e.g. every epoch). PyTorch provides easy APIs to export a model checkpoint. Do make sure to store checkpoints in a location that will not disappear when your workload ends (i.e. not on the ephemeral disk of a Kubernetes pod).
Instrumenting your training code to enable loading a prior checkpoint upon start. This can be an optional input argument to point to an existing checkpoint.
Checkpointing combined with automatic retries can mean your workloads can fail and retry automatically, and pick up the work where they left it.

Early stopping
Waiting until a training job has completed to inspect results only to realize the model is garbage is a huge waste of resources. Ideally, you can have insights into your model performance during the training loop to decide whether a workload should be interrupted early.

This can also be implemented by periodically examining model performance via its checkpoints. If your ML platform provides a way to visualize certain in-progress metrics (e.g. loss, validation sample accuracy, etc.), or extract those from checkpoints, you can call off expensive workloads before they break the bank for nothing.

3. Colocate data and compute
Cloud data transfers can be quite expensive if not configured correctly. For example, transferring data between AWS regions can be twice as costly as within the same region, and transferring S3 data outside of AWS can be ten times as costly. Therefore, it is important that your workloads run in the same Availability Zone as the one where your data is stored. Not having data and compute colocated also yields higher compute costs, as your VMs are sitting around downloading data instead of using their CPUs/GPUs.

AWS	GCP	Azure
Within the same AZ	$0.00	$0.00	$0.00
To a different AZ	$0.02 per GB	$0.02-$0.14 per GB	$0.01-$0.16 per GB
To the internet	$0.05-$0.09 per GB	$0.11-$0.15 per GB	$0.05-$0.18 per GB
Source	Source	Source
Examples of egress costs at major cloud providers.

Talk to your infrastructure team to make sure that your cloud resources are set up to incur the least cost.

4. Maximize GPU utilization

GPUs are often under-utilized.
GPU compute is one of the most expensive cloud resources. Yet, when your GPU VM is downloading data, doing CPU work, or reading data into memory, it is not utilizing its GPU, so you are essentially paying for an idle resource.

Data loading optimization
Optimize the way your training data is being loaded to ensure a continuous flow of data to the GPU. Minimize data transfer overhead by preprocessing and loading data onto the GPU in advance, allowing for seamless and uninterrupted GPU computations.

This is a vast topic of discussion. Read more on this PyTorch documentation page.

Memory management
Efficiently manage GPU memory to maximize utilization. Avoid unnecessary data transfers between the CPU and GPU by keeping data on the GPU as much as possible. If memory constraints arise, consider memory optimization techniques such as data compression or using smaller data types to reduce memory footprint.

Optimized libraries and frameworks
Utilize GPU-optimized libraries and frameworks for machine learning, such as CUDA, cuDNN, and TensorRT. These libraries are designed to leverage the full potential of GPUs and provide efficient implementations of common operations, enabling higher GPU utilization.

Asynchronous operations
Utilize asynchronous operations whenever possible to keep the GPU busy. Asynchronous data transfers, kernel launches, and computations can overlap, enabling the GPU to perform multiple tasks concurrently and improve overall utilization.‍

Profile and optimize
Profile your GPU utilization using tools provided by your GPU vendor or frameworks. Identify potential bottlenecks or areas where GPU resources are underutilized. Based on the profiling results, optimize your code, data pipeline, and model architecture to increase GPU utilization in those areas.

5. Infrastructure-level cost optimizations
Choose the right cloud provider and pricing model
Different cloud providers offer varying pricing structures for machine learning services. Compare the pricing models, instance types, and available options to select the most cost-effective solution for your needs. Some providers also offer discounted pricing for long-term commitments or spot instances, which can significantly reduce costs.‍

Optimize instance types
Cloud providers offer a range of instance types with different performance characteristics and costs. Analyze your workload requirements and choose the instance type that provides the necessary computational power without overprovisioning. Consider options like burstable instances or GPU instances if they align with your workload.

Spot instances and preemptible VMs
Some cloud providers offer spot instances or preemptible VMs at significantly reduced prices compared to on-demand instances. These instances can be reclaimed by the provider at any time, but if your workload is flexible and fault-tolerant, utilizing these lower-cost options can yield substantial cost savings.

Utilize auto-scaling
Take advantage of auto-scaling capabilities offered by cloud providers to automatically adjust the number of instances based on demand. Scale up or down your resources dynamically to match the workload, ensuring you only pay for what you need.

Bonus: Optimizing ML costs beyond cloud
Let's face it, the number one greatest cost to doing ML at your company is likely... humans.

Engineering costs
ML Engineers are very expensive resources. One way to reduce costs is to make sure each ML Engineer is equipped and trained to perform the highest-leverage work at all times. That can take the following forms:

Recurrently groom roadmaps to deprioritize low-impact projects
Carefully select the best tools to maximize productivity
Delegate certain tasks to specialized teams (e.g. leveraging platform and infrastructure teams for infra/system work)
Set up generous knowledge-sharing processes to make sure more seasoned engineers enable newer ones to do their best work (e.g. brown-bag sessions, mentorship programs, foster a culture of sharing)
Labeling costs

Data labeling is a major cost center.
Most data labeling is still done by humans, and can be quite costly. You can optimize this cost center in those ways:

Make sure only the highest-leverage data is being labeled. For example, focus on sampling the long tail of rare events that are underrepresented in your training dataset, and lead to outsized failures in production. There is no need to relabel over and over again the same type of event on which your model already performs very well.
Leverage auto-labeling techniques. You may not get the same quality labels as from human labelers, but for certain data, using simpler models, algorithmic heuristics, or data mining techniques can help reduce the volume of data that needs to be sent to your labeling service.
Wrap-up
Because of their heavy reliance on large datasets and powerful compute, ML workloads are particularly costly. Large ML organizations have entire teams dedicated to cost tracking and optimization.

However, that does not mean that you cannot do anything about it at your scale. With careful design, consideration, and optimization, you can greatly reduce your cost, all the while making great progress on your model development and model performance.

Reach out to us on our Discord server to discuss how to keep your cloud bill under control.
"""

@sematic.func
def pipeline(a: float, b: float, c: float) -> List[PromptResponse]:
    """
    ## This is the docstring

    A trivial pipeline to showcase basic future encapsulation.

    This pipeline simply adds a bunch of numbers. It shows how functions can
    be arbitrarily nested.

    ### It supports markdown

    `pretty_cool`.
    """
    # sum1 = add(a, b)
    # sum2 = add(b, c)
    # sum3 = add(a, c)
    # return add3(sum1, sum2, sum3)
    return [
        PromptResponse(
            prompt="Something short",
            response="Something also short",
        ),
        PromptResponse(
            prompt=ARTICLE,
            response="Reduce costs by optimizing infra usage.",
        ),
    ]
