#!/usr/bin/env bash
# Plugin file for Murano services
# -------------------------------

# Dependencies:
# ``functions`` file
# ``DEST``, ``DATA_DIR``, ``STACK_USER`` must be defined

# Save trace setting
XTRACE=$(set +o | grep xtrace)
set -o xtrace


# Defaults
# --------

# Set up default repos
MURANO_REPO=${MURANO_REPO:-${GIT_BASE}/openstack/murano.git}
MURANO_BRANCH=${MURANO_BRANCH:-stable/liberty}

# Variables, which used in this function
# https://github.com/openstack-dev/devstack/blob/master/functions-common#L500-L506
GITREPO["python-muranoclient"]=${MURANO_PYTHONCLIENT_REPO:-${GIT_BASE}/openstack/python-muranoclient.git}
GITBRANCH["python-muranoclient"]=${MURANO_PYTHONCLIENT_BRANCH:-stable/liberty}
GITDIR["python-muranoclient"]=$DEST/python-muranoclient

# Set up default directories
MURANO_DIR=$DEST/murano
MURANO_CONF_DIR=${MURANO_CONF_DIR:-/etc/murano}
MURANO_CONF_FILE=${MURANO_CONF_DIR}/murano.conf
MURANO_POLICY_FILE=${MURANO_CONF_DIR}/policy.json
MURANO_DEBUG=${MURANO_DEBUG:-True}
MURANO_ENABLE_MODEL_POLICY_ENFORCEMENT=${MURANO_ENABLE_MODEL_POLICY_ENFORCEMENT:-False}

MURANO_SERVICE_HOST=${MURANO_SERVICE_HOST:-$SERVICE_HOST}
MURANO_SERVICE_PORT=${MURANO_SERVICE_PORT:-8082}
MURANO_SERVICE_PROTOCOL=${MURANO_SERVICE_PROTOCOL:-$SERVICE_PROTOCOL}

MURANO_ADMIN_USER=${MURANO_ADMIN_USER:-murano}

MURANO_KEYSTONE_SIGNING_DIR=${MURANO_KEYSTONE_SIGNING_DIR:-/tmp/keystone-signing-muranoapi}

MURANO_DEFAULT_ROUTER=${MURANO_DEFAULT_ROUTER:-''}
MURANO_EXTERNAL_NETWORK=${MURANO_EXTERNAL_NETWORK:-''}

# MURANO_RABBIT_VHOST allows to specify a separate virtual host for Murano services.
# This is not required if all OpenStack services are deployed by devstack scripts
#   on a single node. In this case '/' virtual host (which is the default) is enough.
# The problem arise when Murano installed in 'devbox' mode, allowing two or more
#   devboxes to use one common OpenStack host. In this case it's better devboxes
#   use separated virtual hosts, to avoid conflicts between Murano services.
# This couldn't be done using exitsting variables, so that's why this variable was added.
MURANO_RABBIT_VHOST=${MURANO_RABBIT_VHOST:-''}

# Support entry points installation of console scripts
if [[ -d $MURANO_DIR/bin ]]; then
    MURANO_BIN_DIR=$MURANO_DIR/bin
else
    MURANO_BIN_DIR=$(get_python_exec_prefix)
fi


# create_murano_accounts() - Set up common required murano accounts
#
# Tenant      User       Roles
# ------------------------------
# service     murano     admin
function create_murano_accounts() {
    if ! is_service_enabled key; then
        return
    fi

    create_service_user "murano"

    if [[ "$KEYSTONE_CATALOG_BACKEND" = 'sql' ]]; then
        get_or_create_service "murano" "application_catalog" "Application Catalog Service"
        get_or_create_endpoint "application_catalog" \
            "$REGION_NAME" \
            "$MURANO_SERVICE_PROTOCOL://$MURANO_SERVICE_HOST:$MURANO_SERVICE_PORT" \
            "$MURANO_SERVICE_PROTOCOL://$MURANO_SERVICE_HOST:$MURANO_SERVICE_PORT" \
            "$MURANO_SERVICE_PROTOCOL://$MURANO_SERVICE_HOST:$MURANO_SERVICE_PORT"
    fi
}


function mkdir_chown_stack {
    if [[ ! -d "$1" ]]; then
        sudo mkdir -p "$1"
    fi
    sudo chown $STACK_USER "$1"
}


