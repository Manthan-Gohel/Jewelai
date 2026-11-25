"""New workspaces must never inherit example business facts."""
import pytest

from app.api.v1.auth import save_connection
from app.models.models import User
from app.services.ai.generator import ResponseGenerator, build_system_instruction


@pytest.mark.asyncio
async def test_new_connection_has_no_invented_business_details(db_session):
    user = User(name="New owner", email="new-defaults@example.com", password_hash="unused-test-hash")
    db_session.add(user)
    db_session.flush()
    try:
        account = await save_connection(db_session, user, "test-token", {
            "user_id": "new-defaults-instagram-id", "username": "new_jeweller", "name": "New Jeweller",
        })
        saved = account.settings
        assert saved.business_name == "New Jeweller"
        assert saved.auto_reply_enabled is False
        assert saved.tagline == ""
        assert saved.store_timings == ""
        assert saved.store_address is None
        assert saved.gold_rate_24k_per_10g == saved.gold_rate_22k_per_10g == saved.gold_rate_18k_per_10g == 0

        class Provider:
            async def generate_text(self, **kwargs):
                self.prompt = kwargs["prompt"]
                return "Please ask the store for its current rates."

        provider = Provider()
        await ResponseGenerator(provider).generate_response("Gold rates?", "en", "inquiry", [], [], saved)
        assert "₹0" not in provider.prompt
        assert "not configured" in provider.prompt.lower()
        assert "today gold rates" not in provider.prompt.lower()
    finally:
        db_session.delete(user)
        db_session.commit()


def test_missing_settings_do_not_imply_a_demo_business():
    assert "Luxe Aura" not in build_system_instruction(None)


@pytest.mark.parametrize("value", [-1, "NaN", "Infinity"])
def test_gold_rates_reject_negative_or_nonfinite_values(value):
    from pydantic import ValidationError
    from app.schemas.schemas import BusinessSettingsUpdate

    with pytest.raises(ValidationError):
        BusinessSettingsUpdate(gold_rate_22k_per_10g=value)


def test_clearing_one_rate_leaves_other_rates_untouched():
    from app.schemas.schemas import BusinessSettingsUpdate

    assert BusinessSettingsUpdate(gold_rate_22k_per_10g=None).model_dump(exclude_unset=True) == {
        "gold_rate_22k_per_10g": 0,
    }
