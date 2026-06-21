from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import PlanTripSerializer
from .services.hos_engine import simulate_hos
from .services.log_builder import assemble_trip_plan, build_timeline
from .services.plan_enrichment import enrich_trip_plan
from .services.route_engine import GeocodingError, RoutingError, build_route


class PlanTripView(APIView):
    def post(self, request):
        serializer = PlanTripSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        cycle_used = data["current_cycle_used_hours"]

        try:
            route = build_route(
                data["current_location"],
                data["pickup_location"],
                data["dropoff_location"],
            )
        except GeocodingError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except RoutingError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        hos_result = simulate_hos(route, cycle_used)

        route_data = {
            "total_distance_miles": round(route.total_distance_miles, 2),
            "total_drive_duration_hours": round(route.total_drive_duration_hours, 2),
            "polyline": route.polyline,
        }

        trip_start = timezone.now()
        plan = assemble_trip_plan(
            route_data,
            hos_result.events,
            hos_result.requires_restart,
            trip_start=trip_start,
        )

        if cycle_used >= 70:
            plan["requires_restart"] = True

        timed = build_timeline(hos_result.events, trip_start)
        plan = enrich_trip_plan(
            plan,
            hos_result.events,
            timed,
            cycle_start=cycle_used,
            requires_restart=plan.get("requires_restart", False),
        )

        return Response(plan, status=status.HTTP_200_OK)
