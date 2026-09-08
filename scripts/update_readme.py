from pathlib import Path
from datetime import datetime, date, timedelta
from collections import Counter
import json
import math
import re
import subprocess
import time

import requests


# ============================================================
# CONFIGURATION
# ============================================================

USERNAME = "kl2400030372"

README = Path("README.md")
ASSETS = Path("assets")
HEATMAP = ASSETS / "leetcode-heatmap.svg"

LEETCODE_API = "https://leetcode.com/graphql"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/139 Safari/537.36"
    ),
    "Referer": "https://leetcode.com/",
}

IGNORE_DIRS = {
    ".git",
    ".github",
    "scripts",
    "assets",
    "__pycache__",
}


# ============================================================
# BASIC HELPERS
# ============================================================

def safe_int(value, default=0):
    """
    Safely convert a value to an integer.

    LeetCode sometimes returns nested dictionaries, so this
    function prevents the formatting error from the previous
    version.
    """
    if isinstance(value, dict):
        value = value.get("count", default)

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def format_number(value):
    """Format numbers with commas."""
    return f"{safe_int(value):,}"


def percentage(part, total):
    """Return a percentage string."""
    part = safe_int(part)
    total = safe_int(total)

    if total == 0:
        return "0.0%"

    return f"{(part / total) * 100:.1f}%"


def escape_markdown(text):
    """Prevent table-breaking characters."""
    return str(text).replace("|", "\\|").replace("\n", " ")


# ============================================================
# LEETCODE GRAPHQL
# ============================================================

def leetcode_query(query, variables=None):
    """
    Execute a LeetCode GraphQL query.

    Retries a few times because external APIs occasionally
    behave like external APIs.
    """

    for attempt in range(3):

        try:
            response = requests.post(
                LEETCODE_API,
                headers=HEADERS,
                json={
                    "query": query,
                    "variables": variables or {},
                },
                timeout=30,
            )

            response.raise_for_status()

            result = response.json()

            if result.get("errors"):
                raise RuntimeError(result["errors"])

            return result.get("data", {})

        except Exception:

            if attempt == 2:
                raise

            time.sleep(2)


# ============================================================
# GET MAIN LEETCODE STATISTICS
# ============================================================

def get_leetcode_stats():

    query = """
    query DashboardStats(
        $username: String!,
        $year: Int!
    ) {

        allQuestionsCount {
            difficulty
            count
        }

        matchedUser(username: $username) {

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

        userContestRanking(username: $username) {
            attendedContestsCount
            rating
            globalRanking
            topPercentage
            totalParticipants
        }
    }
    """

    data = leetcode_query(
        query,
        {
            "username": USERNAME,
            "year": datetime.now().year,
        },
    )

    if not data.get("matchedUser"):
        raise RuntimeError(
            f"LeetCode user '{USERNAME}' was not found."
        )

    return data


# ============================================================
# NORMALIZE LEETCODE DATA
# ============================================================

def normalize_stats(data):

    all_questions = {
        item["difficulty"]: safe_int(item.get("count"))
        for item in data.get("allQuestionsCount", [])
    }

    submit_stats = (
        data["matchedUser"]
        .get("submitStatsGlobal", {})
    )

    accepted_raw = submit_stats.get(
        "acSubmissionNum",
        [],
    )

    total_raw = submit_stats.get(
        "totalSubmissionNum",
        [],
    )

    accepted = {
        item["difficulty"]: {
            "count": safe_int(item.get("count")),
            "submissions": safe_int(
                item.get("submissions")
            ),
        }
        for item in accepted_raw
    }

    total = {
        item["difficulty"]: {
            "count": safe_int(item.get("count")),
            "submissions": safe_int(
                item.get("submissions")
            ),
        }
        for item in total_raw
    }

    difficulties = [
        "All",
        "Easy",
        "Medium",
        "Hard",
    ]

    solved = {}
    accepted_submissions = {}
    total_submissions = {}

    for difficulty in difficulties:

        accepted_data = accepted.get(
            difficulty,
            {},
        )

        total_data = total.get(
            difficulty,
            {},
        )

        solved[difficulty] = safe_int(
            accepted_data.get("count")
        )

        accepted_submissions[difficulty] = safe_int(
            accepted_data.get("submissions")
        )

        total_submissions[difficulty] = safe_int(
            total_data.get("submissions")
        )

    calendar_data = (
        data["matchedUser"].get("userCalendar")
        or {}
    )

    raw_calendar = calendar_data.get(
        "submissionCalendar",
        "{}",
    )

    try:

        if isinstance(raw_calendar, str):
            calendar = json.loads(raw_calendar)

        elif isinstance(raw_calendar, dict):
            calendar = raw_calendar

        else:
            calendar = {}

    except json.JSONDecodeError:

        calendar = {}

    normalized_calendar = {
        int(timestamp): safe_int(count)
        for timestamp, count in calendar.items()
    }

    return {
        "all_questions": all_questions,
        "solved": solved,
        "accepted_submissions": accepted_submissions,
        "total_submissions": total_submissions,
        "calendar": normalized_calendar,
        "calendar_meta": calendar_data,
        "contest": data.get("userContestRanking"),
    }


