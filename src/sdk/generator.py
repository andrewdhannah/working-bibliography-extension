"""
Librarian Extension Generator — Creates a contract-compliant extension scaffold.

Usage:
    python3 -m src.sdk.generator --name my-extension --domain knowledge.reference \\
        --capability "search,Search Items,R0,read:items,item_search" \\
        --dependency embedding.generate

Generates a complete extension package with identity, contract, manifest,
MCP scaffold, handshake reference, validation fixtures, and documentation.
"""

import os
import sys
import re
import json
import shutil
import argparse
from datetime import datetime, timezone


TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "templates", "minimal-extension")


def sanitize_id(name: str) -> str:
    """Convert a name to a valid extension_id."""
    s = name.lower().strip()
    s = re.sub(r'[^a-z0-9-]', '-', s)
    s = re.sub(r'-+', '-', s)
    return s.strip('-')


def generate_extension_id(name: str) -> str:
    """Generate a unique extension ID."""
    base = sanitize_id(name)
    return f"{base}-extension"


def generate_contract_id(ext_id: str) -> str:
    """Generate a contract ID from extension ID."""
    return f"{ext_id}-contract-v1"


def parse_capability(cap_str: str) -> dict:
    """Parse a capability definition string.
    
    Format: name,Display Name,Risk,Permission,Tool
    Example: search,Search Items,R0,read:items,item_search
    """
    parts = [p.strip() for p in cap_str.split(",")]
    return {
        "name": parts[0] if len(parts) > 0 else "unknown",
        "display_name": parts[1] if len(parts) > 1 else parts[0].replace(".", " ").title(),
        "risk": parts[2] if len(parts) > 2 else "R0",
        "permission": parts[3] if len(parts) > 3 else f"read:{parts[0].split('.')[0] if '.' in parts[0] else parts[0]}",
        "tool": parts[4] if len(parts) > 4 else f"ext_{parts[0].replace('.', '_')}",
        "description": f"{parts[1] if len(parts) > 1 else parts[0]} capability"
    }


def parse_dependency(dep_str: str) -> str:
    """Parse a dependency string."""
    return dep_str.strip()


def validate_capability_name(name: str, ext_id: str) -> bool:
    """Validate that a capability name follows namespace rules."""
    # Must not be generic (e.g., 'search' without a prefix)
    generic_names = {"search", "read", "write", "list", "get", "create", "delete", "update"}
    if name in generic_names:
        print(f"  ⚠ Capability name '{name}' is generic. Use 'domain.action' format (e.g., 'knowledge.search')")
    return True


def generate(args) -> str:
    """Generate an extension package.
    
    Args:
        args: parsed command-line arguments
    
    Returns:
        Path to the generated extension directory
    """
    # Determine paths
    output_dir = os.path.abspath(args.output or ".")
    ext_id = generate_extension_id(args.name)
    contract_id = generate_contract_id(ext_id)
    display_name = args.display_name or args.name.replace("-", " ").title()
    domain = args.domain or "custom"
    declared_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    port = int(args.port or 9000)

    # Parse capabilities
    capabilities = []
    for cap_str in args.capability or ["read,Read,R0,read:items,ext_read"]:
        cap = parse_capability(cap_str)
        validate_capability_name(cap["name"], ext_id)
        capabilities.append(cap)

    # Parse dependencies
    dependencies = [parse_dependency(d) for d in args.dependency or []]

    # Build template context
    context = {
        "extension_id": ext_id,
        "display_name": display_name,
        "domain": domain,
        "contract_id": contract_id,
        "description": args.description or f"{display_name} — a governed Librarian extension in the {domain} domain.",
        "declared_at": declared_at,
        "repo_path": os.path.join(output_dir, ext_id),
        "port": port,
        "capabilities": capabilities,
        "dependencies": dependencies,
    }

    # Create output directory
    ext_dir = os.path.join(output_dir, ext_id)
    if os.path.exists(ext_dir):
        print(f"  ⚠ Directory {ext_dir} already exists. Overwriting.")
        shutil.rmtree(ext_dir)

    print(f"\n Generating extension: {display_name} ({ext_id})\n")

    # Copy template (non-JSON structure files)
    shutil.copytree(TEMPLATE_DIR, ext_dir, ignore=shutil.ignore_patterns('*.json'))

    # Generate JSON files directly (avoids template rendering errors)
    _generate_extension_json(ext_dir, context)
    _generate_contract_json(ext_dir, context)
    _generate_capabilities_json(ext_dir, context)
    _generate_permissions_json(ext_dir, context)
    _generate_fixture_json(ext_dir, context)

    # Process template-rendered files (.md, .py)
    file_count = 0
    for root, dirs, files in os.walk(ext_dir):
        for filename in files:
            if not filename.endswith((".md", ".py")):
                continue
            filepath = os.path.join(root, filename)
            with open(filepath) as f:
                content = f.read()
            content = render_template(content, context)
            with open(filepath, "w") as f:
                f.write(content)
            file_count += 1

    print(f"  Created {file_count} files")
    print(f"  Location: {ext_dir}")
    print(f"  State:    REGISTERED (handshake required)")
    print()

    # Print next steps
    print("  Next steps:")
    print(f"    cd {ext_id}")
    print(f"    cp -r ../working-bibliography-extension/src/handshake/* src/handshake/")
    print(f"    python3 src/mcp/server.py")
    print()
    print("  Documentation (requires running Librarian MCP):")
    print(f"    librarian_documentation_generate --type extension_status \\")
    print(f"      --extension-id {ext_id} --output-path docs/EXTENSION-STATUS.md")
    print(f"    librarian_documentation_drift_check --file-path docs/EXTENSION-STATUS.md")
    print()

    return ext_dir


