"""
litrun Grammar & Structured Output Engine
Converts JSON schemas and standard formats into GGML BNF (GBNF) grammars
to enforce deterministic, hallucination-free outputs on constrained edge devices.
"""

from __future__ import annotations
import json
from typing import Any, Dict, List, Optional, Union


# Canonical Standard JSON Grammar in GBNF
STANDARD_JSON_GBNF = r"""root ::= object
value ::= object | array | string | number | ("true" | "false" | "null") ws

object ::=
  "{" ws (
            string ":" ws value
    ("," ws string ":" ws value)*
  )? "}" ws

array ::=
  "[" ws (
            value
    ("," ws value)*
  )? "]" ws

string ::=
  "\"" (
    [^"\\\x7F\x00-\x1F] |
    "\\" (["\\/bfnrt] | "u" [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F])
  )* "\"" ws

number ::= ("-"? ([0-9] | [1-9] [0-9]*)) ("." [0-9]+)? ([eE] [-+]? [0-9]+)? ws

ws ::= [ \t\n\r]*
"""


def json_schema_to_gbnf(schema: Dict[str, Any]) -> str:
    """
    Translates a subset of JSON Schema into strict GBNF grammar.
    Supports object properties, strings, numbers, integers, booleans, enums, and arrays.
    """
    rules: Dict[str, str] = {}
    rule_counter = 0

    def escape_str(s: str) -> str:
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'

    def parse_node(node: Dict[str, Any], rule_name: Optional[str] = None) -> str:
        nonlocal rule_counter
        if rule_name is None:
            rule_counter += 1
            rule_name = f"rule_{rule_counter}"

        node_type = node.get("type")
        enum_vals = node.get("enum")

        # Enum check
        if enum_vals is not None:
            options = []
            for val in enum_vals:
                if isinstance(val, str):
                    options.append(f'{escape_str(val)} ws')
                elif isinstance(val, bool):
                    options.append(f'"{str(val).lower()}" ws')
                elif isinstance(val, (int, float)):
                    options.append(f'"{val}" ws')
                elif val is None:
                    options.append('"null" ws')
            rule_def = " | ".join(options) if options else '"null" ws'
            rules[rule_name] = rule_def
            return rule_name

        if node_type == "object":
            props = node.get("properties", {})
            required = set(node.get("required", []))
            prop_rules = []

            for p_name, p_schema in props.items():
                p_val_rule = parse_node(p_schema)
                p_str = f'{escape_str(p_name)} ws ":" ws {p_val_rule}'
                if p_name in required:
                    prop_rules.append(p_str)
                else:
                    opt_rule_name = f"opt_{rule_name}_{p_name}"
                    rules[opt_rule_name] = f'({p_str})?'
                    prop_rules.append(opt_rule_name)

            if not prop_rules:
                rules[rule_name] = r'"{" ws "}" ws'
            else:
                body = ' ("," ws '.join(prop_rules)
                if len(prop_rules) > 1:
                    body += ")" * (len(prop_rules) - 1)
                rules[rule_name] = f'"\\{{" ws {body} "}}" ws'
            return rule_name

        elif node_type == "array":
            items = node.get("items", {})
            item_rule = parse_node(items)
            rules[rule_name] = f'"[" ws ({item_rule} ("," ws {item_rule})*)? "]" ws'
            return rule_name

        elif node_type == "string":
            rules[rule_name] = r'"\"" [^"\\\x7F\x00-\x1F]* "\"" ws'
            return rule_name

        elif node_type in ["number", "integer"]:
            if node_type == "integer":
                rules[rule_name] = r'("-"? [0-9]+) ws'
            else:
                rules[rule_name] = r'("-"? [0-9]+ ("." [0-9]+)?) ws'
            return rule_name

        elif node_type == "boolean":
            rules[rule_name] = r'("true" | "false") ws'
            return rule_name

        elif node_type == "null":
            rules[rule_name] = r'"null" ws'
            return rule_name

        # Fallback to any JSON value
        return "val"

    parse_node(schema, "root")

    # Add shared primitives
    out_lines = [f"root ::= {rules.get('root', 'object')}"]
    for r_name, r_def in rules.items():
        if r_name != "root":
            out_lines.append(f"{r_name} ::= {r_def}")

    out_lines.append("ws ::= [ \\t\\n\\r]*")
    return "\n".join(out_lines) + "\n"


def resolve_grammar(response_format: Optional[Union[Dict[str, Any], str]] = None) -> Optional[str]:
    """
    Parses OpenAI-compatible response_format or direct GBNF strings into a ready GBNF grammar.
    """
    if not response_format:
        return None

    if isinstance(response_format, str):
        if response_format.strip().lower() in ["json", "json_object"]:
            return STANDARD_JSON_GBNF
        return response_format

    if isinstance(response_format, dict):
        fmt_type = response_format.get("type", "")
        if fmt_type == "json_object":
            return STANDARD_JSON_GBNF
        elif fmt_type == "json_schema":
            schema_data = response_format.get("json_schema", {})
            schema = schema_data.get("schema", schema_data)
            if isinstance(schema, dict):
                return json_schema_to_gbnf(schema)

    return None