function configure_murano_rpc_backend() {
    # Configure the rpc service.
    iniset_rpc_backend muranoapi $MURANO_CONF_FILE DEFAULT

    # TODO(ruhe): get rid of this ugly workaround.
    inicomment $MURANO_CONF_FILE DEFAULT rpc_backend

    iniset $MURANO_CONF_FILE rabbitmq host $RABBIT_HOST
    iniset $MURANO_CONF_FILE rabbitmq login $RABBIT_USERID
    iniset $MURANO_CONF_FILE rabbitmq password $RABBIT_PASSWORD

    # Set non-default rabbit virtual host if required.
    if [[ -n "$MURANO_RABBIT_VHOST" ]]; then
        iniset $MURANO_CONF_FILE DEFAULT rabbit_virtual_host $MURANO_RABBIT_VHOST
        iniset $MURANO_CONF_FILE rabbitmq virtual_host $MURANO_RABBIT_VHOST
    fi
}

function configure_murano_networking {
    # Use keyword 'public' if Murano external network was not set.
    # If it was set but the network is not exist then
    # first available external network will be selected.
    local ext_net=${MURANO_EXTERNAL_NETWORK:-'public'}
    local ext_net_id=$(neutron net-external-list \
            | grep " $ext_net " | get_field 2)

    # Try to select first available external network
    if [[ -n "$ext_net_id" ]]; then
        ext_net_id=$(neutron net-external-list -f csv -c id \
            | tail -n +2 | tail -n 1)
    fi

    # Configure networking options for Murano
    if [[ -n "$ext_net" ]] && [[ -n "$ext_net_id" ]]; then
        iniset $MURANO_CONF_FILE networking external_network $ext_net_id
        iniset $MURANO_CONF_FILE networking create_router 'true'
    else
        iniset $MURANO_CONF_FILE networking create_router 'false'
    fi

    if [[ -n "$MURANO_DEFAULT_ROUTER" ]]; then
        iniset $MURANO_CONF_FILE networking router_name $MURANO_DEFAULT_ROUTER
    fi
}

# Entry points
# ------------

# configure_murano() - Set config files, create data dirs, etc
function configure_murano {
    mkdir_chown_stack "$MURANO_CONF_DIR"

    # Generate Murano configuration file and configure common parameters.
    oslo-config-generator --namespace keystonemiddleware.auth_token \
                          --namespace murano \
                          --namespace oslo.db \
                          --namespace oslo.messaging \
                          > $MURANO_CONF_FILE
    cp $MURANO_DIR/etc/murano/murano-paste.ini $MURANO_CONF_DIR
    cp $MURANO_DIR/etc/murano/policy.json $MURANO_POLICY_FILE

    cleanup_murano

    iniset $MURANO_CONF_FILE DEFAULT debug $MURANO_DEBUG
    iniset $MURANO_CONF_FILE DEFAULT use_syslog $SYSLOG

    # Murano Policy Enforcement Configuration
    if [[ -n "$MURANO_ENABLE_MODEL_POLICY_ENFORCEMENT" ]]; then
        iniset $MURANO_CONF_FILE engine enable_model_policy_enforcer $MURANO_ENABLE_MODEL_POLICY_ENFORCEMENT
    fi

    # Murano Api Configuration
    #-------------------------

    # Setup keystone_authtoken section
    iniset $MURANO_CONF_FILE keystone_authtoken auth_uri "http://${KEYSTONE_AUTH_HOST}:5000/v2.0"
    iniset $MURANO_CONF_FILE keystone_authtoken auth_host $KEYSTONE_AUTH_HOST
    iniset $MURANO_CONF_FILE keystone_authtoken auth_port $KEYSTONE_AUTH_PORT
    iniset $MURANO_CONF_FILE keystone_authtoken auth_protocol $KEYSTONE_AUTH_PROTOCOL
    iniset $MURANO_CONF_FILE keystone_authtoken cafile $KEYSTONE_SSL_CA
    iniset $MURANO_CONF_FILE keystone_authtoken admin_tenant_name $SERVICE_TENANT_NAME
    iniset $MURANO_CONF_FILE keystone_authtoken admin_user $MURANO_ADMIN_USER
    iniset $MURANO_CONF_FILE keystone_authtoken admin_password $SERVICE_PASSWORD

    configure_murano_rpc_backend

    # Configure notifications for status information during provisioning
    iniset $MURANO_CONF_FILE DEFAULT notification_driver messagingv2

    # configure the database.
    iniset $MURANO_CONF_FILE database connection `database_connection_url murano`

    # Configure keystone auth url
    iniset $MURANO_CONF_FILE keystone auth_url "http://${KEYSTONE_AUTH_HOST}:5000/v2.0"

    # Configure Murano API URL
    iniset $MURANO_CONF_FILE murano url "http://127.0.0.1:8082"
}


