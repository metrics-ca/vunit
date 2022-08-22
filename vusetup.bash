
source ./bin/activate

export VUNIT_ENV=$(pwd)
cd vunit/vhdl
rm -fr vunit_out/
python3 compile_vunit_lib.py
cd -
export VUNIT_LIB=$VUNIT_ENV/vunit/vhdl/vunit_out/metrics/libraries/sfe/vunit_lib

