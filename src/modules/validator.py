thonimport logging
import re
from typing import Dict, List

from modules.domain_lookup import lookup_domain
from modules.smtp_checker import check_smtp_server

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(
    # Simple but effective email validation regex
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*$"
)

FREE_EMAIL_PROVIDERS = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "live.com",
    "icloud.com",
    "proton.me",
    "protonmail.com",
    "aol.com",
}

DISPOSABLE_EMAIL_PROVIDERS = {
    "mailinator.com",
    "10minutemail.com",
    "temp-mail.org",
    "guerrillamail.com",
    "dispostable.com",
    "trashmail.com",
}

class EmailValidator:
    """
    Coordinates email validation:
      - Syntactic format check
      - Domain DNS & MX lookup
      - SMTP connectivity probe
      - Mailbox and mailbox type heuristic
    """

    def __init__(self, dns_timeout: int = 5, smtp_timeout: int = 8) -> None:
        self.dns_timeout = dns_timeout
        self.smtp_timeout = smtp_timeout

    def _extract_domain(self, email: str) -> str:
        parts = email.rsplit("@", 1)
        if len(parts) != 2:
            return ""
        return parts[1].strip().lower()

    def _determine_mailbox_type(self, domain: str) -> str:
        if not domain:
            return "unknown"
        if domain in DISPOSABLE_EMAIL_PROVIDERS:
            return "disposable"
        if domain in FREE_EMAIL_PROVIDERS:
            return "personal"
        if "." in domain:
            # Heuristic: domains with clear brand or company name considered professional
            return "professional"
        return "unknown"

    def _format_status_from_checks(
        self,
        email: str,
        format_valid: bool,
        domain_info: Dict,
        smtp_info: Dict,
    ) -> Dict:
        message_parts: List[str] = []

        if not format_valid:
            message_parts.append("Email format is invalid.")

        domain_status = domain_info.get("status")
        domain_message = domain_info.get("message", "")
        if domain_message:
            message_parts.append(domain_message)

        smtp_status = smtp_info.get("status")
        smtp_message = smtp_info.get("message", "")
        if smtp_message:
            message_parts.append(smtp_message)

        if not message_parts:
            message_parts.append("Validation completed successfully.")

        combined_message = " ".join(message_parts)

        # Decide high-level statuses
        if not format_valid:
            email_status = "invalid"
            mailbox_status = "invalid"
        elif domain_status == "invalid":
            email_status = "invalid"
            mailbox_status = "invalid"
        elif smtp_status == "ok":
            email_status = "valid"
            mailbox_status = "unknown"
        elif smtp_status == "unreachable":
            email_status = "invalid"
            mailbox_status = "invalid"
        else:
            email_status = "unknown"
            mailbox_status = "unknown"

        domain = self._extract_domain(email)
        mailbox_type = self._determine_mailbox_type(domain)

        return {
            "email": email,
            "email_status": email_status,
            "message": combined_message,
            "format": "valid" if format_valid else "invalid",
            "mailbox_status": mailbox_status,
            "mailbox_type": mailbox_type,
            "domain": domain,
        }

    def validate(self, email: str) -> Dict:
        """
        Run a complete validation workflow for a single email.
        """
        email = email.strip()
        format_valid = bool(EMAIL_REGEX.match(email))
        domain = self._extract_domain(email)

        logger.debug("Starting validation for %s", email)

        if not email or not format_valid or not domain:
            logger.info("Email %s failed basic format/domain checks.", email)
            return self._format_status_from_checks(
                email=email,
                format_valid=format_valid,
                domain_info={
                    "status": "invalid",
                    "message": "Domain missing or email format is invalid.",
                },
                smtp_info={"status": "skipped", "message": ""},
            )

        domain_info = lookup_domain(domain, timeout=self.dns_timeout)
        logger.debug("Domain info for %s: %s", domain, domain_info)

        if domain_info.get("status") != "ok":
            smtp_info = {
                "status": "unreachable",
                "message": "Skipping SMTP check because domain is not reachable or has no MX records.",
            }
        else:
            smtp_info = check_smtp_server(domain, timeout=self.smtp_timeout)

        logger.debug("SMTP info for %s: %s", domain, smtp_info)

        result = self._format_status_from_checks(
            email=email,
            format_valid=format_valid,
            domain_info=domain_info,
            smtp_info=smtp_info,
        )

        logger.info(
            "Validation result for %s: email_status=%s, mailbox_status=%s",
            email,
            result["email_status"],
            result["mailbox_status"],
        )

        return result