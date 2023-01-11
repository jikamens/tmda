#!/bin/bash

export PATH=/usr/local/src/tmda/bin:/usr/local/bin:/usr/bin:/bin

# Unset the following if you have the logger program available and you want log output to syslog
LOGGER=/usr/bin/logger

check() {
    ## determine which user's TMDA config will apply
    USER=`echo $recip | cut -f1 -d@ | cut -f1 -d-`
    export HOME=`grep $USER /etc/passwd | cut -f6 -d:`

    ## Check to see if user has a ~/.tmda/config
    if [ ! -s $HOME/.tmda/config ] && [ -r $HOME/.tmda/config ] && [ -r $HOME/.tmda/crypt_key ]; then
        [ -n "$LOGGER" ] && $LOGGER -p mail.info -t postfix/tmda "Permitting email received for non-TMDA user $USER"
        echo action=permit
        echo
    fi

    ## Check if sender & recip match anything in the incoming filter
    ## files.

    tmda-filter -M $recip $sender | grep MATCH | grep -q bounce$
    ## If they find something in the filters, dispose of the message.
    if [ $? = 0 ]; then
        [ -n "$LOGGER" ] && $LOGGER -p mail.info -t postfix/tmda "Rejecting email recieved from $sender to $recip"
        echo "action=reject Message rejected by recipient (TMDA)."
        echo
    else
        [ -n "$LOGGER" ] && $LOGGER -p mail.info -t postfix/tmda "Permitting email recieved from $sender to $recip"
        echo action=permit
        echo
    fi
}

## Extract sender & recipient addresses
while IFS='=' read var val; do
    case "x$var" in
        "xrecipient")
            recip="$val";;
        "xsender")
            sender="$val";;
        "x")
            if [ -z $sender ]; then
                echo action=permit
                echo
            else
                check
            fi;;
        *)      ;;
    esac
done
