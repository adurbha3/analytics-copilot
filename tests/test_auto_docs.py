from analyticscopilot.auto_docs import generate_markdown_docs, generate_dbt_schema_yaml


def test_markdown_docs_mentions_every_table_and_column():
    docs = generate_markdown_docs()
    assert "mart_verifications" in docs
    for column in ["verification_id", "user_id", "email_domain", "status"]:
        assert column in docs


def test_dbt_schema_yaml_includes_tests():
    yaml_text = generate_dbt_schema_yaml()
    assert "not_null" in yaml_text
    assert "unique" in yaml_text
    assert "accepted_values" in yaml_text
    assert "mart_verifications" in yaml_text
