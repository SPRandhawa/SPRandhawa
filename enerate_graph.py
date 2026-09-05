import datetime
import os
import requests

# Fetch contribution history via GitHub GraphQL API
TOKEN = os.getenv("GITHUB_TOKEN")
USERNAME = "SPRandhawa"

query = """
query($username: String!) {
  user(login: $username) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

url = "https://api.github.com/graphql"
headers = {"Authorization": f"Bearer {TOKEN}"}
response = requests.post(
    url, json={"query": query, "variables": {"username": USERNAME}}, headers=headers
)

data = response.json()
weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"][
    "weeks"
]

# Aggregate total contributions per month for a clean line graph
monthly_counts = {}
for week in weeks:
    for day in week["contributionDays"]:
        month_key = day["date"][:7]  # YYYY-MM
        monthly_counts[month_key] = (
            monthly_counts.get(month_key, 0) + day["contributionCount"]
        )

# Get sorted last 12 months data
sorted_months = sorted(monthly_counts.keys())[-12:]
counts = [monthly_counts[m] for m in sorted_months]
labels = [
    datetime.datetime.strptime(m, "%Y-%m").strftime("%b") for m in sorted_months
]

# SVG Dimensions & Styling
width, height = 800, 300
padding_x, padding_y = 60, 50
graph_w = width - (padding_x * 2)
graph_h = height - (padding_y * 2)

max_val = max(counts) if counts and max(counts) > 0 else 10

# Calculate SVG Points for the Line
points = []
for i, val in enumerate(counts):
    x = padding_x + (i * (graph_w / (len(counts) - 1)))
    y = (height - padding_y) - ((val / max_val) * graph_h)
    points.append((x, y))

points_str = " ".join([f"{x:.1f},{y:.1f}" for x, y in points])

# Create Gradient Area Under Line
first_x, last_x = points[0][0], points[-1][0]
baseline_y = height - padding_y
area_points = f"{first_x:.1f},{baseline_y} {points_str} {last_x:.1f},{baseline_y}"

# Generate SVG String matching your dark (#0d1117) and cyan (#00f5ff) theme
svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#00f5ff" stop-opacity="0.3"/>
      <stop offset="100%" stop-color="#00f5ff" stop-opacity="0.0"/>
    </linearGradient>
  </defs>

  <!-- Background Card -->
  <rect width="100%" height="100%" rx="10" fill="#0d1117" />
  
  <!-- Title -->
  <text x="30" y="35" fill="#00f5ff" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="18" font-weight="bold">Contributions Activity</text>

  <!-- Area Gradient -->
  <polygon points="{area_points}" fill="url(#areaGrad)" />

  <!-- Connection Line -->
  <polyline fill="none" stroke="#00b4d8" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" points="{points_str}" />

  <!-- Data Points & Labels -->
"""

for i, (x, y) in enumerate(points):
    svg_content += f'  <circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#ffffff" stroke="#00f5ff" stroke-width="2" />\n'
    svg_content += f'  <text x="{x:.1f}" y="{height - 20}" fill="#a0e9ff" font-family="sans-serif" font-size="12" text-anchor="middle">{labels[i]}</text>\n'

svg_content += "</svg>"

# Save SVG file
with open("my-activity-graph.svg", "w") as f:
    f.write(svg_content)
