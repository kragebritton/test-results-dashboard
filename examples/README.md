# Examples

## Generate client and Locust scaffolding

```bash
openapi-locustgen \
  --spec examples/simple_openapi.yaml \
  --out generated_api \
  --client-class GeneratedApiClient \
  --user-class GeneratedApiUser
```

## Run Locust

Install `locust` and then run from the repository root:

```bash
locust -f examples/locustfile.py
```

The example locustfile imports the generated code from the `generated_api`
package created by the CLI command above.
