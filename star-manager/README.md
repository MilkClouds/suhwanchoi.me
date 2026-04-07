# star-manager

Manage GitHub Star Lists from a local JSON file. Fetch starred repos, classify them, and sync to GitHub Star Lists via GraphQL.

## Prerequisites

```bash
# gh CLI must be authenticated with the `user` scope
gh auth refresh -s user
```

## Files

| File | Git-tracked | Description |
|------|-------------|-------------|
| `manage.py` | Yes | fetch / review / apply script |
| `repos.json` | **No** | Cached starred repos (contains private repo names) |
| `stars.json` | **No** | Classification data (contains private repo names) |

## Usage

```bash
# 1. Fetch all starred repos
python manage.py fetch

# 2. Review current classification
python manage.py review

# 3. Preview what would change
python manage.py apply --dry-run

# 4. Apply to GitHub star lists
python manage.py apply
```

## stars.json format

```json
{
  "categories": {
    "Category A": ["owner/repo1", "owner/repo2"],
    "Category B": ["owner/repo3"]
  },
  "unclassified": ["owner/repo4"]
}
```

- A repo can appear in multiple categories.
- Edit manually, then run `apply` to sync.

## How apply works

The `updateUserListsForItem` GraphQL mutation **replaces** all list memberships for a repo. To preserve existing list memberships not managed by this tool, the script fetches all current lists and merges their IDs before calling the mutation. Lists whose names appear in `stars.json` are considered "managed"; all others are preserved as-is.