def render_template(content: str, context: dict) -> str:
    """Replace template variables with context values.
    
    Supports:
      {{variable}} — simple variable substitution
      {% for item in list %}...{% endfor %} — iteration
    """
    # Handle for loops first
    result = []
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        # Check for for loop
        for_match = re.match(r'\s*{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%}', line)
        if for_match:
            var_name = for_match.group(1)
            list_name = for_match.group(2)
            items = context.get(list_name, [])
            indent = line[:len(line) - len(line.lstrip())]

            # Find endfor
            loop_lines = []
            i += 1
            while i < len(lines) and '{% endfor %}' not in lines[i]:
                loop_lines.append(lines[i])
                i += 1

            # Generate loop body for each item
            for item in items:
                for loop_line in loop_lines:
                    rendered = loop_line
                    if isinstance(item, dict):
                        for key, val in item.items():
                            rendered = rendered.replace('{{' + var_name + '.' + key + '}}', str(val))
                    else:
                        rendered = rendered.replace('{{' + var_name + '}}', str(item))
                    result.append(rendered)
            i += 1
        else:
            # Simple variable substitution
            for key, val in context.items():
                if isinstance(val, str):
                    line = line.replace('{{' + key + '}}', val)
                elif isinstance(val, int):
                    line = line.replace('{{' + key + '}}', str(val))
            result.append(line)
            i += 1

    return '\n'.join(result)


# ─── JSON Generators ─────────────────────────────────────────────────

