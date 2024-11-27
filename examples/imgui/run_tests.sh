#!/bin/sh

cd ./imgui_test_engine/imgui_test_suite/

make -j$(getconf _NPROCESSORS_ONLN)
LD_LIBRARY_PATH=$CONDA_PREFIX/lib ./imgui_test_suite -v1 -nopause -nogui -nocapture tests
