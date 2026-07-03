from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiExample

from .models import BlogPost
from .serializers import BlogPostSerializer


@extend_schema(
    methods=['GET'],
    responses={200: BlogPostSerializer(many=True)},
    description="List all blog posts from all users, newest first.",
)
@extend_schema(
    methods=['POST'],
    request=BlogPostSerializer,
    responses={201: BlogPostSerializer, 400: None},
    description=(
        "Create a new blog post. The author is set automatically from the "
        "authenticated user's token - do not include it in the body."
    ),
    examples=[
        OpenApiExample(
            'New post',
            value={"title": "My first post",
                   "content": "Hello from the Blog API."},
            request_only=True,
        ),
    ],
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def post_list(request):
    # GET /api/posts/
    if request.method == 'GET':
        posts = BlogPost.objects.all()
        serializer = BlogPostSerializer(posts, many=True)
        return Response(serializer.data)

    # POST /api/posts/
    serializer = BlogPostSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    methods=['GET'],
    responses={200: BlogPostSerializer, 404: None},
    description="Retrieve a single blog post by its ID.",
)
@extend_schema(
    methods=['PUT'],
    request=BlogPostSerializer,
    responses={200: BlogPostSerializer, 400: None, 403: None, 404: None},
    description=(
        "Fully update a post. **Author only** - returns 403 if the post "
        "belongs to another user. All required fields must be sent."
    ),
    examples=[
        OpenApiExample(
            'Full update',
            value={"title": "Updated title", "content": "Rewritten content."},
            request_only=True,
        ),
    ],
)
@extend_schema(
    methods=['PATCH'],
    request=BlogPostSerializer,
    responses={200: BlogPostSerializer, 400: None, 403: None, 404: None},
    description=(
        "Partially update a post. **Author only.** Send just the fields "
        "you want to change."
    ),
    examples=[
        OpenApiExample(
            'Change title only',
            value={"title": "A better title"},
            request_only=True,
        ),
        OpenApiExample(
            'Change content only',
            value={"content": "Updated content for this post."},
            request_only=True,
        ),
        OpenApiExample(
            'Change both fields',
            value={"title": "New title", "content": "New content."},
            request_only=True,
        ),
        OpenApiExample(
            'Invalid: empty title (returns 400)',
            value={"title": ""},
            request_only=True,
        ),
    ],
)
@extend_schema(
    methods=['DELETE'],
    responses={204: None, 403: None, 404: None},
    description="Delete a post. **Author only** — returns 403 otherwise.",
)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def post_detail(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)

    if request.method == 'GET':
        serializer = BlogPostSerializer(post)
        return Response(serializer.data)

    # write operations that need authorization
    if post.author != request.user:
        return Response(
            {"detail": "You can only modify your own posts."},
            status=status.HTTP_403_FORBIDDEN
        )

    if request.method in ('PUT', 'PATCH'):
        serializer = BlogPostSerializer(
            post, data=request.data, partial=(request.method == 'PATCH'))
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    post.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
