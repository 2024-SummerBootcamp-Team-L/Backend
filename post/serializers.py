from rest_framework import serializers
from drf_yasg.utils import swagger_serializer_method
from .models import *


class PostCreateSerializer(serializers.ModelSerializer):
    category_ids = serializers.ListField(
        child=serializers.IntegerField(), allow_null=True, required=False
    )

    class Meta:
        model = Post
        fields = ['title', 'content', 'category_ids']

    def create(self, validated_data):
        category_ids = validated_data.pop('category_ids', None)
        post = Post.objects.create(**validated_data)

        if category_ids:
            for category_id in category_ids:
                if category_id is not None:
                    Post_Category.objects.create(post=post, category=category_id)

        return post


class PostSerializer(serializers.ModelSerializer):
    categories = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'host', 'name', 'title', 'content', 'vote', 'created_at', 'categories']

    @swagger_serializer_method(serializer_or_field=serializers.ListField(child=serializers.IntegerField()))
    def get_categories(self, obj):
        return list(Post_Category.objects.filter(post=obj).values_list('category', flat=True))

    def get_name(self, obj):
        return obj.host.name if obj.host else None


class PostUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['title']


# class PostDetailSerializer(serializers.ModelSerializer):
#     categories = serializers.SerializerMethodField()
#
#     class Meta:
#         model = Post
#         fields = ['id', 'host', 'title', 'content', 'vote', 'created_at', 'updated_at', 'categories']
#
#     def get_categories(self, obj):
#         return list(Post_Category.objects.filter(post=obj).values_list('category', flat=True))
