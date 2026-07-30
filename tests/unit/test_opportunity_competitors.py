"""Unit tests for competitor aggregation in opportunity_service.

Pure-function tests — no database required. Covers the market-gap signal:
"N posters in this cluster mention incumbent X as inadequate."
"""

from packages.core.competitors import aggregate_competitors


class TestAggregateCompetitors:
    def test_counts_and_ranks_by_frequency(self):
        lists = [
            ["Notion", "Todoist"],
            ["notion", "Slack"],
            ["NOTION"],
        ]
        result = aggregate_competitors(lists)
        # Notion mentioned by 3 distinct posts, case-insensitive
        assert result[0] == {"name": "notion", "count": 3}
        names = [c["name"] for c in result]
        assert set(names) == {"notion", "todoist", "slack"}

    def test_respects_limit(self):
        lists = [[f"comp{i}"] for i in range(10)]
        result = aggregate_competitors(lists, limit=3)
        assert len(result) == 3

    def test_ignores_none_and_empty(self):
        lists = [None, [], ["Notion"], [None, "  ", "Todoist"]]
        result = aggregate_competitors(lists)
        names = {c["name"] for c in result}
        assert names == {"notion", "todoist"}

    def test_empty_input_returns_empty_list(self):
        assert aggregate_competitors([]) == []
        assert aggregate_competitors([None, []]) == []
