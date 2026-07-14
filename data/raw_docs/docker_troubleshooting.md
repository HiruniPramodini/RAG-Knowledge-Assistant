# Docker Troubleshooting

## Diagnosing a Container That Crashes on Startup

When a container exits immediately or repeatedly restarts, the first step is always to check its logs, since the application's own error output almost always reveals the root cause.

```
docker logs <container_name_or_id>
```
