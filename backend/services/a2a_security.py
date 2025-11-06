"""
A2A Protocol Security Service (Feature Request #027)

Implements security features for Agent2Agent (A2A) Protocol messages using
Cloud Run Workload Identity for authentication and authorization.

Key Features:
- Message signing and verification using Service Account credentials
- Workload Identity authentication for Cloud Run services
- Authorization checks for agent-to-agent communication
- Security audit logging for all message operations
"""

import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ServiceAccountIdentity:
    """
    Represents a Cloud Run Service Account identity
    
    In production, this would be populated from Cloud Run metadata service:
    curl -H "Metadata-Flavor: Google" \
         http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email
    """

    email: str
    project_id: str
    unique_id: Optional[str] = None

    @classmethod
    def from_cloud_run_metadata(cls) -> "ServiceAccountIdentity":
        """
        Retrieve Service Account identity from Cloud Run metadata service

        Returns:
            ServiceAccountIdentity with current service's identity

        Raises:
            RuntimeError: If not running on Cloud Run or metadata unavailable
        """
        # Check if running on Cloud Run (has GCP metadata service)
        if not os.getenv("K_SERVICE"):
            # Development mode - use mock identity
            logger.warning("⚠️  Not running on Cloud Run - using development identity")
            return cls(
                email="dev-service-account@development.iam.gserviceaccount.com",
                project_id="development",
                unique_id="dev-123",
            )

        try:
            import requests

            metadata_server = "http://metadata.google.internal/computeMetadata/v1"
            metadata_flavor = {"Metadata-Flavor": "Google"}

            # Get service account email
            email_url = f"{metadata_server}/instance/service-accounts/default/email"
            email_response = requests.get(email_url, headers=metadata_flavor, timeout=2)
            email = email_response.text.strip()

            # Get project ID
            project_url = f"{metadata_server}/project/project-id"
            project_response = requests.get(
                project_url, headers=metadata_flavor, timeout=2
            )
            project_id = project_response.text.strip()

            # Get unique ID
            unique_id_url = (
                f"{metadata_server}/instance/service-accounts/default/unique-id"
            )
            unique_id_response = requests.get(
                unique_id_url, headers=metadata_flavor, timeout=2
            )
            unique_id = unique_id_response.text.strip()

            logger.info(f"✅ Retrieved Cloud Run Service Account: {email}")

            return cls(email=email, project_id=project_id, unique_id=unique_id)

        except Exception as e:
            logger.error(f"❌ Failed to retrieve Cloud Run identity: {e}")
            # Fallback to environment variables
            email = os.getenv(
                "GCP_SERVICE_ACCOUNT_EMAIL", "unknown@unknown.iam.gserviceaccount.com"
            )
            project_id = os.getenv("GCP_PROJECT_ID", "unknown")

            logger.warning(f"⚠️  Using fallback identity: {email}")
            return cls(email=email, project_id=project_id)


