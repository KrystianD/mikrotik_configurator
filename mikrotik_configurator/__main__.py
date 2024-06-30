import argparse
import glob
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass

import yaml

import generator
from utils import query_yes_no


@dataclass
class FileInfo:
    path: str
    order: int
    suborder: int

    @property
    def is_reset(self):
        return self.order == 0

    @property
    def sort_order(self):
        return self.order * 1000 + self.suborder

    @staticmethod
    def parse(path: str):
        name = os.path.basename(path)
        p = name.split("-", 1)
        assert len(p) == 2

        numbers = name.split("-", 2)[0]
        numbers = [int(x) for x in numbers.split('_')]
        assert 1 <= len(numbers) <= 2

        if len(numbers) == 1:
            order, suborder = numbers[0], 0
        else:
            order, suborder = numbers

        return FileInfo(path, order, suborder)


def build_files_list(args):
    if len(args.files) == 0:
        files = [FileInfo.parse(x) for x in glob.glob("*.rsc") if re.match("^[0-9]", x)]
        files = list(sorted(files, key=lambda x: x.sort_order))
    else:
        files = [FileInfo.parse(x) for x in args.files]

        if files != list(sorted(files, key=lambda x: x.sort_order)):
            print("mixed up order")
            exit(1)

    return files


def generate(args, cfg, files):
    has_flash = cfg.get("has_flash", False)

    def gen(x: FileInfo):
        s = f'\n/log info message="starting {x.path}..."\n'
        s += generator.render_file(x.path, cfg.get("include_dirs", []), cfg.get("variables", {}))
        s += f'\n/log info message="finished {x.path}"\n'
        return s

    script_blocks = [gen(x) for x in files]
    if args.reset:
        script_blocks = [":delay 7s", *script_blocks]

    base_path = "flash/" if has_flash else ""

    if args.reset:
        script_blocks += [f"/export file={base_path}reset-config.rsc"]
    script_blocks += ["/log info message=\"CONFIGURATION DONE\""]

    script = "\n".join(script_blocks)

    while "\n\n\n" in script:
        script = script.replace("\n\n\n", "\n\n")

    return script


def get_ssh_host_port(args, cfg):
    host = cfg["host"]
    ssh_port = 22

    if args.override_ip is not None:
        host = args.override_ip

        if ":" in host:
            host, ssh_port_str = host.split(":", 1)
            ssh_port = int(ssh_port_str)

    return host, ssh_port


def run_ssh(args, cmd):
    dry_run = args.dry_run

    if args.ssh_pass:
        cmd = ["sshpass", "-p", args.ssh_pass] + cmd

    print(" ".join(cmd))

    if dry_run:
        return "<dryrun>"
    else:
        p = subprocess.run(cmd, stdout=subprocess.PIPE)
        out = p.stdout.decode("utf-8")
        return out


def upload_script(args, cfg, script, script_path):
    host, ssh_port = get_ssh_host_port(args, cfg)

    with tempfile.NamedTemporaryFile(mode="wt") as f:
        f.write(script)
        f.flush()

        cargs = [
            "scp",
            "-P", str(ssh_port),
            "-o", "StrictHostKeyChecking=false",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "PubkeyAcceptedKeyTypes=+ssh-rsa",
            "-o", "LogLevel=ERROR",
            f.name,
            f"admin@{host}:{script_path}"
        ]
        run_ssh(args, cargs)


def run_cmd(args, cfg, cmd):
    host, ssh_port = get_ssh_host_port(args, cfg)

    cargs = [
        "ssh",
        "-p", str(ssh_port),
        "-o", "StrictHostKeyChecking=false",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "PubkeyAcceptedKeyTypes=+ssh-rsa",
        "-o", "LogLevel=ERROR",
        f"admin@{host}",
        cmd,
    ]
    out = run_ssh(args, cargs)

    if "Script file loaded and executed successfully" not in out:
        print("Script error", out)
        exit(1)


def cmd_apply(args, cfg):
    dry_run = args.dry_run

    has_flash = cfg.get("has_flash", False)
    base_path = "flash/" if has_flash else ""

    script_name = "output.rsc"

    files = build_files_list(args)

    if args.reset and not files[0].is_reset:
        print("reset must start with 0_0")
        exit(1)

    if not args.reset and files[0].is_reset:
        print("not reset can't start with 0_0")
        exit(1)

    script = generate(args, cfg, files)

    if not dry_run and args.reset:
        if not query_yes_no("Are you sure you want to reset configuration?", "no"):
            exit(1)

    for index, line in enumerate(script.splitlines(), start=1):
        print('{:4d}: {}'.format(index, line.rstrip()))

    upload_script(args, cfg, script, f"{base_path}{script_name}")

    if args.reset:
        cmd = f"/system reset-configuration no-defaults=yes skip-backup=yes run-after-reset={base_path}{script_name}"
    else:
        cmd = f"/import file={base_path}{script_name}"

    run_cmd(args, cfg, cmd)


def cmd_generate(args, cfg):
    files = build_files_list(args)

    script = generate(args, cfg, files)

    print(script)


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-c', '--config', default="config.yml", type=str, metavar="PATH")

    subparsers = argparser.add_subparsers(required=True)
    sub_apply = subparsers.add_parser('apply')
    sub_apply.add_argument('-n', '--dry-run', action='store_true')
    sub_apply.add_argument('--reset', action='store_true')
    sub_apply.add_argument('--override-ip', type=str)
    argparser.add_argument('--ssh-pass', type=str)
    sub_apply.add_argument('files', type=str, nargs="*", metavar="NAME")
    sub_apply.set_defaults(func=cmd_apply)

    sub_generate = subparsers.add_parser('generate')
    sub_generate.add_argument('--reset', action='store_true')
    sub_generate.add_argument('files', type=str, nargs="*", metavar="NAME")
    sub_generate.set_defaults(func=cmd_generate)

    args = argparser.parse_args()

    if hasattr(yaml, "SafeLoader"):
        cfg = yaml.load(open(args.config, "rt"), Loader=yaml.SafeLoader)
    else:
        # noinspection PyArgumentList
        cfg = yaml.load(open(args.config, "rt"))

    args.func(args, cfg)


main()
