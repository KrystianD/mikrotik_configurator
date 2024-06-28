import argparse
import os
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


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-c', '--config', default="config.yml", type=str, metavar="PATH")
    argparser.add_argument('-n', '--dry-run', action='store_true')
    argparser.add_argument('--reset', action='store_true')
    argparser.add_argument('--override-ip', type=str)
    argparser.add_argument('--ssh-pass', type=str)
    argparser.add_argument('--generate-only', action='store_true')
    argparser.add_argument('files', type=str, nargs="+", metavar="NAME")
    args = argparser.parse_args()

    dry_run = args.dry_run
    if hasattr(yaml, "SafeLoader"):
        cfg = yaml.load(open(args.config, "rt"), Loader=yaml.SafeLoader)
    else:
        # noinspection PyArgumentList
        cfg = yaml.load(open(args.config, "rt"))

    host = cfg["host"]
    has_flash = cfg.get("has_flash", False)

    ssh_port = 22
    if args.override_ip is not None:
        host = args.override_ip

        if ":" in host:
            host, ssh_port_str = host.split(":", 1)
            ssh_port = int(ssh_port_str)

    files = [FileInfo.parse(x) for x in args.files]

    if files != list(sorted(files, key=lambda x: x.sort_order)):
        print("mixed up order")
        exit(1)

    def gen(x):
        s = f'\n/log info message="starting {x}..."\n'
        s += generator.render_file(x, cfg.get("include_dirs", []), cfg.get("variables", {}))
        s += f'\n/log info message="finished {x}"\n'
    def gen(x: FileInfo):
        s = f'\n/log info message="starting {x.path}..."\n'
        s += generator.render_file(x.path, cfg.get("include_dirs", []), cfg.get("variables", {}))
        s += f'\n/log info message="finished {x.path}"\n'
        return s

    script = "\n".join(gen(x) for x in files)
    if args.reset:
        script = ":delay 7s\n" + script

    script += "\n/log info message=\"CONFIGURATION DONE\"\n"

    while "\n\n\n" in script:
        script = script.replace("\n\n\n", "\n\n")

    base_path = "flash/" if has_flash else ""
    script_name = "output.rsc"

    if args.generate_only:
        print(script)
        return

    if args.reset and not files[0].is_reset:
        print("reset must start with 0_0")
        exit(1)

    if not args.reset and files[0].is_reset:
        print("not reset can't start with 0_0")
        exit(1)

    if not dry_run and args.reset:
        if not query_yes_no("Are you sure you want to reset configuration?", "no"):
            exit(1)

    for index, line in enumerate(script.splitlines(), start=1):
        print('{:4d}: {}'.format(index, line.rstrip()))

    with tempfile.NamedTemporaryFile(mode="wt") as f:
        f.write(script)
        f.flush()

        cargs = [
            "scp",
            "-P", str(ssh_port),
            "-o", "StrictHostKeyChecking=false",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "PubkeyAcceptedKeyTypes=+ssh-rsa",
            f.name,
            f"admin@{host}:{base_path}{script_name}"
        ]
        if args.ssh_pass:
            cargs = ["sshpass", "-p", args.ssh_pass] + cargs
        print(" ".join(cargs))
        if not dry_run:
            subprocess.check_call(cargs)

        if args.reset:
            cmd = f"/system reset-configuration no-defaults=yes skip-backup=yes run-after-reset={base_path}{script_name}"
        else:
            cmd = f"/import file={base_path}{script_name}"
        cargs = [
            "ssh",
            "-p", str(ssh_port),
            "-o", "StrictHostKeyChecking=false",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "PubkeyAcceptedKeyTypes=+ssh-rsa",
            f"admin@{host}",
            cmd,
        ]
        if args.ssh_pass:
            cargs = ["sshpass", "-p", args.ssh_pass] + cargs
        print(" ".join(cargs))
        if not dry_run:
            if args.reset:
                subprocess.run(cargs)
            else:
                out = subprocess.check_output(cargs).decode("utf-8")

                if "Script file loaded and executed successfully" not in out:
                    print("Script error")
                    exit(1)


main()
