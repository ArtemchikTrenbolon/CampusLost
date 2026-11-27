from django.db.models import Q
from django.utils.dateparse import parse_date
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import Ad, Building, Category
from .pagination import FeedPagination
from .permissions import IsAuthorOrModerator
from .serializers import (AdPhotoSerializer, AdSerializer, BuildingSerializer,
                          CategorySerializer)

PUBLIC_STATUSES = [Ad.Status.ACTIVE, Ad.Status.IN_RETURN, Ad.Status.RETURNED]
MAX_PHOTOS = 5

FEED_PARAMETERS = [
    OpenApiParameter('type', str, description='Тип: lost или found'),
    OpenApiParameter('category', int, description='id категории'),
    OpenApiParameter('building', int, description='id корпуса'),
    OpenApiParameter('status', str, description='Статус: active, returned, in_return'),
    OpenApiParameter('date_from', str, description='Дата потери/находки от (ГГГГ-ММ-ДД)'),
    OpenApiParameter('date_to', str, description='Дата потери/находки до (ГГГГ-ММ-ДД)'),
    OpenApiParameter('q', str, description='Поиск по названию, описанию, категории, месту'),
]


@extend_schema_view(list=extend_schema(parameters=FEED_PARAMETERS))
class AdViewSet(viewsets.ModelViewSet):
    serializer_class = AdSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrModerator]
    pagination_class = FeedPagination

    def get_queryset(self):
        qs = (Ad.objects
              .select_related('category', 'building', 'location', 'author')
              .prefetch_related('photos'))
        user = self.request.user
        public = Q(status__in=PUBLIC_STATUSES)
        if user.is_authenticated:
            if user.is_moderator:
                return qs
            return qs.filter(public | Q(author=user))
        return qs.filter(public)

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        # Фильтры работают только для списка, чтобы не ломать просмотр одного объявления
        if self.action != 'list':
            return queryset

        params = self.request.query_params

        ad_type = params.get('type')
        if ad_type in Ad.Type.values:
            queryset = queryset.filter(type=ad_type)

        status_value = params.get('status')
        if status_value in Ad.Status.values:
            queryset = queryset.filter(status=status_value)

        for param in ('category', 'building'):
            value = params.get(param)
            if value:
                if not value.isdigit():
                    raise ValidationError({param: 'Должно быть числом'})
                queryset = queryset.filter(**{f'{param}_id': int(value)})

        for param, lookup in (('date_from', 'event_date__gte'), ('date_to', 'event_date__lte')):
            value = params.get(param)
            if value:
                try:
                    parsed = parse_date(value)
                except ValueError:
                    parsed = None
                if parsed is None:
                    raise ValidationError({param: 'Неверная дата, нужен формат ГГГГ-ММ-ДД'})
                queryset = queryset.filter(**{lookup: parsed})

        # Поиск по ключевым словам (в Python, потому что SQLite не понимает регистр кириллицы)
        q = params.get('q', '').strip().lower()
        if q:
            words = q.split()

            def haystack(ad):
                parts = [
                    ad.title, ad.description, ad.category.name,
                    ad.building.name, ad.location.name if ad.location else '',
                ]
                return ' '.join(parts).lower()

            ids = [ad.id for ad in queryset if all(word in haystack(ad) for word in words)]
            queryset = queryset.filter(id__in=ids)

        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        # Объявления модераторов публикуются сразу, остальные идут на проверку
        status_value = Ad.Status.ACTIVE if user.is_moderator else Ad.Status.PENDING
        serializer.save(author=user, status=status_value)

    @extend_schema(request=AdPhotoSerializer, responses={201: AdPhotoSerializer})
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def photos(self, request, pk=None):
        """Загрузить одно фото к объявлению (до 5 штук)."""
        ad = self.get_object()
        if ad.photos.count() >= MAX_PHOTOS:
            return Response({'detail': f'Можно загрузить не более {MAX_PHOTOS} фото'},
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = AdPhotoSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(ad=ad)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    pagination_class = None


class BuildingListView(generics.ListAPIView):
    queryset = Building.objects.prefetch_related('locations')
    serializer_class = BuildingSerializer
    permission_classes = [AllowAny]
    pagination_class = None