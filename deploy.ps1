$worktree_clean = git diff-index --quiet HEAD --

if ($worktree_clean -ne 0) {
    Write-Host Worktree not clean, commit all changes before deploying
    Exit 1
}

$commit = git rev-parse --short HEAD

Invoke-Expression -Command (aws ecr get-login --no-include-email --region eu-central-1)

docker build -t djangotodo .

docker tag djangotodo:latest 846266591173.dkr.ecr.eu-central-1.amazonaws.com/djangotodo:latest

docker tag djangotodo:latest 846266591173.dkr.ecr.eu-central-1.amazonaws.com/djangotodo:$commit

docker push 846266591173.dkr.ecr.eu-central-1.amazonaws.com/djangotodo:latest
docker push 846266591173.dkr.ecr.eu-central-1.amazonaws.com/djangotodo:$commit