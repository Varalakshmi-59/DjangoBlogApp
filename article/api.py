from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from .models import Article, Comment
from .serializers import ArticleSerializer, CommentSerializer

class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['author__username']
    search_fields = ['title', 'content']
    ordering_fields = ['created_date', 'title']
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = Article.objects.select_related('author')\
            .prefetch_related('comments')\
            .annotate(comment_count=Count('comments'))
        
        cache_key = f'article_queryset_{self.action}'
        cached_queryset = cache.get(cache_key)
        
        if cached_queryset is None:
            cached_queryset = queryset
            cache.set(cache_key, cached_queryset, timeout=300)
        
        return cached_queryset

    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def add_comment(self, request, slug=None):
        article = self.get_object()
        serializer = CommentSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(article=article)
            cache.delete(f'article_detail_{slug}')
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @action(detail=False)
    def my_articles(self, request):
        cache_key = f'user_articles_{request.user.id}'
        queryset = cache.get(cache_key)
        
        if queryset is None:
            queryset = self.get_queryset().filter(author=request.user)
            cache.set(cache_key, queryset, timeout=300)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
