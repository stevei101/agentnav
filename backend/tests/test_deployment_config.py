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
        dockerfile_path = "/home/runner/work/agentnav/agentnav/backend/Dockerfile"

        with open(dockerfile_path, "r") as f:
            content = f.read()

        # Check for multi-stage build markers
        assert "AS builder" in content or "as builder" in content
        assert "FROM python:3.11-slim AS builder" in content
        assert "FROM python:3.11-slim" in content.split("AS builder")[1]

    def test_dockerfile_uses_nonroot_user(self):
        """Verify Dockerfile creates and uses non-root user (security)"""
        dockerfile_path = "/home/runner/work/agentnav/agentnav/backend/Dockerfile"

        with open(dockerfile_path, "r") as f:
            content = f.read()

        # Check for non-root user creation and usage
        assert "useradd" in content or "adduser" in content
        assert "USER appuser" in content or "USER " in content

    def test_dockerfile_sets_pythonunbuffered(self):
        """Verify Dockerfile sets PYTHONUNBUFFERED (Cloud Run best practice)"""
        dockerfile_path = "/home/runner/work/agentnav/agentnav/backend/Dockerfile"

        with open(dockerfile_path, "r") as f:
            content = f.read()

        assert "PYTHONUNBUFFERED=1" in content

    def test_dockerfile_optimizes_layer_caching(self):
        """Verify Dockerfile copies dependencies before application code"""
        dockerfile_path = "/home/runner/work/agentnav/agentnav/backend/Dockerfile"

        with open(dockerfile_path, "r") as f:
            content = f.read()

        # Check that dependency files are copied before application code
        lines = content.split('\n')
        pyproject_line = None
        copy_all_line = None

        for i, line in enumerate(lines):
            if 'COPY pyproject.toml' in line or 'COPY requirements.txt' in line:
                pyproject_line = i
            elif 'COPY . .' in line and pyproject_line:
                copy_all_line = i
                break

        # Dependency copy should come before full code copy
        if pyproject_line and copy_all_line:
            assert pyproject_line < copy_all_line

    def test_dockerfile_copies_from_builder(self):
        """Verify runtime stage copies dependencies from builder stage"""
        dockerfile_path = "/home/runner/work/agentnav/agentnav/backend/Dockerfile"

        with open(dockerfile_path, "r") as f:
            content = f.read()

        # Check for COPY --from=builder pattern
        assert "--from=builder" in content


class TestStartupScript:
    """Test startup script configuration for Cloud Run"""

    def test_startup_script_reads_port_env(self):
        """Verify startup script reads PORT from environment"""
        startup_path = "/home/runner/work/agentnav/agentnav/backend/start.sh"

        with open(startup_path, "r") as f:
            content = f.read()

        # Check for PORT environment variable handling
        assert "PORT=" in content
        assert "${PORT" in content

    def test_startup_script_configures_workers(self):
        """Verify startup script configures Uvicorn workers"""
        startup_path = "/home/runner/work/agentnav/agentnav/backend/start.sh"

        with open(startup_path, "r") as f:
            content = f.read()

        # Check for worker configuration
        assert "--workers" in content or "WORKERS" in content

    def test_startup_script_sets_keepalive(self):
        """Verify startup script sets keepalive timeout for Cloud Run"""
        startup_path = "/home/runner/work/agentnav/agentnav/backend/start.sh"

        with open(startup_path, "r") as f:
            content = f.read()

        # Check for timeout-keep-alive setting (recommended: 65s for Cloud Run)
        assert "--timeout-keep-alive" in content

    def test_startup_script_sets_graceful_shutdown(self):
        """Verify startup script configures graceful shutdown"""
        startup_path = "/home/runner/work/agentnav/agentnav/backend/start.sh"

        with open(startup_path, "r") as f:
            content = f.read()

        # Check for graceful shutdown timeout
        assert "--timeout-graceful-shutdown" in content

    def test_startup_script_uses_optimal_worker_count(self):
        """Verify startup script uses optimal worker count for Cloud Run"""
        startup_path = "/home/runner/work/agentnav/agentnav/backend/start.sh"

        with open(startup_path, "r") as f:
            content = f.read()

        # Check for WEB_CONCURRENCY pattern (Cloud Run best practice)
        assert "WEB_CONCURRENCY" in content or "WORKERS" in content