def _generate_extension_json(ext_dir: str, ctx: dict):
    """Generate .librarian/extension.json."""
    data = {
        "$schema": "project-index-v1",
        "project_id": ctx["extension_id"],
        "display_name": ctx["display_name"],
        "repo_path": ctx["repo_path"],
        "default_branch": "main",
        "current_phase": "init",
        "allowed_startup_modes": ["managed", "degraded", "read-only"],
        "tags": ["extension", "governed", ctx["domain"]],
        "deprecated": False,
        "lifecycle_policy_version": "1.1"
    }
    path = os.path.join(ext_dir, ".librarian", "extension.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    os.remove(os.path.join(ext_dir, ".librarian", "extension.json"))


def _generate_contract_json(ext_dir: dict, ctx: dict):
    """Generate docs/EXTENSION-CONTRACT.json."""
    capabilities = []
    for cap in ctx["capabilities"]:
        capabilities.append({
            "capability_id": cap["name"],
            "allowed_operations": [cap["tool"]],
            "risk_classification": cap["risk"],
            "required_permissions": [cap["permission"]]
        })

    contract = {
        "contract_id": ctx["contract_id"],
        "contract_type": "connector_custody",
        "version": "1.0.0",
        "stability": "MAJOR",
        "title": f"{ctx['display_name']} — Librarian Contract",
        "description": f"Formal contract governing the {ctx['extension_id']} extension.",
        "parties": [
            {"role": "extension", "id": ctx["extension_id"], "domain": ctx["domain"]},
            {"role": "core", "id": "librarian", "domain": "governance_kernel"}
        ],
        "identity": {
            "extension_id": ctx["extension_id"],
            "contract_id": ctx["contract_id"],
            "contract_version": "1.0.0"
        },
        "capabilities": {"declarations": capabilities},
        "ownership": {
            "extension_owns": {"domains": [f"{ctx['domain']}_artifacts", f"{ctx['domain']}_metadata"]},
            "core_owns": {"domains": ["governance_authority", "owner_decisions", "project_lifecycle"]}
        },
        "forbidden_operations": {
            "absolute": [
                {"operation": "modify_librarian_authority_state", "rationale": "Never write governance state", "violation_outcome": "REVOKE"},
                {"operation": "create_owner_decisions", "rationale": "Owner decisions are core-only", "violation_outcome": "REVOKE"},
                {"operation": "mutate_sprint_ledger", "rationale": "Sprint ledger is core-controlled", "violation_outcome": "REVOKE"},
                {"operation": f"delete_{ctx['domain']}_artifacts", "rationale": "Artifacts persist for audit", "violation_outcome": "SUSPENDED"}
            ]
        },
        "lifecycle": {
            "state_machine": [
                {"state": "REGISTERED", "meaning": "Identity known", "capabilities_active": False},
                {"state": "CONTRACT_VERIFIED", "meaning": "Contract validated", "capabilities_active": False},
                {"state": "OWNER_APPROVED", "meaning": "Owner authorized", "capabilities_active": False},
                {"state": "ACTIVE", "meaning": "Capabilities accessible", "capabilities_active": True},
                {"state": "SUSPENDED", "meaning": "Drift investigation", "capabilities_active": False},
                {"state": "REVOKED", "meaning": "Permanent termination", "capabilities_active": False}
            ],
            "transitions": [
                {"from": "REGISTERED", "to": "CONTRACT_VERIFIED", "trigger": "validation", "authority": "automated"},
                {"from": "CONTRACT_VERIFIED", "to": "OWNER_APPROVED", "trigger": "approval", "authority": "owner"},
                {"from": "OWNER_APPROVED", "to": "ACTIVE", "trigger": "activation", "authority": "automated"},
                {"from": "ACTIVE", "to": "SUSPENDED", "trigger": "drift", "authority": "automated_notify_owner"},
                {"from": "ACTIVE", "to": "REVOKED", "trigger": "violation", "authority": "owner"},
                {"from": "SUSPENDED", "to": "ACTIVE", "trigger": "restore", "authority": "owner"},
                {"from": "SUSPENDED", "to": "REVOKED", "trigger": "terminate", "authority": "owner"}
            ],
            "terminal_states": ["REVOKED"]
        },
        "evidence": {
            "receipt_types": [{"type": "operation_receipt", "required_fields": ["operation", "timestamp", "result"]}]
        },
        "enforcement": {
            "drift_monitoring": "active",
            "review_frequency": "per_operation",
            "violation_outcomes": {"drift": "SUSPENDED", "contract_breach": "REVOKED"}
        }
    }
    # Replace .md contract with .json
    md_path = os.path.join(ext_dir, "docs", "EXTENSION-CONTRACT.md")
    json_path = os.path.join(ext_dir, "docs", "EXTENSION-CONTRACT.json")
    if os.path.exists(md_path):
        os.remove(md_path)
    with open(json_path, "w") as f:
        json.dump(contract, f, indent=2)


def _generate_capabilities_json(ext_dir: str, ctx: dict):
    """Generate mcp/capabilities.json."""
    capabilities = []
    for cap in ctx["capabilities"]:
        capabilities.append({
            "id": cap["name"],
            "display_name": cap["display_name"],
            "tools": [cap["tool"]],
            "risk": cap["risk"],
            "description": cap["description"],
            "permissions": [cap["permission"]],
            "status": "pending"
        })

    dependencies = []
    for dep in ctx["dependencies"]:
        dependencies.append({"type": "optional", "capability": dep, "description": "Optional capability provider"})

    manifest = {
        "manifest_version": "1.0.0",
        "extension_id": ctx["extension_id"],
        "declared_at": ctx["declared_at"],
        "identity": {
            "extension_id": ctx["extension_id"],
            "display_name": ctx["display_name"],
            "version": "0.1.0",
            "classification": "knowledge_custody_provider",
            "domain": ctx["domain"],
            "contract_id": ctx["contract_id"],
            "contract_version": "1.0.0",
            "declared_at": ctx["declared_at"]
        },
        "capabilities": capabilities,
        "forbidden_actions": [
            {"action": "modify_librarian_authority_state", "violation_outcome": "REVOKE"},
            {"action": "create_owner_decisions", "violation_outcome": "REVOKE"},
            {"action": "mutate_sprint_ledger", "violation_outcome": "REVOKE"},
            {"action": f"delete_{ctx['domain']}_artifacts", "violation_outcome": "SUSPENDED"}
        ],
        "receipt_types": [{"type": "operation_receipt", "description": "Generated per operation"}],
        "dependencies": dependencies
    }
    path = os.path.join(ext_dir, "mcp", "capabilities.json")
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)


