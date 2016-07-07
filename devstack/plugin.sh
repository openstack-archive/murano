#!/usr/bin/env bash
# Plugin file for Murano services
# -------------------------------

# Dependencies:
# ``functions`` file
# ``DEST``, ``DATA_DIR``, ``STACK_USER`` must be defined

# Save trace setting
XTRACE=$(set +o | grep xtrace)
set -o xtrace


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

    get_or_create_service "murano" "application-catalog" "Application Catalog Service"
    get_or_create_endpoint "application-catalog" \
        "$REGION_NAME" \
        "$MURANO_SERVICE_PROTOCOL://$MURANO_SERVICE_HOST:$MURANO_SERVICE_PORT" \
        "$MURANO_SERVICE_PROTOCOL://$MURANO_SERVICE_HOST:$MURANO_SERVICE_PORT" \
        "$MURANO_SERVICE_PROTOCOL://$MURANO_SERVICE_HOST:$MURANO_SERVICE_PORT"

    if is_service_enabled murano-cfapi; then
    get_or_create_service "murano-cfapi" "service-broker" "Murano CloudFoundry Service Broker"
    get_or_create_endpoint "service-broker" \
        "$REGION_NAME" \
        "$MURANO_SERVICE_PROTOCOL://$MURANO_SERVICE_HOST:$MURANO_CFAPI_SERVICE_PORT" \
        "$MURANO_SERVICE_PROTOCOL://$MURANO_SERVICE_HOST:$MURANO_CFAPI_SERVICE_PORT" \
        "$MURANO_SERVICE_PROTOCOL://$MURANO_SERVICE_HOST:$MURANO_CFAPI_SERVICE_PORT"
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

function configure_murano_glare_backend() {
    # Configure Murano to use GlARe application storage backend
    iniset $MURANO_CONF_FILE engine packages_service 'glare'
    iniset $MURANO_CONF_FILE glare url $GLANCE_SERVICE_PROTOCOL://$GLANCE_GLARE_HOSTPORT
    iniset $MURANO_CONF_FILE glare endpoint_type $GLARE_ENDPOINT_TYPE
    echo -e $"\nexport MURANO_PACKAGES_SERVICE='glare'" | sudo tee -a $TOP_DIR/openrc
}

function restart_glare_service() {
    # Restart GlARe service to apply Murano artifact plugin
    if is_running glance-glare; then
        echo_summary "Restarting GlARe to apply config changes"
        stop_process g-glare
        run_process g-glare "$GLANCE_BIN_DIR/glance-glare --config-file=$GLANCE_CONF_DIR/glance-glare.conf"
        echo "Waiting for GlARe [g-glare] ($GLANCE_GLARE_HOSTPORT) to start..."
        if ! wait_for_service $SERVICE_TIMEOUT $GLANCE_SERVICE_PROTOCOL://$GLANCE_GLARE_HOSTPORT; then
            die $LINENO " GlARe [g-glare] did not start"
        fi
    else
        echo_summary "GlARe service wasn't started yet. It will start in usual way."
    fi
}

function install_murano_artifact_plugin() {
    # Provide support of Murano artifacts type to GlARe
    setup_package $MURANO_DIR/contrib/glance -e
}