# init_murano() - Initialize databases, etc.
function init_murano() {
    configure_murano_networking

    # (re)create Murano database
    recreate_database murano utf8

    $MURANO_BIN_DIR/murano-db-manage --config-file $MURANO_CONF_FILE upgrade
    $MURANO_BIN_DIR/murano-manage --config-file $MURANO_CONF_FILE import-package $MURANO_DIR/meta/io.murano
}


# install_murano() - Collect source and prepare
function install_murano() {
    install_murano_pythonclient

    git_clone $MURANO_REPO $MURANO_DIR $MURANO_BRANCH

    setup_develop $MURANO_DIR
}


function install_murano_pythonclient() {
# For using non-released client from git branch, need to add
# LIBS_FROM_GIT=python-muranoclient parameter to localrc.
# Otherwise, murano will install python-muranoclient from requirements.
    if use_library_from_git "python-muranoclient"; then
        git_clone_by_name "python-muranoclient"
        setup_dev_lib "python-muranoclient"
        # Installing bash_completion for murano
        sudo install -D -m 0644 -o $STACK_USER {${GITDIR["python-muranoclient"]}/tools/,/etc/bash_completion.d/}murano.bash_completion
    fi
}


# start_murano() - Start running processes, including screen
function start_murano() {
    screen_it murano-api "cd $MURANO_DIR && $MURANO_BIN_DIR/murano-api --config-file $MURANO_CONF_DIR/murano.conf"
    screen_it murano-engine "cd $MURANO_DIR && $MURANO_BIN_DIR/murano-engine --config-file $MURANO_CONF_DIR/murano.conf"
}


# stop_murano() - Stop running processes
function stop_murano() {
    # Kill the Murano screen windows
    screen -S $SCREEN_NAME -p murano-api -X kill
    screen -S $SCREEN_NAME -p murano-engine -X kill
}

function cleanup_murano() {

    # Cleanup keystone signing dir
    sudo rm -rf $MURANO_KEYSTONE_SIGNING_DIR
}

#### lib/murano-dashboard

# Dependencies:
#
# - ``functions`` file
# - ``DEST``, ``DATA_DIR``, ``STACK_USER`` must be defined
# - ``SERVICE_HOST``

# ``stack.sh`` calls the entry points in this order:
#
# - install_murano_dashboard
# - configure_murano_dashboard
# - cleanup_murano_dashboard

source $TOP_DIR/lib/horizon

# Defaults
# --------

HORIZON_CONFIG=${HORIZON_CONFIG:-$HORIZON_DIR/openstack_dashboard/settings.py}
HORIZON_LOCAL_CONFIG=${HORIZON_LOCAL_CONFIG:-$HORIZON_DIR/openstack_dashboard/local/local_settings.py}

# Set up default repos
MURANO_DASHBOARD_REPO=${MURANO_DASHBOARD_REPO:-${GIT_BASE}/openstack/murano-dashboard.git}
MURANO_DASHBOARD_BRANCH=${MURANO_DASHBOARD_BRANCH:-stable/liberty}

# Set up default directories
MURANO_DASHBOARD_DIR=$DEST/murano-dashboard
MURANO_PYTHONCLIENT_DIR=$DEST/python-muranoclient

MURANO_DASHBOARD_CACHE_DIR=${MURANO_DASHBOARD_CACHE_DIR:-/tmp/murano}

MURANO_REPOSITORY_URL=${MURANO_REPOSITORY_URL:-'http://apps.openstack.org/api/v1/murano_repo/liberty/'}

# Functions
# ---------

function insert_config_block() {
    local target_file="$1"
    local insert_file="$2"
    local pattern="$3"

    if [[ -z "$pattern" ]]; then
        cat "$insert_file" >> "$target_file"
    else
        sed -ne "/$pattern/r  $insert_file" -e 1x  -e '2,${x;p}' -e '${x;p}' -i "$target_file"
    fi
}


function remove_config_block() {
    local config_file="$1"
    local label="$2"

    if [[ -f "$config_file" ]] && [[ -n "$label" ]]; then
        sed -e "/^#${label}_BEGIN/,/^#${label}_END/ d" -i "$config_file"
    fi
}


# Entry points
# ------------

