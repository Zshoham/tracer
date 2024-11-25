#!/bin/sh

cd ./imgui_test_engine/imgui_test_suite/

make -j$(getconf _NPROCESSORS_ONLN)
./imgui_test_suite -v1 -nopause -nogui -nocapture tests
