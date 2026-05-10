from types import SimpleNamespace

import pytest

from ci.cli import DEFAULT_LIVE_ADDRESS_IDS, _select_live_addresses


def test_select_live_addresses_defaults_to_demo_safe_subset() -> None:
    args = SimpleNamespace(
        address_id=None,
        all_addresses=False,
        platform=None,
        limit_addresses=None,
        debug_evidence=False,
    )

    addresses = _select_live_addresses(args)

    assert [address.address_id for address in addresses] == list(DEFAULT_LIVE_ADDRESS_IDS)


def test_select_live_addresses_uses_full_catalog_when_requested() -> None:
    args = SimpleNamespace(
        address_id=None,
        all_addresses=True,
        platform=None,
        limit_addresses=None,
        debug_evidence=False,
    )

    addresses = _select_live_addresses(args)

    assert len(addresses) == 20


def test_select_live_addresses_rejects_unknown_address() -> None:
    args = SimpleNamespace(
        address_id="missing-001",
        all_addresses=False,
        platform=None,
        limit_addresses=None,
        debug_evidence=False,
    )

    with pytest.raises(ValueError, match="Unknown address id"):
        _select_live_addresses(args)
