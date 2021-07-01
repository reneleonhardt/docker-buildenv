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
        "name": "openjdk8-with-ant-gcc",
        "maintainer": "horky@d3s.mff.cuni.cz",
        "package": "java-1.8.0-openjdk-devel",
        "extra_packages": [
            "gcc",
            "bzip2",
            "which",
            "jq",
        ],
        "commands": [
            "curl https://downloads.apache.org/ant/binaries/apache-ant-1.10.10-bin.tar.bz2 -o /tmp/apache-ant-1.10.10-bin.tar.bz2",
            "tar -xjf /tmp/apache-ant-1.10.10-bin.tar.bz2 -C /opt",
            "rm -f /tmp/apache-ant-1.10.10-bin.tar.bz2",
            "ln -s /opt/apache-ant-1.10.10/bin/ant /usr/local/bin/ant",
        ],
    },
    {
        "name": "openjdk9",
        "maintainer": "horky@d3s.mff.cuni.cz",
        "tarball": "https://download.java.net/java/GA/jdk9/9.0.4/binaries/openjdk-9.0.4_linux-x64_bin.tar.gz",
        "basedir": "jdk-9.0.4",
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
    {
        "name": "openjdk12",
        "maintainer": "horky@d3s.mff.cuni.cz",
        "tarball": "https://download.java.net/java/GA/jdk12.0.2/e482c34c86bd4bf8b56c0b35558996b9/10/GPL/openjdk-12.0.2_linux-x64_bin.tar.gz",
        "basedir": "jdk-12.0.2",
    },
    {
        "name": "openjdk13",
        "maintainer": "horky@d3s.mff.cuni.cz",
        "tarball": "https://download.java.net/java/GA/jdk13.0.2/d4173c853231432d94f001e99d882ca7/8/GPL/openjdk-13.0.2_linux-x64_bin.tar.gz",
        "basedir": "jdk-13.0.2",
    },
    {
        "name": "openjdk14",
        "maintainer": "horky@d3s.mff.cuni.cz",
        "tarball": "https://download.java.net/java/GA/jdk14.0.2/205943a0976c4ed48cb16f1043c5c647/12/GPL/openjdk-14.0.2_linux-x64_bin.tar.gz",
        "basedir": "jdk-14.0.2",
    },
    {
        "name": "openj9-openjdk8",
        "maintainer": "horky@d3s.mff.cuni.cz",
        "tarball": "https://github.com/AdoptOpenJDK/openjdk8-binaries/releases/download/jdk8u292-b10_openj9-0.26.0/OpenJDK8U-jdk_x64_linux_openj9_8u292b10_openj9-0.26.0.tar.gz",
        "basedir": "jdk8u292-b10",
    },
    {
        "name": "openj9-openjdk11",
        "maintainer": "horky@d3s.mff.cuni.cz",
        "tarball": "https://github.com/AdoptOpenJDK/openjdk11-binaries/releases/download/jdk-11.0.11%2B9_openj9-0.26.0/OpenJDK11U-jdk_x64_linux_openj9_11.0.11_9_openj9-0.26.0.tar.gz",
        "basedir": "jdk-11.0.11+9",
    },
    {
        "name": "openj9-openjdk16",
        "maintainer": "horky@d3s.mff.cuni.cz",
        "tarball": "https://github.com/AdoptOpenJDK/openjdk16-binaries/releases/download/jdk-16.0.1%2B9_openj9-0.26.0/OpenJDK16U-jdk_x64_linux_openj9_16.0.1_9_openj9-0.26.0.tar.gz",
        "basedir": "jdk-16.0.1+9",
    },
]

COMMON_PACKAGES = [
    "ca-certificates",
    "git",
    "unzip",
]

DOCKERFILE_TEMPLATE_FROM_PACKAGE = '''
FROM fedora:34
MAINTAINER {maintainer_email}
LABEL maintainer="{maintainer_email}"

RUN dnf install -y {common_packages} \\
    && dnf install -y {package} \\
    && dnf clean all{extra_commands}


CMD ["/bin/bash"]

'''

# Following is not needed as we install Java via alternatives
# printf 'export JAVA_HOME="%s"\\nexport PATH="$JAVA_HOME/bin:$PATH"\\n' "/opt/{tarball_basedir}" >/etc/profile.d/java_from_opt.sh \\

DOCKERFILE_TEMPLATE_FROM_TARBALL = """
FROM fedora:34
MAINTAINER {maintainer_email}
LABEL maintainer="{maintainer_email}"

RUN dnf install -y {common_packages} \\
    && dnf clean all \\
    && curl -L "{tarball_url}" -o "/tmp/{tarball_basename}.tar.gz" \\
    && tar -xz -C /opt -f "/tmp/{tarball_basename}.tar.gz" \\
    && rm -f "/tmp/{tarball_basename}.tar.gz" \\
    && alternatives --install /usr/bin/java java /opt/{tarball_basedir}/bin/java 10 \\
    && for i in /opt/{tarball_basedir}/bin/*; do \\
        ii="$( basename "$i" )"; \\
        [ "$ii" != "java" ] \\
            && alternatives --add-slave java "/opt/{tarball_basedir}/bin/java" "/usr/bin/$ii" "$ii" "/opt/{tarball_basedir}/bin/$ii"; \\
    done \\
    && mkdir -p /opt/{tarball_basedir}/lib/security/ \\
    && ln -sf /etc/pki/java/cacerts /opt/{tarball_basedir}/lib/security/ \\
    && /opt/{tarball_basedir}/bin/java -version{extra_commands}


CMD ["/bin/bash"]

"""

def update_version(dockerfile, config):
    packages_to_install = COMMON_PACKAGES[:]
    packages_to_install.extend(config.get('extra_packages', []))
    common_packages = " ".join(packages_to_install)
    extra_commands = "".join(
        " \\\n    && {}".format(cmd)
        for cmd in config.get('commands', [])
    )
    if 'package' in config:
        dockerfile.write(DOCKERFILE_TEMPLATE_FROM_PACKAGE.format(
            common_packages=common_packages,
            maintainer_email=config['maintainer'],
            package=config['package'],
            extra_commands=extra_commands,
        ))
    else:
        dockerfile.write(DOCKERFILE_TEMPLATE_FROM_TARBALL.format(
            common_packages=common_packages,
            maintainer_email=config['maintainer'],
            tarball_basename=config['basedir'],
            tarball_basedir=config['basedir'],
            tarball_url=config['tarball'],
            extra_commands=extra_commands,
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
