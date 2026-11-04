from rest_framework.response import Response
from rest_framework.views import APIView
from .services import dashboard_summary


class DashboardView(APIView):
    def get(self, request):
        return Response(dashboard_summary())
