# murano.sh - DevStack extras script to install Murano

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
