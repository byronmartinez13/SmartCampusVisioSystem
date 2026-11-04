from rest_framework.routers import DefaultRouter
from .views import VideoJobViewSet
from .history import AlertViewSet, HistoryViewSet
from .live import LiveViewSet

router = DefaultRouter()
router.register('live-sessions', LiveViewSet, basename='live-session')
router.register("video-analyses", VideoJobViewSet, basename="video-analysis")
router.register("analysis-history", HistoryViewSet, basename="analysis-history")
router.register("alerts", AlertViewSet, basename="alert")
urlpatterns = router.urls
