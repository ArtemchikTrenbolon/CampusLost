from django.db.models import Q
from rest_framework import generics, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly

from .models import Ad, Building, Category
from .permissions import IsAuthorOrModerator
from .serializers import AdSerializer, BuildingSerializer, CategorySerializer

PUBLIC_STATUSES = [Ad.Status.ACTIVE, Ad.Status.IN_RETURN, Ad.Status.RETURNED]


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