def _generate_permissions_json(ext_dir: str, ctx: dict):
    """Generate mcp/permissions.json."""
    allowed_ops = {}
    for cap in ctx["capabilities"]:
        allowed_ops[cap["permission"]] = {
            "tools": [cap["tool"]],
            "risk": cap["risk"],
            "requires_approval": False,
            "produces_receipt": True
        }

    permissions = {
        "permissions_version": "1.0.0",
        "extension_id": ctx["extension_id"],
        "contract_id": ctx["contract_id"],
        "allowed_operations": allowed_ops,
        "forbidden_operations": [
            "modify_librarian_authority_state",
            "create_owner_decisions",
            "mutate_sprint_ledger",
            f"delete_{ctx['domain']}_artifacts"
        ],
        "enforcement": {
            "drift_monitoring": "active",
            "review_frequency": "per_operation",
            "violation_outcomes": {"drift": "SUSPENDED", "contract_breach": "REVOKED"}
        }
    }
    path = os.path.join(ext_dir, "mcp", "permissions.json")
    with open(path, "w") as f:
        json.dump(permissions, f, indent=2)


def _generate_fixture_json(ext_dir: str, ctx: dict):
    """Generate tests/fixtures/identity-valid.json."""
    capabilities = []
    for cap in ctx["capabilities"]:
        capabilities.append({
            "id": cap["name"],
            "tools": [cap["tool"]],
            "risk": cap["risk"],
            "status": "pending",
            "permissions": [cap["permission"]]
        })

    cap_declarations = []
    for cap in ctx["capabilities"]:
        cap_declarations.append({"capability_id": cap["name"], "allowed_operations": [cap["tool"]]})

    perms = {}
    for cap in ctx["capabilities"]:
        perms[cap["permission"]] = {"tools": [cap["tool"]], "risk": cap["risk"]}

    fixture = {
        "description": f"Valid identity for {ctx['extension_id']}",
        "category": "valid",
        "expected": {"pass": True},
        "data": {
            "identity": {
                "extension_id": ctx["extension_id"],
                "contract_id": ctx["contract_id"],
                "contract_version": "1.0.0",
                "version": "0.1.0",
                "owner_domain": ctx["domain"],
                "declared_at": ctx["declared_at"]
            },
            "contract": {
                "contract_id": ctx["contract_id"],
                "contract_type": "connector_custody",
                "version": "1.0.0",
                "parties": [{"role": "extension", "id": ctx["extension_id"]}, {"role": "core", "id": "librarian"}],
                "capabilities": {"declarations": cap_declarations},
                "ownership": {"extension_owns": {"domains": [ctx["domain"]]}, "core_owns": {"domains": ["authority"]}},
                "forbidden_operations": {"absolute": [{"operation": "modify_librarian_authority_state", "violation_outcome": "REVOKE"}]},
                "lifecycle": {"state_machine": [{"state": "REGISTERED"}, {"state": "ACTIVE"}, {"state": "REVOKED"}]},
                "evidence": {"receipt_types": [{"type": "operation_receipt"}]}
            },
            "capabilities": capabilities,
            "lifecycle": {"state_machine": [{"state": "REGISTERED"}, {"state": "ACTIVE"}, {"state": "REVOKED"}]},
            "permissions": {
                "allowed_operations": perms,
                "forbidden_operations": ["modify_librarian_authority_state"],
                "enforcement": {"drift_monitoring": "active", "violation_outcomes": {}}
            }
        }
    }
    path = os.path.join(ext_dir, "tests", "fixtures", "identity-valid.json")
    with open(path, "w") as f:
        json.dump(fixture, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Generate a Librarian-compatible extension")
    parser.add_argument("--name", "-n", required=True, help="Extension name (e.g., citation-manager)")
    parser.add_argument("--display-name", "-d", help="Display name (defaults to --name)")
    parser.add_argument("--domain", required=True, help="Extension domain (e.g., knowledge.reference)")
    parser.add_argument("--description", help="Short description of the extension")
    parser.add_argument("--capability", "-c", action="append",
                        help="Capability: 'name,Display,Risk,Permission,Tool' (repeatable)")
    parser.add_argument("--dependency", action="append",
                        help="Optional dependency capability (repeatable)")
    parser.add_argument("--output", "-o", default=".", help="Output directory (default: current)")
    parser.add_argument("--port", default="9000", help="MCP server port (default: 9000)")
    parser.add_argument("--list", action="store_true", help="List available templates")

    args = parser.parse_args()

    if args.list:
        print("Available templates:")
        print("  minimal-extension   Standard governed extension scaffold")
        return

    generate(args)


if __name__ == "__main__":
    main()
