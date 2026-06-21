from rest_framework import serializers


class PlanTripSerializer(serializers.Serializer):
    current_location = serializers.CharField(allow_blank=False, trim_whitespace=True)
    pickup_location = serializers.CharField(allow_blank=False, trim_whitespace=True)
    dropoff_location = serializers.CharField(allow_blank=False, trim_whitespace=True)
    current_cycle_used_hours = serializers.FloatField(min_value=0, max_value=70)

    def validate_current_cycle_used_hours(self, value):
        if value < 0 or value > 70:
            raise serializers.ValidationError(
                "current_cycle_used_hours must be between 0 and 70 inclusive."
            )
        return value
