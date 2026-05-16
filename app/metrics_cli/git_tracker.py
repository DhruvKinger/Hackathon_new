from __future__ import annotations

import tarfile
from pathlib import Path
from typing import Dict, List

from git import InvalidGitRepositoryError, Repo
from git.exc import GitCommandError

from .metrics import LanguageAnalyzer, metrics_to_language_summary
from .models import CommitMetrics, MetricsResult


class GitTrackerError(Exception):
    """Raised for git history processing failures."""


class GitHistoryTracker:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        if not self.repo_path.exists() or not self.repo_path.is_dir():
            raise ValueError(f"Repository path does not exist: {repo_path}")

        self._restore_bundled_history_if_needed()

        try:
            self.repo = Repo(self.repo_path)
        except InvalidGitRepositoryError as exc:
            raise GitTrackerError(f"Not a git repository: {repo_path}") from exc

        self.analyzer = LanguageAnalyzer()

    def _restore_bundled_history_if_needed(self) -> None:
        """Restore git metadata for bundled sample_repo in fresh clones."""
        if (self.repo_path / ".git").exists():
            return

        archive = self.repo_path.parent / "sample_repo_git.tgz"
        if self.repo_path.name != "sample_repo" or not archive.exists():
            return

        try:
            with tarfile.open(archive, mode="r:gz") as tar:
                tar.extractall(self.repo_path)
            # Recreate working-tree files from restored git metadata.
            repo = Repo(self.repo_path)
            repo.git.reset("--hard", "HEAD")
        except (tarfile.TarError, OSError) as exc:
            raise GitTrackerError(f"Failed to restore bundled sample repo history: {exc}") from exc
        except (InvalidGitRepositoryError, GitCommandError) as exc:
            raise GitTrackerError(f"Failed to materialize sample repo files: {exc}") from exc

    def collect_history(self, depth: int = 50) -> List[CommitMetrics]:
        if depth < 1:
            depth = 1
        if depth > 500:
            depth = 500

        try:
            commits = list(self.repo.iter_commits("HEAD", max_count=depth))
        except GitCommandError as exc:
            raise GitTrackerError(str(exc)) from exc

        history: List[CommitMetrics] = []
        for commit in reversed(commits):
            language_totals: Dict[str, MetricsResult] = {}
            for blob in commit.tree.traverse():
                if blob.type != "blob":
                    continue

                file_path = blob.path
                language = self.analyzer.detect_language(file_path)
                if not language:
                    continue

                content = blob.data_stream.read().decode("utf-8", errors="ignore")
                metrics = self.analyzer.analyze_content(content, file_path, language)
                _merge_result(language_totals, language, metrics)

            summary = metrics_to_language_summary(language_totals)
            history_metrics = {
                language: {
                    "loc": values["loc"],
                    "cc_avg": values["cc_avg"],
                }
                for language, values in summary.items()
            }
            history.append(
                CommitMetrics(
                    commit=commit.hexsha,
                    date=commit.committed_datetime.isoformat(),
                    author=str(commit.author),
                    metrics=history_metrics,
                )
            )

        return history


def _merge_result(language_totals: Dict[str, MetricsResult], language: str, result: MetricsResult) -> None:
    existing = language_totals.get(language)
    if existing is None:
        language_totals[language] = MetricsResult(
            files=result.files,
            loc=result.loc,
            comment_lines=result.comment_lines,
            blank_lines=result.blank_lines,
            functions=list(result.functions),
        )
        return

    existing.files += result.files
    existing.loc += result.loc
    existing.comment_lines += result.comment_lines
    existing.blank_lines += result.blank_lines
    existing.functions.extend(result.functions)
