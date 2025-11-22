# openapi-locustgen

A small library and CLI for generating thin Python API clients and Locust load testing scaffolding from OpenAPI 3.x specifications. The goal is to make it easy to transform an OpenAPI file into a reusable client with adapters for different HTTP backends, plus base Locust user classes to compose realistic load tests.

This repository is under active development. The initial versions focus on parsing OpenAPI documents, defining a minimal internal model, and providing a command-line entry point for code generation.

## Usage

```bash
openapi-locustgen \
  --spec examples/simple_openapi.yaml \
  --out generated_api \
  --client-class GeneratedApiClient \
  --user-class GeneratedApiUser
```

This produces a small package with:

* `client.py` – a thin API client built from your OpenAPI spec
* `locust_base.py` – a `FastHttpUser` subclass that wires in the generated client via the Locust adapter

See `examples/` for an example Locustfile that uses the generated package.
