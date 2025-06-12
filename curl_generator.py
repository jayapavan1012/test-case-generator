#!/usr/bin/env python3
"""
CURL Command Generator for Spring Boot Controllers

This script parses a Java Spring Boot controller file and generates
corresponding `curl` commands for each API endpoint it finds.
It creates different scenarios (success, failure) for relevant endpoints.
"""

import argparse
import re
import json
import os

class CurlGenerator:
    """
    Parses a Spring Boot controller file and generates curl commands.
    """
    def __init__(self, controller_file_path):
        self.file_path = controller_file_path
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"The file '{self.file_path}' was not found.")
        self.file_content = self._read_file()
        self.base_path = ""
        self.endpoints = []

    def _read_file(self):
        """Reads the content of the controller file."""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def parse_controller(self):
        """
        Parses the entire controller to extract the base path and all endpoints.
        """
        print(f"🔍 Parsing controller file: {self.file_path}")
        self._extract_base_path()
        self._extract_endpoints()
        print(f"✅ Found {len(self.endpoints)} endpoints.")

    def _extract_base_path(self):
        """Extracts the class-level @RequestMapping value."""
        match = re.search(r'@RequestMapping\("(.+?)"\)', self.file_content)
        if match:
            self.base_path = match.group(1)
            print(f"  -> Found base path: {self.base_path}")

    def _extract_endpoints(self):
        """
        Uses regex to find all methods annotated with HTTP mappings
        and extracts their details.
        """
        # This regex captures the annotation, its content, and the method parameters
        endpoint_pattern = re.compile(
            r'(@(Get|Post|Put|Delete|Patch)Mapping\(([\s\S]*?)\))\s+'
            r'(?:@ResponseBody\s+)?'
            r'(?:public|private|protected)\s+[\s\S]*?\s+\w+\s*'
            r'\(([\s\S]*?)\)'
        )

        for match in endpoint_pattern.finditer(self.file_content):
            http_method = match.group(2).upper()
            annotation_content = match.group(3).strip()
            method_params_str = match.group(4).strip()

            path = self._get_path_from_annotation(annotation_content)
            consumes = self._get_media_type_from_annotation(annotation_content, 'consumes')
            params = self._parse_method_params(method_params_str)
            
            endpoint_info = {
                "http_method": http_method,
                "path": path,
                "consumes": consumes,
                "params": params
            }
            self.endpoints.append(endpoint_info)
            print(f"  -> Found endpoint: {http_method} {self.base_path}{path}")

    def _get_path_from_annotation(self, annotation_content):
        """Extracts the path (value) from an annotation's content."""
        # Try to find value = "..."
        match = re.search(r'value\s*=\s*"(.*?)"', annotation_content)
        if match:
            return match.group(1)
        # Otherwise, try to find the first "..."
        match = re.search(r'"(.*?)"', annotation_content)
        if match:
            return match.group(1)
        return ""

    def _get_media_type_from_annotation(self, annotation_content, param_name):
        """Extracts and simplifies media types like 'consumes' or 'produces'."""
        if f'{param_name}\s*=\s*MediaType.APPLICATION_JSON_VALUE' in annotation_content:
            return 'application/json'
        if f'{param_name}\s*=\s*MediaType.TEXT_PLAIN_VALUE' in annotation_content:
            return 'text/plain'
        return 'application/json' # Default to JSON

    def _parse_method_params(self, params_str):
        """Parses method parameters to find annotations like @RequestBody."""
        params = []
        body_match = re.search(r'@RequestBody\s+([\w\.<>]+)\s+(\w+)', params_str)
        if body_match:
            params.append({
                "annotation": "RequestBody",
                "data_type": body_match.group(1),
                "name": body_match.group(2)
            })
        
        # Regex for @RequestParam
        req_param_matches = re.finditer(r'@RequestParam\(\s*"(.*?)"[\s\S]*?\)\s+([\w\.<>]+)\s+(\w+)', params_str)
        for match in req_param_matches:
            params.append({
                "annotation": "RequestParam",
                "param_name": match.group(1),
                "data_type": match.group(2),
                "name": match.group(3)
            })

        # Regex for @PathVariable
        path_var_matches = re.finditer(r'@PathVariable\(\s*"(.*?)"[\s\S]*?\)\s+([\w\.<>]+)\s+(\w+)', params_str)
        for match in path_var_matches:
            params.append({
                "annotation": "PathVariable",
                "param_name": match.group(1),
                "data_type": match.group(2),
                "name": match.group(3)
            })
        return params

    def _generate_sample_data(self, data_type, is_success_case=True):
        """Generates placeholder data for a request body."""
        scenario = "SUCCESS" if is_success_case else "FAILURE (e.g., missing fields or invalid data)"
        
        if "String" in data_type:
            return f"Sample text payload for {scenario} case."

        # Default to a JSON object for complex types
        if is_success_case:
            return {"TODO": f"Add valid JSON for a {data_type} object.", "exampleKey": "exampleValue"}
        else:
            # For failure, we can send an empty object or one with invalid data
            return {"error_scenario": True}

    def generate_curls(self, base_url="http://localhost:8080"):
        """
        Generates the final list of curl command strings.
        """
        if not self.endpoints:
            return ["# No endpoints found to generate curl commands for."]

        all_commands = [f"# Generated curl commands for {os.path.basename(self.file_path)}\n"]

        for endpoint in self.endpoints:
            # Build the base URL and handle path variables
            final_url = f"{base_url}{self.base_path}{endpoint['path']}"
            path_vars = [p for p in endpoint['params'] if p['annotation'] == 'PathVariable']
            for p_var in path_vars:
                final_url = final_url.replace(f"{{{p_var['param_name']}}}", "SAMPLE_ID")

            # Handle query parameters
            req_params = [p for p in endpoint['params'] if p['annotation'] == 'RequestParam']
            if req_params:
                query_string = "&".join([f"{p['param_name']}=SAMPLE_VALUE" for p in req_params])
                final_url += f"?{query_string}"
            
            command_base = f"curl -v -X {endpoint['http_method']} '{final_url}'"
            command_base += f' -H "Content-Type: {endpoint["consumes"]}"'
            command_base += ' -H "Accept: application/json"'

            body_param = next((p for p in endpoint['params'] if p['annotation'] == 'RequestBody'), None)

            # --- Generate commands for different scenarios ---
            
            all_commands.append(f"# Endpoint: {endpoint['http_method']} {self.base_path}{endpoint['path']}")
            
            if body_param:
                # Success case with data
                data_success = self._generate_sample_data(body_param['data_type'], is_success_case=True)
                cmd_success = command_base + f" --data-raw '{json.dumps(data_success)}'"
                all_commands.append("# ✅ SUCCESS Case: Provide a valid request body.")
                all_commands.append(cmd_success)
                all_commands.append("")

                # Failure case with data
                data_failure = self._generate_sample_data(body_param['data_type'], is_success_case=False)
                cmd_failure = command_base + f" --data-raw '{json.dumps(data_failure)}'"
                all_commands.append("# ❌ FAILURE Case: Provide an invalid or incomplete body.")
                all_commands.append(cmd_failure)
            
            else: # No request body
                all_commands.append("# ✅ SUCCESS Case: No request body needed.")
                all_commands.append(command_base)

            all_commands.append("\n" + ("-"*60) + "\n")
        
        return all_commands

def main():
    """Main function to run the script from the command line."""
    parser = argparse.ArgumentParser(
        description="Generate curl commands from a Spring Boot controller file.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "controller_file", 
        help="The path to the Java controller file."
    )
    parser.add_argument(
        "--url", 
        default="http://localhost:8080", 
        help="The base URL for the running application."
    )
    parser.add_argument(
        "-o", "--output",
        help="Optional: File to save the generated curl commands (e.g., requests.sh)."
    )
    args = parser.parse_args()

    try:
        generator = CurlGenerator(args.controller_file)
        generator.parse_controller()
        curls = generator.generate_curls(base_url=args.url)

        output_content = "\n".join(curls)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write("#!/bin/bash\n\n")
                f.write(output_content)
            print(f"\n✅ Successfully saved curl commands to '{args.output}'")
            # Make the output file executable
            os.chmod(args.output, 0o755)
            print(f"  -> Made '{args.output}' executable.")
        else:
            print("\n--- Generated CURL Commands ---")
            print(output_content)
            print("-----------------------------")

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main() 