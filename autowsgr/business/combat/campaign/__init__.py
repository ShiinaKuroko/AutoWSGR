"""战役业务用例。"""

from autowsgr.business.combat.campaign.compat import CampaignRunner
from autowsgr.business.combat.campaign.executor import CampaignExecutor
from autowsgr.business.combat.campaign.spec import (
    CAMPAIGN_DAILY_LIMIT,
    CAMPAIGN_FLEET_TYPES,
    CAMPAIGN_NAME_MAP,
    CAMPAIGN_NAMES,
    CampaignSpec,
    parse_campaign_name,
)


__all__ = [
    'CAMPAIGN_DAILY_LIMIT',
    'CAMPAIGN_FLEET_TYPES',
    'CAMPAIGN_NAMES',
    'CAMPAIGN_NAME_MAP',
    'CampaignExecutor',
    'CampaignRunner',
    'CampaignSpec',
    'parse_campaign_name',
]
