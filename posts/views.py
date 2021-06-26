from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseServerError

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "index.html", {"page": page,
                                          'paginator': paginator})


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    return render(request, "follow.html", {"page": page,
                                           'paginator': paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        "group": group,
        "page": page,
        'paginator': paginator,
    }
    return render(request, "group.html", context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    if request.user.is_authenticated:
        followed_authors = User.objects.filter(following__user=request.user)
        following = author in followed_authors
    else:
        following = False

    context = {
        'page': page,
        'author': author,
        'paginator': paginator,
        'following': following,
    }
    return render(request, 'profile.html', context)


def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm()
    comments = post.comments.all()
    context = {'form': form,
               'post': post,
               'comments': comments,
               'author': author
               }
    return render(request, 'post.html', context)


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:index')

    return render(request, 'new_post.html', {'form': form})


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)

    if request.user.username != username:
        return redirect('posts:post', post.author, post.id)

    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)

    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('posts:post', post.author, post.id)

    return render(request, 'new_post.html', {'form': form, 'object': post})


@login_required
def post_delete(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)

    if request.user.username != username:
        return redirect('posts:post', post.author, post.id)

    post.delete()

    return redirect('posts:profile', username)


@login_required
@require_http_methods(['POST'])
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('posts:post', post.author, post.id)

    return render(request, 'post.html', {'form': form, 'post': post})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)

    if request.user == author:
        return redirect('posts:profile', username=username)

    author.following.get_or_create(user=request.user, author=author)

    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)

    Follow.objects.filter(user=request.user, author=author).delete()

    return redirect('posts:profile', username=username)


def page_not_found(request, exception):
    return render(
        request, "misc/404.html", {"path": request.path}, status=404)


# def server_error(request):
#     return render(request, "misc/500.html", status=500)
