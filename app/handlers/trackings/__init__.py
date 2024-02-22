from aiogram import Router

from filters.subscription_filter import SubscriptionFilter
from .creating_trackings import router as creating_trackings_router
from .editing_tracking import router as editing_tracking_router
from .tracking_list import router as tracking_list_router
from .notifications_tracking import router as notifications_tracking_router

router = Router()

router.message.filter(SubscriptionFilter())
router.callback_query.filter(SubscriptionFilter())

router.include_router(creating_trackings_router)
router.include_router(editing_tracking_router)
router.include_router(tracking_list_router)
router.include_router(notifications_tracking_router)