function is_murano_backend_glare() {
    is_service_enabled g-glare && [[ "$MURANO_USE_GLARE" == "True" ]] && return 0
    return 1
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

    if [[ -n "$MURANO_DEFAULT_DNS" ]]; then
        iniset $MURANO_CONF_FILE networking default_dns $MURANO_DEFAULT_DNS
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
    # Format logging
    if [ "$LOG_COLOR" == "True" ] && [ "$SYSLOG" == "False" ]; then
        setup_colorized_logging $MURANO_CONF_FILE DEFAULT
    else
        # Show user_name and project_name instead of user_id and project_id
        iniset $MURANO_CONF_FILE DEFAULT logging_context_format_string "%(asctime)s.%(msecs)03d %(levelname)s %(name)s [%(request_id)s %(user_name)s %(project_name)s] %(instance)s%(message)s"
    fi

    iniset $MURANO_CONF_FILE DEFAULT home_region $REGION_NAME

    # Murano Policy Enforcement Configuration
    if [[ -n "$MURANO_ENABLE_MODEL_POLICY_ENFORCEMENT" ]]; then
        iniset $MURANO_CONF_FILE engine enable_model_policy_enforcer $MURANO_ENABLE_MODEL_POLICY_ENFORCEMENT
    fi

    # Murano Api Configuration
    #-------------------------

    # Setup keystone_authtoken section
    iniset $MURANO_CONF_FILE keystone_authtoken auth_uri "http://${KEYSTONE_AUTH_HOST}:5000"
    iniset $MURANO_CONF_FILE keystone_authtoken auth_host $KEYSTONE_AUTH_HOST
    iniset $MURANO_CONF_FILE keystone_authtoken auth_port $KEYSTONE_AUTH_PORT
    iniset $MURANO_CONF_FILE keystone_authtoken auth_protocol $KEYSTONE_AUTH_PROTOCOL
    iniset $MURANO_CONF_FILE keystone_authtoken cafile $KEYSTONE_SSL_CA
    iniset $MURANO_CONF_FILE keystone_authtoken admin_tenant_name $SERVICE_TENANT_NAME
    iniset $MURANO_CONF_FILE keystone_authtoken admin_user $MURANO_ADMIN_USER
    iniset $MURANO_CONF_FILE keystone_authtoken admin_password $SERVICE_PASSWORD

    configure_murano_rpc_backend

    # Configure notifications for status information during provisioning
    iniset $MURANO_CONF_FILE oslo_messaging_notifications driver messagingv2

    # configure the database.
    iniset $MURANO_CONF_FILE database connection `database_connection_url murano`

    # Configure keystone auth url
    iniset $MURANO_CONF_FILE keystone auth_url "http://${KEYSTONE_AUTH_HOST}:5000"

    # Configure Murano API URL
    iniset $MURANO_CONF_FILE murano url "http://127.0.0.1:8082"

    # Configure the number of engine workers
    if [[ -n "$MURANO_ENGINE_WORKERS" ]]; then
        iniset $MURANO_CONF_FILE engine workers $MURANO_ENGINE_WORKERS
    fi
    if is_murano_backend_glare; then
        configure_murano_glare_backend
    fi
}

# set the murano packages service backend
function set_packages_service_backend() {
    if is_murano_backend_glare; then
        MURANO_PACKAGES_SERVICE='glare'
    else
        MURANO_PACKAGES_SERVICE='murano'
    fi
}

