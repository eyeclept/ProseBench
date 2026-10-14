#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf 'Usage: %s --model MODEL --thinking LEVEL --prompt-file PATH --max-time SECONDS\n' "$0" >&2
  exit 2
}

model= thinking= prompt_file= max_time=
while (($#)); do
  case "$1" in
    --model|--thinking|--prompt-file|--max-time)
      (($# >= 2)) || usage
      case "$1" in
        --model) model=$2 ;;
        --thinking) thinking=$2 ;;
        --prompt-file) prompt_file=$2 ;;
        --max-time) max_time=$2 ;;
      esac
      shift 2 ;;
    *) usage ;;
  esac
done
[[ -n "$model" && -n "$thinking" && -n "$prompt_file" && "$max_time" =~ ^[1-9][0-9]*$ ]] || usage
[[ -f "$prompt_file" ]] || { printf 'Prompt file not found: %s\n' "$prompt_file" >&2; exit 2; }
repo=$(realpath "$(dirname "${BASH_SOURCE[0]}")/..")
source "$repo/container/pin.env"
[[ "$PROSEBENCH_OMP_VERSION" == 18.10.3 && "$PROSEBENCH_IMAGE_DIGEST" == sha256:* ]] || {
  printf 'Invalid image pin in container/pin.env\n' >&2; exit 2;
}
[[ -f "$HOME/.omp/agent/mcp.json" ]] || { printf 'Host Firecrawl MCP config missing\n' >&2; exit 2; }
mkdir -p "$HOME/.local/share/prosebench/omp-state"
state=$(realpath "$HOME/.local/share/prosebench/omp-state")
prompt=$(realpath "$prompt_file")
firecrawl=$(mktemp "$state/.firecrawl.XXXXXXXX")
chmod 600 "$firecrawl"
trap 'rm -f -- "$firecrawl"' EXIT
jq -e '{mcpServers: {firecrawl: (.mcpServers.firecrawl // error("Firecrawl entry missing"))}}' "$HOME/.omp/agent/mcp.json" > "$firecrawl"
[[ $(jq -r '.mcpServers.firecrawl.enabled // true' "$firecrawl") == true ]] || {
  printf 'Host Firecrawl entry disabled\n' >&2; exit 2;
}
args=(run --rm --interactive --network host --workdir /workspace
  --env OMP_MCP_REQUIRE_READY=1
  --volume "$repo:/workspace:ro"
  --volume "$state:/home/bench/.omp/agent"
  --volume "$repo/container/agent/models.yml:/home/bench/.omp/agent/models.yml:ro"
  --volume "$repo/container/agent/config.yml:/home/bench/.omp/agent/config.yml:ro"
  --volume "$repo/container/agent/AGENTS.md:/home/bench/.omp/agent/AGENTS.md:ro"
  --volume "$repo/container/agent/RULES.md:/home/bench/.omp/agent/RULES.md:ro"
  --volume "$firecrawl:/home/bench/.omp/agent/mcp.json:ro")
if [[ -n "${OPENROUTER_API_KEY:-}" ]]; then
  args+=(--env OPENROUTER_API_KEY)
fi
# --max-time bounds tool loops and long reasoning (pilot: 155 Firecrawl calls, 1390s on one Rule 3 run). The runner
# sets it per run (default 1200 s; 2400 s for runs that hit 1200 s) and records it as max_time_s.
podman "${args[@]}" "$PROSEBENCH_IMAGE_DIGEST" \
  --model "$model" --thinking "$thinking" \
  --system-prompt-template /workspace/bench/prompts/system.md \
  --no-tools --no-extensions --no-skills --no-rules --no-title \
  --max-time "$max_time" \
  --no-session --mode json -p < "$prompt"
