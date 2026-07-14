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
