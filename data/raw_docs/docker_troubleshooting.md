# Docker Troubleshooting

## Diagnosing a Container That Crashes on Startup

When a container exits immediately or repeatedly restarts, the first step is always to check its logs, since the application's own error output almost always reveals the root cause.

```
docker logs <container_name_or_id>
```

If the container has already exited and been removed, add the `-a` flag to see logs from all containers, including stopped ones, or use `docker ps -a` first to find the container's ID even after it has stopped.

## Common Causes of Startup Crashes

**1. Missing or incorrect environment variables.** Many applications fail immediately if a required environment variable (like a database connection string or API key) is missing. The application's startup logs typically show a clear error naming the missing variable.

**2. Port already in use.** If another process on the host is already using the port the container tries to bind to, the container will fail to start. This shows up as an "address already in use" error. Check what's using the port with `docker ps` (to see other running containers) or by inspecting host processes.

**3. Command or entrypoint errors.** If the `CMD` or `ENTRYPOINT` in the Dockerfile references a file, script, or executable that doesn't exist in the final image (for example, a typo in a file path, or a file that wasn't copied in during the build), the container will exit immediately with a "file not found" or "exec format error."


**4. Application dependency failures.** If the application depends on another service (a database, a cache, a message queue) that isn't ready yet or isn't reachable, the app may crash on startup rather than retrying. This is especially common in Docker Compose setups where services start in an unpredictable order unless explicit dependency ordering (`depends_on`) is configured.

**5. Insufficient memory or resource limits.** If a container has a memory limit set that's too low for the application to even initialize, it can be killed by the system immediately after starting, often with no clear application-level error — check `docker inspect` for an "OOMKilled" status in these cases.

## Restart Policies and Crash Loops

By default, a crashed container simply stops. Docker's restart policies control what happens after a crash:

- `--restart no` (default) — the container stays stopped
- `--restart on-failure` — restarts only if the container exits with a non-zero (error) status
- `--restart always` — always restarts, regardless of exit status, even after a host reboot

A container repeatedly crashing and restarting is often called a "crash loop." If a container is stuck in a crash loop, checking `docker logs` immediately after each restart is essential, since the container may not stay up long enough to inspect it interactively.

