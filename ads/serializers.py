from django.utils import timezone
from rest_framework import serializers

from .models import Ad, AdPhoto, Building, Category, Location, Match


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ('id', 'name', 'building')


class BuildingSerializer(serializers.ModelSerializer):
    locations = LocationSerializer(many=True, read_only=True)

    class Meta:
        model = Building
        fields = ('id', 'name', 'address', 'locations')


class AdPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdPhoto
        fields = ('id', 'image')

    def validate_image(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError('Файл больше 5 МБ')
        return value


class AdSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    building_name = serializers.CharField(source='building.name', read_only=True)
    location_name = serializers.SerializerMethodField()
    author_name = serializers.SerializerMethodField()
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    photos = AdPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = Ad
        fields = (
            'id', 'type', 'type_display', 'title', 'description',
            'category', 'category_name', 'building', 'building_name',
            'location', 'location_name', 'event_date',
            'status', 'status_display', 'author', 'author_name',
            'photos', 'created_at',
        )
        read_only_fields = ('status', 'author', 'created_at')

    def get_location_name(self, obj) -> str:
        return obj.location.name if obj.location else ''

    def get_author_name(self, obj) -> str:
        # Показываем имя и инициал фамилии, полные данные остаются приватными
        first = obj.author.first_name
        last = obj.author.last_name
        return f'{first} {last[:1]}.'.strip() if last else (first or 'Пользователь')

    def validate_event_date(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError('Дата не может быть в будущем')
        return value

    def validate(self, attrs):
        building = attrs.get('building', getattr(self.instance, 'building', None))
        location = attrs.get('location', getattr(self.instance, 'location', None))
        if building and location and location.building_id != building.id:
            raise serializers.ValidationError({'location': 'Это место находится в другом корпусе'})
        return attrs


class MatchSerializer(serializers.ModelSerializer):
    ad = serializers.SerializerMethodField()

    class Meta:
        model = Match
        fields = ('id', 'score', 'status', 'ad')

    def get_ad(self, obj) -> dict:
        # Показываем «противоположное» объявление относительно того, для которого ищем
        other = obj.found_ad if self.context['own_type'] == Ad.Type.LOST else obj.lost_ad
        return AdSerializer(other, context=self.context).data