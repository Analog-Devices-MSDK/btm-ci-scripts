set -e
pip3 install --upgrade build 
python3 -m build
rm -rf dist
pip3 install dist/*.whl --force-reinstall
python3 -c "import resource_manager"
set +e