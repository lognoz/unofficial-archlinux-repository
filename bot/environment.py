#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import textwrap
import subprocess

from utils.process import output


class Environment(object):
    def prepare_mirror(self):
        self._execute("chmod 777 " + app.mirror)

    def prepare_git(self):
        self._execute(
            "git config user.email 'hawbot@lognoz.org'; "
            "git config user.name 'hawbot';"
        )

    def prepare_ssh(self):
        self._execute(
            "eval $(ssh-agent); " +
            "chmod 600 ./deploy_key; " +
            "ssh-add ./deploy_key; " +
            "mkdir -p ~/.ssh; " +
            "chmod 0700 ~/.ssh; " +
            "ssh-keyscan -t rsa -H %s >> ~/.ssh/known_hosts; "
            % config.ssh.host
        )

    def prepare_pacman(self):
        content = (f"""
        [{config.database}]
        SigLevel = Optional TrustedOnly
        Server = file:///{app.mirror}
        """)

        if os.path.exists(f"{app.mirror}/{config.database}.db"):
            with open("/etc/pacman.conf", "a+") as fp:
                fp.write(textwrap.dedent(content))

        self._execute("sudo pacman -Sy")

    def clean_mirror(self):
        if not os.path.exists(f"{app.mirror}/{config.database}.db"):
            return

        database = output(f"pacman -Sl {config.database}")
        files = self._get_mirror_packages()
        packages = []

        for package in database.split("\n"):
            split = package.split(" ")
            packages.append(split[1] + "-" + split[2] + "-")

        for fp in files:
            if self._in_mirror(packages, fp) is False:
                os.remove(app.mirror + "/" + fp)

    def _in_mirror(self, packages, fp):
        for package in packages:
            if fp.startswith(package):
                return True

        return False

    def _get_mirror_packages(self):
        packages = []
        for root, dirs, files in os.walk(app.mirror):
            for fp in files:
                if not fp.endswith(".tar.xz"):
                    continue

                packages.append(fp)

        return packages

    def _execute(self, commands):
        subprocess.run(
            commands,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )


def register():
    environment = Environment()

    container.register("environment.prepare_git", environment.prepare_git)
    container.register("environment.prepare_mirror", environment.prepare_mirror)
    container.register("environment.prepare_pacman", environment.prepare_pacman)
    container.register("environment.prepare_ssh", environment.prepare_ssh)
    container.register("environment.clean_mirror", environment.clean_mirror)
