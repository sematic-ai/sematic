# GitHub[^1]

## Summary

At Sematic, we believe testing is crucial to enhancing your development loop, whether
it be "traditional" code, [unit testing of ML pipelines](./testing.md), or running full
[regression pipelines](https://www.sematic.dev/blog/continuous-learning-for-safer-and-better-ml-models)
involving your data and models.

```TODO: Write summary of functionality```



## GitHub Configuration

The following steps must be done by somebody with permissions to administer the GitHub
organization that you wish to integrate with Sematic.

### Getting an access token for usage by Sematic

```TODO: Short Summary```

#### Allow Usage of Personal Access Tokens
```TODO: Refine```
*Organization Settings > Third-party Access section > Personal access tokens > Settings*

**Allow access via fine-grained personal access tokens**

Save

#### Create a Personal Access Token
```TODO: Refine```

*User settings > Developer Settings > Personal access tokens > Fine-grained tokens*

Generate New Token

- fill out name
- fill out description
- set expiration for one year
- Select "Resource owner" to be the GitHub organization you wish to check commits in
- Under "Repository access", select repositories you wish to use Sematic's GitHub integration with
- *Permissions > Repository permissions > Commit statuses*. Set access to "Read and write"
- "Generate Token" button
- Copy the token, save it to a secure place

#### Approve Personal Access Token
```TODO: Refine```

This step is only required if you required administrator approval for
Personal Access Token usage in the
[Allow Usage of Personal Access Tokens](#allow-usage-of-personal-access-tokens)
section above.

*Organization Settings > Third-party Access section > Personal access tokens > Pending requests*

Approve the Personal Access Token request.

### Requiring Sematic Checks to Pass

(Optional)

```TODO: Write```

## CI Configuration

```TODO: Write```

## Sematic Configuration

```TODO: Write```

[^1]: This feature of Sematic is only available with the "Enterprise Edition."
Before using, please reach out to Sematic via support@sematic.dev to obtain a
license for "Sematic EE."