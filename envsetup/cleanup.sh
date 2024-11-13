safe_delete() {
    local dir_path="$1"

    if [ -d "$dir_path" ]; then
        trash -rf "${dir_path}"/*
    else
        echo "Directory $dir_path does not exist. Skipping deletion."
    fi
}

for i in {0..3}; do
    safe_delete /home/btm-ci/Workspace/btm-ci-github-runner"$i"/_work
done

safe_delete /home/btm-ci/Workspace/adi-msdk-github-runner0/_work
safe_delete /home/btm-ci/Workspace/adi-msdk-github-runner1/_work
safe_delete /home/btm-ci/Workspace/pc-adi-github-runner0/_work
