FROM node:26.13.1-bookworm AS tooling

RUN test "$(node --version)" = "v${NODE_VERSION}" \
 && npm install --global corepack@0.36.0 \
 && corepack enable \
 && corepack prepare yarn@1.22.22 --activate \
 && test "$(corepack --version)" = 0.36.0 \
 && test "$(yarn --version)" = 1.22.22

RUN yarn global add @fission-ai/openspec@1.14.0 \
 && test "$(openspec --version)" = 1.14.0

FROM tooling AS development

ARG USERNAME=dev

ARG WORKSPACE_DIR
RUN : "${WORKSPACE_DIR:?WORKSPACE_DIR build arg is required}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        build-essential \
        ca-certificates \
        curl \
        fd-find \
        gh \
        git \
        jq \
        less \
        openssh-client \
        pkg-config \
        python3 \
        ripgrep \
        sudo \
        tar \
        unzip \
        util-linux \
        xz-utils \
        zip \
    && rm -rf /var/lib/apt/lists/*

# Rename the node user, which is the image default.
RUN usermod --login ${USERNAME} --move-home --home /home/${USERNAME} node \
    && groupmod --new-name ${USERNAME} node

ENV GH_CONFIG_DIR=/home/${USERNAME}/.config/gh

RUN install -d -o ${USERNAME} -g ${USERNAME} /home/${USERNAME}/.config \
    && install -d -m 0700 -o ${USERNAME} -g ${USERNAME} ${GH_CONFIG_DIR}

# Allow the user to run sudo without a password.
RUN mkdir -p /etc/sudoers.d \
    && echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME} \
    && chmod 0440 /etc/sudoers.d/${USERNAME}

RUN git config --system --add safe.directory ${WORKSPACE_DIR}

RUN CI=1 yarn global add lefthook@2.1.16 \
    && test "$(lefthook version)" = 2.1.16

RUN openspec config set profile custom \
    && openspec config set workflows '["propose","explore","apply","update","sync","archive","verify"]'

RUN yarn global add context-mode@1.0.169

COPY docker/dev/bin/ /usr/local/bin/
COPY docker/dev/.codex/ /usr/local/.codex/
RUN chmod +x \
    /usr/local/bin/codex \
    /usr/local/bin/setup-codex-context-mode \
    /usr/local/bin/setup-git-hooks

USER ${USERNAME}

RUN install -d /home/${USERNAME}/.codex

RUN openspec config set profile custom \
    && openspec config set workflows '["propose","explore","apply","update","sync","archive","verify"]'
