#!/bin/bash

# Install dependencies for Oh My Zsh and plugins
apt update && \
apt install -y curl git zsh && \
apt clean

# Install Oh My Zsh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended

# Clone additional plugins
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-/home/androidusr/.oh-my-zsh/custom}/plugins/zsh-autosuggestions && \
git clone https://github.com/zsh-users/zsh-syntax-highlighting ${ZSH_CUSTOM:-/home/androidusr/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting && \
git clone https://github.com/zdharma-continuum/fast-syntax-highlighting ${ZSH_CUSTOM:-/home/androidusr/.oh-my-zsh/custom}/plugins/fast-syntax-highlighting && \
git clone https://github.com/marlonrichert/zsh-autocomplete ${ZSH_CUSTOM:-/home/androidusr/.oh-my-zsh/custom}/plugins/zsh-autocomplete

# Configure .zshrc with desired plugins
sed -i 's/^plugins=(.*)$/plugins=(git zsh-autosuggestions zsh-syntax-highlighting fast-syntax-highlighting zsh-autocomplete)/' ~/.zshrc && \
echo 'source $ZSH/oh-my-zsh.sh' >> ~/.zshrc 