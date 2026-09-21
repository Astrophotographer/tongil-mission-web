from api._trip_parse import parse_primary_json, strip_code_fence


def test_strip_fence():
    raw = "```json\n{\"recommended_site\":\"임진각\"}\n```"
    assert "임진각" in strip_code_fence(raw)


def test_parse_primary_minimal():
    data = parse_primary_json(
        '{"recommended_site":"임진각","nearby_area":"파주 임진각","reason":"r","learning_goals":["g"],"field_missions":["m"],"timeline":[{"time":"10:00","place":"임진각","activity":"견학"},{"time":"12:00","place":"파주","activity":"점심"}]}'
    )
    assert data["recommended_site"] == "임진각"
    assert len(data["timeline"]) == 2
    assert data["timeline"][0]["time"] == "10:00"


def test_parse_primary_requires_timeline():
    try:
        parse_primary_json(
            '{"recommended_site":"임진각","nearby_area":"파주","reason":"r","learning_goals":["g"],"field_missions":["m"]}'
        )
        assert False, "expected ValueError"
    except ValueError as e:
        assert "timeline" in str(e)