class TestCIConfigurationModernization:
    """Test CI/CD configuration for modern Cloud Run deployment"""

    def test_ci_uses_modern_gcloud_syntax(self):
        """Verify CI uses modern gcloud run deploy syntax"""
        ci_path = "/home/runner/work/agentnav/agentnav/.github/workflows/build.yml"

        with open(ci_path, "r") as f:
            content = f.read()

        # Check for modern gcloud deploy with resource specifications
        assert "--memory" in content
        assert "--cpu" in content
        assert "--timeout" in content
        assert "--concurrency" in content

    def test_ci_configures_cloud_run_scaling(self):
        """Verify CI configures min/max instances for Cloud Run"""
        ci_path = "/home/runner/work/agentnav/agentnav/.github/workflows/build.yml"

        with open(ci_path, "r") as f:
            content = f.read()

        # Check for scaling configuration
        assert "--min-instances" in content
        assert "--max-instances" in content

    def test_ci_sets_environment_variables(self):
        """Verify CI sets production environment variables"""
        ci_path = "/home/runner/work/agentnav/agentnav/.github/workflows/build.yml"

        with open(ci_path, "r") as f:
            content = f.read()

        # Check for environment variable configuration
        assert "--set-env-vars" in content or "set-env-vars" in content

    def test_ci_configures_cpu_throttling(self):
        """Verify CI configures CPU throttling for cost optimization"""
        ci_path = "/home/runner/work/agentnav/agentnav/.github/workflows/build.yml"

        with open(ci_path, "r") as f:
            content = f.read()

        # Check for CPU throttling flag
        assert "--cpu-throttling" in content

    def test_ci_sets_explicit_port(self):
        """Verify CI explicitly sets port for Cloud Run"""
        ci_path = "/home/runner/work/agentnav/agentnav/.github/workflows/build.yml"

        with open(ci_path, "r") as f:
            content = f.read()

        # Check for port configuration
        assert "--port" in content


class TestFastAPIConfiguration:
    """Test FastAPI configuration for Cloud Run security"""

    def test_main_has_cors_configuration(self):
        """Verify main.py has CORS configuration"""
        main_path = "/home/runner/work/agentnav/agentnav/backend/main.py"

        with open(main_path, "r") as f:
            content = f.read()

        # Check for CORS middleware
        assert "CORSMiddleware" in content
        assert "CORS_ORIGINS" in content

    def test_main_has_security_headers_middleware(self):
        """Verify main.py has security headers middleware"""
        main_path = "/home/runner/work/agentnav/agentnav/backend/main.py"

        with open(main_path, "r") as f:
            content = f.read()

        # Check for security headers
        assert "Strict-Transport-Security" in content
        assert "X-Frame-Options" in content
        assert "X-Content-Type-Options" in content

    def test_main_has_trusted_host_middleware(self):
        """Verify main.py has TrustedHostMiddleware"""
        main_path = "/home/runner/work/agentnav/agentnav/backend/main.py"

        with open(main_path, "r") as f:
            content = f.read()

        # Check for TrustedHostMiddleware
        assert "TrustedHostMiddleware" in content
        assert "ALLOWED_HOSTS" in content

    def test_main_has_healthz_endpoint(self):
        """Verify main.py has /healthz endpoint (Cloud Run standard)"""
        main_path = "/home/runner/work/agentnav/agentnav/backend/main.py"

        with open(main_path, "r") as f:
            content = f.read()

        # Check for /healthz endpoint
        assert "/healthz" in content
        assert "healthz_check" in content or "healthz" in content

    def test_main_configures_cors_max_age(self):
        """Verify CORS is configured with max_age for preflight caching"""
        main_path = "/home/runner/work/agentnav/agentnav/backend/main.py"

        with open(main_path, "r") as f:
            content = f.read()

        # Check for max_age in CORS configuration
        assert "max_age" in content


class TestDeploymentBestPractices:
    """Test adherence to Cloud Run deployment best practices"""

    def test_dockerfile_minimizes_layers(self):
        """Verify Dockerfile uses efficient layering strategy"""
        dockerfile_path = "/home/runner/work/agentnav/agentnav/backend/Dockerfile"

        with open(dockerfile_path, "r") as f:
            content = f.read()

        # Check for combined RUN commands and efficient layering
        lines = [line for line in content.split('\n') if line.strip().startswith('RUN')]
        
        # Should have limited number of RUN commands (efficient layering)
        assert len(lines) <= 5

    def test_startup_script_uses_exec(self):
        """Verify startup script uses exec for proper signal handling"""
        startup_path = "/home/runner/work/agentnav/agentnav/backend/start.sh"

        with open(startup_path, "r") as f:
            content = f.read()

        # Check for exec command (proper signal handling)
        assert "exec uvicorn" in content

    def test_dockerfile_exposes_port(self):
        """Verify Dockerfile exposes the correct port"""
        dockerfile_path = "/home/runner/work/agentnav/agentnav/backend/Dockerfile"

        with open(dockerfile_path, "r") as f:
            content = f.read()

        # Check for EXPOSE instruction
        assert "EXPOSE 8080" in content or "EXPOSE" in content

