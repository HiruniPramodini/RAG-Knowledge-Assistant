# Docker Fundamentals

## What is Docker?

Docker is a platform for building, shipping, and running applications inside containers. A container packages an application together with all its dependencies — libraries, system tools, code, and runtime — so it runs the same way regardless of where it's deployed. This solves the classic "it works on my machine" problem, because the container includes everything the application needs to run, isolated from the host system's configuration.

## Containers vs Virtual Machines

Virtual machines virtualize an entire operating system, including its own kernel, which makes them heavy (often gigabytes in size) and slow to start (minutes). Containers, by contrast, share the host machine's kernel and only package the application layer, making them lightweight (often megabytes) and fast to start (seconds). Multiple containers can run on a single host OS without the overhead of multiple full operating systems.

## Images vs Containers

A Docker image is a read-only template containing the application code, runtime, libraries, and configuration needed to run a piece of software. A container is a running instance of an image. You can create many containers from the same image, each running independently with its own writable layer on top of the shared read-only image.

## The Dockerfile

A Dockerfile is a text file containing instructions for building a Docker image. Common instructions include:

- `FROM` — specifies the base image to build on top of (e.g. `python:3.11-slim`)
- `WORKDIR` — sets the working directory inside the container for subsequent instructions
- `COPY` — copies files from the host machine into the image
- `RUN` — executes a command during the image build process (e.g. installing dependencies)
- `CMD` — specifies the default command to run when a container starts from the image
- `EXPOSE` — documents which network port the container listens on

A typical Dockerfile for a Python API might look like:

```
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Building and Running Containers

To build an image from a Dockerfile, use `docker build -t image-name .` — the `-t` flag tags the image with a name, and the `.` tells Docker to look for the Dockerfile in the current directory.

To run a container from an image, use `docker run -p 8000:8000 image-name` — the `-p` flag maps a port on the host machine to a port inside the container, allowing external traffic to reach the containerized application.

## Docker Compose

Docker Compose is a tool for defining and running multi-container applications using a single YAML configuration file (`docker-compose.yml`). Instead of manually starting each container with separate `docker run` commands, Compose lets you define all services (for example, an API, a database, and a monitoring dashboard) in one file and start them together with `docker compose up`. This is especially useful for local development environments that mimic a production system made of multiple interconnected services.

## Volumes and Persistent Data

By default, any data written inside a container is lost when the container is removed, because containers are meant to be ephemeral and disposable. Docker volumes solve this by mapping a directory inside the container to a location on the host machine (or a Docker-managed storage area), so data persists across container restarts and removals. This is essential for databases and any application that needs to retain state.

## Why Containers Matter for MLOps

In machine learning systems, containers are used to package a trained model along with its serving code and exact dependency versions (a specific version of scikit-learn or PyTorch, for example). This ensures the model behaves identically whether it's tested on a developer's laptop or deployed to a production cluster, eliminating a common source of subtle bugs where a model works during development but fails or behaves differently in production due to mismatched library versions.
