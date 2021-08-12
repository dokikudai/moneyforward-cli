# See here for image contents: https://github.com/microsoft/vscode-dev-containers/tree/v0.187.0/containers/python-3/.devcontainer/base.Dockerfile

# [Choice] Python version: 3, 3.9, 3.8, 3.7, 3.6
ARG VARIANT="3.9"
FROM mcr.microsoft.com/vscode/devcontainers/python:0-${VARIANT}

# [Option] Install Node.js
ARG INSTALL_NODE="true"
ARG NODE_VERSION="lts/*"
RUN if [ "${INSTALL_NODE}" = "true" ]; then su vscode -c "umask 0002 && . /usr/local/share/nvm/nvm.sh && nvm install ${NODE_VERSION} 2>&1"; fi

# [Optional] If your pip requirements rarely change, uncomment this section to add them to the image.
# COPY requirements.txt /tmp/pip-tmp/
# RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
#    && rm -rf /tmp/pip-tmp

# [Optional] Uncomment this section to install additional OS packages.
# RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
#     && apt-get -y install --no-install-recommends <your-package-list-here>

# [Optional] Uncomment this line to install global node packages.
# RUN su vscode -c "source /usr/local/share/nvm/nvm.sh && npm install -g <your-package-here>" 2>&1

# gibo インストールとtabによる保管機能の有効化
RUN curl -L https://raw.github.com/simonwhitaker/gibo/master/gibo -so /usr/local/bin/gibo \
        && chmod +x /usr/local/bin/gibo \
        && gibo update \
        && wget https://raw.githubusercontent.com/simonwhitaker/gibo/master/shell-completions/gibo-completion.bash -P /etc/bash_completion.d/

# bash-completion インストール
RUN apt-get update \
        && apt-get install bash-completion

# llエイリアス設定
RUN sed -i 's/#alias ll=/alias ll=/' /home/vscode/.bashrc
