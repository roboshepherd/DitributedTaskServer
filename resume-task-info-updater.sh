#!/bin/bash

dbus-send --session     --dest='uk.ac.newport.ril.TaskServer' --type=signal '/taskserver' 'uk.ac.newport.ril.TaskServer.TaskInfoUpdaterState' string:'run'
