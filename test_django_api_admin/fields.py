from rest_framework import serializers


class LocationField(serializers.Field):
    def to_representation(self, value):
        """
        Object instance -> Dict (For GET requests)
        'value' is the entire model instance because of source='*'
        """
        if isinstance(value, dict):
            return {
                "lat": value["latitude"],
                "lng": value["longitude"]
            }
        return {
            "lat": value.latitude,
            "lng": value.longitude
        }

    def to_internal_value(self, data):
        """
        Dict -> Dict (For POST/PUT/PATCH requests)
        'data' is the dictionary {"lat": 10, "lng": 20} from the JSON
        """
        if 'lat' not in data or 'lng' not in data:
            raise serializers.ValidationError(
                "Both 'lat' and 'lng' are required in location.")

        return {
            'latitude': data['lat'],
            'longitude': data['lng']
        }
