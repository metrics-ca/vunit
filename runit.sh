#! /bin/bash

#source ./vusetup.bash
echo "PACKARD_HOME: $PACKARD_HOME"
echo "PATH: $PATH"

python3 -m venv myenv
source myenv/bin/activate
git submodule update --init --recursive
python setup.py develop

# Do sim command here
./runall.py --email=${EMAIL}

r=$?
if [ $r -ne 0 ]
then
    echo "Regress command for vunit_tests failed! Return value is '$r'"
    echo "Regress command for vunit_tests failed! Return value is '$r'" > vunit_tests.result
else
    # Do check command here
    ./check_vunit_regress.py
fi

echo "DONE VUNIT"
