import json
import re
import subprocess
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

import requests


# ============================================================
# CONFIGURATION
# ============================================================

# IMPORTANT:
# Put your ACTUAL LEETCODE username here.
# Do NOT put your GitHub username unless they are the same.
USERNAME = "kl2400030372"

README_FILE = Path("README.md")
ASSETS_DIR = Path("assets")
HEATMAP_FILE = ASSETS_DIR / "leetcode-heatmap.svg"

LEETCODE_GRAPHQL = "https://leetcode.com/graphql"

START_MARKER = "<!-- LEETCODE_DASHBOARD_START -->"
END_MARKER = "<!-- LEETCODE_DASHBOARD_END -->"

HEADERS = {
    "Content-Type": "application/json",
    "Referer": "https://leetcode.com/",
    "User-Agent": "Mozilla/5.0",
}


# ============================================================
# GRAPHQL
# ============================================================

def leetcode_query(query, variables=None):
    response = requests.post(
        LEETCODE_GRAPHQL,
        headers=HEADERS,
        json={
            "query": query,
            "variables": variables or {},
        },
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if "errors" in data:
        raise RuntimeError(data["errors"])

    return data["data"]


# ============================================================
# LEETCODE PROFILE STATISTICS
# ============================================================

def get_leetcode_stats():
    query = """
    query userStats($username: String!) {
        allQuestionsCount {
            difficulty
            count
        }

        matchedUser(username: $username) {
            username

            profile {
                ranking
                reputation
                starRating
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
        }
    }
    """

    data = leetcode_query(
        query,
        {"username": USERNAME}
    )

    user = data.get("matchedUser")

    if not user:
        raise RuntimeError(
            f"LeetCode user '{USERNAME}' was not found. "
            "Check the USERNAME value in scripts/update_readme.py."
        )

    return data


# ============================================================
# SUBMISSION CALENDAR
# ============================================================

def get_submission_calendar(year):
    query = """
    query userCalendar($username: String!, $year: Int!) {
        matchedUser(username: $username) {
            userCalendar(year: $year) {
                activeYears
                streak
                totalActiveDays
                submissionCalendar
            }
        }
    }
    """

    data = leetcode_query(
        query,
        {
            "username": USERNAME,
            "year": year,
        }
    )

    user = data.get("matchedUser")

    if not user:
        return {}

    calendar = user.get("userCalendar")

    if not calendar:
        return {}

    raw = calendar.get("submissionCalendar", "{}")

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


# ============================================================
# PROBLEM METADATA
# ============================================================

def get_problem_metadata(slug):
    query = """
    query questionData($titleSlug: String!) {
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
            {"titleSlug": slug}
        )

        return data.get("question")

    except Exception:
        return None


# ============================================================
# FIND PROBLEM FOLDERS
# ============================================================

def find_problem_folders():
    problems = []

    ignored = {
        ".git",
        ".github",
        "scripts",
        "assets",
    }

    for item in Path(".").iterdir():

        if not item.is_dir():
            continue

        if item.name in ignored:
            continue

        match = re.match(
            r"^(\d+)-(.+)$",
            item.name
        )

        if not match:
            continue

        number = int(match.group(1))
        slug = match.group(2)

        problems.append({
            "number": number,
            "slug": slug,
            "folder": item,
        })

    problems.sort(
        key=lambda x: x["number"]
    )

    return problems


# ============================================================
# SOLUTION FILES
# ============================================================

def find_solution_files(folder):
    extensions = {
        ".java": "Java",
        ".py": "Python",
        ".cpp": "C++",
        ".c": "C",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".go": "Go",
        ".rs": "Rust",
        ".kt": "Kotlin",
        ".swift": "Swift",
    }

    results = []

    for file in folder.iterdir():

        if not file.is_file():
            continue

        if file.suffix.lower() in extensions:
            results.append(
                (
                    file,
                    extensions[file.suffix.lower()]
                )
            )

    return results


# ============================================================
# GIT DATE
# ============================================================

def get_problem_date(folder):
    try:
        result = subprocess.run(
            [
                "git",
                "log",
                "-1",
                "--format=%aI",
                "--",
                str(folder),
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        value = result.stdout.strip()

        if value:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            ).date()

    except Exception:
        pass

    return None


# ============================================================
# BUILD PROBLEM DATA
# ============================================================

def build_problem_data():

    folders = find_problem_folders()

    problems = []

    print(
        f"Found {len(folders)} problem folders."
    )

    for item in folders:

        print(
            f"Reading #{item['number']} - {item['slug']}"
        )

        metadata = get_problem_metadata(
            item["slug"]
        )

        if not metadata:
            print(
                f"Could not fetch metadata for "
                f"{item['slug']}"
            )
            continue

        solution_files = find_solution_files(
            item["folder"]
        )

        languages = sorted(
            {
                language
                for _, language in solution_files
            }
        )

        problems.append({
            "number": int(
                metadata["questionFrontendId"]
            ),
            "title": metadata["title"],
            "slug": metadata["titleSlug"],
            "difficulty": metadata["difficulty"],
            "topics": [
                tag["name"]
                for tag in metadata.get(
                    "topicTags",
                    []
                )
            ],
            "languages": languages,
            "folder": str(item["folder"]),
            "date": get_problem_date(
                item["folder"]
            ),
        })

    problems.sort(
        key=lambda x: x["number"]
    )

    return problems


# ============================================================
# FORMATTERS
# ============================================================

def difficulty_emoji(difficulty):

    if difficulty == "Easy":
        return "🟢"

    if difficulty == "Medium":
        return "🟡"

    return "🔴"


def progress_bar(value, maximum, length=20):

    if maximum <= 0:
        return "░" * length

    ratio = min(
        max(value / maximum, 0),
        1
    )

    filled = int(
        ratio * length
    )

    return (
        "█" * filled
        + "░" * (length - filled)
    )


def percentage(value, maximum):

    if maximum <= 0:
        return 0

    return round(
        value / maximum * 100,
        1
    )


def format_number(value):

    return f"{value:,}"


# ============================================================
# STREAK CALCULATION
# ============================================================

def calculate_streaks(calendar):

    active_dates = set()

    for timestamp in calendar:

        try:
            dt = datetime.fromtimestamp(
                int(timestamp)
            ).date()

            active_dates.add(dt)

        except Exception:
            continue

    if not active_dates:
        return 0, 0, active_dates

    sorted_dates = sorted(
        active_dates
    )

    longest = 1
    current_run = 1

    for i in range(
        1,
        len(sorted_dates)
    ):

        if (
            sorted_dates[i]
            == sorted_dates[i - 1]
            + timedelta(days=1)
        ):
            current_run += 1

        else:
            current_run = 1

        longest = max(
            longest,
            current_run
        )

    today = date.today()

    if today in active_dates:
        current = 0
        check = today

        while check in active_dates:
            current += 1
            check -= timedelta(days=1)

    elif (
        today - timedelta(days=1)
        in active_dates
    ):
        current = 0
        check = today - timedelta(days=1)

        while check in active_dates:
            current += 1
            check -= timedelta(days=1)

    else:
        current = 0

    return current, longest, active_dates


# ============================================================
# HEATMAP
# ============================================================

def generate_heatmap(calendar):

    ASSETS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    today = date.today()

    end_date = today

    # 52 weeks + alignment
    start_date = (
        end_date
        - timedelta(days=364)
    )

    start_date -= timedelta(
        days=(start_date.weekday() + 1) % 7
    )

    dates = []

    current = start_date

    while current <= end_date:

        dates.append(current)
        current += timedelta(days=1)

    counts = {}

    for timestamp, count in calendar.items():

        try:
            dt = datetime.fromtimestamp(
                int(timestamp)
            ).date()

            counts[dt] = int(count)

        except Exception:
            continue

    maximum = max(
        counts.values(),
        default=0
    )

    def level(count):

        if count <= 0:
            return 0

        if maximum <= 1:
            return 4

        ratio = count / maximum

        if ratio <= 0.25:
            return 1

        if ratio <= 0.50:
            return 2

        if ratio <= 0.75:
            return 3

        return 4

    cell = 12
    gap = 3

    weeks = []

    current = start_date

    while current <= end_date:

        week = []

        for day_index in range(7):

            day = current + timedelta(
                days=day_index
            )

            if day <= end_date:
                week.append(day)

        weeks.append(week)

        current += timedelta(days=7)

    width = len(weeks) * (
        cell + gap
    ) + 40

    height = 7 * (
        cell + gap
    ) + 30

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" '
        'fill="#0d1117"/>',
    ]

    # Day labels
    labels = [
        ("Mon", 1),
        ("Wed", 3),
        ("Fri", 5),
    ]

    for label, row in labels:

        y = 15 + row * (
            cell + gap
        )

        svg.append(
            f'<text x="0" y="{y}" '
            f'font-size="9" '
            f'fill="#8b949e">{label}</text>'
        )

    for week_index, week in enumerate(weeks):

        for day in week:

            row = (
                day.weekday()
            )

            x = 25 + week_index * (
                cell + gap
            )

            y = 5 + row * (
                cell + gap
            )

            count = counts.get(
                day,
                0
            )

            lvl = level(count)

            opacity = [
                "0.08",
                "0.25",
                "0.45",
                "0.70",
                "1.0",
            ][lvl]

            title = (
                f"{count} submission"
                + (
                    "s"
                    if count != 1
                    else ""
                )
                + f" on {day.isoformat()}"
            )

            svg.append(
                f'<rect x="{x}" y="{y}" '
                f'width="{cell}" height="{cell}" '
                f'rx="2" '
                f'fill="#39d353" '
                f'fill-opacity="{opacity}">'
                f'<title>{title}</title>'
                f'</rect>'
            )

    svg.append("</svg>")

    HEATMAP_FILE.write_text(
        "\n".join(svg),
        encoding="utf-8"
    )


# ============================================================
# DASHBOARD SECTIONS
# ============================================================

def stats_section(
    solved,
    total_submissions,
    acceptance,
    current_streak,
    longest_streak,
    active_days,
):

    return f"""
## 📊 LeetCode Statistics

| 🧩 Total Solved | 🟢 Easy | 🟡 Medium | 🔴 Hard |
|:---:|:---:|:---:|:---:|
| **{format_number(solved)}** | **{format_number(solved['Easy'])}** | **{format_number(solved['Medium'])}** | **{format_number(solved['Hard'])}** |

| 🔥 Current Streak | 🏆 Longest Streak | 📅 Active Days | 📤 Submissions | 🎯 Acceptance |
|:---:|:---:|:---:|:---:|:---:|
| **{current_streak} days** | **{longest_streak} days** | **{active_days}** | **{format_number(total_submissions)}** | **{acceptance}%** |
"""


def difficulty_section(
    solved,
    total_questions
):

    rows = []

    for difficulty, emoji in [
        ("Easy", "🟢"),
        ("Medium", "🟡"),
        ("Hard", "🔴"),
    ]:

        current = solved[difficulty]
        maximum = total_questions[difficulty]

        percent = percentage(
            current,
            maximum
        )

        bar = progress_bar(
            current,
            maximum,
            25
        )

        rows.append(
            f"| {emoji} **{difficulty}** "
            f"| **{current} / {maximum}** "
            f"| `{bar}` **{percent}%** |"
        )

    return f"""
## 🎯 Difficulty Progress

| Difficulty | Solved | Progress |
|:---|---:|:---|
{chr(10).join(rows)}
"""


def topic_section(topic_counts):

    if not topic_counts:
        return ""

    top_topics = topic_counts.most_common(
        15
    )

    maximum = top_topics[0][1]

    rows = []

    for topic, count in top_topics:

        bar = progress_bar(
            count,
            maximum,
            18
        )

        rows.append(
            f"| **{topic}** | {count} | "
            f"`{bar}` |"
        )

    return f"""
## 🧠 DSA Skills

| Topic | Problems | Distribution |
|:---|---:|:---|
{chr(10).join(rows)}
"""


def language_section(language_counts):

    if not language_counts:
        return ""

    total = sum(
        language_counts.values()
    )

    rows = []

    for language, count in language_counts.most_common():

        percent = percentage(
            count,
            total
        )

        bar = progress_bar(
            count,
            max(language_counts.values()),
            20
        )

        rows.append(
            f"| **{language}** | {count} | "
            f"`{bar}` {percent}% |"
        )

    return f"""
## 💻 Languages

| Language | Solutions | Usage |
|:---|---:|:---|
{chr(10).join(rows)}
"""


def milestone_section(total_solved):

    milestones = [
        1,
        10,
        25,
        50,
        100,
        150,
        200,
        300,
        500,
        1000,
    ]

    rows = []

    for milestone in milestones:

        if total_solved >= milestone:
            status = "✅ Completed"
        else:
            remaining = milestone - total_solved
            status = (
                f"🔒 {remaining} to go"
            )

        rows.append(
            f"| **{milestone} Problems** | {status} |"
        )

    return f"""
## 🏅 Milestones

| Milestone | Status |
|:---|:---|
{chr(10).join(rows)}
"""


def problem_section(problems):

    sections = []

    for difficulty in [
        "Easy",
        "Medium",
        "Hard",
    ]:

        selected = [
            p
            for p in problems
            if p["difficulty"] == difficulty
        ]

        if not selected:
            continue

        emoji = difficulty_emoji(
            difficulty
        )

        rows = []

        for p in selected:

            folder_link = (
                f"./{p['folder']}"
            )

            topics = ", ".join(
                p["topics"][:4]
            )

            languages = ", ".join(
                p["languages"]
            )

            rows.append(
                f"| **#{p['number']}** | "
                f"[{p['title']}]"
                f"({folder_link}) | "
                f"{topics or '—'} | "
                f"{languages or '—'} |"
            )

        sections.append(
            f"""
### {emoji} {difficulty}

| # | Problem | Topics | Language |
|:---:|:---|:---|:---|
{chr(10).join(rows)}
"""
        )

    return "\n".join(
        sections
    )


def recent_activity_section(problems):

    dated = [
        p
        for p in problems
        if p["date"] is not None
    ]

    dated.sort(
        key=lambda x: x["date"],
        reverse=True
    )

    recent = dated[:20]

    if not recent:
        return ""

    rows = []

    for p in recent:

        rows.append(
            f"| {p['date'].strftime('%d %b %Y')} "
            f"| {difficulty_emoji(p['difficulty'])} "
            f"| [{p['title']}]"
            f"(./{p['folder']}) |"
        )

    return f"""
## 📅 Recent Solved Problems

| Date | Level | Problem |
|:---|:---:|:---|
{chr(10).join(rows)}
"""


def monthly_progress_section(problems):

    dated = [
        p
        for p in problems
        if p["date"] is not None
    ]

    if not dated:
        return ""

    months = Counter(
        p["date"].strftime("%Y-%m")
        for p in dated
    )

    rows = []

    for month, count in sorted(
        months.items(),
        reverse=True
    )[:12]:

        rows.append(
            f"| **{month}** | {count} |"
        )

    return f"""
## 📈 Monthly Progress

| Month | Problems Solved |
|:---|---:|
{chr(10).join(rows)}
"""


# ============================================================
# README GENERATION
# ============================================================

def build_dashboard():

    print("Fetching LeetCode statistics...")

    data = get_leetcode_stats()

    user = data["matchedUser"]

    ac_stats = {
        item["difficulty"]: item
        for item in user[
            "submitStatsGlobal"
        ]["acSubmissionNum"]
    }

    total_stats = {
        item["difficulty"]: item
        for item in user[
            "submitStatsGlobal"
        ]["totalSubmissionNum"]
    }

    solved = {
        "Easy": ac_stats.get(
            "Easy",
            {}
        ).get("count", 0),

        "Medium": ac_stats.get(
            "Medium",
            {}
        ).get("count", 0),

        "Hard": ac_stats.get(
            "Hard",
            {}
        ).get("count", 0),
    }

    solved["All"] = (
        solved["Easy"]
        + solved["Medium"]
        + solved["Hard"]
    )

    total_submissions = (
        total_stats.get(
            "All",
            {}
        ).get("submissions", 0)
    )

    accepted_submissions = (
        ac_stats.get(
            "All",
            {}
        ).get("submissions", 0)
    )

    if total_submissions:
        acceptance = round(
            accepted_submissions
            / total_submissions
            * 100,
            1
        )
    else:
        acceptance = 0

    # Global LeetCode question counts
    total_questions = {}

    for item in data[
        "allQuestionsCount"
    ]:

        difficulty = item[
            "difficulty"
        ]

        if difficulty == "All":
            continue

        total_questions[
            difficulty
        ] = item["count"]

    for difficulty in [
        "Easy",
        "Medium",
        "Hard",
    ]:

        total_questions.setdefault(
            difficulty,
            0
        )

    print("Fetching submission calendar...")

    current_year = date.today().year

    calendar = {}

    for year in [
        current_year - 1,
        current_year,
    ]:

        calendar.update(
            get_submission_calendar(
                year
            )
        )

    current_streak, longest_streak, active_dates = (
        calculate_streaks(calendar)
    )

    generate_heatmap(calendar)

    print("Reading repository problems...")

    problems = build_problem_data()

    topic_counts = Counter()

    language_counts = Counter()

    for problem in problems:

        for topic in problem["topics"]:
            topic_counts[topic] += 1

        for language in problem["languages"]:
            language_counts[language] += 1

    # --------------------------------------------------------
    # Dashboard header
    # --------------------------------------------------------

    dashboard = f"""
{START_MARKER}

# 🧩 {USERNAME}'s LeetCode Journey

> Daily problem solving • Data Structures & Algorithms • Continuous improvement

---

{stats_section(
    solved,
    total_submissions,
    acceptance,
    current_streak,
    longest_streak,
    len(active_dates),
)}

## 🔥 Submission Activity

![LeetCode Submission Heatmap](./assets/leetcode-heatmap.svg)

---

{difficulty_section(
    solved,
    total_questions
)}

---

{topic_section(topic_counts)}

---

{language_section(language_counts)}

---

{monthly_progress_section(problems)}

---

{milestone_section(solved["All"])}

---

{recent_activity_section(problems)}

---

## 📚 Problems Solved

{problem_section(problems)}

---

### 🚀 Keep Solving

**{solved["All"]} problems solved.**

Every submission is another step toward stronger problem-solving skills.

{END_MARKER}
"""

    # --------------------------------------------------------
    # Preserve custom README content outside markers
    # --------------------------------------------------------

    if README_FILE.exists():

        old_readme = README_FILE.read_text(
            encoding="utf-8"
        )

    else:
        old_readme = ""

    if (
        START_MARKER in old_readme
        and END_MARKER in old_readme
    ):

        before = old_readme.split(
            START_MARKER,
            1
        )[0]

        after = old_readme.split(
            END_MARKER,
            1
        )[1]

        final_readme = (
            before.rstrip()
            + "\n\n"
            + dashboard.strip()
            + "\n\n"
            + after.lstrip()
        )

    else:

        final_readme = (
            dashboard.strip()
            + "\n"
        )

    README_FILE.write_text(
        final_readme,
        encoding="utf-8"
    )

    print(
        "README dashboard updated successfully."
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    if (
        USERNAME
        == "YOUR_LEETCODE_USERNAME"
    ):

        raise RuntimeError(
            "Set USERNAME to your actual "
            "LeetCode username first."
        )

    build_dashboard()
