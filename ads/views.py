from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import Ad, Building, Category
from .permissions import IsAuthorOrModerator
from .serializers import (AdPhotoSerializer, AdSerializer, BuildingSerializer,
                          CategorySerializer)

PUBLIC_STATUSES = [Ad.Status.ACTIVE, Ad.Status.IN_RETURN, Ad.Status.RETURNED]
MAX_PHOTOS = 5


class AdViewSet(viewsets.ModelViewSet):
    serializer_class = AdSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrModerator]

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

    def perform_create(self, serializer):
        user = self.request.user
        # Объявления модераторов публикуются сразу, остальные идут на проверку
        status = Ad.Status.ACTIVE if user.is_moderator else Ad.Status.PENDING
        serializer.save(author=user, status=status)

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