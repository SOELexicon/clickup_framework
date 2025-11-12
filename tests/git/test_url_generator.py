"""Tests for URL parsing and generation."""

import unittest
from clickup_framework.git.url_generator import (
    parse_remote_url,
    generate_commit_url,
    generate_branch_url,
    generate_pr_url,
    URLParseError
)


class TestParseRemoteURL(unittest.TestCase):
    """Tests for parse_remote_url function."""

    def test_parse_github_https(self):
        """Test parsing GitHub HTTPS URL."""
        url = "https://github.com/owner/repo.git"
        result = parse_remote_url(url)

        self.assertEqual(result['host'], 'github.com')
        self.assertEqual(result['owner'], 'owner')
        self.assertEqual(result['repo'], 'repo')

    def test_parse_github_https_no_git_extension(self):
        """Test parsing GitHub HTTPS URL without .git extension."""
        url = "https://github.com/owner/repo"
        result = parse_remote_url(url)

        self.assertEqual(result['host'], 'github.com')
        self.assertEqual(result['owner'], 'owner')
        self.assertEqual(result['repo'], 'repo')

    def test_parse_github_ssh(self):
        """Test parsing GitHub SSH URL."""
        url = "git@github.com:owner/repo.git"
        result = parse_remote_url(url)

        self.assertEqual(result['host'], 'github.com')
        self.assertEqual(result['owner'], 'owner')
        self.assertEqual(result['repo'], 'repo')

    def test_parse_github_ssh_no_git_extension(self):
        """Test parsing GitHub SSH URL without .git extension."""
        url = "git@github.com:owner/repo"
        result = parse_remote_url(url)

        self.assertEqual(result['host'], 'github.com')
        self.assertEqual(result['owner'], 'owner')
        self.assertEqual(result['repo'], 'repo')

    def test_parse_gitlab_https(self):
        """Test parsing GitLab HTTPS URL."""
        url = "https://gitlab.com/owner/repo.git"
        result = parse_remote_url(url)

        self.assertEqual(result['host'], 'gitlab.com')
        self.assertEqual(result['owner'], 'owner')
        self.assertEqual(result['repo'], 'repo')

    def test_parse_gitlab_ssh(self):
        """Test parsing GitLab SSH URL."""
        url = "git@gitlab.com:owner/repo.git"
        result = parse_remote_url(url)

        self.assertEqual(result['host'], 'gitlab.com')
        self.assertEqual(result['owner'], 'owner')
        self.assertEqual(result['repo'], 'repo')

    def test_parse_nested_owner_path(self):
        """Test parsing URL with nested owner path (e.g., groups/subgroups)."""
        url = "https://gitlab.com/group/subgroup/repo.git"
        result = parse_remote_url(url)

        self.assertEqual(result['host'], 'gitlab.com')
        self.assertEqual(result['owner'], 'group')
        self.assertEqual(result['repo'], 'subgroup')

    def test_invalid_host(self):
        """Test that unsupported hosts raise URLParseError."""
        url = "https://bitbucket.org/owner/repo.git"

        with self.assertRaises(URLParseError) as ctx:
            parse_remote_url(url)

        self.assertIn("Unsupported host", str(ctx.exception))

    def test_invalid_ssh_host(self):
        """Test that SSH URLs with unsupported hosts raise URLParseError."""
        url = "git@bitbucket.org:owner/repo.git"

        with self.assertRaises(URLParseError) as ctx:
            parse_remote_url(url)

        self.assertIn("Unsupported host", str(ctx.exception))

    def test_invalid_format(self):
        """Test that malformed URLs raise URLParseError."""
        url = "not-a-valid-url"

        with self.assertRaises(URLParseError):
            parse_remote_url(url)

    def test_missing_path_components(self):
        """Test that URLs without owner/repo raise URLParseError."""
        url = "https://github.com/owner"

        with self.assertRaises(URLParseError) as ctx:
            parse_remote_url(url)

        self.assertIn("Invalid path format", str(ctx.exception))


