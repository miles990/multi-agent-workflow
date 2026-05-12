#!/bin/bash
# Best-effort dependency installer for portable shell tools.

maw_has_command() {
    command -v "$1" >/dev/null 2>&1
}

maw_install_system_package() {
    local package="$1"

    if [ "${MAW_DISABLE_AUTO_INSTALL:-}" = "1" ]; then
        return 1
    fi

    if maw_has_command brew; then
        brew install "$package" >/dev/null 2>&1 && return 0
    fi

    if maw_has_command apt-get; then
        sudo apt-get update >/dev/null 2>&1 || true
        sudo apt-get install -y "$package" >/dev/null 2>&1 && return 0
    fi

    if maw_has_command apk; then
        sudo apk add "$package" >/dev/null 2>&1 && return 0
    fi

    if maw_has_command dnf; then
        sudo dnf install -y "$package" >/dev/null 2>&1 && return 0
    fi

    if maw_has_command yum; then
        sudo yum install -y "$package" >/dev/null 2>&1 && return 0
    fi

    return 1
}

maw_ensure_command() {
    local command_name="$1"
    local package_name="${2:-$1}"

    if maw_has_command "$command_name"; then
        return 0
    fi

    maw_install_system_package "$package_name" && maw_has_command "$command_name"
}

maw_random_hex() {
    local bytes="${1:-4}"

    if maw_ensure_command openssl openssl; then
        openssl rand -hex "$bytes"
        return 0
    fi

    if [ -r /dev/urandom ] && maw_has_command od; then
        od -An -N "$bytes" -tx1 /dev/urandom | tr -d ' \n'
        return 0
    fi

    printf '%s' "$(date +%s)$$"
}
