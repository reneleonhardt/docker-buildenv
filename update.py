#!/usr/bin/env python3

import os
import sys

VERSIONS = [
    {
        "name": "openjdk8",
        "maintainer": "horky@d3s.mff.cuni.cz",
        "package": "java-1.8.0-openjdk-devel",
    },
    {
        "name": "openjdk10",
        "maintainer": "horky@d3s.mff.cuni.cz",
        "tarball": "https://download.java.net/java/GA/jdk10/10.0.2/19aef61b38124481863b1413dce1855f/13/openjdk-10.0.2_linux-x64_bin.tar.gz",
        "basedir": "jdk-10.0.2",
    },
    {
        "name": "openjdk11",
        "maintainer": "horky@d3s.mff.cuni.cz",
        "package": "java-11-openjdk-devel",
    },
]

DOCKERFILE_TEMPLATE_FROM_PACKAGE = '''
FROM fedora:34
MAINTAINER {maintainer_email}
LABEL maintainer="{maintainer_email}"

RUN dnf install -y ca-certificates git \\
    && dnf install -y {package} \\
    && dnf clean all


CMD ["/bin/bash"]

'''

DOCKERFILE_TEMPLATE_FROM_TARBALL = """
FROM fedora:34
MAINTAINER {maintainer_email}
LABEL maintainer="{maintainer_email}"

RUN dnf install -y ca-certificates git \\
    && dnf clean all \\
    && curl "{tarball_url}" -o "/tmp/{tarball_basename}.tar.gz" \\
    && tar -xz -C /opt -f "/tmp/{tarball_basename}.tar.gz" \\
    && rm -f "/tmp/{tarball_basename}.tar.gz" \\
    && printf 'export JAVA_HOME="%s"\\nexport PATH="$JAVA_HOME/bin:$PATH"\\n' "/opt/{tarball_basedir}" >/etc/profile.d/java_from_opt.sh \\
    && ln -sf /etc/pki/java/cacerts /opt/{tarball_basedir}/lib/security/ \\
    && /opt/{tarball_basedir}/bin/java -version


CMD ["/bin/bash"]

"""

def update_version(dockerfile, config):
    if 'package' in config:
        dockerfile.write(DOCKERFILE_TEMPLATE_FROM_PACKAGE.format(
            maintainer_email=config['maintainer'],
            package=config['package'],
        ))
    else:
        dockerfile.write(DOCKERFILE_TEMPLATE_FROM_TARBALL.format(
            maintainer_email=config['maintainer'],
            tarball_basename=config['basedir'],
            tarball_basedir=config['basedir'],
            tarball_url=config['tarball'],
        ))

def main():
    for ver in VERSIONS:
        base_dir = "buildenv-" + ver['name']
        try:
            os.mkdir(base_dir, mode = 0o777)
        except FileExistsError:
            pass
        with open(os.path.join(base_dir, 'Dockerfile'), 'w') as f:
            print("Updating {} ...".format(ver['name']), file=sys.stderr)
            update_version(f, ver)

if __name__ == '__main__':
    main()
