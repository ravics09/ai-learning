"""
tool_sandbox_least_privilege.py
===============================
Least-privilege tool dispatch + HITL + egress allow-list for an agent.

WHY THIS EXISTS
---------------
Excessive agency (OWASP LLM06) is what turns a prompt injection into real
damage. The fix is NOT a smarter model — it's making a fooled model harmless:

    * Deny tools by default; expose only what's needed.
    * Run each tool with the END-USER's scope, not a superuser account.
    * Require human approval (HITL) for irreversible / high-value actions.
    * Enforce an egress allow-list so exfiltration fails even if injected
      (defeats the "confused deputy" exfiltration pattern).
    * Bound autonomy: cap the number of tool calls per session.
    * Audit every decision.

All security decisions live in DETERMINISTIC code here — never in the prompt.

Run:  python tool_sandbox_least_privilege.py
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Set


# ---------------------------------------------------------------------------
# Identity & policy
# ---------------------------------------------------------------------------
@dataclass
class User:
    user_id: str
    role: str                       # e.g. "viewer", "editor"
    # tenant_id ALWAYS comes from the verified auth token, never client input.
    tenant_id: str


@dataclass
class Policy:
    # Deny by default: a tool must be explicitly allowed for a role.
    allowed_tools: Dict[str, Set[str]]      # role -> {tool names}
    high_risk_tools: Set[str]               # require HITL
    egress_allowlist: Set[str]              # permitted outbound domains
    max_tool_calls: int = 5                 # bound autonomy (LLM10)


class PolicyError(Exception):
    pass


class ApprovalRequired(Exception):
    """Signals the orchestrator to pause for human approval (HITL)."""


# ---------------------------------------------------------------------------
# The tool broker: the single choke point every tool call passes through.
# ---------------------------------------------------------------------------
@dataclass
class ToolBroker:
    policy: Policy
    tools: Dict[str, Callable]
    _calls_made: int = 0
    audit: List[str] = field(default_factory=list)

    def _log(self, msg: str) -> None:
        self.audit.append(msg)
        print(f"[audit] {msg}")

    def call(self, tool_name: str, user: User, approved: bool = False, **kwargs):
        # 1) Bound autonomy: stop runaway agent loops.
        if self._calls_made >= self.policy.max_tool_calls:
            raise PolicyError("tool-call budget exhausted for this session")
        self._calls_made += 1

        # 2) Least privilege: is this tool allowed for this user's role?
        allowed = self.policy.allowed_tools.get(user.role, set())
        if tool_name not in allowed:
            self._log(f"DENY {tool_name} for role={user.role}")
            raise PolicyError(f"tool '{tool_name}' not permitted for role '{user.role}'")

        # 3) HITL gate for high-risk / irreversible actions.
        if tool_name in self.policy.high_risk_tools and not approved:
            self._log(f"HITL required for {tool_name} by {user.user_id}")
            raise ApprovalRequired(f"human approval required for '{tool_name}'")

        # 4) Egress control for anything that sends data outbound.
        if tool_name == "send_email":
            domain = kwargs.get("to", "").split("@")[-1]
            if domain not in self.policy.egress_allowlist:
                self._log(f"BLOCK egress to {domain!r} (not on allow-list)")
                raise PolicyError(f"outbound domain '{domain}' not allowed")

        # 5) Execute — pass the user through so the tool runs AS the user.
        self._log(f"ALLOW {tool_name} by {user.user_id} (tenant={user.tenant_id})")
        return self.tools[tool_name](_user=user, **kwargs)


# ---------------------------------------------------------------------------
# Example tools. Each is scoped to the calling user.
# ---------------------------------------------------------------------------
def search_docs(_user: User, query: str) -> str:
    # A real impl would filter by _user.tenant_id at the datastore level.
    return f"[docs for tenant {_user.tenant_id}] results for {query!r}"


def send_email(_user: User, to: str, body: str) -> str:
    return f"email sent to {to} on behalf of {_user.user_id}"


def delete_account(_user: User) -> str:
    return f"account {_user.user_id} deleted"


def build_broker() -> ToolBroker:
    policy = Policy(
        allowed_tools={
            "viewer": {"search_docs"},
            "editor": {"search_docs", "send_email", "delete_account"},
        },
        high_risk_tools={"send_email", "delete_account"},
        egress_allowlist={"example.com"},   # only corporate domain allowed
        max_tool_calls=5,
    )
    tools = {
        "search_docs": search_docs,
        "send_email": send_email,
        "delete_account": delete_account,
    }
    return ToolBroker(policy=policy, tools=tools)


if __name__ == "__main__":
    broker = build_broker()
    viewer = User("u-viewer", "viewer", "tenant-A")
    editor = User("u-editor", "editor", "tenant-A")

    # Allowed: viewer can search.
    print(broker.call("search_docs", viewer, query="q3 report"), "\n")

    # Denied: viewer cannot send email (least privilege).
    try:
        broker.call("send_email", viewer, to="x@example.com", body="hi")
    except PolicyError as e:
        print("blocked as expected:", e, "\n")

    # HITL: editor sending email needs approval first.
    try:
        broker.call("send_email", editor, to="ceo@example.com", body="hi")
    except ApprovalRequired as e:
        print("pausing for approval:", e)
        # Human approves -> retry with approved=True
        print(broker.call("send_email", editor, to="ceo@example.com",
                          body="hi", approved=True), "\n")

    # Egress blocked: even an approved email to a bad domain is refused.
    try:
        broker.call("send_email", editor, to="attacker@evil.example",
                   body="secrets", approved=True)
    except PolicyError as e:
        print("exfiltration blocked:", e)
