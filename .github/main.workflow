workflow "Build patch" {
  on = "push"
  resolves = ["actions/bin/sh@master"]
}

action "actions/bin/sh@master" {
  uses = "actions/bin/sh@master"
  runs = "./travis_build.sh"
}
