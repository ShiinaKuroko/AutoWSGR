"""Minimal import checks for the new application/common package boundary."""


def test_application_and_common_packages_import_without_side_effects() -> None:
    import autowsgr.application
    import autowsgr.common

    assert autowsgr.application.__doc__
    assert autowsgr.common.__doc__
