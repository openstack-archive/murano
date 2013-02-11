#!/bin/bash

function usage {
  echo "Usage: $0 [OPTION]..."
  echo "Run Loadbalancer's test suite(s)"
  echo ""
  echo "  -V, --virtual-env        Always use virtualenv.  Install automatically if not present"
  echo "  -N, --no-virtual-env     Don't use virtualenv.  Run tests in local environment"
  echo "  -f, --force              Force a clean re-build of the virtual environment. Useful when dependencies have been added."
  echo "  --unittests-only         Run unit tests only, exclude functional tests."
  echo "  -c, --coverage           Generate coverage report"
  echo "  -p, --pep8               Just run pep8"
  echo "  -h, --help               Print this usage message"
  echo ""
  echo "Note: with no options specified, the script will try to run the tests in a virtual environment,"
  echo "      If no virtualenv is found, the script will ask if you would like to create one.  If you "
  echo "      prefer to run tests NOT in a virtual environment, simply pass the -N option."
  exit
}

function process_option {
  case "$1" in
    -h|--help) usage;;
    -V|--virtual-env) let always_venv=1; let never_venv=0;;
    -N|--no-virtual-env) let always_venv=0; let never_venv=1;;
    -p|--pep8) let just_pep8=1;;
    -f|--force) let force=1;;
    --unittests-only) noseopts="$noseopts --exclude-dir=windc/tests/functional";;
    -c|--coverage) coverage=1;;
    -*) noseopts="$noseopts $1";;
    *) noseargs="$noseargs $1"
  esac
}

venv=.venv
with_venv=tools/with_venv.sh
always_venv=0
never_venv=0
force=0
noseargs=
noseopts=
wrapper=""
just_pep8=0
coverage=0

for arg in "$@"; do
  process_option $arg
done

# If enabled, tell nose to collect coverage data
if [ $coverage -eq 1 ]; then
   noseopts="$noseopts --with-coverage --cover-package=windc --cover-inclusive"
fi

function run_tests {
  # Just run the test suites in current environment
  ${wrapper} $NOSETESTS 2> run_tests.log
}

function run_pep8 {
  echo "Running pep8 ..."
  PEP8_OPTIONS="--exclude=$PEP8_EXCLUDE --repeat"
  PEP8_INCLUDE="bin/* windc tools setup.py run_tests.py"
  ${wrapper} pep8 $PEP8_OPTIONS $PEP8_INCLUDE
  PEP_RESULT=$?
  case "$TERM" in
      *color* ) function out { printf "\033[3%d;1m%s\033[m\n" "$1" "$2"; } ;;
      * ) function out { printf "%s\n" "$2"; } ;;
  esac
  if [ $PEP_RESULT -eq 0 ]; then
      out 2 "PEP8 OK"
  else
      out 1 "PEP8 FAIL"
  fi
  return $PEP_RESULT
}


NOSETESTS="python run_tests.py $noseopts $noseargs"

if [ $never_venv -eq 0 ]
then
  # Remove the virtual environment if --force used
  if [ $force -eq 1 ]; then
    echo "Cleaning virtualenv..."
    rm -rf ${venv}
  fi
  if [ -e ${venv} ]; then
    wrapper="${with_venv}"
  else
    if [ $always_venv -eq 1 ]; then
      # Automatically install the virtualenv
      python tools/install_venv.py || exit 1
      wrapper="${with_venv}"
    else
      echo -e "No virtual environment found...create one? (Y/n) \c"
      read use_ve
      if [ "x$use_ve" = "xY" -o "x$use_ve" = "x" -o "x$use_ve" = "xy" ]; then
        # Install the virtualenv and run the test suite in it
        python tools/install_venv.py || exit 1
        wrapper=${with_venv}
      fi
    fi
  fi
fi

# Delete old coverage data from previous runs
if [ $coverage -eq 1 ]; then
    ${wrapper} coverage erase
fi

if [ $just_pep8 -eq 1 ]; then
    run_pep8
    exit $?
fi

run_tests
TEST_RESULT=$?

if [ -z "$noseargs" ]; then
    run_pep8 || exit 1
fi

if [ $coverage -eq 1 ]; then
    echo "Generating coverage report in covhtml/"
    ${wrapper} coverage html -d covhtml -i --include='windc/*' --omit='windc/db/migrate_repo*,windc/common*,windc/tests*'
fi

exit $TEST_RESULT
