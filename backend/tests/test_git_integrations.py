import uuid
from types import SimpleNamespace

import pytest

from app.routers.profile import _enriched_block_config
from app.services import external_integrations


@pytest.mark.asyncio
async def test_gitlab_sync_does_not_create_synthetic_pinned_repositories(monkeypatch):
    async def fake_fetch_json_value(*args, **kwargs):
        return [
            {
                "id": 1,
                "path_with_namespace": "user/project-one",
                "name": "project-one",
                "web_url": "https://gitlab.example/user/project-one",
                "visibility": "public",
                "star_count": 10,
                "forks_count": 2,
                "last_activity_at": "2026-06-01T00:00:00Z",
            }
        ]

    async def fail_if_called(*args, **kwargs):
        raise AssertionError("GitHub pinned API must not be used for GitLab")

    monkeypatch.setattr(
        external_integrations, "_fetch_json_value", fake_fetch_json_value
    )
    monkeypatch.setattr(
        external_integrations, "fetch_github_pinned_repositories", fail_if_called
    )

    result = await external_integrations.fetch_code_provider_repositories(
        provider="gitlab",
        access_token="token",
        base_url="https://gitlab.example",
        api_base="https://gitlab.example/api/v4",
        username="user",
        user_id="42",
    )

    assert result["repositories"]
    assert result["pinned_repositories"] == []
    assert result["pinned_source"] == "unsupported"


@pytest.mark.asyncio
async def test_github_empty_pinned_response_does_not_fallback_to_all_repositories(
    monkeypatch,
):
    async def fake_fetch_json_value(*args, **kwargs):
        return [
            {
                "id": 1,
                "full_name": "user/project-one",
                "name": "project-one",
                "html_url": "https://github.com/user/project-one",
                "private": False,
                "stargazers_count": 10,
                "forks_count": 2,
                "updated_at": "2026-06-01T00:00:00Z",
            }
        ]

    async def fake_fetch_github_pinned_repositories(*args, **kwargs):
        return []

    monkeypatch.setattr(
        external_integrations, "_fetch_json_value", fake_fetch_json_value
    )
    monkeypatch.setattr(
        external_integrations,
        "fetch_github_pinned_repositories",
        fake_fetch_github_pinned_repositories,
    )

    result = await external_integrations.fetch_code_provider_repositories(
        provider="github",
        access_token="token",
        base_url="https://github.com",
        api_base="https://api.github.com",
        username="user",
        user_id="42",
    )

    assert result["repositories"]
    assert result["pinned_repositories"] == []
    assert result["pinned_source"] == "github_pinned_items_empty"


def test_git_block_does_not_use_account_from_another_provider():
    github_account = SimpleNamespace(
        id=uuid.uuid4(),
        provider="github",
        provider_uid="github-user",
        display_name="GitHub User",
        is_active=True,
        account_metadata={
            "username": "github-user",
            "repositories": [{"name": "repo", "is_private": False}],
            "pinned_repositories": [{"name": "repo", "is_private": False}],
        },
        sync_error=None,
        last_synced_at=None,
    )
    profile = SimpleNamespace(
        user=SimpleNamespace(connected_accounts=[github_account]),
    )
    block = SimpleNamespace(
        block_type="widget_github",
        config={"provider": "gitlab", "show_pinned_repos": True},
    )

    config = _enriched_block_config(profile, block)

    assert config["provider"] == "gitlab"
    assert config["git_provider"] == "gitlab"
    assert config["git_provider_label"] == "GitLab"
    assert "connected_account_id" not in config
    assert "git_display_name" not in config
    assert "git_repositories" not in config
    assert "git_pinned_repositories" not in config
