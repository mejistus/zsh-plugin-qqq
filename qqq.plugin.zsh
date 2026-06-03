# qqq oh-my-zsh plugin

typeset -g QQQ_PLUGIN_DIR="${${(%):-%x}:A:h}"

function qqq() {
  if ! command -v python3 >/dev/null 2>&1; then
    print -u2 "qqq: python3 is required"
    return 1
  fi

  python3 "$QQQ_PLUGIN_DIR/donut.py" "$@"
}

function qqq-donut() {
  qqq "$@"
}
