# murano.sh - DevStack extras script to install Murano

if is_service_enabled murano; then
    if [[ "$1" == "source" ]]; then
        # Initial source
        source $TOP_DIR/lib/murano
    elif [[ "$1" == "stack" && "$2" == "install" ]]; then
        echo_summary "Installing Murano"
        install_murano
    elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
        echo_summary "Configuring Murano"
        configure_murano
        create_murano_accounts
    elif [[ "$1" == "stack" && "$2" == "extra" ]]; then
        echo_summary "Initializing Murano"
        init_murano
        start_murano
    fi

    if [[ "$1" == "unstack" ]]; then
        stop_murano
    fi
fi
