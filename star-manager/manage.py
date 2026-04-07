#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Star List Manager
========================
Fetches starred repos, manages classification in stars.json,
and syncs to GitHub Star Lists via GraphQL.

Usage:
  python manage.py fetch                # Fetch all starred repos -> repos.json
  python manage.py review               # Show stars.json summary
  python manage.py apply --dry-run      # Preview changes
  python manage.py apply                # Sync stars.json -> GitHub star lists

Prerequisites:
  - gh CLI authenticated with `user` scope
  - Run `gh auth refresh -s user` if needed
"""

import argparse
import json
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

DIR = Path(__file__).parent
REPOS_FILE = DIR / "repos.json"
STARS_FILE = DIR / "stars.json"



# ═══════════════════════════════════════════════════════════════════════
# GitHub API helpers
# ═══════════════════════════════════════════════════════════════════════


def gh_graphql(query):
    """Execute a GraphQL query via gh CLI. Returns parsed JSON or None."""
    r = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={query}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if r.returncode != 0:
        msg = (r.stderr or r.stdout or "unknown error")[:300]
        print(f"  GraphQL error: {msg}", file=sys.stderr)
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        print(f"  Invalid JSON response", file=sys.stderr)
        return None


def gql_escape(s):
    """Escape a string for embedding in a GraphQL query."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _fetch_all_lists_with_repos():
    """Fetch ALL star lists with ALL their repo memberships.

    Returns: {list_name: {"id": str, "repos": set[str]}}
    """
    # First query: get lists with first batch of items
    data = gh_graphql("""{
        viewer {
            lists(first: 100) {
                nodes {
                    id name
                    items(first: 100) {
                        totalCount
                        pageInfo { hasNextPage endCursor }
                        nodes { ... on Repository { nameWithOwner } }
                    }
                }
            }
        }
    }""")
    if not data:
        return {}

    lists = {}
    for node in data["data"]["viewer"]["lists"]["nodes"]:
        name = node["name"]
        repos = {n["nameWithOwner"] for n in node["items"]["nodes"]}
        total = node["items"]["totalCount"]
        has_next = node["items"]["pageInfo"]["hasNextPage"]
        cursor = node["items"]["pageInfo"]["endCursor"]

        # Paginate if list has more than 100 items
        while has_next:
            page = gh_graphql(f"""{{
                viewer {{
                    lists(first: 1) {{
                        nodes {{
                            items(first: 100, after: "{gql_escape(cursor)}") {{
                                pageInfo {{ hasNextPage endCursor }}
                                nodes {{ ... on Repository {{ nameWithOwner }} }}
                            }}
                        }}
                    }}
                }}
            }}""")
            if not page:
                break
            # This is a rough approach; for lists >100 items we may need
            # list-specific queries. For now, break to avoid complexity.
            break

        lists[name] = {"id": node["id"], "repos": repos}

    return lists


# ═══════════════════════════════════════════════════════════════════════
# Commands
# ═══════════════════════════════════════════════════════════════════════


