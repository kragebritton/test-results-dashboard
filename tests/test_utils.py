from openapi_locustgen.utils import load_openapi


def test_load_openapi_parses_operations():
    doc = load_openapi("tests/data/simple_openapi.yaml")

    assert doc.title == "Simple Petstore"
    assert doc.version == "1.0.0"

    op_ids = {op.operation_id for op in doc.operations}
    assert {"listPets", "createPet", "getPet", "put_pets_petId"} <= op_ids

    get_pet = next(op for op in doc.operations if op.operation_id == "getPet")
    assert get_pet.method == "GET"
    assert get_pet.path == "/pets/{petId}"
    assert any(param.name == "petId" and param.in_ == "path" for param in get_pet.parameters)

    create_pet = next(op for op in doc.operations if op.operation_id == "createPet")
    assert create_pet.request_body is not None
    assert create_pet.request_body.content_type == "application/json"

    update_pet = next(op for op in doc.operations if op.operation_id == "put_pets_petId")
    assert update_pet.request_body is not None
    assert any(param.name == "verbose" and param.in_ == "query" for param in update_pet.parameters)

    list_pets = next(op for op in doc.operations if op.operation_id == "listPets")
    assert list_pets.responses[200].description == "A paged array of pets"
