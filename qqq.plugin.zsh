# qqq oh-my-zsh plugin

function qqq() {
  local plugin_dir="${0:A:h}"

  if ! command -v python3 >/dev/null 2>&1; then
    print -u2 "qqq: python3 is required"
    return 1
  fi

  python3 "$plugin_dir/donut.py" "$@"
}

function qqq-donut() {
  qqq "$@"
}
