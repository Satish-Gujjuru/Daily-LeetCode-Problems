import os
import re
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter, defaultdict

import requests


USERNAME = "Satish-Gujjuru"
README_FILE = Path("README.md")
ASSETS_DIR = Path("assets")
HEATMAP_FILE = ASSETS_DIR / "leetcode-heatmap.svg"

GRAPHQL_URL = "https://leetcode.com/graphql"


def leetcode_query(query, variables):
    response = requests.post(
        GRAPHQL_URL,
        json={
            "query": query,
            "variables": variables
        },
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        },
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    if "errors" in data:
        raise RuntimeError(data["errors"])

    return data["data"]


def get_leetcode_stats():
    query = """
    query UserStats($username: String!, $year: Int) {
        allQuestionsCount {
            difficulty
            count
        }

        matchedUser(username: $username) {
            username

            profile {
                ranking
                reputation
            }

            submitStatsGlobal {
                acSubmissionNum {
                    difficulty
                    count
                    submissions
                }

                totalSubmissionNum {
                    difficulty
                    count
                    submissions
                }
            }

            userCalendar(year: $year) {
                activeYears
                streak
                totalActiveDays
                submissionCalendar
            }
        }
    }
    """

    current_year = datetime.now(timezone.utc).year

    return leetcode_query(
        query,
        {
            "username": USERNAME,
            "year": current_year
        }
    )


def get_problem_details(slug):
    query = """
    query Problem($titleSlug: String!) {
        question(titleSlug: $titleSlug) {
            questionFrontendId
            title
            titleSlug
            difficulty

            topicTags {
                name
            }
        }
    }
    """

    try:
        data = leetcode_query(
            query,
            {
                "titleSlug": slug
            }
        )

        return data.get("question")

    except Exception:
        return None


def get_repository_problems():
    problems = []

    for path in Path(".").iterdir():

        if not path.is_dir():
            continue

        if path.name in {
            ".git",
            ".github",
            "scripts",
            "assets"
        }:
            continue

        match = re.match(r"^(\d+)-(.+)$", path.name)

        if not match:
            continue

        number = match.group(1)
        slug = match.group(2)

        details = get_problem_details(slug)

        if details:
            title = details["title"]
            difficulty = details["difficulty"]
            topics = [
                tag["name"]
                for tag in details.get("topicTags", [])
            ]
            problem_slug = details["titleSlug"]

        else:
            title = slug.replace("-", " ").title()
            difficulty = "Unknown"
            topics = []
            problem_slug = slug

        solution_files = []

        for file in path.iterdir():

            if file.name.lower() == "readme.md":
                continue

            if file.is_file():
                solution_files.append(file.name)

        github_url = (
            f"https://github.com/{USERNAME}/"
            f"Daily-LeetCode-Problems/tree/main/{path.name}"
        )

        try:
            result = subprocess.run(
                [
                    "git",
                    "log",
                    "-1",
                    "--format=%aI",
                    "--",
                    str(path)
                ],
                capture_output=True,
                text=True,
                check=True
            )

            date = result.stdout.strip()

        except Exception:
            date = ""

        problems.append({
            "number": int(number),
            "title": title,
            "slug": problem_slug,
            "difficulty": difficulty,
            "topics": topics,
            "folder": path.name,
            "github_url": github_url,
            "date": date,
            "files": solution_files
        })

    problems.sort(key=lambda x: x["number"])

    return problems


def calculate_streak(calendar):
    dates = []

    for timestamp, count in calendar.items():

        if int(count) <= 0:
            continue

        date = datetime.fromtimestamp(
            int(timestamp),
            tz=timezone.utc
        ).date()

        dates.append(date)

    dates = sorted(set(dates))

    if not dates:
        return 0, 0

    longest = 1
    current = 1

    for i in range(1, len(dates)):

        difference = (
            dates[i] - dates[i - 1]
        ).days

        if difference == 1:
            current += 1
        else:
            current = 1

        longest = max(longest, current)

    today = datetime.now(timezone.utc).date()

    if dates[-1] == today:
        current_streak = 1

        i = len(dates) - 1

        while i > 0:

            if (dates[i] - dates[i - 1]).days == 1:
                current_streak += 1
                i -= 1
            else:
                break

    elif (today - dates[-1]).days == 1:
        current_streak = 1

        i = len(dates) - 1

        while i > 0:

            if (dates[i] - dates[i - 1]).days == 1:
                current_streak += 1
                i -= 1
            else:
                break

    else:
        current_streak = 0

    return current_streak, longest


