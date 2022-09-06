from django.shortcuts import render, get_object_or_404, redirect
from .forms import PostForm
from .models import Post, Group, User
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt

NUMBER_OF_POST: int = 10


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, NUMBER_OF_POST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, NUMBER_OF_POST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
        'title': f'Записи сообщестава: {group}',
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    user_profile = Post.objects.select_related('author').filter(author=author)
    posts_count = Post.objects.filter(author=author).count()
    paginator = Paginator(user_profile, NUMBER_OF_POST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'user_profile': user_profile,
        'page_obj': page_obj,
        'posts_count': posts_count,
        'author': author,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    author_post = Post.objects.select_related('author')
    post_count = author_post.count()
    title = post.text[0:30]
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
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author = request.user
            new_post.save()
            return redirect(f'/profile/{user}/')
        return render(
            request,
            'posts/create_post.html', {'form': form})
    form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})


def post_edit(request, post_id):
    is_edit = True
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(request.POST or None, instance=post)
    context = {
        'is_edit': is_edit, 'post': post, 'form': form
    }
    if request.user != post.author:
        return redirect(f'/posts/{post_id}/')
    if request.method == 'POST':
        if form.is_valid:
            form.save()
            return redirect(f'/posts/{post_id}/')
    return render(request, 'posts/create_post.html', context)