# configure_murano_dashboard() - Set config files, create data dirs, etc
function configure_murano_dashboard() {
    remove_config_block "$HORIZON_CONFIG" "MURANO_CONFIG_SECTION"

    configure_settings_py
    configure_local_settings_py

    restart_apache_server
}


function configure_settings_py() {
    local horizon_config_part=$(mktemp)

    mkdir_chown_stack "$MURANO_DASHBOARD_CACHE_DIR"

    # Write changes for dashboard config to a separate file
    cat << EOF >> "$horizon_config_part"

#MURANO_CONFIG_SECTION_BEGIN
#-------------------------------------------------------------------------------
METADATA_CACHE_DIR = '$MURANO_DASHBOARD_CACHE_DIR'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join('$MURANO_DASHBOARD_DIR', 'openstack-dashboard.sqlite')
    }
}
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
MIDDLEWARE_CLASSES += ('muranodashboard.middleware.ExceptionMiddleware',)
MURANO_REPO_URL = '$MURANO_REPOSITORY_URL'
#-------------------------------------------------------------------------------
#MURANO_CONFIG_SECTION_END

EOF

    # Insert changes into dashboard config before the line matching the pattern
    insert_config_block "$HORIZON_CONFIG" "$horizon_config_part" "from openstack_dashboard import policy"

    # Install Murano as plugin for Horizon
    ln -sf $MURANO_DASHBOARD_DIR/muranodashboard/local/_50_murano.py $HORIZON_DIR/openstack_dashboard/local/enabled/
}


function configure_local_settings_py() {
    if [[ -f "$HORIZON_LOCAL_CONFIG" ]]; then
        sed -e "s/\(^\s*OPENSTACK_HOST\s*=\).*$/\1 '$HOST_IP'/" -i "$HORIZON_LOCAL_CONFIG"
    fi
}


# init_murano_dashboard() - Initialize databases, etc.
function init_murano_dashboard() {
    # clean up from previous (possibly aborted) runs
    # create required data files

    local horizon_manage_py="$HORIZON_DIR/manage.py"

    python "$horizon_manage_py" collectstatic --noinput
    python "$horizon_manage_py" compress --force
    python "$horizon_manage_py" syncdb --noinput

    restart_apache_server
}


# install_murano_dashboard() - Collect source and prepare
function install_murano_dashboard() {
    echo_summary "Install Murano Dashboard"

    git_clone $MURANO_DASHBOARD_REPO $MURANO_DASHBOARD_DIR $MURANO_DASHBOARD_BRANCH

    setup_develop $MURANO_DASHBOARD_DIR
}


# cleanup_murano_dashboard() - Remove residual data files, anything left over from previous
# runs that a clean run would need to clean up
function cleanup_murano_dashboard() {
    echo_summary "Cleanup Murano Dashboard"
    remove_config_block "$HORIZON_CONFIG" "MURANO_CONFIG_SECTION"
    rm $HORIZON_DIR/openstack_dashboard/local/enabled/_50_murano.py
}

# Main dispatcher

if is_service_enabled murano; then
    if [[ "$1" == "source" ]]; then
        # Initial source
        source $TOP_DIR/lib/murano
        if is_service_enabled horizon; then
            source $TOP_DIR/lib/murano-dashboard
        fi
    elif [[ "$1" == "stack" && "$2" == "pre-install" ]]; then
        echo_summary "Configuring Murano pre-requisites"
        if is_service_enabled n-net; then
            disable_service n-net
            enable_service q-svc q-agt q-dhcp q-l3 q-meta q-metering
        fi
        enable_service heat h-api h-api-cfn h-api-cw h-eng
    elif [[ "$1" == "stack" && "$2" == "install" ]]; then
        echo_summary "Installing Murano"
        install_murano
        if is_service_enabled horizon; then
            install_murano_dashboard
        fi
    elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
        echo_summary "Configuring Murano"
        configure_murano
        create_murano_accounts
        if is_service_enabled horizon; then
            configure_murano_dashboard
        fi
    elif [[ "$1" == "stack" && "$2" == "extra" ]]; then
        echo_summary "Initializing Murano"
        init_murano
        if is_service_enabled horizon; then
            init_murano_dashboard
        fi
        start_murano
    fi

    if [[ "$1" == "unstack" ]]; then
        stop_murano
        cleanup_murano
        if is_service_enabled horizon; then
            cleanup_murano_dashboard
        fi
    fi
fi

# Restore xtrace
$XTRACE

