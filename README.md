# openapi-locustgen

A small library and CLI for generating thin Python API clients and Locust load testing scaffolding from OpenAPI 3.x specifications. The goal is to make it easy to transform an OpenAPI file into a reusable client with adapters for different HTTP backends, plus base Locust user classes to compose realistic load tests.

This repository is under active development. The initial versions focus on parsing OpenAPI documents, defining a minimal internal model, and providing a command-line entry point for code generation.
