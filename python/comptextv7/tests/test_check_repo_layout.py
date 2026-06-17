from scripts.check_repo_layout import check_repo_layout


def test_expected_repo_layout_is_present():
    assert check_repo_layout() == []
