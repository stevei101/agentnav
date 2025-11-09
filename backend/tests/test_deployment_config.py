"""
Unit Tests for Cloud Run Deployment Configuration (FR#175)

Tests cover:
- Dockerfile best practices validation
- Startup script configuration
- CI/CD modernization
- Deployment configuration patterns
"""

import pytest
import os


class TestDockerfileConfiguration:
    """Test Dockerfile configuration best practices"""

    def test_dockerfile_uses_multistage_build(self):
        """Verify Dockerfile uses multi-stage build pattern"""
        import os

        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dockerfile_path = os.path.join(backend_dir, "Dockerfile")

        with open(dockerfile_path, "r") as f:
            content = f.read()

        # Check for multi-stage build markers
        assert "AS builder" in content or "as builder" in content
        assert "FROM python:3.11-slim AS builder" in content
        assert "FROM python:3.11-slim" in content.split("AS builder")[1]

    def test_dockerfile_uses_nonroot_user(self):
        """Verify Dockerfile creates and uses non-root user (security)"""
        import os

        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dockerfile_path = os.path.join(backend_dir, "Dockerfile")

        with open(dockerfile_path, "r") as f:
            content = f.read()

        # Check for non-root user creation and usage
        assert "useradd" in content or "adduser" in content
        assert "USER appuser" in content or "USER " in content

    def test_dockerfile_sets_pythonunbuffered(self):
        """Verify Dockerfile sets PYTHONUNBUFFERED (Cloud Run best practice)"""
        import os

        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dockerfile_path = os.path.join(backend_dir, "Dockerfile")

        with open(dockerfile_path, "r") as f:
            content = f.read()

        assert "PYTHONUNBUFFERED=1" in content

    def test_dockerfile_optimizes_layer_caching(self):
        """Verify Dockerfile copies dependencies before application code"""
        import os

        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dockerfile_path = os.path.join(backend_dir, "Dockerfile")

        with open(dockerfile_path, "r") as f:
            content = f.read()

        # Check that dependency files are copied before application code
        lines = content.split("\n")
        pyproject_line = None
        copy_all_line = None

        for i, line in enumerate(lines):
            if "COPY pyproject.toml" in line or "COPY requirements.txt" in line:
                pyproject_line = i
            elif "COPY . ." in line and pyproject_line:
                copy_all_line = i
                break

        # Dependency copy should come before full code copy
        if pyproject_line and copy_all_line:
            assert pyproject_line < copy_all_line

    def test_dockerfile_copies_from_builder(self):
        """Verify runtime stage copies dependencies from builder stage"""
        import os

        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dockerfile_path = os.path.join(backend_dir, "Dockerfile")

        with open(dockerfile_path, "r") as f:
            content = f.read()

        # Check for COPY --from=builder pattern
        assert "--from=builder" in content


class TestStartupScript:
    """Test startup script configuration for Cloud Run"""

    def test_startup_script_reads_port_env(self):
        """Verify startup script reads PORT from environment"""
        import os

        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        startup_path = os.path.join(backend_dir, "start.sh")

        with open(startup_path, "r") as f:
            content = f.read()

        # Check for PORT environment variable handling
        assert "PORT=" in content
        assert "${PORT" in content

    def test_startup_script_configures_workers(self):
        """Verify startup script configures Uvicorn workers"""
        import os

        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        startup_path = os.path.join(backend_dir, "start.sh")

        with open(startup_path, "r") as f:
            content = f.read()

        # Check for worker configuration
        assert "--workers" in content or "WORKERS" in content

    def test_startup_script_sets_keepalive(self):
        """Verify startup script sets keepalive timeout for Cloud Run"""
        import os

        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        startup_path = os.path.join(backend_dir, "start.sh")

        with open(startup_path, "r") as f:
            content = f.read()

        # Check for timeout-keep-alive setting (recommended: 65s for Cloud Run)
        assert "--timeout-keep-alive" in content

    def test_startup_script_sets_graceful_shutdown(self):
        """Verify startup script configures graceful shutdown"""
        import os

        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        startup_path = os.path.join(backend_dir, "start.sh")

        with open(startup_path, "r") as f:
            content = f.read()

        # Check for graceful shutdown timeout
        assert "--timeout-graceful-shutdown" in content

    def test_startup_script_uses_optimal_worker_count(self):
        """Verify startup script uses optimal worker count for Cloud Run"""
        import os

        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        startup_path = os.path.join(backend_dir, "start.sh")

        with open(startup_path, "r") as f:
            content = f.read()

        # Check for WEB_CONCURRENCY pattern (Cloud Run best practice)
        assert "WEB_CONCURRENCY" in content or "WORKERS" in content


class TestCIConfigurationModernization:
    """Test CI/CD configuration for modern Cloud Run deployment"""

    def _load_workflow(self):
        import os

        repo_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        ci_path = os.path.join(repo_root, ".github", "workflows", "cloud-run-deploy.yml")
        with open(ci_path, "r") as f:
            return f.read()

    def test_ci_uses_reusable_podman_workflow(self):
        content = self._load_workflow()
        assert (
            "uses: stevei101/podman-cloudrun-deploy-gha/.github/workflows/podman-cloudrun-deploy.yaml@main"
            in content
        ), "Deployment workflow must reference reusable Podman Cloud Run pattern"

    def test_ci_defines_backend_inputs(self):
        content = self._load_workflow()
        assert "service_name: agentnav-backend" in content, "Backend service name missing"
        assert 'container_port: "8080"' in content, "Backend container port must be 8080"
        assert "BACKEND_REGION: europe-west1" in content, "Backend region env must be europe-west1"
        assert "cloud_run_region: ${{ env.BACKEND_REGION }}" in content, "Backend region should reference env variable"

    def test_ci_defines_frontend_inputs(self):
        content = self._load_workflow()
        assert "service_name: agentnav-frontend" in content, "Frontend service name missing"
        assert 'container_port: "80"' in content, "Frontend container port must be 80"
        assert "FRONTEND_REGION: us-central1" in content, "Frontend region env must be us-central1"
        assert "cloud_run_region: ${{ env.FRONTEND_REGION }}" in content, "Frontend region should reference env variable"

    def test_ci_sets_required_environment_variables(self):
        content = self._load_workflow()
        assert "ENVIRONMENT=production" in content, "Backend must set production environment"
        assert "ALLOWED_HOSTS=agentnav.lornu.com\\\\,*.run.app" in content, "Backend must include allowed hosts"
        assert "CORS_ORIGINS=https://agentnav.lornu.com" in content, "Backend must include CORS origins"
        assert 'additional_env_vars: "PORT=80"' in content, "Frontend deployment must set PORT=80"

    def test_ci_references_artifact_registry(self):
        content = self._load_workflow()
        assert "GAR_REPOSITORY: agentnav-containers" in content, "GAR repository env must be defined"
        assert "gar_repository: ${{ env.GAR_REPOSITORY }}" in content, "GAR repository input should reference env variable"
        assert "allow_unauthenticated: true" in content, "Deployments should allow unauthenticated access"