def create_heatmap(calendar):
    ASSETS_DIR.mkdir(exist_ok=True)

    values = {
        datetime.fromtimestamp(
            int(timestamp),
            tz=timezone.utc
        ).date(): int(count)

        for timestamp, count in calendar.items()
        if int(count) > 0
    }

    if not values:
        HEATMAP_FILE.write_text(
            "<svg xmlns='http://www.w3.org/2000/svg' "
            "width='900' height='100'></svg>"
        )
        return

    max_value = max(values.values())

    today = datetime.now(timezone.utc).date()

    start = today.replace(
        day=1,
        month=1
    )

    width = 900
    cell = 13
    gap = 3

    svg = []

    svg.append(
        f"<svg xmlns='http://www.w3.org/2000/svg' "
        f"width='{width}' height='180'>"
    )

    svg.append(
        "<rect width='100%' height='100%' "
        "rx='10' fill='#0d1117'/>"
    )

    for i in range(365):

        date = start.fromordinal(
            start.toordinal() + i
        )

        if date > today:
            break

        week = (
            date - start
        ).days // 7

        day = date.weekday()

        count = values.get(date, 0)

        if count == 0:
            fill = "#161b22"

        else:
            ratio = count / max_value

            if ratio < 0.25:
                fill = "#0e4429"
            elif ratio < 0.5:
                fill = "#006d32"
            elif ratio < 0.75:
                fill = "#26a641"
            else:
                fill = "#39d353"

        x = 45 + week * (cell + gap)
        y = 28 + day * (cell + gap)

        svg.append(
            f"<rect x='{x}' y='{y}' "
            f"width='{cell}' height='{cell}' "
            f"rx='2' fill='{fill}'>"
            f"<title>{date}: {count} submissions</title>"
            f"</rect>"
        )

    svg.append(
        "<text x='45' y='165' fill='#8b949e' "
        "font-size='12'>Less</text>"
    )

    for i, color in enumerate([
        "#161b22",
        "#0e4429",
        "#006d32",
        "#26a641",
        "#39d353"
    ]):

        x = 80 + i * 18

        svg.append(
            f"<rect x='{x}' y='155' "
            f"width='12' height='12' rx='2' "
            f"fill='{color}'/>"
        )

    svg.append(
        "<text x='180' y='165' fill='#8b949e' "
        "font-size='12'>More</text>"
    )

    svg.append("</svg>")

    HEATMAP_FILE.write_text(
        "\n".join(svg),
        encoding="utf-8"
    )


def progress_bar(value, maximum, length=24):

    if maximum == 0:
        filled = 0
    else:
        filled = round(
            (value / maximum) * length
        )

    filled = min(filled, length)

    return "█" * filled + "░" * (length - filled)


