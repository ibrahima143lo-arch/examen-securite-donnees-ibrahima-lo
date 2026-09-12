FROM jenkins/jenkins:lts-jdk17

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        curl \
        ca-certificates \
        gnupg \
    && rm -rf /var/lib/apt/lists/*

# Docker CLI only (the Debian docker.io package no longer ships /usr/bin/docker on this base
# image — we talk to the host's Docker Desktop engine via the mounted socket, so we only need
# the client binary, not a nested daemon).
ARG DOCKER_CLI_VERSION=29.8.0
RUN curl -fsSL "https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKER_CLI_VERSION}.tgz" -o /tmp/docker-cli.tgz \
    && tar -xzf /tmp/docker-cli.tgz -C /usr/local/bin --strip-components=1 docker/docker \
    && rm /tmp/docker-cli.tgz

# SAST
RUN pip3 install --break-system-packages --no-cache-dir semgrep

# Secret detection
ARG GITLEAKS_VERSION=8.21.2
RUN curl -fsSL "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz" -o /tmp/gitleaks.tar.gz \
    && tar -xzf /tmp/gitleaks.tar.gz -C /usr/local/bin gitleaks \
    && rm /tmp/gitleaks.tar.gz

# SCA
ARG TRIVY_VERSION=0.74.0
RUN curl -fsSL "https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}/trivy_${TRIVY_VERSION}_Linux-64bit.tar.gz" -o /tmp/trivy.tar.gz \
    && tar -xzf /tmp/trivy.tar.gz -C /usr/local/bin trivy \
    && rm /tmp/trivy.tar.gz

# Let jenkins user talk to the mounted host docker socket. On Docker Desktop the socket is
# owned by root:root (not a "docker" group), so the jenkins user needs to join gid 0 to get
# the group-rw bit rather than us inventing a same-named group with a mismatched gid.
RUN usermod -aG root jenkins

USER jenkins

RUN jenkins-plugin-cli --plugins \
        "workflow-aggregator" \
        "git" \
        "docker-workflow" \
        "htmlpublisher" \
        "junit"
