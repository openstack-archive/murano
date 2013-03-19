#!/bin/bash

image_file=$1

function die {
    echo "$@"
    exit 1
}

[ -z "$image_file" ] && die "VM name MUST be provided!"
[ -f "$image_file" ] || die "File '$image_file' not found."

echo "Starting VM '$image_file' ..."

kvm \
  -m 2048 \
  -drive file="$image_file",if=virtio \
  -redir tcp:3389::3389 -redir tcp:3390::3390 \
  -nographic \
  -usbdevice tablet \
  -vnc :20

