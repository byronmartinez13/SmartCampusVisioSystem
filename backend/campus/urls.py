from rest_framework.routers import DefaultRouter
from .api_views import ClassroomViewSet, CourseViewSet, SubjectViewSet, TeacherViewSet
from .scheduling_api import ProposalViewSet
from .operations import RuleViewSet, SettingsView, AuditView
from django.urls import path

router = DefaultRouter()
router.register("classrooms", ClassroomViewSet)
router.register("teachers", TeacherViewSet)
router.register("subjects", SubjectViewSet)
router.register("courses", CourseViewSet)
router.register("assignments", ProposalViewSet, basename="assignment")
router.register('assignment-rules', RuleViewSet, basename='assignment-rule')
urlpatterns = [path('settings/', SettingsView.as_view()), path('administrative-events/', AuditView.as_view())] + router.urls
