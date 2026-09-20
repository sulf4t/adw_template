# ADW: AI Developer Workflows. Source this file from ~/.zshrc:
#   echo 'source ~/adw/adw.zsh' >> ~/.zshrc
# Every command acts on the repo you are standing in ($PWD).

export ADW_HOME="${ADW_HOME:-${${(%):-%x}:A:h}}"

adw() {
  local cmd="${1:-help}"
  [[ $# -gt 0 ]] && shift
  local run=(uv run --quiet)
  local dir=(--working-dir "$PWD")
  case "$cmd" in
    init)                 "${run[@]}" "$ADW_HOME/adws/adw_init.py" "${dir[@]}" "$@" ;;
    prime)                "${run[@]}" "$ADW_HOME/adws/adw_slash_command.py" /prime "${dir[@]}" "$@" ;;
    prompt)               "${run[@]}" "$ADW_HOME/adws/adw_prompt.py" "${dir[@]}" "$@" ;;
    chore|feature|bug)    "${run[@]}" "$ADW_HOME/adws/adw_plan.py" "$cmd" "${dir[@]}" "$@" ;;
    build)                "${run[@]}" "$ADW_HOME/adws/adw_build.py" "${dir[@]}" "$@" ;;
    test)                 "${run[@]}" "$ADW_HOME/adws/adw_test.py" "${dir[@]}" "$@" ;;
    review)               "${run[@]}" "$ADW_HOME/adws/adw_review.py" "${dir[@]}" "$@" ;;
    ship)                 "${run[@]}" "$ADW_HOME/adws/adw_ship.py" "${dir[@]}" "$@" ;;
    full)                 "${run[@]}" "$ADW_HOME/adws/adw_full.py" "${dir[@]}" "$@" ;;
    afk)                  "${run[@]}" "$ADW_HOME/adws/adw_afk.py" "${dir[@]}" "$@" ;;
    doctor)               "${run[@]}" "$ADW_HOME/adws/adw_doctor.py" "$@" ;;
    help|-h|--help)       _adw_help ;;
    *)                    "${run[@]}" "$ADW_HOME/adws/adw_prompt.py" "${dir[@]}" "$cmd" "$@" ;;
  esac
}

_adw_help() {
  cat <<'HELP'
adw <command> [args] [--model sonnet|opus] [--dry-run]     acts on the current directory

  init                 copy templates into this repo, run /install and /prime      (adwi)
  prime                agent reads the repo and summarizes it                      (adwp)
  "<text>"             one-shot prompt, no template
  chore|feature|bug "<text>"   write a plan, print the spec path
  build <spec>         implement a spec                                            (adwb)
  test [--e2e <file>]  run test.md, fix failures, re-run (max 4)                   (adwt)
  review <spec>        compare the diff to the spec, fix blockers (max 2 passes)
  ship [spec]          branch if needed, commit, push, open the PR
  full "<text>"        classify, plan, build, test, review, ship                  (adwf)
  afk [--once]         poll GitHub issues and run full on each new one
  doctor               check git, uv, claude, gh
HELP
}

alias adwi='adw init'
alias adwp='adw prime'
alias adwb='adw build'
alias adwt='adw test'
alias adwf='adw full'
