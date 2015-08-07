#!/bin/bash
TARGET_PATH=$1

mv "$(readlink destinationFile)" "$TARGET_PATH"
