from __future__ import annotations

import logging
import re
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from radon.complexity import cc_visit

from .models import FunctionMetrics, MetricsResult

LOGGER = logging.getLogger(__name__)

LANGUAGE_BY_EXTENSION = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".java": "Java",
    ".c": "C/C++",
    ".cc": "C/C++",
    ".cpp": "C/C++",
    ".h": "C/C++",
    ".hpp": "C/C++",
    ".go": "Go",
    ".rb": "Ruby",
}

C_LIKE_LANGUAGES = {"JavaScript", "TypeScript", "Java", "C/C++", "Go"}


class LanguageAnalyzer:
    """Analyze source files and compute LOC/comment/blank/CC metrics."""

    def detect_language(self, file_path: str) -> Optional[str]:
        return LANGUAGE_BY_EXTENSION.get(Path(file_path).suffix.lower())

    def scan_repository(self, repo_path: str) -> Tuple[Dict[str, MetricsResult], List[FunctionMetrics]]:
        root = Path(repo_path)
        language_totals: Dict[str, MetricsResult] = {}
        all_functions: List[FunctionMetrics] = []

        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            if ".git" in path.parts:
                continue

            language = self.detect_language(str(path))
            if not language:
                LOGGER.warning("Skipping unsupported extension: %s", path)
                continue

            relative_path = path.relative_to(root).as_posix()
            content = path.read_text(encoding="utf-8", errors="ignore")
            file_metrics = self.analyze_content(content, relative_path, language)
            merge_result(language_totals, language, file_metrics)
            all_functions.extend(file_metrics.functions)

        return language_totals, all_functions

    def analyze_content(self, content: str, file_path: str, language: Optional[str] = None) -> MetricsResult:
        language_name = language or self.detect_language(file_path)
        if not language_name:
            return MetricsResult()

        lines = content.splitlines()
        loc = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        comment_lines = self._count_comment_lines(lines, language_name)
        functions = self._extract_functions(content, file_path, language_name)

        return MetricsResult(
            files=1,
            loc=loc,
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            functions=functions,
        )

    def _count_comment_lines(self, lines: List[str], language: str) -> int:
        if language == "Python":
            return self._count_comments_python(lines)
        if language == "Ruby":
            return self._count_comments_ruby(lines)
        return self._count_comments_clike(lines)

    def _count_comments_python(self, lines: List[str]) -> int:
        count = 0
        in_multiline = False
        multi_delim = ""

        for raw_line in lines:
            line = raw_line.strip()
            if in_multiline:
                count += 1
                if multi_delim in line:
                    in_multiline = False
                    multi_delim = ""
                continue

            if not line:
                continue
            if line.startswith("#"):
                count += 1
                continue

            for delim in ('"""', "'''"):
                if line.startswith(delim):
                    count += 1
                    if line.count(delim) < 2:
                        in_multiline = True
                        multi_delim = delim
                    break

        return count

    def _count_comments_ruby(self, lines: List[str]) -> int:
        count = 0
        in_multiline = False

        for raw_line in lines:
            line = raw_line.strip()
            if in_multiline:
                count += 1
                if line.startswith("=end"):
                    in_multiline = False
                continue

            if not line:
                continue
            if line.startswith("#"):
                count += 1
                continue
            if line.startswith("=begin"):
                count += 1
                in_multiline = True

        return count

    def _count_comments_clike(self, lines: List[str]) -> int:
        count = 0
        in_multiline = False

        for raw_line in lines:
            line = raw_line.strip()
            if in_multiline:
                count += 1
                if "*/" in line:
                    in_multiline = False
                continue

            if not line:
                continue
            if line.startswith("//"):
                count += 1
                continue
            if "/*" in line:
                count += 1
                if "*/" not in line or line.index("/*") > line.index("*/"):
                    in_multiline = True

        return count

    def _extract_functions(self, content: str, file_path: str, language: str) -> List[FunctionMetrics]:
        if language == "Python":
            return self._extract_python_functions(content, file_path)
        if language in C_LIKE_LANGUAGES:
            return self._extract_brace_functions(content, file_path, language)
        if language == "Ruby":
            return self._extract_ruby_functions(content, file_path)
        return []

    def _extract_python_functions(self, content: str, file_path: str) -> List[FunctionMetrics]:
        functions: List[FunctionMetrics] = []
        for block in cc_visit(content):
            if hasattr(block, "name") and hasattr(block, "complexity"):
                functions.append(
                    FunctionMetrics(
                        file=file_path,
                        function=str(block.name),
                        language="Python",
                        cc=int(block.complexity),
                    )
                )
        return functions

    def _extract_brace_functions(self, content: str, file_path: str, language: str) -> List[FunctionMetrics]:
        patterns = [
            re.compile(r"\bfunction\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)\s*\{"),
            re.compile(r"\b(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\([^)]*\)\s*=>\s*\{"),
            re.compile(
                r"\b(?:public|private|protected|static|final|async|inline|virtual|constexpr|\s)+"
                r"[A-Za-z_][A-Za-z0-9_:<>\[\]*&\s]*\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^;{}]*\)\s*\{"
            ),
        ]

        results: List[FunctionMetrics] = []
        seen: set[Tuple[str, int]] = set()
        for pattern in patterns:
            for match in pattern.finditer(content):
                name = match.group(1)
                start_index = match.end() - 1
                body = self._extract_brace_block(content, start_index)
                if body is None:
                    continue

                key = (name, start_index)
                if key in seen:
                    continue
                seen.add(key)

                cc_value = self._compute_branch_complexity(body)
                results.append(
                    FunctionMetrics(
                        file=file_path,
                        function=name,
                        language=language,
                        cc=cc_value,
                    )
                )

        return results

    def _extract_ruby_functions(self, content: str, file_path: str) -> List[FunctionMetrics]:
        lines = content.splitlines()
        results: List[FunctionMetrics] = []
        i = 0
        while i < len(lines):
            match = re.match(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_!?=]*)", lines[i])
            if not match:
                i += 1
                continue

            name = match.group(1)
            block_lines = [lines[i]]
            depth = 1
            i += 1
            while i < len(lines) and depth > 0:
                current = lines[i]
                stripped = current.strip()
                if re.match(r"^(def|class|module|if|unless|case|begin|while|until|for|do)\b", stripped):
                    depth += 1
                if stripped == "end":
                    depth -= 1
                block_lines.append(current)
                i += 1

            body = "\n".join(block_lines)
            cc_value = self._compute_branch_complexity(body)
            results.append(
                FunctionMetrics(file=file_path, function=name, language="Ruby", cc=cc_value)
            )

        return results

    def _extract_brace_block(self, content: str, open_brace_idx: int) -> Optional[str]:
        if open_brace_idx < 0 or open_brace_idx >= len(content) or content[open_brace_idx] != "{":
            return None

        depth = 0
        for i in range(open_brace_idx, len(content)):
            if content[i] == "{":
                depth += 1
            elif content[i] == "}":
                depth -= 1
                if depth == 0:
                    return content[open_brace_idx : i + 1]

        return None

    def _compute_branch_complexity(self, function_body: str) -> int:
        branch_regex = re.compile(r"\b(if|else\s+if|for|while|case|catch|elif|unless|when)\b|\?")
        branch_count = len(branch_regex.findall(function_body))
        return max(1, 1 + branch_count)


def metrics_to_language_summary(language_totals: Dict[str, MetricsResult]) -> Dict[str, Dict[str, float]]:
    summary: Dict[str, Dict[str, float]] = {}
    for language, metrics in sorted(language_totals.items()):
        cc_values = [function.cc for function in metrics.functions]
        cc_avg = (sum(cc_values) / len(cc_values)) if cc_values else 0.0
        summary[language] = {
            "files": metrics.files,
            "loc": metrics.loc,
            "comment_lines": metrics.comment_lines,
            "blank_lines": metrics.blank_lines,
            "cc_avg": round(cc_avg, 4),
        }
    return summary


def function_list_to_dicts(functions: Iterable[FunctionMetrics]) -> List[Dict[str, object]]:
    return [asdict(function) for function in functions]


def merge_result(language_totals: Dict[str, MetricsResult], language: str, result: MetricsResult) -> None:
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
