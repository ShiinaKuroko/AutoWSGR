"""战役业务用例。"""

from autowsgr.business.combat.campaign.executor import CampaignExecutor
from autowsgr.business.combat.campaign.spec import (
    CAMPAIGN_NAME_MAP,
    CAMPAIGN_NAMES,
    CampaignSpec,
    parse_campaign_name,
)


__all__ = [
    'CAMPAIGN_NAMES',
    'CAMPAIGN_NAME_MAP',
    'CampaignExecutor',
    'CampaignSpec',
    'parse_campaign_name',
]