# ============================================================
# GET PROBLEM INFORMATION
# ============================================================

def get_problem_information(slug):

    query = """
    query Problem($slug: String!) {

        question(titleSlug: $slug) {

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
            {"slug": slug},
        )

        return data.get("question")

    except Exception as error:

        print(
            f"⚠️ Could not fetch problem '{slug}': {error}"
        )

        return None


# ============================================================
# GITHUB PROBLEM INFORMATION
# ============================================================

def get_git_date(folder):

    try:

        result = subprocess.check_output(
            [
                "git",
                "log",
                "-1",
                "--format=%aI",
                "--",
                str(folder),
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()

        if result:

            return datetime.fromisoformat(
                result.replace("Z", "+00:00")
            ).date()

    except Exception:
        pass

    return date.today()


# ============================================================
# LANGUAGE DETECTION
# ============================================================

LANGUAGE_MAP = {
    ".java": "Java",
    ".py": "Python",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".c": "C",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".kt": "Kotlin",
    ".cs": "C#",
    ".sql": "SQL",
}


def detect_languages(folder):

    languages = Counter()

    for file in folder.rglob("*"):

        if not file.is_file():
            continue

        if file.name.lower() == "readme.md":
            continue

        extension = file.suffix.lower()

        if extension in LANGUAGE_MAP:

            languages[LANGUAGE_MAP[extension]] += 1

    return dict(languages)


# ============================================================
# SCAN ALL PROBLEM FOLDERS
# ============================================================

def scan_problems():

    problems = []

    for folder in sorted(Path(".").iterdir()):

        if not folder.is_dir():
            continue

        if folder.name in IGNORE_DIRS:
            continue

        match = re.match(
            r"^(\d+)-(.+)$",
            folder.name,
        )

        if not match:
            continue

        number = int(match.group(1))
        slug = match.group(2)

        print(
            f"   Reading #{number} - {slug}"
        )

        metadata = get_problem_information(slug)

        if metadata:

            title = metadata.get(
                "title",
                slug.replace("-", " ").title(),
            )

            difficulty = metadata.get(
                "difficulty",
                "Unknown",
            )

            topics = [
                tag["name"]
                for tag in metadata.get(
                    "topicTags",
                    [],
                )
            ]

        else:

            title = slug.replace(
                "-",
                " ",
            ).title()

            difficulty = "Unknown"

            topics = []

        languages = detect_languages(folder)

        problems.append(
            {
                "number": number,
                "slug": slug,
                "title": title,
                "difficulty": difficulty,
                "topics": topics,
                "languages": languages,
                "date": get_git_date(folder),
                "path": folder.as_posix(),
            }
        )

    problems.sort(
        key=lambda problem: problem["number"]
    )

    return problems


# ============================================================
# STREAK CALCULATION
# ============================================================

def calculate_streaks(calendar):

    active_dates = set()

    for timestamp, count in calendar.items():

        if count <= 0:
            continue

        try:

            active_date = datetime.fromtimestamp(
                timestamp
            ).date()

            active_dates.add(active_date)

        except Exception:
            continue

    if not active_dates:
        return 0, 0, 0

    today = date.today()

    # Current streak
    current_streak = 0

    cursor = today

    while cursor in active_dates:

        current_streak += 1

        cursor -= timedelta(days=1)

    # If no submission today, continue from yesterday
    if current_streak == 0:

        cursor = today - timedelta(days=1)

        while cursor in active_dates:

            current_streak += 1

            cursor -= timedelta(days=1)

    # Longest streak
    longest_streak = 0
    running = 0
    previous = None

    for current_date in sorted(active_dates):

        if (
            previous is not None
            and current_date
            == previous + timedelta(days=1)
        ):

            running += 1

        else:

            running = 1

        longest_streak = max(
            longest_streak,
            running,
        )

        previous = current_date

    return (
        current_streak,
        longest_streak,
        len(active_dates),
    )


# ============================================================
# HEATMAP
# ============================================================

def heat_color(level):

    colors = [
        "#161b22",
        "#0e4429",
        "#006d32",
        "#26a641",
        "#39d353",
    ]

    level = max(
        0,
        min(4, level),
    )

    return colors[level]


def create_heatmap(calendar):
    import json
    from datetime import timezone

    ASSETS.mkdir(
        parents=True,
        exist_ok=True,
    )

    today = date.today()
    start = today - timedelta(days=364)

    # ------------------------------------------------------------
    # Convert LeetCode submission calendar timestamps to dates
    # ------------------------------------------------------------
    def calendar_to_dates(calendar_data):
        result = {}

        if isinstance(calendar_data, str):
            try:
                calendar_data = json.loads(calendar_data)
            except json.JSONDecodeError:
                return result

        if not isinstance(calendar_data, dict):
            return result

        for timestamp, count in calendar_data.items():
            try:
                dt = datetime.fromtimestamp(
                    int(timestamp),
                    tz=timezone.utc,
                ).date()

                result[dt] = safe_int(count)

            except (ValueError, TypeError, OverflowError):
                continue

        return result

    # ------------------------------------------------------------
    # Current-year data
    # ------------------------------------------------------------
    daily_submissions = calendar_to_dates(calendar)

    # ------------------------------------------------------------
    # Fetch previous-year data
    #
    # The normal dashboard query only requests the current year.
    # A rolling 365-day heatmap can cross the year boundary, so
    # we fetch the previous year's calendar here.
    # ------------------------------------------------------------
    previous_year_query = """
    query PreviousYearCalendar(
        $username: String!,
        $year: Int!
    ) {
        matchedUser(username: $username) {
            userCalendar(year: $year) {
                submissionCalendar
            }
        }
    }
    """

    try:
        previous_data = leetcode_query(
            previous_year_query,
            {
                "username": USERNAME,
                "year": today.year - 1,
            },
        )

        previous_calendar = (
            previous_data
            .get("matchedUser", {})
            .get("userCalendar", {})
            .get("submissionCalendar", {})
        )

        previous_dates = calendar_to_dates(
            previous_calendar
        )

        # Merge previous year into current year.
        for day, count in previous_dates.items():
            if start <= day <= today:
                daily_submissions[day] = count

    except Exception:
        # If the previous-year request fails, keep the
        # current-year data instead of breaking the whole README.
        pass

    # ------------------------------------------------------------
    # Build exactly the previous 365 days
    # ------------------------------------------------------------
    days = []

    current = start

    while current <= today:
        days.append(
            (
                current,
                daily_submissions.get(current, 0),
            )
        )

        current += timedelta(days=1)

    # ------------------------------------------------------------
    # Rolling-year statistics
    # ------------------------------------------------------------
    total_submissions = sum(
        count for _, count in days
    )

    active_days = sum(
        1
        for _, count in days
        if count > 0
    )

    max_streak = 0
    current_streak = 0

    for _, count in days:
        if count > 0:
            current_streak += 1
            max_streak = max(
                max_streak,
                current_streak,
            )
        else:
            current_streak = 0

    maximum = max(
        [count for _, count in days] + [1]
    )

    # ------------------------------------------------------------
    # LeetCode-style layout
    # ------------------------------------------------------------
    cell_size = 13
    gap = 4

    left = 34
    top = 65

    first_day = start

    # Sunday = 0, Monday = 1, ..., Saturday = 6
    leading_days = (
        first_day.weekday() + 1
    ) % 7

    total_cells = (
        leading_days + len(days)
    )

    weeks = math.ceil(
        total_cells / 7
    )

    width = max(
        980,
        left
        + weeks * (cell_size + gap)
        + 24,
    )

    height = 235

    svg = []

    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}">'
    )

    # Card background
    svg.append(
        '<rect '
        f'width="{width}" '
        f'height="{height}" '
        'rx="14" '
        'fill="#1f1f1f"/>'
    )

    # Subtle border
    svg.append(
        '<rect '
        f'x="0.5" y="0.5" '
        f'width="{width - 1}" '
        f'height="{height - 1}" '
        'rx="14" '
        'fill="none" '
        'stroke="#303030"/>'
    )

    # ------------------------------------------------------------
    # Header
    # ------------------------------------------------------------

    header_text = (
        f"{total_submissions} "
        "submissions in the past one year"
    )

    svg.append(
        '<text '
        'x="24" y="30" '
        'fill="#f0f0f0" '
        'font-size="17" '
        'font-family="Arial, Helvetica, sans-serif">'
        f'<tspan font-weight="700">'
        f'{total_submissions}'
        f'</tspan>'
        f'<tspan> submissions in the past one year</tspan>'
        '</text>'
    )

    # Info icon
    svg.append(
        '<circle '
        'cx="390" cy="25" '
        'r="8" '
        'fill="none" '
        'stroke="#8b8b8b" '
        'stroke-width="1.4"/>'
    )

    svg.append(
        '<text '
        'x="388" y="29" '
        'fill="#8b8b8b" '
        'font-size="10" '
        'font-family="Arial">'
        'i'
        '</text>'
    )

    # Right-side statistics
    stats_x = width - 330

    svg.append(
        f'<text '
        f'x="{stats_x}" y="30" '
        'fill="#8b8b8b" '
        'font-size="13" '
        'font-family="Arial">'
        'Total active days: '
        f'<tspan fill="#f0f0f0" font-weight="700">'
        f'{active_days}'
        f'</tspan>'
        '</text>'
    )

    svg.append(
        f'<text '
        f'x="{stats_x + 150}" y="30" '
        'fill="#8b8b8b" '
        'font-size="13" '
        'font-family="Arial">'
        'Max streak: '
        f'<tspan fill="#f0f0f0" font-weight="700">'
        f'{max_streak}'
        f'</tspan>'
        '</text>'
    )

    # Current dropdown-like control
    dropdown_x = width - 92

    svg.append(
        f'<rect '
        f'x="{dropdown_x}" y="48" '
        'width="68" height="30" '
        'rx="6" '
        'fill="#303030"/>'
    )

    svg.append(
        f'<text '
        f'x="{dropdown_x + 12}" y="68" '
        'fill="#f0f0f0" '
        'font-size="12" '
        'font-family="Arial">'
        'Current'
        '</text>'
    )

    svg.append(
        f'<path '
        f'd="M {dropdown_x + 51} 60 '
        f'l 5 5 l 5 -5" '
        'fill="none" '
        'stroke="#9b9b9b" '
        'stroke-width="1.4"/>'
    )

    # ------------------------------------------------------------
    # Month labels
    # ------------------------------------------------------------
    month_positions = {}

    for index, (day, _) in enumerate(days):
        position = leading_days + index
        column = position // 7

        key = (day.year, day.month)

        if key not in month_positions:
            month_positions[key] = column

    for (year, month), column in month_positions.items():
        month_name = datetime(
            year,
            month,
            1,
        ).strftime("%b")

        x = (
            left
            + column * (cell_size + gap)
        )

        svg.append(
            f'<text '
            f'x="{x}" y="201" '
            'fill="#9b9b9b" '
            'font-size="11" '
            'font-family="Arial">'
            f'{month_name}'
            '</text>'
        )

    # ------------------------------------------------------------
    # Heatmap cells
    # ------------------------------------------------------------
    for index, (day, count) in enumerate(days):

        position = (
            leading_days + index
        )

        column = position // 7
        row = position % 7

        x = (
            left
            + column * (cell_size + gap)
        )

        y = (
            top
            + row * (cell_size + gap)
        )

        if count <= 0:
            level = 0

        else:
            level = min(
                4,
                max(
                    1,
                    math.ceil(
                        count
                        / maximum
                        * 4
                    ),
                ),
            )

        if count == 1:
            submission_text = "1 submission"
        else:
            submission_text = (
                f"{count} submissions"
            )

        # Example:
        # 3 submissions on Sep 1, 2026
        tooltip = (
            f"{submission_text} on "
            f"{day.strftime('%b')} "
            f"{day.day}, "
            f"{day.year}"
        )

        svg.append(
            f'<rect '
            f'x="{x}" '
            f'y="{y}" '
            f'width="{cell_size}" '
            f'height="{cell_size}" '
            f'rx="3" '
            f'fill="{heat_color(level)}">'
            f'<title>{tooltip}</title>'
            f'</rect>'
        )

    # ------------------------------------------------------------
    # Legend
    # ------------------------------------------------------------
    legend_y = 225

    svg.append(
        '<text '
        'x="20" '
        f'y="{legend_y}" '
        'fill="#8b8b8b" '
        'font-size="11" '
        'font-family="Arial">'
        'Less'
        '</text>'
    )

    for level in range(5):

        x = (
            53
            + level * 18
        )

        svg.append(
            f'<rect '
            f'x="{x}" '
            f'y="{legend_y - 11}" '
            'width="12" '
            'height="12" '
            'rx="3" '
            f'fill="{heat_color(level)}"/>'
        )

    svg.append(
        '<text '
        f'x="153" '
        f'y="{legend_y}" '
        'fill="#8b8b8b" '
        'font-size="11" '
        'font-family="Arial">'
        'More'
        '</text>'
    )

    svg.append("</svg>")

    HEATMAP.write_text(
        "\n".join(svg),
        encoding="utf-8",
    )


# ============================================================
# DIFFICULTY PROGRESS BAR
# ============================================================

def progress_bar(solved, total, width=24):

    solved = safe_int(solved)
    total = safe_int(total)

    if total == 0:
        return "░" * width

    ratio = solved / total

    filled = round(
        ratio * width
    )

    return (
        "█" * filled
        + "░" * (width - filled)
    )


# ============================================================
# STATISTICS SECTION
# ============================================================

def build_statistics_section(
    stats,
    problems,
):

    solved = stats["solved"]

    accepted = stats[
        "accepted_submissions"
    ]["All"]

    total = stats[
        "total_submissions"
    ]["All"]

    current_streak, longest_streak, active_days = (
        calculate_streaks(
            stats["calendar"]
        )
    )

    easy_total = stats[
        "all_questions"
    ].get("Easy", 0)

    medium_total = stats[
        "all_questions"
    ].get("Medium", 0)

    hard_total = stats[
        "all_questions"
    ].get("Hard", 0)

    return f"""
