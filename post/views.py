from rest_framework.views import APIView
from rest_framework import status
import json
from .models import *
from rest_framework.response import Response
from .serializers import *
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user.utils import *

class PostCreateView(APIView):
    @swagger_auto_schema(
        tags=['게시판'],
        request_body=PostCreateSerializer,
        responses={201: PostSerializer, 400: 'Bad Request'}
    )
    # 게시글 생성
    def post(self, request):
        user_id, error_response = get_user_id_from_token(request)
        if error_response:
            return error_response

        serializer = PostCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(id=user_id)
                post = serializer.save(host=user)
                post_serializer = PostSerializer(post)

                return Response({'message': '생성되었습니다.'}, status=status.HTTP_201_CREATED)
            except User.DoesNotExist:
                return Response({'error': '사용자를 찾을 수 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ----------------------------------------------------------------------------------------------------------------------------#

class PostUpdateView(APIView):
    @swagger_auto_schema(
        tags=['게시판'],
        request_body=PostUpdateSerializer,
    )
    #게시글 수정
    def patch(self, request, post_id):
        user_id, error_response = get_user_id_from_token(request)
        if error_response:
            return error_response

        try:
            post = Post.objects.get(id=post_id)

            if post.host.id != user_id:
                return Response({'error': '게시물을 수정할 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)

            serializer = PostSerializer(post, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'message': '게시물이 성공적으로 수정되었습니다.'}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Post.DoesNotExist:
            return Response({'error': '게시물을 찾을 수 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# ----------------------------------------------------------------------------------------------------------------------------#
class PostDeleteView(APIView):
    @swagger_auto_schema(
        tags=['게시판']
    )
    # 게시글 삭제
    def delete(self, request, post_id):
        user_id, error_response = get_user_id_from_token(request)
        if error_response:
            return error_response

        try:
            post = Post.objects.get(id=post_id)

            if post.host.id != user_id:
                return Response({'error': '게시물을 삭제할 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)

            post.soft_delete()
            return Response({"message": "게시물이 성공적으로 삭제되었습니다."})
        except Post.DoesNotExist:
            return Response({"error": "삭제할 게시물을 찾을 수 없습니다."},
                            status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ----------------------------------------------------------------------------------------------------------------------------#

class PostVoteView(APIView):
    @swagger_auto_schema(
        tags=['게시판']
    )
    # 게시글 추천
    def patch(self, request, post_id):
        user_id, error_response = get_user_id_from_token(request)
        if error_response:
            return error_response

        try:
            post = Post.objects.get(id=post_id)

            # 현재 사용자가 게시글 작성자인지 확인
            if post.host.id == user_id:
                return Response({'error': '자신의 게시물에는 추천을 할 수 없습니다.'}, status=status.HTTP_403_FORBIDDEN)

            like_post, created = LikePost.objects.get_or_create(post=post, user_id=user_id)

            if created:
                # 새로 생성된 경우, 추천 상태로 설정
                post.vote += 1
                message = '게시물 추천이 완료되었습니다.'
            else:
                if like_post.is_deleted:
                    # 기존에 추천이 취소된 상태 -> 추천 상태로 변경
                    like_post.is_deleted = False
                    post.vote += 1
                    message = '게시물 추천이 완료되었습니다.'
                else:
                    # 기존에 추천 상태 -> 추천 취소 상태로 변경
                    like_post.is_deleted = True
                    post.vote -= 1
                    message = '게시물 추천이 취소되었습니다.'

            like_post.save()
            post.save()

            return Response({'message': message, 'votes': post.vote}, status=status.HTTP_200_OK)
        except Post.DoesNotExist:
            return Response({'error': '게시물을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# ----------------------------------------------------------------------------------------------------------------------------#
# 조회 방법 - 모든 게시판 조회

class AllPostGetView(APIView):
    @swagger_auto_schema(
        responses={
            200: PostSerializer,
            400: 'Bad Request'
        },
        tags=['게시판 목록'],
    )
    def get(self, request):
        posts = Post.undeleted_objects.all()
        if not posts.exists():
            return Response({'message': '게시물이 존재하지 않습니다.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# ----------------------------------------------------------------------------------------------------------------------------#

# 특정 유저의 게시판 조회
class UserPostsGetView(APIView):
    @swagger_auto_schema(
        responses={
            200: PostSerializer,
            405: 'Not found'
        },
        tags=['게시판 목록'],
    )
    def get(self, request):
        user_id, error_response = get_user_id_from_token(request)
        if error_response:
            return error_response

        user_posts = Post.undeleted_objects.filter(host=user_id)
        if not user_posts.exists():
            return Response({'message': '게시물이 존재하지 않습니다.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = PostSerializer(user_posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# ----------------------------------------------------------------------------------------------------------------------------#

# class PostDetailView(APIView):
#     @swagger_auto_schema(
#         tags=['게시판'],
#         responses={200: PostDetailSerializer, 404: '게시물을 찾을 수 없습니다.'}
#     )
#     # 게시글 조회
#     def get(self, request, post_id):
#         try:
#             post = Post.objects.get(id=post_id)
#             serializer = PostDetailSerializer(post)
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         except Post.DoesNotExist:
#             return Response({'error': '게시물을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
