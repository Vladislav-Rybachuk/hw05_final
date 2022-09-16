from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from .forms import PostForm, CommentForm
from .models import Post, Group, User, Comment, Follow

QUANTITY = 10


def paginated_context(queryset, request):
    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {
        'paginator': paginator,
        'page_number': page_number,
        'page_obj': page_obj,
    }


def index(request):
    """
    Главная страница. Отображает последние опубликованные посты.
    """
    context = paginated_context(
        Post.objects.all().order_by('pub_date'), request
    )
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """
    Страница группы. Отображает отфильтрованные по группе посты.
    """
    group = get_object_or_404(Group, slug=slug)
    group_posts_list = group.posts.all()
    context = {
        'group': group,
        'group_posts_list': group_posts_list,
    }
    context.update(paginated_context(
        group.posts.all().order_by('pub_date'), request)
    )
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """
    Страница профиля. Отображает отфильтрованные по пользователю посты.
    """
    author = get_object_or_404(User, username=username)
    author_posts = author.posts.all()
    count_post = author_posts.count()
    qs = Follow.objects.filter(user_id=request.user.id, author_id=author.id)
    if qs.exists():
        following = True
    else:
        following = False
    context = {
        'author': author,
        'following': following,
        'count_post': count_post,
    }
    context.update(paginated_context(
        author.posts.all().order_by('pub_date'), request)
    )
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """
    Отображение выбранного поста.
    """
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post__id=post_id)
    post_count = Post.objects.filter(author_id=post.author.id).count()
    context = {
        'post_count': post_count,
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """
    Страница создания поста.
    """
    form = PostForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', username=request.user)
        return render(request, 'posts/post_create.html',
                      {'form': form})
    context = {
        'form': form,
    }
    return render(request, 'posts/post_create.html', context)


@login_required
def post_edit(request, post_id):
    """Страница редактирования поста."""
    selected_post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=selected_post
    )
    
    if request.method == 'POST':
        if form.is_valid():
            post = form.save()
            return redirect('posts:post_detail', post_id=post.pk)
    context = {
        'form': form,
        'title': 'Редактировать пост',
        'is_edit': True
    }
    return render(request, 'posts/post_create.html', context)


@login_required
def add_comment(request, post_id):
    """Добавление комментария."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Страница подписок."""
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, settings.PAGINATOR_OBJ_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписка на пользователя."""
    author = get_object_or_404(User, username=username).id
    if str(request.user) == username:
        return redirect('posts:profile', username=username)
    else:
        Follow.objects.get_or_create(user_id=request.user.id, author_id=author)
        return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Отписка от пользователя"""
    author = get_object_or_404(User, username=username).id
    Follow.objects.filter(user_id=request.user.id, author_id=author).delete()
    return redirect('posts:profile', username=username)