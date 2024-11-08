import asyncio
import os
from typing import Optional

from aiClient import AIClient
from stringExtension import ModelName, plural


project_folder = "."

template_locations: dict[str, str] = {
    "object": f"{project_folder}/tools/templates/domain/object.txt",
    "command": f"{project_folder}/tools/templates/persistence/command.txt",
    "query": f"{project_folder}/tools/templates/persistence/query.txt",
    "service": f"{project_folder}/tools/templates/services/service.txt",
    "controller": f"{project_folder}/tools/templates/api/controller.txt",
}


def get_location(
    gentype: str, model: ModelName, name: Optional[ModelName] = None
) -> str:
    if gentype == "object":
        return f"{project_folder}/domain/{model}s/{model}.py"
    if gentype == "command":
        return f"{project_folder}/persistence/{model}s/commands/{name or ('upsert' + model.pascal)}Command.py"
    if gentype == "query":
        return f"{project_folder}/persistence/{model}s/queries/{name or ('get' + plural(model.pascal) + 'ByIds')}Query.py"
    if gentype == "service":
        return f"{project_folder}/services/{model}s/{model}Service.py"
    if gentype == "controller":
        return f"{project_folder}/api/{model}s/{model}Controller.py"
    raise Exception("Not a valid generation type")


def addRoutes_to_routing_file(model: ModelName):
    routing_file_path = f"{project_folder}/api/routing.py"

    import_line = f"from api.{model}s.{model}Controller import {model.pascal}Controller\n"
    register_line = f"        {model.pascal}Controller(),\n"

    # Read the existing content of the routing.py file
    with open(routing_file_path, "r") as f:
        lines = f.readlines()

    # Add the import line at an appropriate location (e.g., after the last import)
    last_import_index = next(
        (i for i, line in reversed(list(enumerate(lines))) if "import" in line), -1
    )
    lines.insert(last_import_index + 1, import_line)

    # Add the register line at an appropriate location (e.g., inside addRoutes function)
    last_register_index = next(
        (
            i
            for i, line in reversed(list(enumerate(lines)))
            if "Controller()," in line
        ),
        -1,
    )
    lines.insert(last_register_index + 1, register_line)

    # Write the updated content back to routing.py
    with open(routing_file_path, "w") as f:
        f.writelines(lines)


async def generate(gentype: str, model: ModelName, action_name: Optional[ModelName] = None, prompt: str = ""):
    location = get_location(gentype, model, action_name)
    template_location = template_locations[gentype]

    with open(template_location) as f:
        template_str = f.read()

    full_str = (
        template_str.replace("{Model}", model.pascal)
        .replace("{model}", model.camel)
        .replace("{model_}", model.snake)
        .replace("{model-}", model.kebab)
    )

    if gentype == "query" and action_name is None:
        action_name = ModelName("get" + plural(model.pascal) + "ByIds")
    if gentype == "command" and action_name is None:
        action_name = ModelName("upsert" + model.pascal)

    full_str = full_str.replace("{Name}", action_name.pascal if action_name else "")

    if prompt != "":
        system = """
You will be given a chunk of code and a prompt. You are to adjust the code according to the prompt, then return it. Do not return anything other than the code. The code will likely use things from custom libraries, and custom classes. This is fine, use them as best you can.

For most requests you'll mostly be editing mongo queries and commands, and you may need to make them into aggregates. These will not be difficult. Just generate the code as best you can, and use context clues from the code (e.g. if it's a get by ____ query, adjust so it gets by that parameter). Sometimes, you will be asked to generate domain objects.

All parameters are camel case, all classes are pascal case. Do NOT use snake_case.

You should change the given code as much as you need to to follow the prompt. The code given is just a generic template.

The custom classes will all be children of the Abstract Entity class:

@dataclass
class AbstractEntity(BaseEntity):
    id: UUID
    createdDate: datetime
    createdBy: Optional[UUID]
    updatedDate: datetime
    updatedBy: Optional[UUID]

    @classmethod
    def getCollectionName(cls):
        collection_name = plural(lowerFirstLetter(cls.__name__))
        return collection_name

    def fillInfo(self):
        // Fills values like createdDate, updatedBy, etc.

@dataclass
class BaseEntity:
    
    def toDict(self, safedate = False):
        // Turns this object to a dict

    @classmethod
    def fromDict(cls, d: dict):
        // Makes an object from a dict
        """.strip()

        fullPrompt = f"Prompt: {prompt}\nCode:\n{full_str}"

        client = AIClient()
        full_str = await client.chatCompletion(system, fullPrompt, "gpt-4o-2024-08-06")
        full_str = full_str.replace("```python\n", "").replace("```", "").replace("```python\n", "")

    directory = os.path.dirname(location)
    if not os.path.exists(directory):
        os.makedirs(directory)

    if gentype == "controller":
        addRoutes_to_routing_file(model)

    with open(location, "w") as f:
        f.write(full_str)


async def generate_full(model: ModelName, prompt: str = ""):
    await generate("object", model, prompt=prompt)
    # generate("query", model)
    # generate("command", model)
    await generate("service", model)
    await generate("controller", model)

async def main():
    gentype_csv = ", ".join(list(template_locations.keys()))
    gentype = input(f"Generation type? (full, {gentype_csv}): ")
    model = input("Model name: ")
    action_name = None
    prompt = ""

    if gentype in ["query", "command"]:
        action_name = input("Action name: ")
    prompt = input("Prompt: ")


    if gentype == "full":
        await generate_full(ModelName(model), prompt)
    else:
        await generate(
            gentype, ModelName(model), ModelName(action_name) if action_name else None, prompt
        )

if __name__ == "__main__":
    asyncio.run(main())