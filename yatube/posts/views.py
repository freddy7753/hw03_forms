from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

from .forms import PostForm
from .models import Post, Group, User
from .utils import get_paginator_obj

TITLE_COUNT_SYMBOL: int = 30


def index(request):
    post_list = Post.objects.select_related('author', 'group')
    page_obj = get_paginator_obj(post_list, request)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('group', 'author')
    page_obj = get_paginator_obj(post_list, request)
    context = {
        'group': group,
        'page_obj': page_obj,
        'title': f'Записи сообщестава: {group}',
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    user_posts = author.posts.select_related(
        'author', 'group')
    posts_count = Post.objects.filter(author=author).count()
    page_obj = get_paginator_obj(user_posts, request)
    context = {
        'page_obj': page_obj,
        'posts_count': posts_count,
        'author': author,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    author_post = Post.objects.select_related('author')
    post_count = author_post.count()
    title = post.text[:TITLE_COUNT_SYMBOL]
    context = {
        'title': title,
        'post': post,
        'post_count': post_count,
        'auhtor_post': author_post,
    }
    return render(request, 'posts/post_detail.html', context)


@csrf_exempt
def post_create(request):
    user = get_object_or_404(User, id=request.user.pk)
    form = PostForm(request.POST or None)
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect(reverse('posts:profile', args=[user]))
    return render(
        request,
        'posts/create_post.html', {'form': form})


def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect(reverse('posts:post_detail', args=[post_id]))
    is_edit = True
    form = PostForm(request.POST or None, instance=post)
    context = {
        'is_edit': is_edit, 'post': post, 'form': form
    }
    if request.method == 'POST':
        if form.is_valid:
            form.save()
            return redirect(reverse('posts:post_detail', args=[post_id]))
    return render(request, 'posts/create_post.html', context)
