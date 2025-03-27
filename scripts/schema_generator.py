#!/usr/bin/env python
"""
Script to generate OpenAPI schema as a standalone file.
Run this with: python schema_generator.py
"""
import os
import sys
import json
import yaml

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paylink.settings')
import django
django.setup()

from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.renderers import OpenApiYamlRenderer, OpenApiJsonRenderer

if __name__ == '__main__':
    # Generate schema
    generator = SchemaGenerator(title="PayLink API", description="API for PayLink application with VTPass integration")
    schema = generator.get_schema(request=None, public=True)
    
    # Save as JSON
    json_schema = json.dumps(schema, indent=2)
    with open('openapi_schema.json', 'w') as f:
        f.write(json_schema)
    print("OpenAPI schema saved as openapi_schema.json")
    
    # Save as YAML
    yaml_schema = yaml.dump(schema, default_flow_style=False)
    with open('openapi_schema.yaml', 'w') as f:
        f.write(yaml_schema)
    print("OpenAPI schema saved as openapi_schema.yaml")
    
    print("Done!")
