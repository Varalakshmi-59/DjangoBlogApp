from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Article, Comment

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'comment_author', 'comment_content', 'comment_date']
        read_only_fields = ['comment_date']

class ArticleSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'created_date', 'article_image', 
                 'slug', 'author', 'comments', 'comment_count']
        read_only_fields = ['created_date', 'slug', 'comment_count']

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        validated_data['slug'] = slugify(validated_data['title'])
        return super().create(validated_data)

    def validate_title(self, value):
        if Article.objects.filter(title=value).exists():
            raise serializers.ValidationError("An article with this title already exists.")
        return value
