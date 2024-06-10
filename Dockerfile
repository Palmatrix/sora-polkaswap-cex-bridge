FROM ubuntu:20.04

# Supresses unwanted user interaction during package installation
ENV DEBIAN_FRONTEND=noninteractive
RUN echo "Building Docker image..."

ADD . /pmx-dev
#make sure the script has the right permissions
RUN chmod 755 /pmx-dev/scripts/setup-environment/setup-script-exec-rights.sh
# give our scripts the right permissions
RUN ./pmx-dev/scripts/setup-environment/setup-script-exec-rights.sh

RUN mkdir /ccxt
WORKDIR /ccxt

RUN echo "installing some random stuff..."
# clone https://github.com/Palmatrix-Ltd/ccxt.git to /ccxt
RUN apt-get update && apt-get install -y git

RUN echo "cloning ccxt repo..."
# avoid downloading 1GB of commit history by using --depth 1
RUN git clone --branch master --depth 1 https://github.com/ccxt/ccxt.git /ccxt
RUN echo "creating symlink from mounted data to ccxt folder..."
RUN ln -s /pmx-dev /ccxt

################################################################
# copied from ccxt docker setup:
################################################################

# Update packages (use eu.archive.ubuntu.com instead of archive.ubuntu.com — should speed up apt-get update)
RUN sed -i 's/archive\.ubuntu\.com/eu\.archive\.ubuntu\.com/' /etc/apt/sources.list

# Miscellaneous deps
RUN apt-get update && apt-get install -y --no-install-recommends curl gnupg git ca-certificates
# PHP
RUN apt-get install -y software-properties-common && add-apt-repository -y ppa:ondrej/php
RUN apt-get update && apt-get install -y --no-install-recommends php8.1 php8.1-curl php8.1-iconv php8.1-mbstring php8.1-bcmath php8.1-gmp
# Node
RUN apt-get update
RUN apt-get install -y ca-certificates curl gnupg
RUN mkdir -p /etc/apt/keyrings
RUN curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
ENV NODE_MAJOR=20
RUN echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list
RUN apt-get update && apt-get install -y nodejs
# Python 3
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip
RUN pip3 install 'idna==2.9' --force-reinstall
RUN pip3 install --upgrade setuptools==65.7.0
RUN pip3 install tox
RUN pip3 install aiohttp
RUN pip3 install cryptography
RUN pip3 install requests
# Dotnet
RUN curl -fsSL https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb -o packages-microsoft-prod.deb
RUN dpkg -i packages-microsoft-prod.deb
RUN rm packages-microsoft-prod.deb
RUN apt-get update
RUN apt-get install -y dotnet-sdk-7.0
# Installs as a local Node & Python module, so that `require ('ccxt')` and `import ccxt` should work after that
RUN npm install
RUN ln -s /ccxt /usr/lib/node_modules/
RUN echo "export NODE_PATH=/usr/lib/node_modules" >> $HOME/.bashrc
RUN cd python \
    && pip3 install -e . \
    && cd ..
## Install composer and everything else that it needs and manages
RUN /ccxt/composer-install.sh
RUN apt-get update && apt-get install -y --no-install-recommends zip unzip php-zip
RUN mv /ccxt/composer.phar /usr/local/bin/composer
RUN composer install
## Remove apt sources
RUN apt-get -y autoremove && apt-get clean && apt-get autoclean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

################################################################
# end | copied from ccxt docker setup:
################################################################

# copy and merge our src/ccxt-sora-polkaswap/ts/*.ts sources into /ccxt"
RUN echo "add sora.ts and ccxt implementation specific files..."

ADD ./src/ccxt-sora-polkaswap/ts/abstract/sora.ts /ccxt/ts/src/abstract
# RUN cp /ccxt/pmx-dev/ts/abstract/sora.ts /ccxt/ts/src/abstract
ADD ./src/ccxt-sora-polkaswap/ts/sora.ts /ccxt/ts/src
# RUN cp /ccxt/pmx-dev/ts/sora.ts /ccxt/ts/src/
ADD ./src/ccxt-sora-polkaswap/ts/pro/sora.ts /ccxt/ts/src/pro
# RUN cp /ccxt/pmx-dev/ts/pro/sora.ts /ccxt/ts/src/pro
# TODO run script to merge /pmx-dev/src/ccxt-sora-polkaswap/ccxt.ts into /ccxt/ccxt.ts
# RUN node /pmx-dev/src/ccxt-sora-polkaswap/merge_ccxt.ts
# quick n dirty: just copy the file
ADD ./src/ccxt-sora-polkaswap/ccxt.ts /ccxt/ts
# RUN cp /ccxt/pmx-dev/ccxt.ts /ccxt/ts
# uncomment to run the build in one go
# RUN echo "building ccxt with npm...(might take a while)"
# RUN npm run build
RUN echo "docker setup executed successfully. Olè!"

# [+] Building 268.6s (56/56) FINISHED