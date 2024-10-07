set -e
for i in {0..3}; do
    
    trash -rf /home/btm-ci/Workspace/btm-ci-github-runner"$i"/_work/*
    
done

trash -rf /home/btm-ci/Workspace/adi-msdk-github-runner0/_work/*
trash -rf /home/btm-ci/Workspace/adi-msdk-github-runner1/_work/*
trash -rf /home/btm-ci/Workspace/pc-adi-github-runner0/_work/*