## 📊 LeetCode Statistics

| Metric | Value |
|---|---:|
| 🧩 **Problems Solved** | **{format_number(solved["All"])}** |
| 🟢 Easy | {format_number(solved["Easy"])} / {format_number(easy_total)} |
| 🟡 Medium | {format_number(solved["Medium"])} / {format_number(medium_total)} |
| 🔴 Hard | {format_number(solved["Hard"])} / {format_number(hard_total)} |
| 🎯 Acceptance Rate | **{percentage(accepted, total)}** |
| 🔥 Current Streak | **{current_streak} days** |
| 🏆 Longest Streak | **{longest_streak} days** |
| 📅 Active Days | **{active_days}** |
| 📁 Problems in Repository | **{len(problems)}** |

### Difficulty Progress

| Difficulty | Progress | Completion |
|---|---|---:|
| 🟢 Easy | `{progress_bar(solved["Easy"], easy_total)}` | {percentage(solved["Easy"], easy_total)} |
| 🟡 Medium | `{progress_bar(solved["Medium"], medium_total)}` | {percentage(solved["Medium"], medium_total)} |
| 🔴 Hard | `{progress_bar(solved["Hard"], hard_total)}` | {percentage(solved["Hard"], hard_total)} |
"""


# ============================================================
# CONTEST SECTION
# ============================================================

def build_contest_section(stats):

    contest = stats.get("contest")

    if not contest:
        return ""

    rating = safe_int(
        contest.get("rating")
    )

    ranking = safe_int(
        contest.get("globalRanking")
    )

    contests = safe_int(
        contest.get(
            "attendedContestsCount"
        )
    )

    top = contest.get(
        "topPercentage"
    )

    if top is not None:

        try:
            top_text = (
                f"{float(top):.2f}%"
            )

        except (
            TypeError,
            ValueError,
        ):
            top_text = "N/A"

    else:

        top_text = "N/A"

    return f"""
