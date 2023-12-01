
#! /usr/bin/bash

ENV_SIM="env_sim"
ENV_YML="ENV_SIM.yml"

LOCAL_PATH=$(pwd)

echo -e "Refresh ${ENV_SIM}\n"

cd "${HOME}/sim/sal_jads/"

# make sure that the environment is not activate
mamba deactivate

# remove the environment
mamba remove -n ${ENV_SIM} --all

# create the environment
mamba env create -f ${ENV_YML}

cd ${LOCAL_PATH}