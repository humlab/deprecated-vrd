#!/usr/bin/env bash

warn () {
    echo 1>&2 "$(tput setaf 3)[WARNING] $@$(tput sgr 0)"
}

panic () {
    echo 1>&2 "$(tput setaf 1)[ERROR] $@$(tput sgr 0)"
    kill $BASHPID
}

info () {
    echo 1>&2 "$(tput setaf 6)[INFO] $@$(tput sgr 0)"
}

debug () {
    echo "$(tput setaf 2)[DEBUG] $@$(tput sgr 0)"
}
