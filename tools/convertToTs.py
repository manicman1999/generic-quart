import dataclasses
import datetime
import os
import re
import sys
import importlib.util
from dataclasses import is_dataclass, fields
from typing import Any, List, Set, Tuple, Type, Dict, get_args, get_type_hints
import uuid


def python_type_to_typescript(python_type: str) -> str:
    mapping = {
        "str": "string",
        "int": "number",
        "bool": "boolean",
        "UUID": "string",
        "datetime": "Date",
        "float": "number",
        "dict": "any",
        
        # Special
        "Optional[UUID]": "string | null",
        "Exception": "any",
        "T": "any"
    }
    if python_type.startswith("Optional["):
        inner_type = python_type[9:-1]
        ts_type = mapping.get(inner_type, inner_type)
        return f"{ts_type} | null"
    if "enum" in python_type.lower() or "type" in python_type.lower():
        return "number"
    return mapping.get(python_type, python_type)


def get_class_name(cls: Type) -> str:
    return cls.__name__


def get_bases(cls: Type) -> List[str]:
    return [base.__name__ for base in cls.__bases__ if base.__name__ != "object"]


def get_fields(cls: Type) -> List[str]:
    fields = []
    type_hints = get_type_hints(cls)
    for field_name, field_type in type_hints.items():
        is_optional = "Optional" in str(field_type)
        is_list = "list" in str(field_type) or "tuple" in str(field_type)
        op_string = ""

        if is_list or is_optional:
            field_type = get_args(field_type)[0]

        ts_type = python_type_to_typescript(str(field_type.__name__))

        if is_list:
            ts_type += "[]"

        if is_optional:
            op_string = "?"

        field_line = f"    {field_name}{op_string}: {ts_type};"
        fields.append(field_line)
    return fields


def get_properties(cls: Type) -> List[str]:
    properties = []
    classes = cls.__mro__  # Get the method resolution order to include base classes
    for base_cls in classes:
        for attr_name, attr_value in base_cls.__dict__.items():
            if "_" in attr_name:
                continue
            if isinstance(attr_value, property):
                prop_type = get_type_hints(attr_value.fget).get("return")

                if prop_type:
                    is_optional = "Optional" in str(prop_type)
                    is_list = "list" in str(prop_type.__name__).lower() or "tuple" in str(prop_type.__name__)
                    op_string = ""

                    if is_list or is_optional:
                        prop_type = get_args(prop_type)[0]

                    ts_type = python_type_to_typescript(str(prop_type.__name__))

                    if is_list:
                        ts_type += "[]"

                    if is_optional:
                        op_string = "?"
                        
                    properties.append(f"    {attr_name}{op_string}: {ts_type};")
    return properties


def get_classes_from_module(module):
    return [obj for name, obj in vars(module).items() if is_dataclass(obj)]


def convert_to_typescript(cls: Type) -> str:
    class_name = get_class_name(cls)
    bases = get_bases(cls)
    fields = get_fields(cls)
    properties = get_properties(cls)

    ts_class = f"export interface {class_name} {{\n"
    ts_class += "\n".join(fields + properties)
    ts_class += "\n}"
    return ts_class


def process_domain_folder(
    domain_folder: str, top_level_folder: str, skip_files: List[str] = []
) -> List[str]:
    ts_classes = []
    abs_domain_folder = os.path.abspath(domain_folder)
    abs_top_level_folder = os.path.abspath(top_level_folder)
    sys.path.insert(0, abs_top_level_folder)  # Add top-level folder to sys.path
    class_names: Set[str] = set()

    for root, _, files in os.walk(abs_domain_folder):
        for file in files:
            if file in skip_files:
                print(f"Skipping {file}.")
                continue
            if file.endswith(".py"):
                print(f"Converting {file}.")
                module_path = os.path.join(root, file)
                relative_module_path = os.path.relpath(
                    module_path, abs_top_level_folder
                )
                module_name = re.sub(
                    r"\.py$", "", relative_module_path.replace(os.sep, ".")
                )

                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)  # type: ignore
                spec.loader.exec_module(module)  # type: ignore

                dataclasses = get_classes_from_module(module)
                for dataclass in dataclasses:
                    class_name = dataclass.__name__
                    if class_name in class_names:
                        continue
                    if "Generated" in class_name:
                        continue
                    ts_classes.append(convert_to_typescript(dataclass))
                    class_names.add(class_name)

    sys.path.pop(0)  # Remove top-level folder from sys.path
    return ts_classes


def write_to_file(ts_classes: List[str], output_file: str):
    with open(output_file, "w") as f:
        for ts_class in sorted(ts_classes, key=lambda x: x.lower().count("dto")):
            f.write(ts_class + "\n\n")


# Example usage
domain_folder = "domain"
top_level_folder = ""  # The top-level folder for your Flask app
output_file = "C:\\Users\\mattm\\Desktop\\Code\\generic-frontend\\src\\objects\\objects.tsx"
skip_files = ["openAIClient.py", "option.py", "domainError.py"]

ts_classes = process_domain_folder(domain_folder, top_level_folder, skip_files)
write_to_file(ts_classes, output_file)
