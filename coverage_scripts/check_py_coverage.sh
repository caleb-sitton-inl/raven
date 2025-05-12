#!/bin/bash
SCRIPT_DIRNAME=`dirname $(readlink -f "$0")`
RAVEN_DIR=`(cd $SCRIPT_DIRNAME/..; pwd)`
cd $RAVEN_DIR

source $RAVEN_DIR/coverage_scripts/initialize_coverage.sh

#coverage help run
FRAMEWORK_DIR=`(cd ravenframework && pwd)`
if [[ "$FRAMEWORK_DIR" == "/c/"* ]] # It's a Windows path
then
  FRAMEWORK_DIR="C:${FRAMEWORK_DIR:2}" # coverage.py is picky about this for --source and --omit
fi

echo $PYTHONPATH

export COVERAGE_RCFILE="$RAVEN_DIR/coverage_scripts/.coveragerc"
EXTRA="--source=$FRAMEWORK_DIR --omit=$FRAMEWORK_DIR/contrib/* --parallel-mode "
export COVERAGE_FILE=`pwd`/.coverage

# coverage erase
# ($RAVEN_DIR/run_tests "$@" --python-command="coverage run $EXTRA ")
# RUN_TESTS_SUCCESS=$?

# get display var
DISPLAY_VAR=`(echo $DISPLAY)`
# reset it
export DISPLAY=

#get DISPLAY BACK
DISPLAY=$DISPLAY_VAR

echo DISPLAY $DISPLAY
echo Xvfb `which Xvfb`
if which Xvfb
then
    Xvfb :8888 &
    xvfbPID=$!
    oldDisplay=$DISPLAY
    export DISPLAY=:8888
    cd $FRAMEWORK_DIR/../tests/framework/PostProcessors/TopologicalPostProcessor
    coverage run $EXTRA $FRAMEWORK_DIR/Driver.py test_topology_ui.xml interactiveCheck || true
    cd $FRAMEWORK_DIR/../tests/framework/PostProcessors/DataMiningPostProcessor/Clustering/
    coverage run $EXTRA $FRAMEWORK_DIR/Driver.py hierarchical_ui.xml interactiveCheck || true
    kill -9 $xvfbPID || true
    export DISPLAY=$oldDisplay
else
    ## Try these tests anyway, we can get some coverage out of them even if the
    ## UI fails or is unavailable.
    cd $FRAMEWORK_DIR/../tests/framework/PostProcessors/TopologicalPostProcessor
    coverage run $EXTRA $FRAMEWORK_DIR/Driver.py test_topology_ui.xml interactiveCheck || true
    cd $FRAMEWORK_DIR/../tests/framework/PostProcessors/DataMiningPostProcessor/Clustering/
    coverage run $EXTRA $FRAMEWORK_DIR/Driver.py hierarchical_ui.xml interactiveCheck || true
fi

# INPUT_FILE=$RAVEN_DIR/tests/framework/PostProcessors/TopologicalPostProcessor/test_topology_ui.xml
# coverage run $EXTRA $RAVEN_DIR/raven_framework.py $INPUT_FILE interactiveCheck
# TOPOLOGY_UI_SUCCESS=$?

# INPUT_FILE=$RAVEN_DIR/tests/framework/PostProcessors/DataMiningPostProcessor/Clustering/hierarchical_ui.xml
# coverage run $EXTRA $RAVEN_DIR/raven_framework.py $INPUT_FILE interactiveCheck
# HIERARCHICAL_UI_SUCCESS=$?

# Prepare data and generate the html documents

coverage combine
coverage html

# if [ $RUN_TESTS_SUCCESS -ne 0 ]
# then
#   echo "run_tests finished but some tests failed"
# fi

# if [ $TOPOLOGY_UI_SUCCESS -ne 0 ]
# then
#   echo "topology_ui test finished but failed"
# fi

# if [ $HIERARCHICAL_UI_SUCCESS -ne 0 ]
# then
#   echo "hierarchical_ui test finished but failed"
# fi

# if [$RUN_TESTS_SUCCESS || $TOPOLOGY_UI_SUCCESS || $HIERARCHICAL_UI_SUCCESS]
# then
#   exit 1
# else
#   exit 0
# fi