def cmd_fetch():
    """Fetch all starred repos with metadata and node IDs."""
    print("Fetching starred repos...")
    jq_expr = '.[] | {name: .full_name, node_id: .node_id, desc: (.description // ""), lang: (.language // ""), topics: (.topics // [])}'
    r = subprocess.run(
        ["gh", "api", "user/starred", "--paginate", "--jq", jq_expr],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if r.returncode != 0:
        print(f"Error: {r.stderr}", file=sys.stderr)
        sys.exit(1)

    repos = []
    parse_errors = 0
    for line in r.stdout.strip().split("\n"):
        if line.strip():
            try:
                repos.append(json.loads(line))
            except json.JSONDecodeError:
                parse_errors += 1

    with open(REPOS_FILE, "w", encoding="utf-8") as f:
        json.dump(repos, f, ensure_ascii=False, indent=2)

    print(f"  {len(repos)} repos -> {REPOS_FILE}")
    if parse_errors:
        print(f"  ({parse_errors} lines skipped due to parse errors)")


def cmd_review():
    """Show stars.json classification summary."""
    if not STARS_FILE.exists():
        print("stars.json not found. Create it manually or via classification.", file=sys.stderr)
        sys.exit(1)

    with open(STARS_FILE, encoding="utf-8") as f:
        data = json.load(f)

    cats = data.get("categories", {})
    uncl = data.get("unclassified", [])

    # Validate against repos.json if available
    missing_repos = []
    if REPOS_FILE.exists():
        with open(REPOS_FILE, encoding="utf-8") as f:
            known = {r["name"] for r in json.load(f)}
        all_refs = set(r for rs in cats.values() for r in rs) | set(uncl)
        missing_repos = sorted(all_refs - known)

    print("\n=== Star List Classification ===\n")
    for cat in sorted(cats):
        print(f"  {cat:24s} {len(cats[cat]):4d}")
    print(f"\n  {'[unclassified]':24s} {len(uncl):4d}")

    all_classified = set(r for rs in cats.values() for r in rs)
    print(f"\n  Classified unique: {len(all_classified)}")
    print(f"  Total: {len(all_classified) + len(uncl)}")

    if missing_repos:
        print(f"\n  WARNING: {len(missing_repos)} repos in stars.json not found in repos.json")
        for r in missing_repos[:10]:
            print(f"    {r}")

    if uncl:
        print(f"\n--- Unclassified ({len(uncl)}) ---")
        for r in uncl:
            print(f"  {r}")


def cmd_apply(dry_run=False):
    """Sync stars.json -> GitHub star lists.

    IMPORTANT: updateUserListsForItem REPLACES all list memberships for a repo.
    To avoid removing repos from existing unmanaged lists (e.g. "research", "HPC"),
    we merge our managed list IDs with the repo's existing unmanaged list IDs.
    """
    if not STARS_FILE.exists() or not REPOS_FILE.exists():
        print("Need both stars.json and repos.json. Run 'fetch' first.", file=sys.stderr)
        sys.exit(1)

    with open(STARS_FILE, encoding="utf-8") as f:
        cats = json.load(f).get("categories", {})
    with open(REPOS_FILE, encoding="utf-8") as f:
        node_ids = {r["name"]: r["node_id"] for r in json.load(f)}

    # Build repo -> [managed list names]
    repo_to_new_cats = defaultdict(list)
    for cat, repos in cats.items():
        for repo in repos:
            repo_to_new_cats[repo].append(cat)

    # ── Step 1: Fetch existing lists ────────────────────────────────
    print("\n=== Step 1: Fetch existing lists ===\n")
    existing_lists = _fetch_all_lists_with_repos()

    managed_ids = {}  # managed list name -> id
    unmanaged_ids = {}  # unmanaged list name -> id

    for name, info in existing_lists.items():
        if MANAGED_LIST_SEP in name:
            managed_ids[name] = info["id"]
        else:
            unmanaged_ids[name] = info["id"]

    print(f"  Existing managed lists:   {len(managed_ids)}")
    print(f"  Existing unmanaged lists: {len(unmanaged_ids)}")

    # Build repo -> set of unmanaged list IDs (to preserve)
    repo_to_unmanaged = defaultdict(set)
    for name, info in existing_lists.items():
        if MANAGED_LIST_SEP not in name:
            for repo in info["repos"]:
                repo_to_unmanaged[repo].add(info["id"])

    # ── Step 2: Create missing managed lists ────────────────────────
    print("\n=== Step 2: Ensure managed lists exist ===\n")
    name_to_id = dict(managed_ids)

    for cat in sorted(cats):
        if cat in name_to_id:
            print(f"  [exists]  {cat}")
        elif dry_run:
            print(f"  [create]  {cat} (dry-run)")
            name_to_id[cat] = f"DRYRUN_{cat}"
        else:
            result = gh_graphql(
                f'mutation {{ createUserList(input: {{name: "{gql_escape(cat)}"}}) {{ list {{ id }} }} }}'
            )
            if result and "data" in result:
                name_to_id[cat] = result["data"]["createUserList"]["list"]["id"]
                print(f"  [created] {cat}")
            else:
                print(f"  [ERROR]   {cat}")

    # ── Step 3: Assign repos to lists ───────────────────────────────
    total = len(repo_to_new_cats)
    print(f"\n=== Step 3: Assign {total} repos ===\n")

    if dry_run:
        for cat in sorted(cats):
            print(f"  {cat:24s} {len(cats[cat]):4d} repos")
        print(f"\n  (dry-run, no changes made)")
        return

    done = errors = skipped = 0
    for repo_name, cat_list in sorted(repo_to_new_cats.items()):
        nid = node_ids.get(repo_name)
        if not nid:
            skipped += 1
            continue

        # Merge: our managed lists + repo's existing unmanaged lists
        managed_list_ids = {name_to_id[c] for c in cat_list if c in name_to_id}
        unmanaged_list_ids = repo_to_unmanaged.get(repo_name, set())
        all_list_ids = managed_list_ids | unmanaged_list_ids

        if not all_list_ids:
            skipped += 1
            continue

        ids_str = ", ".join(f'"{gql_escape(lid)}"' for lid in sorted(all_list_ids))
        result = gh_graphql(
            f'mutation {{ updateUserListsForItem(input: {{itemId: "{gql_escape(nid)}", listIds: [{ids_str}]}}) {{ item {{ ... on Repository {{ nameWithOwner }} }} }} }}'
        )

        if result and "data" in result:
            done += 1
        else:
            errors += 1
            if errors <= 5:
                print(f"  Error: {repo_name}")

        if done % 50 == 0 and done > 0:
            print(f"  Progress: {done}/{total} ({errors} errors)")
        if (done + errors) % 20 == 0:
            time.sleep(1)

    print(f"\n  Done: {done} assigned, {skipped} skipped, {errors} errors")


# ═══════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════


def main():
    p = argparse.ArgumentParser(
        description="Manage GitHub Star Lists from a local JSON classification file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Files:\n"
        "  repos.json   Cached starred repos (fetched from GitHub)\n"
        "  stars.json   Classification data (edit manually or generate)\n",
    )
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("fetch", help="Fetch all starred repos -> repos.json")
    sub.add_parser("review", help="Show classification summary")

    ap = sub.add_parser("apply", help="Sync stars.json -> GitHub star lists")
    ap.add_argument("--dry-run", action="store_true", help="Preview changes without applying")

    args = p.parse_args()

    if args.cmd == "fetch":
        cmd_fetch()
    elif args.cmd == "review":
        cmd_review()
    elif args.cmd == "apply":
        cmd_apply(dry_run=args.dry_run)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