class TestGenerateCommitURL(unittest.TestCase):
    """Tests for generate_commit_url function."""

    def test_generate_github_commit_url_https(self):
        """Test generating commit URL from GitHub HTTPS remote."""
        remote = "https://github.com/owner/repo.git"
        sha = "abc123def456"

        url = generate_commit_url(remote, sha)

        self.assertEqual(url, "https://github.com/owner/repo/commit/abc123def456")

    def test_generate_github_commit_url_ssh(self):
        """Test generating commit URL from GitHub SSH remote."""
        remote = "git@github.com:owner/repo.git"
        sha = "abc123def456"

        url = generate_commit_url(remote, sha)

        self.assertEqual(url, "https://github.com/owner/repo/commit/abc123def456")

    def test_generate_gitlab_commit_url(self):
        """Test generating commit URL from GitLab remote."""
        remote = "https://gitlab.com/owner/repo.git"
        sha = "abc123def456"

        url = generate_commit_url(remote, sha)

        self.assertEqual(url, "https://gitlab.com/owner/repo/commit/abc123def456")

    def test_short_sha(self):
        """Test generating commit URL with short SHA."""
        remote = "https://github.com/owner/repo.git"
        sha = "abc123"

        url = generate_commit_url(remote, sha)

        self.assertEqual(url, "https://github.com/owner/repo/commit/abc123")

    def test_empty_sha_raises_error(self):
        """Test that empty SHA raises ValueError."""
        remote = "https://github.com/owner/repo.git"

        with self.assertRaises(ValueError) as ctx:
            generate_commit_url(remote, "")

        self.assertIn("Commit SHA cannot be empty", str(ctx.exception))

    def test_invalid_remote_raises_error(self):
        """Test that invalid remote URL raises URLParseError."""
        remote = "not-a-valid-url"
        sha = "abc123"

        with self.assertRaises(URLParseError):
            generate_commit_url(remote, sha)


class TestGenerateBranchURL(unittest.TestCase):
    """Tests for generate_branch_url function."""

    def test_generate_github_branch_url(self):
        """Test generating branch URL for GitHub."""
        remote = "https://github.com/owner/repo.git"
        branch = "feature/new-feature"

        url = generate_branch_url(remote, branch)

        self.assertEqual(url, "https://github.com/owner/repo/tree/feature/new-feature")

    def test_generate_gitlab_branch_url(self):
        """Test generating branch URL for GitLab."""
        remote = "https://gitlab.com/owner/repo.git"
        branch = "feature/new-feature"

        url = generate_branch_url(remote, branch)

        self.assertEqual(url, "https://gitlab.com/owner/repo/tree/feature/new-feature")

    def test_empty_branch_raises_error(self):
        """Test that empty branch name raises ValueError."""
        remote = "https://github.com/owner/repo.git"

        with self.assertRaises(ValueError) as ctx:
            generate_branch_url(remote, "")

        self.assertIn("Branch name cannot be empty", str(ctx.exception))


class TestGeneratePRURL(unittest.TestCase):
    """Tests for generate_pr_url function."""

    def test_generate_github_pr_url_with_number(self):
        """Test generating PR URL for existing GitHub PR."""
        remote = "https://github.com/owner/repo.git"
        pr_number = 123

        url = generate_pr_url(remote, pr_number)

        self.assertEqual(url, "https://github.com/owner/repo/pull/123")

    def test_generate_github_pr_url_new(self):
        """Test generating PR creation URL for GitHub."""
        remote = "https://github.com/owner/repo.git"

        url = generate_pr_url(remote)

        self.assertEqual(url, "https://github.com/owner/repo/compare")

    def test_generate_gitlab_mr_url_with_number(self):
        """Test generating MR URL for existing GitLab MR."""
        remote = "https://gitlab.com/owner/repo.git"
        mr_number = 456

        url = generate_pr_url(remote, mr_number)

        self.assertEqual(url, "https://gitlab.com/owner/repo/-/merge_requests/456")

    def test_generate_gitlab_mr_url_new(self):
        """Test generating MR creation URL for GitLab."""
        remote = "https://gitlab.com/owner/repo.git"

        url = generate_pr_url(remote)

        self.assertEqual(url, "https://gitlab.com/owner/repo/-/merge_requests/new")


if __name__ == '__main__':
    unittest.main()