## 🏁 Contest Profile

| Rating | Global Rank | Top Percentage | Contests |
|---:|---:|---:|---:|
| **{rating:,}** | **{ranking:,}** | **{top_text}** | **{contests}** |
"""


# ============================================================
# RECENT PROBLEMS
# ============================================================

def build_recent_section(problems):

    recent = sorted(
        problems,
        key=lambda p: p["date"],
        reverse=True,
    )[:10]

    if not recent:
        return ""

    icons = {
        "Easy": "🟢",
        "Medium": "🟡",
        "Hard": "🔴",
        "Unknown": "⚪",
    }

    rows = [
        "## 🕐 Recently Added",
        "",
        "| Problem | Difficulty | Date |",
        "|---|---|---|",
    ]

    for problem in recent:

        rows.append(
            f'| [{problem["number"]}. '
            f'{escape_markdown(problem["title"])}]'
            f'(./{problem["path"]}) | '
            f'{icons.get(problem["difficulty"], "⚪")} '
            f'{problem["difficulty"]} | '
            f'{problem["date"]} |'
        )

    return "\n".join(rows)


# ============================================================
# ALL PROBLEMS SECTION
# ============================================================

def build_problems_section(problems):

    groups = {
        "Easy": [],
        "Medium": [],
        "Hard": [],
        "Unknown": [],
    }

    for problem in problems:

        groups.setdefault(
            problem["difficulty"],
            [],
        ).append(problem)

    sections = [
        "## 🧩 Problems Solved",
        "",
    ]

    order = [
        ("Easy", "🟢"),
        ("Medium", "🟡"),
        ("Hard", "🔴"),
        ("Unknown", "⚪"),
    ]

    for difficulty, icon in order:

        items = groups.get(
            difficulty,
            [],
        )

        if not items:
            continue

        sections.append(
            f"### {icon} {difficulty} "
            f"({len(items)})"
        )

        sections.append("")

        sections.append(
            "| # | Problem | Topics | Solution | Date |"
        )

        sections.append(
            "|---:|---|---|---|---|"
        )

        for problem in sorted(
            items,
            key=lambda p: p["number"],
        ):

            topics = ", ".join(
                problem["topics"][:4]
            )

            if not topics:
                topics = "—"

            sections.append(
                f'| {problem["number"]} | '
                f'**{escape_markdown(problem["title"])}** | '
                f'{escape_markdown(topics)} | '
                f'[Open](./{problem["path"]}) | '
                f'{problem["date"]} |'
            )

        sections.append("")

    return "\n".join(sections)


# ============================================================
# TOPICS SECTION
# ============================================================

def build_topics_section(problems):

    topics = Counter()

    for problem in problems:

        topics.update(
            problem["topics"]
        )

    if not topics:
        return ""

    rows = [
        "## 🧠 Top Topics",
        "",
        "| Topic | Problems |",
        "|---|---:|",
    ]

    for topic, count in topics.most_common(15):

        rows.append(
            f"| {escape_markdown(topic)} | {count} |"
        )

    return "\n".join(rows)


# ============================================================
# LANGUAGES SECTION
# ============================================================

def build_languages_section(problems):

    languages = Counter()

    for problem in problems:

        languages.update(
            problem["languages"]
        )

    if not languages:
        return ""

    rows = [
        "## 💻 Languages Used",
        "",
        "| Language | Solutions |",
        "|---|---:|",
    ]

    for language, count in languages.most_common():

        rows.append(
            f"| {language} | {count} |"
        )

    return "\n".join(rows)


# ============================================================
# 30-DAY ACTIVITY
# ============================================================

def build_activity_section(stats):

    calendar = stats["calendar"]

    if not calendar:
        return ""

    today = date.today()

    start = today - timedelta(days=29)

    rows = [
        "## 📅 Last 30 Days",
        "",
        "| Date | Submissions |",
        "|---|---:|",
    ]

    current = start

    while current <= today:

        timestamp = int(
            datetime(
                current.year,
                current.month,
                current.day,
            ).timestamp()
        )

        count = calendar.get(
            timestamp,
            0,
        )

        rows.append(
            f"| {current.isoformat()} | {count} |"
        )

        current += timedelta(days=1)

    return "\n".join(rows)


# ============================================================
# COMPLETE README
# ============================================================

def build_readme(
    stats,
    problems,
):

    solved = stats["solved"]

    current_streak, longest_streak, _ = (
        calculate_streaks(
            stats["calendar"]
        )
    )

    generated = datetime.now().strftime(
        "%d %b %Y, %H:%M"
    )

    statistics = build_statistics_section(
        stats,
        problems,
    )

    contest = build_contest_section(
        stats
    )

    recent = build_recent_section(
        problems
    )

    all_problems = build_problems_section(
        problems
    )

    topics = build_topics_section(
        problems
    )

    languages = build_languages_section(
        problems
    )

    activity = build_activity_section(
        stats
    )

    return f"""# 🧑‍💻 Satish's LeetCode Journey