# install_murano_apps() - Install Murano apps from repository murano-apps, if required
function install_murano_apps() {
    if [[ -z $MURANO_APPS ]]; then
        return
    fi

    # clone murano-apps only if app installation is required
    git_clone $MURANO_APPS_REPO $MURANO_APPS_DIR $MURANO_APPS_BRANCH

    set_packages_service_backend

    # install Murano apps defined in the comma-separated list $MURANO_APPS
    for murano_app in ${MURANO_APPS//,/ }; do
        find $MURANO_APPS_DIR -type d -name "package" | while read package; do
            full_name=$(grep "FullName" "$package/manifest.yaml" | awk -F ':' '{print $2}' | tr -d ' ')
            if [[ $full_name = $murano_app ]]; then
                pushd $package
                zip -r app.zip .
                murano --os-username $OS_USERNAME \
                       --os-password $OS_PASSWORD \
                       --os-tenant-name $OS_PROJECT_NAME \
                       --os-auth-url http://$KEYSTONE_AUTH_HOST:5000 \
                       --murano-url http://127.0.0.1:8082 \
                       --murano-packages-service $MURANO_PACKAGES_SERVICE \
                       package-import \
                       --is-public \
                       --exists-action u \
                       app.zip
                popd
            fi
      done
    done
}


# configure_service_broker() - set service broker specific options to config
function configure_service_broker {
    #Add needed options to murano.conf
    iniset $MURANO_CONF_FILE cfapi tenant "$MURANO_CFAPI_DEFAULT_TENANT"
    iniset $MURANO_CONF_FILE cfapi bind_host "$MURANO_SERVICE_HOST"
    iniset $MURANO_CONF_FILE cfapi bind_port "$MURANO_CFAPI_SERVICE_PORT"
    iniset $MURANO_CONF_FILE cfapi auth_url "http://${KEYSTONE_AUTH_HOST}:5000"
}

function prepare_core_library() {
    cd $MURANO_DIR/meta/io.murano && zip -r io.murano.zip .
}

function remove_core_library_zip() {
    rm -f $MURANO_DIR/meta/io.murano/io.murano.zip
}

# init_murano() - Initialize databases, etc.
function init_murano() {
    configure_murano_networking

    # (re)create Murano database
    recreate_database murano utf8

    $MURANO_BIN_DIR/murano-db-manage --config-file $MURANO_CONF_FILE upgrade
}

function setup_core_library() {
    prepare_core_library

    set_packages_service_backend

    murano --os-username admin \
           --os-password $ADMIN_PASSWORD \
           --os-tenant-name admin \
           --os-auth-url http://$KEYSTONE_AUTH_HOST:5000 \
           --os-region-name $REGION_NAME \
           --murano-url http://127.0.0.1:8082 \
           --murano-packages-service $MURANO_PACKAGES_SERVICE \
           package-import $MURANO_DIR/meta/io.murano/io.murano.zip \
           --is-public
    remove_core_library_zip

}
# install_murano() - Collect source and prepare
function install_murano() {
    install_murano_pythonclient

    git_clone $MURANO_REPO $MURANO_DIR $MURANO_BRANCH

    setup_develop $MURANO_DIR

    if is_murano_backend_glare; then
        install_murano_artifact_plugin
    fi
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


# start_service_broker() - start murano CF service broker
function start_service_broker() {
    screen_it murano-cfapi "cd $MURANO_DIR && $MURANO_BIN_DIR/murano-cfapi --config-file $MURANO_CONF_DIR/murano.conf"
}


# stop_service_broker() - stop murano CF service broker
function stop_service_broker() {
    # Kill the Murano screen windows
    screen -S $SCREEN_NAME -p murano-cfapi -X kill
}


function cleanup_murano() {

    # Cleanup keystone signing dir
    sudo rm -rf $MURANO_KEYSTONE_SIGNING_DIR
}

function configure_murano_tempest_plugin() {

    # Check tempest for enabling
    if is_service_enabled tempest; then
        echo_summary "Configuring Murano Tempest plugin"
        # Set murano service availability flag
        iniset $TEMPEST_CONFIG service_available murano "True"
        # Running tempest in isolation will using tempest user.
        if sudo id -u tempest >/dev/null 2>&1; then
            sudo chown -R tempest:stack $MURANO_DIR/murano_tempest_tests
        fi
        if is_service_enabled murano-cfapi; then
            # Enable Service Broker tests if cfapi enabled and set murano-cfapi service availability flag
            iniset $TEMPEST_CONFIG service_available murano_cfapi "True"
            iniset $TEMPEST_CONFIG service_broker run_service_broker_tests "True"
        fi
        if is_service_enabled g-glare; then
            # TODO(freerunner): This is bad way to configure tempest to
            # TODO see glare as enabled. We need to move it out to tempest
            # TODO of glance repo when glare become official OS API.
            iniset $TEMPEST_CONFIG service_available glare "True"
        fi
        if is_murano_backend_glare; then
            iniset $TEMPEST_CONFIG application_catalog glare_backend "True"
        fi
    fi
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
MURANO_DASHBOARD_BRANCH=${MURANO_DASHBOARD_BRANCH:-master}

# Set up default directories
MURANO_DASHBOARD_DIR=$DEST/murano-dashboard
MURANO_PYTHONCLIENT_DIR=$DEST/python-muranoclient

MURANO_DASHBOARD_CACHE_DIR=${MURANO_DASHBOARD_CACHE_DIR:-/tmp/murano}

MURANO_REPOSITORY_URL=${MURANO_REPOSITORY_URL:-'http://apps.openstack.org/api/v1/murano_repo/liberty/'}

# Entry points
# ------------

# configure_murano_dashboard() - Set config files, create data dirs, etc
function configure_murano_dashboard() {
    configure_local_settings_py

    restart_apache_server
}


function configure_local_settings_py() {
    local horizon_config_part=$(mktemp)

    mkdir_chown_stack "$MURANO_DASHBOARD_CACHE_DIR"

    if is_murano_backend_glare; then
    # Make Murano use GlARe only if MURANO_USE_GLARE set to True and GlARe
    # service is enabled
        local murano_use_glare=True
    else
        local murano_use_glare=False
    fi

    if [[ -f "$HORIZON_LOCAL_CONFIG" ]]; then
        sed -e "s/\(^\s*OPENSTACK_HOST\s*=\).*$/\1 '$HOST_IP'/" -i "$HORIZON_LOCAL_CONFIG"
    fi

    # Install Murano as plugin for Horizon
    ln -sf $MURANO_DASHBOARD_DIR/muranodashboard/local/enabled/_50_murano.py $HORIZON_DIR/openstack_dashboard/local/enabled/

    # Install setting to Horizon
    ln -sf $MURANO_DASHBOARD_DIR/muranodashboard/local/local_settings.d/_50_murano.py $HORIZON_DIR/openstack_dashboard/local/local_settings.d/

    # Change Murano dashboard settings
    sed -e "s/\(^\s*MURANO_USE_GLARE\s*=\).*$/\1 $murano_use_glare/" -i $HORIZON_DIR/openstack_dashboard/local/local_settings.d/_50_murano.py
    sed -e "s%\(^\s*MURANO_REPO_URL\s*=\).*$%\1 '$MURANO_REPOSITORY_URL'%" -i $HORIZON_DIR/openstack_dashboard/local/local_settings.d/_50_murano.py
    sed -e "s%\(^\s*'NAME':\).*$%\1 os.path.join('$MURANO_DASHBOARD_DIR', 'openstack-dashboard.sqlite')%" -i $HORIZON_DIR/openstack_dashboard/local/local_settings.d/_50_murano.py
    echo -e $"\nMETADATA_CACHE_DIR = '$MURANO_DASHBOARD_CACHE_DIR'" | sudo tee -a $HORIZON_DIR/openstack_dashboard/local/local_settings.d/_50_murano.py

}

# init_murano_dashboard() - Initialize databases, etc.
function init_murano_dashboard() {
    # clean up from previous (possibly aborted) runs
    # create required data files

    local horizon_manage_py="$HORIZON_DIR/manage.py"

    python "$horizon_manage_py" collectstatic --noinput
    python "$horizon_manage_py" compress --force
    python "$horizon_manage_py" migrate --noinput

    # Compile message for murano-dashboard
    cd $MURANO_DASHBOARD_DIR/muranodashboard
    python "$horizon_manage_py" compilemessages

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

    rm $HORIZON_DIR/openstack_dashboard/local/enabled/_50_murano.py

    rm $HORIZON_DIR/openstack_dashboard/local/local_settings.d/_50_murano.py
}

# Main dispatcher

if is_service_enabled murano; then
    if [[ "$1" == "stack" && "$2" == "install" ]]; then
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
        if is_service_enabled murano-cfapi; then
            configure_service_broker
        fi
    elif [[ "$1" == "stack" && "$2" == "extra" ]]; then
        echo_summary "Initializing Murano"
        init_murano
        if is_service_enabled horizon; then
            init_murano_dashboard
        fi
        start_murano
        if is_murano_backend_glare; then
            restart_glare_service
        fi
        if is_service_enabled murano-cfapi; then
            start_service_broker
        fi
        setup_core_library
        configure_murano_tempest_plugin

        # Give Murano some time to Start
        sleep 3

        # Install Murano apps, if needed
        install_murano_apps
    fi

    if [[ "$1" == "unstack" ]]; then
        stop_murano
        if is_service_enabled murano-cfapi; then
            stop_service_broker
        fi
        cleanup_murano
        if is_service_enabled horizon; then
            cleanup_murano_dashboard
        fi
    fi
fi

# Restore xtrace
$XTRACE
