# NOTE: This doesn't really work.

import json
import re

from stringExtension import capitalize_first_letter, kebab_to_pascal

inputTypeMatch = {
    'Any': 'any',
    'bool': 'boolean',
    'string': 'string',
    'str': 'string',
    'str[]': 'string[]',
    'int': 'number',
    'float': 'number'
}

routeVarPattern = r'<[^:]+:[^>]+>'


def convert_to_ts(registry_path: str, ts_path: str):
    with open(registry_path, "r") as f:
        registry_data = json.load(f)

    ts_classes = {}
    seen_types: set[str] = set()

    for controller in registry_data:
        for controller_name, routes in controller.items():
            class_name = controller_name.split("Controller")[0] + "API"
            if class_name not in ts_classes:
                ts_classes[class_name] = []

            for route in routes:
                # Generate TypeScript function
                rulePath: list[str] = route['rule'].split('/')
                rulePathNames: list[str] = []
                
                routeInputs: list[tuple[str, str, str]] = [] # <string:userId>, string, userId
                
                for section in rulePath:
                    match = re.match(routeVarPattern, section)
                    if match:
                        inputType = section.split(":")[0].strip('<')
                        inputType = inputTypeMatch.get(inputType, inputType)
                        
                        varName = section.split(":")[1].strip('>')
                        rulePathNames.append(f"By{capitalize_first_letter(varName)}")
                        
                        routeInputs.append((section, inputType, varName))
                    else:
                        rulePathNames.append(capitalize_first_letter(kebab_to_pascal(section)))
                
                
                func_name = f"{route['methods'][0].lower()}{capitalize_first_letter(kebab_to_pascal(route['prefix'].strip('/')))}{''.join(rulePathNames)}"
                func_name = func_name.replace("__", "_").replace("__", "_").strip("_")

                url = f"${{HOST}}{route['prefix']}{route['rule']}"
                pattern = r'<[^:]+:([^>]+)>'
                url = re.sub(pattern, r'${\1}', url)
                
                input_type = route.get("inputType")
                output_type = route.get("outputType")
                
                pattern = r'list\[(\w+)\]'
                
                if input_type is not None:
                    input_type = re.sub(pattern, r'\1[]', input_type)
                    input_type = inputTypeMatch.get(input_type, input_type)
                    seen_types.add(input_type.replace('[]', ''))
                if output_type is not None:
                    output_type = re.sub(pattern, r'\1[]', output_type)
                    output_type = inputTypeMatch.get(output_type, output_type)
                    seen_types.add(output_type.replace('[]', ''))
                
                inputVars = ', '.join([f"{routeInput[2]}: {routeInput[1]}" for routeInput in routeInputs])
                
                dataString = ""
                if input_type is not None:
                    inputVars = f"input: {input_type} | any{', ' + inputVars if len(inputVars) > 0 else ''}"
                    dataString = ",\n            body: JSON.stringify(input)"
            
                if inputVars != "":
                    inputVars += ", cookieToken?: string"
                else:
                    inputVars = "cookieToken?: string"
                
                inputVars += ", queryParams?: QueryParams"
                
                ts_function = f"""
    static async {func_name}({inputVars}): Promise<{output_type or "any"}> {{
        let token = cookieToken ?? '';

        if (token == '' && typeof window !== 'undefined') {{
            token = getCookie('token') || '';  // Still fall back to localStorage for now if needed
        }}

        let queryString = '';
        if (queryParams) {{
            queryString = '?' + Object.keys(queryParams)
                .filter(key => queryParams[key] !== undefined)
                .map(key => 
                    encodeURIComponent(key) + '=' + encodeURIComponent(String(queryParams[key]))
                )
                .join('&');
        }}
        
        console.log("Calling {func_name} with token: " + token)
        const response = await fetch(`{url}${{queryString}}`, {{
            method: '{route['methods'][0]}',
            headers: {{
                'Authorization': `Bearer ${{token}}`,
                'Content-Type': 'application/json'
            }}{dataString}
        }});

        const responseData = await response.json();

        if (!response.ok) {{
            const domainError = responseData as DomainError;  // Cast responseData as DomainError
            throw new DomainErrorException(domainError);
        }}

        return responseData;
    }}
"""

                ts_classes[class_name].append(ts_function)

    ts_output = []
    for class_name, functions in ts_classes.items():
        class_definition = f"""
export class {class_name} {{
{"".join(functions)}
}}
"""
        ts_output.append(class_definition)

    
    full_string = f"""// DO NOT EDIT THIS FILE. IT IS AUTOGENERATED.
import {{ {', '.join(filter(lambda x: x not in inputTypeMatch.values(), seen_types))}, DomainError }} from '../objects/objects';
import {{ HOST }} from './config';
import {{ getCookie }} from './cookieHandler';
import DomainErrorException from './domainError';

type QueryParams = {{
    [key: string]: string | number | undefined;
}};

"""
    
    full_string += "".join(ts_output)

    # Write TypeScript classes to file
    with open(ts_path, "w") as f:
        f.write(full_string)


# Example usage:
convert_to_ts("registry.json", "C:\\Users\\mattm\\Desktop\\Code\\generic-frontend\\src\\common\\api.tsx")
