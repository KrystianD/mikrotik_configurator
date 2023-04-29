import os
from textwrap import indent
from typing import Dict, List

from jinja2 import Environment, FileSystemLoader
from netaddr import *

from utils import read_text_file

script_dir = os.path.dirname(os.path.realpath(__file__))

cleanups = []


def escape_for_mikrotik(cnt):
    return cnt \
        .replace('\\', '\\\\') \
        .replace("\t", "\\t") \
        .replace("\r", "\\r") \
        .replace("\n", "\\n") \
        .replace('"', '\\"')


def load_file(path, name):
    _, ext = os.path.splitext(name)
    assert ext == ".txt"
    file_cnt = escape_for_mikrotik(read_text_file(os.path.expanduser(path)).strip())
    esc = escape_for_mikrotik(file_cnt)

    cnt = f"""
:execute script=":put \\"{esc}\\"" file="{name}"
:while ([:len [/file find where name=\"{name}\"]]=0) do={{:delay 100ms}}
"""
    return cnt


def generate_catch_block(body):
    return f""":do {{
{indent(body.strip(), "    ")}
}} on-error={{}}
"""


def register_cleanup(caller):
    body = caller()

    body = generate_catch_block(body)

    cleanups.insert(0, body)
    return ""


def escape_string(caller):
    body = caller().strip()
    return f'"{escape_for_mikrotik(body)}"'


def rollback_delete_chain(name):
    body = generate_catch_block(f"""
/ip firewall filter remove [find chain="{name}"]
/ip firewall filter remove [find jump-target="{name}"]
/ip firewall nat remove [find chain="{name}"]
/ip firewall nat remove [find jump-target="{name}"]
/ip firewall mangle remove [find chain="{name}"]
/ip firewall mangle remove [find jump-target="{name}"]
""")
    cleanups.insert(0, body)
    return ""


def render_file(path: str, include_dirs: List[str], variables: Dict[str, str]):
    global cleanups
    cleanups = []

    env = Environment(
        loader=FileSystemLoader([
            os.path.join("."),
            *include_dirs,
        ]),
    )

    env.line_comment_prefix = '#'

    env.globals['register_cleanup'] = register_cleanup
    env.globals['escape_string'] = escape_string
    env.globals['rollback_delete_chain'] = rollback_delete_chain
    env.globals = {**env.globals, **variables}

    env.filters["ipnet"] = lambda x: str(IPNetwork(x))
    env.filters["network"] = lambda x: str(IPNetwork(x).cidr)
    env.filters["host"] = lambda x: str(IPNetwork(x).ip)
    env.filters["netmask"] = lambda x: str(IPNetwork(x).netmask)
    env.filters["with_host"] = lambda x, host: IPNetwork(x).network + IPAddress(f"0.0.0.{host}")

    content = env.get_template(os.path.basename(path))
    content = content.render(load_file=load_file)

    content = "\n".join(cleanups) + "\n\n" + content
    return content
