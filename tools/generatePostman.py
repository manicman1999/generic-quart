import json

from stringExtension import plural


def convert_to_postman(registry_path: str, postman_path: str):
    with open(registry_path, "r") as f:
        registry_data = json.load(f)

    postman_collection = {
        "info": {
            "name": "Generic (Generated)",
            "description": "Generated from registry.json",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": [],
    }

    for controller in registry_data:
        for controller_name, routes in controller.items():
            folder = {
                "name": plural(controller_name.replace("Controller", "")),
                "item": [],
            }
            for route in routes:
                request = {
                    "name": f"{route['methods'][0]} {route['prefix']}{route['rule']}",
                    "request": {
                        "method": route["methods"][0],
                        "header": [
                            {
                                "key": "Authorization",
                                "value": "Bearer {{token}}",
                                "type": "text",
                            },
                            {
                                "key": "Content-Type",
                                "value": "application/json",
                                "type": "text",
                            },
                        ]
                        if not route.get("jwtOptional")
                        else [
                            {
                                "key": "Content-Type",
                                "value": "application/json",
                                "type": "text",
                            }
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps(route.get("inputTemplate", {}), indent=4),
                        },
                        "url": {
                            "raw": f"{{{{api_host}}}}{route['prefix']}{route['rule']}",
                            "protocol": "",
                            "host": ["{{api_host}}"],
                            "path": route["prefix"].strip("/").split("/")
                            + list(
                                filter(
                                    lambda s: s != "",
                                    route["rule"].strip("/").split("/"),
                                )
                            ),
                        },
                    },
                    "response": [],
                }
                folder["item"].append(request)
            postman_collection["item"].append(folder)

    with open(postman_path, "w") as f:
        jsonString = json.dumps(postman_collection, indent=4)
        f.write(jsonString)


# Example usage:
convert_to_postman("registry.json", "postman_collection.json")