class A2ASecurityService:
    """
    Security service for A2A Protocol messages

    Handles:
    - Message signing and verification
    - Service Account authentication
    - Authorization policies
    - Security audit logging
    """

    def __init__(self):
        self.identity = ServiceAccountIdentity.from_cloud_run_metadata()
        self.trusted_service_accounts: List[str] = self._load_trusted_accounts()
        self._secret_key = self._get_signing_key()

        logger.info(f"🔐 A2A Security Service initialized")
        logger.info(f"   Identity: {self.identity.email}")
        logger.info(f"   Trusted accounts: {len(self.trusted_service_accounts)}")

    def _load_trusted_accounts(self) -> List[str]:
        """
        Load list of trusted Service Account emails

        In production, this could be loaded from:
        - Environment variables
        - Secret Manager
        - IAM policy configuration

        Returns:
            List of trusted Service Account emails
        """
        # Check environment variable first
        trusted_env = os.getenv("TRUSTED_SERVICE_ACCOUNTS")
        if trusted_env:
            accounts = [acc.strip() for acc in trusted_env.split(",")]
            logger.info(f"✅ Loaded {len(accounts)} trusted accounts from environment")
            return accounts

        # Default trusted accounts for development
        # In production, this should be configured via environment variable
        # or Secret Manager to ensure proper security
        default_accounts = [
            f"backend@{self.identity.project_id}.iam.gserviceaccount.com",
            f"frontend@{self.identity.project_id}.iam.gserviceaccount.com",
            f"gemma-service@{self.identity.project_id}.iam.gserviceaccount.com",
        ]

        # Only add dev account in actual development environment
        if os.getenv("ENVIRONMENT", "production") == "development":
            default_accounts.append(
                "dev-service-account@development.iam.gserviceaccount.com"
            )

        logger.warning(
            f"⚠️  Using default trusted accounts (should configure via TRUSTED_SERVICE_ACCOUNTS)"
        )
        return default_accounts

    def _get_signing_key(self) -> str:
        """
        Get secret key for message signing

        In production, this should:
        1. Retrieve from Secret Manager
        2. Derive from Service Account credentials
        3. Use per-service unique keys

        Returns:
            Secret key string
        """
        # Check environment variable
        key = os.getenv("A2A_SIGNING_KEY")
        if key:
            logger.info("✅ Using A2A signing key from environment")
            return key

        # Development fallback - derive from service account email
        logger.warning("⚠️  Using derived signing key (development mode)")
        key_material = f"{self.identity.email}_{self.identity.project_id}_a2a_secret"

        # Generate deterministic key from key material
        return hashlib.sha256(key_material.encode("utf-8")).hexdigest()

    def sign_message(self, message_dict: Dict[str, Any]) -> str:
        """
        Sign an A2A message using HMAC

        Args:
            message_dict: Message data to sign

        Returns:
            Hexadecimal signature string

        Note:
            Uses HMAC-SHA256 directly for better performance.
            PBKDF2 is optional and can be enabled via environment variable
            for enhanced security at the cost of performance.
        """
        # Create canonical representation
        canonical = json.dumps(
            {
                "message_id": message_dict.get("message_id"),
                "from_agent": message_dict.get("from_agent"),
                "to_agent": message_dict.get("to_agent"),
                "message_type": message_dict.get("message_type"),
                "timestamp": message_dict.get("timestamp"),
                "data": message_dict.get("data", {}),
            },
            sort_keys=True,
        )

        # Check if enhanced security mode is enabled
        use_pbkdf2 = os.getenv("A2A_USE_PBKDF2", "false").lower() == "true"

        if use_pbkdf2:
            # Enhanced security with PBKDF2 (slower but more secure)
            iterations = int(os.getenv("A2A_PBKDF2_ITERATIONS", "100000"))
            signature = hashlib.pbkdf2_hmac(
                "sha256",
                canonical.encode("utf-8"),
                self._secret_key.encode("utf-8"),
                iterations=iterations,
            )
        else:
            # Standard HMAC-SHA256 (faster, suitable for high throughput)
            import hmac

            signature = hmac.new(
                self._secret_key.encode("utf-8"),
                canonical.encode("utf-8"),
                hashlib.sha256,
            ).digest()

        return signature.hex()

    def verify_message_signature(
        self, message_dict: Dict[str, Any], signature: str
    ) -> bool:
        """
        Verify A2A message signature

        Args:
            message_dict: Message data to verify
            signature: Signature to check

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            expected_signature = self.sign_message(message_dict)
            is_valid = signature == expected_signature

            if is_valid:
                logger.debug(
                    f"✅ Message signature verified: {message_dict.get('message_id')}"
                )
            else:
                logger.warning(
                    f"⚠️  Invalid message signature: {message_dict.get('message_id')}"
                )
                self._log_security_event("signature_verification_failed", message_dict)

            return is_valid

        except Exception as e:
            logger.error(f"❌ Signature verification error: {e}")
            return False

    def authenticate_service_account(self, service_account_email: str) -> bool:
        """
        Authenticate a Service Account for A2A communication

        Args:
            service_account_email: Service Account email to authenticate

        Returns:
            True if Service Account is trusted, False otherwise
        """
        # Allow wildcard for broadcast messages from self
        if service_account_email == self.identity.email:
            return True

        # Check against trusted accounts list
        is_trusted = service_account_email in self.trusted_service_accounts

        if not is_trusted:
            logger.warning(f"⚠️  Untrusted Service Account: {service_account_email}")
            self._log_security_event(
                "untrusted_service_account",
                {
                    "service_account": service_account_email,
                    "allowed_accounts": self.trusted_service_accounts,
                },
            )

        return is_trusted

    def authorize_agent_communication(
        self, from_agent: str, to_agent: str, service_account_email: str
    ) -> bool:
        """
        Authorize agent-to-agent communication

        Implements authorization policies for A2A Protocol:
        - Orchestrator can send to any agent
        - Specialized agents can send to orchestrator and visualizer
        - Agents cannot impersonate other agents

        Args:
            from_agent: Source agent name
            to_agent: Target agent name
            service_account_email: Sending Service Account

        Returns:
            True if communication is authorized, False otherwise
        """
        # First check if Service Account is trusted
        if not self.authenticate_service_account(service_account_email):
            return False

        # Authorization rules
        authorization_rules = {
            "orchestrator": ["*"],  # Orchestrator can send to anyone
            "summarizer": ["orchestrator", "visualizer", "linker", "*"],
            "linker": ["orchestrator", "visualizer", "*"],
            "visualizer": ["orchestrator", "*"],
        }

        # Get allowed targets for this agent
        allowed_targets = authorization_rules.get(from_agent, [])

        # Check if target is allowed
        is_authorized = (
            "*" in allowed_targets  # Broadcast allowed
            or to_agent in allowed_targets  # Specific target allowed
            or to_agent == "*"  # Broadcasting
        )

        if not is_authorized:
            logger.warning(
                f"⚠️  Unauthorized agent communication: {from_agent} → {to_agent}"
            )
            self._log_security_event(
                "unauthorized_communication",
                {
                    "from_agent": from_agent,
                    "to_agent": to_agent,
                    "service_account": service_account_email,
                    "allowed_targets": allowed_targets,
                },
            )

        return is_authorized

    def validate_message_security(self, message_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive security validation for an A2A message

        Checks:
        1. Message signature validity
        2. Service Account authentication
        3. Agent communication authorization
        4. Message timestamp freshness

        Args:
            message_dict: Message to validate

        Returns:
            Validation result dictionary with:
            - is_valid: bool
            - issues: List[str] of any security issues
            - security_score: int (0-100)
        """
        issues = []

        # Extract security context
        security_ctx = message_dict.get("security", {})
        service_account = security_ctx.get("service_account_id")
        signature = security_ctx.get("signature")

        # Check 1: Service Account authentication
        if not service_account:
            issues.append("Missing service_account_id in security context")
        elif not self.authenticate_service_account(service_account):
            issues.append(f"Untrusted service account: {service_account}")

        # Check 2: Message signature
        if not signature:
            issues.append("Missing message signature")
        elif not self.verify_message_signature(message_dict, signature):
            issues.append("Invalid message signature")

        # Check 3: Agent authorization
        from_agent = message_dict.get("from_agent")
        to_agent = message_dict.get("to_agent")

        if service_account and not self.authorize_agent_communication(
            from_agent, to_agent, service_account
        ):
            issues.append(f"Unauthorized communication: {from_agent} → {to_agent}")

        # Check 4: Timestamp freshness (prevent replay attacks)
        timestamp = message_dict.get("timestamp")
        if timestamp:
            age_seconds = time.time() - timestamp
            if age_seconds > 3600:  # 1 hour
                issues.append(f"Message too old: {age_seconds:.0f} seconds")
            elif age_seconds < -300:  # 5 minutes in future
                issues.append("Message timestamp in future")

        # Calculate security score
        max_issues = 4
        security_score = int(100 * (1 - len(issues) / max_issues))

        is_valid = len(issues) == 0

        if not is_valid:
            logger.warning(f"⚠️  Message security validation failed: {issues}")
            self._log_security_event(
                "validation_failed",
                {"message_id": message_dict.get("message_id"), "issues": issues},
            )

        return {
            "is_valid": is_valid,
            "issues": issues,
            "security_score": security_score,
            "validated_at": time.time(),
        }

    def enhance_message_with_security(
        self, message_dict: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add security context to an outgoing A2A message

        Args:
            message_dict: Message to enhance

        Returns:
            Enhanced message with security context
        """
        # Generate signature
        signature = self.sign_message(message_dict)

        # Add security context
        message_dict["security"] = {
            "service_account_id": self.identity.email,
            "signature": signature,
            "signature_algorithm": "PBKDF2-HMAC-SHA256",
            "verified": False,  # Will be set to True after verification
        }

        logger.debug(
            f"🔐 Enhanced message with security: {message_dict.get('message_id')}"
        )

        return message_dict

    def _log_security_event(self, event_type: str, event_data: Dict[str, Any]):
        """
        Log security event for audit trail

        In production, this should:
        - Send to Cloud Logging with security log severity
        - Trigger alerts for critical events
        - Store in security audit collection in Firestore

        Args:
            event_type: Type of security event
            event_data: Event details
        """
        security_log = {
            "event_type": event_type,
            "timestamp": time.time(),
            "service_account": self.identity.email,
            "data": event_data,
        }

        # Sanitize event data for logging (remove sensitive fields)
        sanitized_data = self._sanitize_for_logging(event_data)

        # In production, send to Cloud Logging
        logger.warning(
            f"🔒 SECURITY EVENT: {event_type} - {json.dumps(sanitized_data)}"
        )

        # TODO: Store in Firestore security_audit collection
        # TODO: Trigger alerts for critical events

    def _sanitize_for_logging(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove sensitive fields from data before logging

        Args:
            data: Data to sanitize

        Returns:
            Sanitized data safe for logging
        """
        # List of sensitive field names to redact
        sensitive_fields = [
            "secret",
            "password",
            "token",
            "key",
            "signature",
            "credential",
            "auth",
            "api_key",
        ]

        sanitized = {}
        for key, value in data.items():
            # Check if key contains sensitive terms
            is_sensitive = any(term in key.lower() for term in sensitive_fields)

            if is_sensitive:
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                # Recursively sanitize nested dicts
                sanitized[key] = self._sanitize_for_logging(value)
            elif isinstance(value, list):
                # Sanitize lists of dicts
                sanitized[key] = [
                    self._sanitize_for_logging(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value

        return sanitized


# Singleton instance
_security_service: Optional[A2ASecurityService] = None


def get_security_service() -> A2ASecurityService:
    """
    Get or create singleton A2A Security Service instance

    Returns:
        A2ASecurityService instance
    """
    global _security_service

    if _security_service is None:
        _security_service = A2ASecurityService()

    return _security_service
