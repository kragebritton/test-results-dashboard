"""Example Locustfile showing how to use generated scaffolding."""

from locust import SequentialTaskSet, task
from generated_api.locust_base import GeneratedApiUser


class ExampleScenario(SequentialTaskSet):
    def on_start(self):
        self.api = self.user.api

    @task
    def list_pets(self):
        response = self.api.listPets()
        assert 200 <= response.status_code < 300


class WebsiteUser(GeneratedApiUser):
    tasks = [ExampleScenario]