<p align="center">
  <img
    src="./assets/leetcode-heatmap.svg"
    alt="LeetCode submission heatmap"
    width="950"
  />
</p>

<p align="center">
  <b>Daily LeetCode practice, automatically tracked through GitHub.</b>
  <br>
  Accepted solutions synced by LeetSync are reflected in this dashboard.
</p>

---

## ⚡ Quick Overview

| 🧩 Solved | 🟢 Easy | 🟡 Medium | 🔴 Hard | 🔥 Streak | 🏆 Best Streak |
|---:|---:|---:|---:|---:|---:|
| **{format_number(solved["All"])}** | **{format_number(solved["Easy"])}** | **{format_number(solved["Medium"])}** | **{format_number(solved["Hard"])}** | **{current_streak} days** | **{longest_streak} days** |

---

{statistics}

{contest}

{recent}

{all_problems}

{topics}

{languages}

{activity}

---

## 🔗 Profiles

- 🟧 [LeetCode](https://leetcode.com/u/{USERNAME}/)
- 🐙 [GitHub](https://github.com/{USERNAME})

---

<p align="center">
  <sub>
    🤖 Automatically updated by GitHub Actions
    <br>
    Last update: {generated}
  </sub>
</p>
"""


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "🚀 Building LeetCode dashboard..."
    )

    print(
        "📡 Fetching LeetCode statistics..."
    )

    raw_data = get_leetcode_stats()

    stats = normalize_stats(
        raw_data
    )

    print(
        "📅 Reading submission calendar..."
    )

    print(
        "📁 Scanning solved-problem folders..."
    )

    problems = scan_problems()

    print(
        f"   Found {len(problems)} problem folders."
    )

    print(
        "🔥 Creating submission heatmap..."
    )

    create_heatmap(
        stats["calendar"]
    )

    print(
        "📝 Generating README..."
    )

    README.write_text(
        build_readme(
            stats,
            problems,
        ),
        encoding="utf-8",
    )

    print(
        "✅ Dashboard generated successfully!"
    )

    print(
        f"   Total solved : {stats['solved']['All']}"
    )

    print(
        f"   Easy         : {stats['solved']['Easy']}"
    )

    print(
        f"   Medium       : {stats['solved']['Medium']}"
    )

    print(
        f"   Hard         : {stats['solved']['Hard']}"
    )

    print(
        f"   GitHub folders: {len(problems)}"
    )


if __name__ == "__main__":
    main()