def generate_readme(stats, problems):

    user = stats["matchedUser"]

    solved = {
        item["difficulty"]: item["count"]
        for item in user["submitStatsGlobal"]["acSubmissionNum"]
    }

    total_submissions = {
        item["difficulty"]: item["submissions"]
        for item in user["submitStatsGlobal"]["totalSubmissionNum"]
    }

    all_questions = {
        item["difficulty"]: item["count"]
        for item in stats["allQuestionsCount"]
    }

    easy = solved.get("Easy", 0)
    medium = solved.get("Medium", 0)
    hard = solved.get("Hard", 0)

    total_solved = solved.get("All", easy + medium + hard)

    submissions = total_submissions.get(
        "All",
        0
    )

    accepted_submissions = (
        total_submissions.get("All", 0)
    )

    acceptance_rate = (
        (submissions and
         (solved.get("All", 0) / submissions) * 100)
        or 0
    )

    calendar = json.loads(
        user["userCalendar"]["submissionCalendar"]
    )

    current_streak, longest_streak = calculate_streak(
        calendar
    )

    create_heatmap(calendar)

    topic_counter = Counter()

    language_counter = Counter()

    for problem in problems:

        for topic in problem["topics"]:
            topic_counter[topic] += 1

        for file in problem["files"]:

            extension = Path(file).suffix.lower()

            languages = {
                ".java": "Java",
                ".py": "Python",
                ".cpp": "C++",
                ".c": "C",
                ".js": "JavaScript",
                ".ts": "TypeScript"
            }

            if extension in languages:
                language_counter[
                    languages[extension]
                ] += 1

    lines = []

    lines.append("# 🧠 LeetCode")
    lines.append("")
    lines.append(
        "### Daily LeetCode solutions, automatically tracked."
    )
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 📊 LeetCode Statistics")
    lines.append("")

    lines.append(
        "| 🧩 Problems Solved | 🟢 Easy | 🟡 Medium | 🔴 Hard |"
    )
    lines.append(
        "|:---:|:---:|:---:|:---:|"
    )
    lines.append(
        f"| **{total_solved}** | **{easy}** | "
        f"**{medium}** | **{hard}** |"
    )

    lines.append("")
    lines.append(
        "| 📈 Acceptance Rate | 🔥 Current Streak | "
        "🏆 Max Streak | 💻 Submissions |"
    )
    lines.append(
        "|:---:|:---:|:---:|:---:|"
    )
    lines.append(
        f"| **{acceptance_rate:.1f}%** | "
        f"**{current_streak} Days** | "
        f"**{longest_streak} Days** | "
        f"**{submissions}** |"
    )

    lines.append("")
    lines.append(
        f"> **Last Updated:** `{datetime.now().strftime('%d %b %Y, %H:%M UTC')}`"
    )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("# 📅 Submission Heatmap")
    lines.append("")
    lines.append(
        "![LeetCode Submission Heatmap]"
        "(./assets/leetcode-heatmap.svg)"
    )

    lines.append("")
    lines.append(
        f"**🔥 Current Streak:** `{current_streak} days`  "
    )
    lines.append(
        f"**🏆 Longest Streak:** `{longest_streak} days`  "
    )
    lines.append(
        f"**📅 Active Days:** "
        f"`{user['userCalendar']['totalActiveDays']}`"
    )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("# 🎯 Problem Solving Progress")
    lines.append("")
    lines.append("## Difficulty Breakdown")
    lines.append("")

    difficulty_data = [
        ("🟢 Easy", easy, all_questions.get("Easy", 0)),
        ("🟡 Medium", medium, all_questions.get("Medium", 0)),
        ("🔴 Hard", hard, all_questions.get("Hard", 0))
    ]

    for name, value, maximum in difficulty_data:

        lines.append(
            f"### {name}"
        )

        lines.append("")
        lines.append(
            f"**{value} / {maximum}**"
        )

        lines.append("")
        lines.append(
            f"`{progress_bar(value, maximum)}`"
        )

        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("# 📚 Problems Solved")
    lines.append("")

    for difficulty, emoji in [
        ("Easy", "🟢"),
        ("Medium", "🟡"),
        ("Hard", "🔴")
    ]:

        selected = [
            p for p in problems
            if p["difficulty"] == difficulty
        ]

        lines.append(
            f"## {emoji} {difficulty}"
        )

        lines.append("")
        lines.append(
            "| # | Problem | Topics | Solution |"
        )
        lines.append(
            "|---:|---|---|---|"
        )

        for index, problem in enumerate(
            selected,
            start=1
        ):

            topics = ", ".join(
                problem["topics"]
            ) or "—"

            lines.append(
                f"| {index} | "
                f"{problem['title']} | "
                f"{topics} | "
                f"[View](./{problem['folder']}) |"
            )

        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("# 🧩 Topics")
    lines.append("")

    lines.append(
        "| Topic | Problems |"
    )

    lines.append(
        "|---|---:|"
    )

    for topic, count in topic_counter.most_common():

        lines.append(
            f"| {topic} | {count} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("# 💻 Languages")
    lines.append("")

    lines.append(
        "| Language | Problems |"
    )

    lines.append(
        "|---|---:|"
    )

    for language, count in language_counter.most_common():

        lines.append(
            f"| {language} | {count} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("# 🗓️ Daily Submission History")
    lines.append("")

    lines.append(
        "| # | Date | Problem | Difficulty | Topics |"
    )

    lines.append(
        "|---:|---|---|:---:|---|"
    )

    for index, problem in enumerate(
        sorted(
            problems,
            key=lambda x: x["date"],
            reverse=True
        ),
        start=1
    ):

        date = problem["date"][:10]

        emoji = {
            "Easy": "🟢",
            "Medium": "🟡",
            "Hard": "🔴"
        }.get(
            problem["difficulty"],
            "⚪"
        )

        topics = ", ".join(
            problem["topics"]
        ) or "—"

        lines.append(
            f"| {index} | {date} | "
            f"[{problem['title']}]"
            f"({problem['github_url']}) | "
            f"{emoji} {problem['difficulty']} | "
            f"{topics} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("# 🧠 DSA Skills")
    lines.append("")
    lines.append(
        "### Data Structures"
    )
    lines.append("")
    lines.append(
        "`Arrays` `Strings` `HashMap` `HashSet` "
        "`Linked List` `Stack` `Queue` `Trees` "
        "`Graphs` `Heap` `Trie`"
    )

    lines.append("")
    lines.append(
        "### Algorithms & Patterns"
    )
    lines.append("")
    lines.append(
        "`Binary Search` `Two Pointers` "
        "`Sliding Window` `Recursion` "
        "`Backtracking` `Greedy` "
        "`Dynamic Programming` `Sorting`"
    )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(
        "### 🚀 One Problem Every Day"
    )
    lines.append("")
    lines.append(
        "**Learn → Solve → Optimize → Commit → Repeat**"
    )
    lines.append("")
    lines.append(
        "<p align='center'>"
        "<i>Dashboard automatically updated using "
        "LeetCode data and GitHub Actions.</i>"
        "</p>"
    )

    README_FILE.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )


def main():

    print("Fetching LeetCode statistics...")

    stats = get_leetcode_stats()

    print("Scanning repository problems...")

    problems = get_repository_problems()

    print(
        f"Found {len(problems)} problem folders."
    )

    generate_readme(
        stats,
        problems
    )

    print("README updated successfully.")


if __name__ == "__main__":
    main()
