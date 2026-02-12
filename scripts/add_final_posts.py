#!/usr/bin/env python3
"""
Add final 24 posts to reach 100+ total for better clustering.
Focus on domains that need more coverage.
"""

import json
from datetime import datetime, timedelta

# Final 24 posts for better clustering
final_posts = [
    # Entertainment (4 posts)
    {
        "url": "https://reddit.com/r/Music/comments/music001",
        "title": "Need a music discovery app that creates genre-transition playlists based on my mood progression",
        "content": "I want to start with upbeat pop, gradually transition to indie rock, then end with chill lo-fi. Current apps just shuffle or play similar songs. I need intelligent transitions that match my energy levels throughout the day. Like a DJ for my emotions.",
        "source": "reddit",
        "author": "playlist_curator",
        "published_at": (datetime.now() - timedelta(days=4)).isoformat() + "Z",
        "metadata": {
            "upvotes": 678,
            "comments": 234,
            "domain": "entertainment",
            "subreddit": "Music",
            "tags": ["music", "discovery", "mood", "playlists", "ai"],
        },
    },
    {
        "url": "https://twitter.com/movie_buff/status/1234570020",
        "title": "Why isn't there a movie recommendation engine that learns from watch history across all streaming services?",
        "content": "I have Netflix, Hulu, Disney+, Prime, and HBO. Each has its own algorithm. I want ONE app that knows what I've watched everywhere, understands my taste patterns, and suggests movies from ALL platforms. Cross-platform taste graph.",
        "source": "twitter",
        "author": "streaming_optimizer",
        "published_at": (datetime.now() - timedelta(days=8)).isoformat() + "Z",
        "metadata": {
            "likes": 892,
            "retweets": 334,
            "domain": "entertainment",
            "tags": ["movies", "streaming", "recommendation", "cross-platform", "ai"],
        },
    },
    {
        "url": "https://news.ycombinator.com/item?id=39902017",
        "title": "Someone build a live concert discovery app that uses location + music taste + schedule sync",
        "content": "I miss great concerts because I don't know they're happening. Track my Spotify taste, check my calendar for free slots, alert me when favorite artists are in town. Auto-suggest similar artists I'd love. Never miss a show again.",
        "source": "hackernews",
        "author": "concert_lover",
        "published_at": (datetime.now() - timedelta(days=11)).isoformat() + "Z",
        "metadata": {
            "upvotes": 456,
            "comments": 167,
            "domain": "entertainment",
            "tags": ["concerts", "music", "location", "calendar", "discovery"],
        },
    },
    {
        "url": "https://reddit.com/r/television/comments/tv001",
        "title": "I wish there was a binge-watching optimizer that schedules TV episodes around my calendar gaps",
        "content": "I start shows but never finish. I want an app that knows how long each episode is, finds gaps in my calendar, and schedules viewing sessions. 'You have 47 minutes before your meeting - perfect for episode 3'. Optimize entertainment consumption.",
        "source": "reddit",
        "author": "efficient_viewer",
        "published_at": (datetime.now() - timedelta(days=15)).isoformat() + "Z",
        "metadata": {
            "upvotes": 723,
            "comments": 198,
            "domain": "entertainment",
            "subreddit": "television",
            "tags": [
                "tv",
                "binge-watching",
                "scheduling",
                "time-management",
                "calendar",
            ],
        },
    },
    # Fitness & Health (4 posts)
    {
        "url": "https://reddit.com/r/Fitness/comments/fit001",
        "title": "Need a form checker app that uses phone camera to analyze my lifting technique in real-time",
        "content": "Bad form causes injuries. Use computer vision to track my squat depth, bar path, knee alignment. Give real-time audio cues: 'chest up', 'deeper'. Record sets, show progress over time. AI personal trainer for home workouts.",
        "source": "reddit",
        "author": "home_gym_enthusiast",
        "published_at": (datetime.now() - timedelta(days=6)).isoformat() + "Z",
        "metadata": {
            "upvotes": 834,
            "comments": 267,
            "domain": "fitness",
            "subreddit": "Fitness",
            "tags": ["fitness", "form-check", "computer-vision", "weightlifting", "ai"],
        },
    },
    {
        "url": "https://twitter.com/runner_tech/status/1234570021",
        "title": "Why isn't there a running app that predicts injury risk using gait analysis from phone sensors?",
        "content": "Overuse injuries sideline runners for months. Use phone accelerometer to analyze gait asymmetry, impact forces, cadence. Predict injury risk before pain starts. Suggest recovery days or form adjustments. Preventive running analytics.",
        "source": "twitter",
        "author": "running_scientist",
        "published_at": (datetime.now() - timedelta(days=10)).isoformat() + "Z",
        "metadata": {
            "likes": 567,
            "retweets": 189,
            "domain": "fitness",
            "tags": [
                "running",
                "injury-prevention",
                "gait-analysis",
                "sensors",
                "predictive",
            ],
        },
    },
    {
        "url": "https://news.ycombinator.com/item?id=39902018",
        "title": "Someone build a meal prep service that optimizes for macros + taste preferences + budget",
        "content": "Hitting macros with food I actually enjoy is hard. AI-generated meal plans: input protein/carbs/fats targets, dietary restrictions, favorite ingredients, budget. Get 7-day plan with grocery list and prep instructions. Bodybuilding nutrition made easy.",
        "source": "hackernews",
        "author": "macro_tracker",
        "published_at": (datetime.now() - timedelta(days=13)).isoformat() + "Z",
        "metadata": {
            "upvotes": 712,
            "comments": 245,
            "domain": "fitness",
            "tags": [
                "nutrition",
                "meal-prep",
                "macros",
                "optimization",
                "bodybuilding",
            ],
        },
    },
    {
        "url": "https://reddit.com/r/yoga/comments/yoga001",
        "title": "I wish there was a yoga practice app that adapts sequences based on energy levels and tight spots",
        "content": "Generic yoga videos don't address my needs. Start each session: rate energy (1-10), mark tight areas (hamstrings, shoulders). AI generates custom sequence targeting those areas at appropriate intensity. Dynamic, personalized yoga.",
        "source": "reddit",
        "author": "adaptive_yogi",
        "published_at": (datetime.now() - timedelta(days=17)).isoformat() + "Z",
        "metadata": {
            "upvotes": 645,
            "comments": 178,
            "domain": "fitness",
            "subreddit": "yoga",
            "tags": ["yoga", "personalization", "flexibility", "adaptive", "wellness"],
        },
    },
    # Education & Learning (4 posts)
    {
        "url": "https://news.ycombinator.com/item?id=39902019",
        "title": "Need a knowledge graph builder that connects everything I learn from books, courses, and articles",
        "content": "I forget connections between concepts. Automatically extract key ideas from my Kindle highlights, course notes, articles I read. Build a personal knowledge graph. See relationships, surface forgotten insights. Second brain with AI.",
        "source": "hackernews",
        "author": "knowledge_worker",
        "published_at": (datetime.now() - timedelta(days=5)).isoformat() + "Z",
        "metadata": {
            "upvotes": 923,
            "comments": 312,
            "domain": "education",
            "tags": ["learning", "knowledge-graph", "note-taking", "ai", "connections"],
        },
    },
    {
        "url": "https://reddit.com/r/languagelearning/comments/lang001",
        "title": "Why isn't there a language exchange app that uses AI to match conversation partners by learning goals and schedule?",
        "content": "Finding compatible language partners is hit-or-miss. Match by: target language, proficiency level, learning style (casual vs structured), available times, interests. Auto-suggest conversation topics. Schedule recurring sessions. Duolingo meets Tinder.",
        "source": "reddit",
        "author": "polyglot_connector",
        "published_at": (datetime.now() - timedelta(days=9)).isoformat() + "Z",
        "metadata": {
            "upvotes": 756,
            "comments": 234,
            "domain": "education",
            "subreddit": "languagelearning",
            "tags": [
                "language-learning",
                "exchange",
                "matchmaking",
                "conversation",
                "schedule",
            ],
        },
    },
    {
        "url": "https://twitter.com/online_learner/status/1234570022",
        "title": "Someone build a course completion accountability system with social pressure and money at stake",
        "content": "I buy courses and never finish. Join a cohort, put $100 on the line. Complete weekly milestones or money goes to charity. Peer accountability through group chat. Get refund + bonus if you finish. Financial motivation for online learning.",
        "source": "twitter",
        "author": "course_completer",
        "published_at": (datetime.now() - timedelta(days=14)).isoformat() + "Z",
        "metadata": {
            "likes": 834,
            "retweets": 289,
            "domain": "education",
            "tags": [
                "online-learning",
                "accountability",
                "gamification",
                "motivation",
                "cohort",
            ],
        },
    },
    {
        "url": "https://news.ycombinator.com/item?id=39902020",
        "title": "I wish there was a skill tree visualizer for career paths showing prerequisites and time estimates",
        "content": "Career development feels overwhelming. Show skills as a tree: 'To become Senior Engineer, you need: System Design (6 months) + Team Leadership (3 months) + Domain Expertise (1 year)'. Track progress, suggest learning resources. RPG-style career planning.",
        "source": "hackernews",
        "author": "career_gamer",
        "published_at": (datetime.now() - timedelta(days=18)).isoformat() + "Z",
        "metadata": {
            "upvotes": 1023,
            "comments": 378,
            "domain": "education",
            "tags": [
                "career",
                "skills",
                "visualization",
                "learning-path",
                "gamification",
            ],
        },
    },
    # Developer Tools (4 posts)
    {
        "url": "https://reddit.com/r/devops/comments/dev001",
        "title": "Need a CI/CD pipeline visualizer that shows exactly why builds are slow and suggests optimizations",
        "content": "10-minute builds kill productivity. Visualize pipeline as a dependency graph, highlight bottlenecks, suggest parallelization opportunities. Show impact: 'Caching node_modules saves 2 min'. Automatically apply optimizations. Fast CI/CD as a service.",
        "source": "reddit",
        "author": "devops_optimizer",
        "published_at": (datetime.now() - timedelta(days=7)).isoformat() + "Z",
        "metadata": {
            "upvotes": 567,
            "comments": 167,
            "domain": "developer-tools",
            "subreddit": "devops",
            "tags": ["ci-cd", "optimization", "visualization", "performance", "devops"],
        },
    },
    {
        "url": "https://twitter.com/api_dev/status/1234570023",
        "title": "Why isn't there a tool that generates comprehensive API tests from production traffic automatically?",
        "content": "Writing tests is tedious. Record production API calls, cluster by endpoint/params, generate test cases covering edge cases. Mock responses for fast tests. Update tests when API changes. Production-driven test generation.",
        "source": "twitter",
        "author": "test_automation_pro",
        "published_at": (datetime.now() - timedelta(days=12)).isoformat() + "Z",
        "metadata": {
            "likes": 445,
            "retweets": 134,
            "domain": "developer-tools",
            "tags": ["testing", "api", "automation", "production", "test-generation"],
        },
    },
    {
        "url": "https://news.ycombinator.com/item?id=39902021",
        "title": "Someone build a dependency updater that runs tests on PRs before merging package updates",
        "content": "Updating dependencies is risky. Renovate creates PRs but doesn't verify they work. I want: auto-update, run full test suite, if green auto-merge, if red notify with error details. Safe, hands-off dependency management.",
        "source": "hackernews",
        "author": "safe_updater",
        "published_at": (datetime.now() - timedelta(days=16)).isoformat() + "Z",
        "metadata": {
            "upvotes": 678,
            "comments": 201,
            "domain": "developer-tools",
            "tags": ["dependencies", "automation", "testing", "ci", "safety"],
        },
    },
    {
        "url": "https://reddit.com/r/coding/comments/code001",
        "title": "I wish there was a code navigation tool that understands business logic flow across microservices",
        "content": "Tracing requests through microservices is painful. Click on a function, see the entire call chain: API → Service A → Queue → Service B → DB. Show data transformations at each step. Distributed tracing meets IDE navigation.",
        "source": "reddit",
        "author": "microservices_navigator",
        "published_at": (datetime.now() - timedelta(days=20)).isoformat() + "Z",
        "metadata": {
            "upvotes": 734,
            "comments": 189,
            "domain": "developer-tools",
            "subreddit": "coding",
            "tags": [
                "microservices",
                "tracing",
                "navigation",
                "distributed",
                "debugging",
            ],
        },
    },
    # Career (4 posts)
    {
        "url": "https://twitter.com/job_hunter/status/1234570024",
        "title": "Need a job search CRM that tracks applications, follow-ups, and interview feedback automatically",
        "content": "Job hunting is chaotic. Track every application, auto-remind for follow-ups, log interview questions/feedback, analyze rejection patterns. 'You're rejected most at phone screens - improve your pitch'. Data-driven job search.",
        "source": "twitter",
        "author": "organized_job_seeker",
        "published_at": (datetime.now() - timedelta(days=3)).isoformat() + "Z",
        "metadata": {
            "likes": 912,
            "retweets": 334,
            "domain": "career",
            "tags": ["job-search", "crm", "tracking", "organization", "data"],
        },
    },
    {
        "url": "https://news.ycombinator.com/item?id=39902022",
        "title": "Why isn't there a LinkedIn but for showing real work samples instead of job titles?",
        "content": "Resumes lie. I want a portfolio platform where developers share actual code, designers show real projects, writers display published work. Verify contributions via GitHub/Behance/Medium. Hire based on output, not credentials. Proof of work network.",
        "source": "hackernews",
        "author": "work_portfolio_believer",
        "published_at": (datetime.now() - timedelta(days=8)).isoformat() + "Z",
        "metadata": {
            "upvotes": 1234,
            "comments": 456,
            "domain": "career",
            "tags": [
                "portfolio",
                "hiring",
                "networking",
                "proof-of-work",
                "professional",
            ],
        },
    },
    {
        "url": "https://reddit.com/r/careeradvice/comments/advice001",
        "title": "Someone build a performance review prep tool that analyzes Slack/email to quantify impact",
        "content": "Self-reviews are hard. Scan my Slack messages, emails, commits. Extract accomplishments, quantify impact ('helped 23 teammates', 'shipped 5 features'). Generate review draft with evidence. Data-backed self-promotion.",
        "source": "reddit",
        "author": "performance_optimizer",
        "published_at": (datetime.now() - timedelta(days=13)).isoformat() + "Z",
        "metadata": {
            "upvotes": 789,
            "comments": 234,
            "domain": "career",
            "subreddit": "careeradvice",
            "tags": [
                "performance-review",
                "data-analysis",
                "impact",
                "self-promotion",
                "automation",
            ],
        },
    },
    {
        "url": "https://twitter.com/remote_career/status/1234570025",
        "title": "I wish there was a skills arbitrage platform matching remote workers with high-value markets",
        "content": "I'm in a low-cost country with valuable skills. Match me with US/EU companies willing to pay global rates. Handle contracts, payments, taxes. Geographic arbitrage marketplace. Work remotely, earn more, live better.",
        "source": "twitter",
        "author": "global_talent",
        "published_at": (datetime.now() - timedelta(days=19)).isoformat() + "Z",
        "metadata": {
            "likes": 867,
            "retweets": 289,
            "domain": "career",
            "tags": [
                "remote-work",
                "arbitrage",
                "global",
                "marketplace",
                "compensation",
            ],
        },
    },
    # Travel (4 posts)
    {
        "url": "https://reddit.com/r/digitalnomad/comments/nomad001",
        "title": "Need a visa calculator that shows where I can work remotely based on my passport and stay duration",
        "content": "Visa rules are confusing. Input: passport country, desired stays (3 months Thailand, 2 months Portugal). Output: visa requirements, cost, processing time, restrictions. Include remote work legality. Digital nomad compliance made easy.",
        "source": "reddit",
        "author": "visa_optimizer",
        "published_at": (datetime.now() - timedelta(days=2)).isoformat() + "Z",
        "metadata": {
            "upvotes": 923,
            "comments": 312,
            "domain": "travel",
            "subreddit": "digitalnomad",
            "tags": ["travel", "visa", "remote-work", "legal", "nomad"],
        },
    },
    {
        "url": "https://twitter.com/travel_hacker2/status/1234570026",
        "title": "Why isn't there a points optimizer that maximizes credit card rewards for planned trips?",
        "content": "I have 5 credit cards with different reward structures. Input upcoming trip details, get strategy: 'Book flights with card A (3x points), hotels with card B (5x), dining with card C'. Maximize every purchase. Points arbitrage calculator.",
        "source": "twitter",
        "author": "points_maximizer",
        "published_at": (datetime.now() - timedelta(days=7)).isoformat() + "Z",
        "metadata": {
            "likes": 712,
            "retweets": 245,
            "domain": "travel",
            "tags": ["travel", "credit-cards", "rewards", "optimization", "points"],
        },
    },
    {
        "url": "https://news.ycombinator.com/item?id=39902023",
        "title": "Someone build a local food finder that uses Instagram tags to discover authentic restaurants",
        "content": "TripAdvisor is full of tourist traps. Analyze Instagram: where do locals tag photos, what do they eat, when are restaurants busy. Recommend hidden gems with high local-to-tourist ratio. Find authentic food anywhere.",
        "source": "hackernews",
        "author": "foodie_explorer",
        "published_at": (datetime.now() - timedelta(days=12)).isoformat() + "Z",
        "metadata": {
            "upvotes": 845,
            "comments": 267,
            "domain": "travel",
            "tags": ["travel", "food", "instagram", "local", "recommendations"],
        },
    },
    {
        "url": "https://reddit.com/r/backpacking/comments/pack001",
        "title": "I wish there was a travel gear optimizer that suggests what to pack based on destination weather and activities",
        "content": "Overpacking is my nemesis. Input: destination, dates, planned activities. Output: optimal packing list with alternatives ('rain likely - pack umbrella or waterproof jacket?'). Learn from past trips. Pack smarter, travel lighter.",
        "source": "reddit",
        "author": "minimalist_traveler",
        "published_at": (datetime.now() - timedelta(days=18)).isoformat() + "Z",
        "metadata": {
            "upvotes": 634,
            "comments": 178,
            "domain": "travel",
            "subreddit": "backpacking",
            "tags": ["travel", "packing", "optimization", "weather", "gear"],
        },
    },
]

# Load existing posts
with open("/Users/elizabethstein/Projects/app-idea-miner/data/sample_posts.json") as f:
    existing_posts = json.load(f)

# Merge
all_posts = existing_posts + final_posts

print(
    f"📊 Total posts: {len(all_posts)} (existing: {len(existing_posts)}, new: {len(final_posts)})"
)

# Get all domains
domains = {}
for post in all_posts:
    domain = post["metadata"]["domain"]
    domains[domain] = domains.get(domain, 0) + 1

print(f"\n🏷️  Domain distribution ({len(domains)} domains):")
for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True):
    print(f"   {domain}: {count} posts")

# Save merged data
with open(
    "/Users/elizabethstein/Projects/app-idea-miner/data/sample_posts.json", "w"
) as f:
    json.dump(all_posts, f, indent=2, ensure_ascii=False)

print(f"\n✅ Saved {len(all_posts)} posts to data/sample_posts.json")
print("🎯 Target reached: 100+ posts for better clustering!")
