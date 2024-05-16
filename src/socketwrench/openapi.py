import inspect
from pathlib import Path

from socketwrench import FileResponse, Response
from socketwrench.tags import gettag


def openapi_schema(routes_dict):
    openapi = {
        "openapi": "3.0.0",
        "info": {
            "title": "API Documentation",
            "version": "1.0"
        },
        "paths": {}
    }


    for route_name, func in routes_dict.items():
        route_info = getattr(func, "openapi", {}) or {}
        docstring = func.__doc__
        if "summary" not in route_info:
            route_info["summary"] = docstring.split('\n')[0] if docstring else "No summary available."
        allowed_methods = getattr(func, "allowed_methods", ["GET"]) or ["GET"]
        autofill = getattr(func, "autofill", {}) or {}
        if "parameters" not in route_info:
            parameters = []
            sig = getattr(func, "sig", inspect.signature(func)) or inspect.signature(func)
            for name, param in sig.parameters.items():
                if name in autofill:
                    continue
                param_info = {
                    "name": name,
                    "in": "path" if f"{{{name}}}" in route_name else "query",
                    "required": param.default == param.empty or f"{{{name}}}" in route_name,
                    "schema": {"type": "string"}
                }
                parameters.append(param_info)

            route_info["parameters"] = parameters
        if "responses" not in route_info:
            sig = getattr(func, "sig", inspect.signature(func)) or inspect.signature(func)
            return_type = sig.return_annotation
            if return_type is inspect._empty:
                try:
                    last_line = inspect.getsourcelines(func)[0][-1].strip()
                    if "return" not in last_line:
                        return_type = None
                    else:
                        r = last_line.split("return ", 1)[1].strip()
                        if r in ["True", "False"]:
                            return_type = bool
                        elif r.isdigit() or (r[0] == '-1' and r[1:].isdigit()):
                            return_type = int
                        elif r.replace('.', '', 1).isdigit() or (r[0] == '-' and r[1:].replace('.', '', 1).isdigit()):
                            return_type = float
                        elif (r.startswith('"') and r.endswith('"')) \
                            or (r.startswith("'") and r.endswith("'")) \
                            or (r.startswith('"""') and r.endswith('"""')) \
                            or (r.startswith("f'") and r.endswith("'")) \
                            or (r.startswith('f"') and r.endswith('"')):
                            return_type = str
                        elif r.startswith('b"') and r.endswith('"') or r.startswith("b'") and r.endswith("'"):
                            return_type = bytes
                        elif r.startswith("[") and r.endswith("]"):
                            return_type = list
                        elif r.startswith("{") and r.endswith("}"):
                            return_type = dict
                        elif r.startswith("(") and r.endswith(")"):
                            return_type = tuple
                        elif r.startswith("Path(") and r.endswith(")"):
                            return_type = Path
                        elif "Response(" in r and r.endswith(")"):
                            class_name = r.split("(")[0]
                            # try to import the class from .types
                            try:
                                module = __import__("socketwrench.types", fromlist=[class_name])
                                return_type = getattr(module, class_name)
                            except:
                                return_type = Response
                except:
                    pass
            if return_type is not inspect._empty:
                if return_type is None:
                    route_info["responses"] = {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        }
                    }
                elif return_type is Path or issubclass(return_type, Path) or return_type is FileResponse or issubclass(return_type, FileResponse):
                    content_type = getattr(return_type, "default_content_type", "application/octet-stream")
                    route_info["responses"] = {
                        "200": {
                            "description": "File response",
                            "content": {
                                content_type: {
                                    "schema": {"type": "string", "format": "binary"}
                                }
                            }
                        }
                    }
                elif return_type is str or issubclass(return_type, str):
                    route_info["responses"] = {
                        "200": {
                            "description": "Success",
                            "content": {
                                "text/html": {
                                    "schema": {"type": "string"}
                                }
                            }
                        }
                    }
                elif return_type is bytes or issubclass(return_type, bytes) or return_type is memoryview or issubclass(return_type, memoryview) \
                    or return_type is bytearray or issubclass(return_type, bytearray) or return_type is Response or issubclass(return_type, Response):
                    content_type = getattr(return_type, "default_content_type", "application/octet-stream")
                    route_info["responses"] = {
                        "200": {
                            "description": "Success",
                            "content": {
                                content_type: {
                                    "schema": {"type": "string", "format": "binary"}
                                }
                            }
                        }
                    }
                else:
                    route_info["responses"] = {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        }
                    }
            else:
                route_info["responses"] = {
                    "200": {
                        "description": "Success",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    }
                }

        if "tags" not in route_info:
            tags = getattr(func, "tags", []) or []
            if gettag(func, "do_not_serve", False):
                tags.append("private")
            route_info["tags"] = tags

        openapi["paths"][route_name] = {}
        for method in allowed_methods:
            openapi["paths"][route_name][method.lower()] = route_info
    return openapi
