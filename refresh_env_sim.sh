
#! /usr/bin/bash

ENV_SIM="env_sim"
ENV_YML="ENV_SIM.yml"
PWD=$(pwd)

cd $HOME}/sim/sal_jads

echo -e "Script to manage Python environment ${ENV_SIM}\n"

read -n1 -p "create new yml based on current? [N,y]" doit 

case $doit in  
    y|Y)
      echo -e " Exporting ${ENV_SIM} to ${ENV_YML}\n"
      mamba env export -n ${ENV_SIM} > ${ENV_YML}
      echo -e " -> New ${ENV_YML} created\n";;
    n|N) 
      echo -e " -> NO new ${ENV_YML} created\n";;
    *) 
      echo -e " -> did nothing";; 
esac

read -n1 -p "refresh ${ENV_SIM} based upon current ${ENV_YML}? [Y,n]" doit 

case $doit in  
    y|Y)
      # make sure that the environment is not activate
      mamba deactivate

      # remove the environment
      mamba remove -n ${ENV_SIM} --all

      # show environments list to check that it is removed
      mamba env list

      # create the environment
      mamba env create -f ${ENV_YML}
      echo -e " -> New ${ENV_SIM} created\n";;
    n|N) 
      echo -e " -> ${ENV_SIM} still the same\n";;
    *) 
      echo -e " -> did nothing";; 
esac

mamba activate ${ENV_SIM}

mamba list  

mamba env list

cd ${PWD}
