# ProseBench omp container

## Build and pin

Run these commands from the repository root. The build copies the installed omp ELF from the host. It does not copy the host omp profile.

```sh
sha256sum /home/eyeclept/.local/bin/omp
# Expected: 366ffcda80db57b825921b6ff4b0e5e623bc62cf18478f2828cd8a322fc72ff9
podman build --build-context omp-bin=/home/eyeclept/.local/bin \
  -f container/Containerfile -t localhost/prosebench-omp:18.10.3 container
podman image inspect localhost/prosebench-omp:18.10.3 --format '{{.Id}}'
```

Record the resulting image ID in `PROSEBENCH_IMAGE_DIGEST` in `container/pin.env`. The runner uses that digest, not the mutable image tag. Do not put `agent.db`, an application programming interface (API) key, or the host MCP configuration in the build context.

## Claude login

The owner must log in once before running the Claude models. The following command opens the Anthropic OAuth login inside the image and stores credentials in the dedicated host volume.

```sh
mkdir -p "$HOME/.local/share/prosebench/omp-state"
podman run --rm -it --network host \
  --volume "$HOME/.local/share/prosebench/omp-state:/home/bench/.omp/agent" \
  --volume "$PWD/container/agent/models.yml:/home/bench/.omp/agent/models.yml:ro" \
  --volume "$PWD/container/agent/config.yml:/home/bench/.omp/agent/config.yml:ro" \
  --volume "$PWD/container/agent/AGENTS.md:/home/bench/.omp/agent/AGENTS.md:ro" \
  --volume "$PWD/container/agent/RULES.md:/home/bench/.omp/agent/RULES.md:ro" \
  "$(. container/pin.env; printf '%s' "$PROSEBENCH_IMAGE_DIGEST")" login anthropic
```

Do not copy the host `~/.omp/agent/agent.db` into this volume. The login uses an interactive browser flow. Until login succeeds, the smoke table marks Claude models `needs-login`.

## Run and smoke

Set `OPENROUTER_API_KEY` in the shell before running OpenRouter models. The runner passes the variable to Podman at runtime. It never writes the key into the image, config, or results.

```sh
printf 'Reply with the single word: ok\n' > container/.smoke-prompt.md
container/omp-run.sh --model openrouter/qwen/qwen3.8-flash --thinking off \
  --prompt-file container/.smoke-prompt.md
container/smoke.sh
rm container/.smoke-prompt.md
```

Pass any existing prompt file to `--prompt-file`. The runner sends its bytes on omp standard input, not as an `@file` attachment. It mounts the repository read-only. Standard output contains only omp JSONL events. Errors go to standard error. The script preserves the omp exit code.

The runner uses `--no-session --mode json --no-title --no-tools --no-extensions --no-skills --no-rules` and `--system-prompt-template /workspace/bench/prompts/system.md`. `--no-tools` removes built-in coding tools but leaves Firecrawl MCP callable. `OMP_MCP_REQUIRE_READY=1` stops the run if Firecrawl cannot load before the prompt. `retry.enabled: false` prevents omp from retrying a failed endpoint call. The template omits the stock coding-agent prompt and generated skill and rule sections. The smoke script tries `off`, `minimal`, and `low` if an endpoint rejects an effort level. It records model-reported cost and all prompt tokens, including cached tokens.

The `freetoken` model uses the `openai-completions` API, `auth: none`, a 65611-token context window, and `compat.thinkingFormat: qwen-chat-template`. At `off`, omp sends `chat_template_kwargs.enable_thinking=false`. A direct endpoint request returned `reasoning_content: null` and `content: "ok"`. Use this command to repeat that check:

```sh
curl -sS -X POST http://127.0.0.1:11434/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"ornith-1.5-35b-a3b","messages":[{"role":"user","content":"Reply with the single word: ok"}],"chat_template_kwargs":{"enable_thinking":false}}' \
  | jq '{reasoning_content: .choices[0].message.reasoning_content, content: .choices[0].message.content}'
```

OMP returned `mcp__firecrawl_search` in an assistant tool call during the OpenRouter tool smoke. Its tool execution completed with `isError=false`. This shows that MCP tools remain callable with the runner flags.

## Prompt overhead

The six-token Qwen prompt was `Reply with one word: ok`, without a trailing newline (`omp toks`, `qwen3`: 6). With Firecrawl mounted, Qwen 3.8 Flash reported 16388 prompt tokens for both `--system-prompt` and `--system-prompt-template`. Each run reported 4 uncached input tokens and 16384 cached input tokens. Both injected 16382 tokens above the bare prompt. The template is selected because it does not render generated skill or rule sections if those features change. `bench/roster.yml` records `routing.harness_overhead_tokens: 16382`. This includes Firecrawl tool schemas and MCP instructions. Re-measure if the Firecrawl tool list or omp binary changes.

## Firecrawl rotation

Update only the `mcpServers.firecrawl` entry in the host `~/.omp/agent/mcp.json`. Each runner invocation extracts that one entry into a mode-600 temporary file in the dedicated state directory. It mounts the file read-only as the container's MCP configuration and deletes the temporary file on exit. Other host MCP servers never enter the container. The persistent state directory stays on the host and is not part of the image.
