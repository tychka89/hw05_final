from django.core.paginator import Paginator
from django.shortcuts import redirect, render, get_object_or_404
from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse


number_of_elements: int = 10


def index(request):
    post_list = Post.objects.select_related('group')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('group')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'posts': post_list,
        'page_obj': page_obj
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    username = get_object_or_404(User, username=username)
    profile_post_list = (Post.objects.filter(author=username)
                         .order_by('-pub_date'))
    paginator = Paginator(profile_post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    number_of_posts = profile_post_list.count()
    is_profile = True
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=username
        ).exists()
    else:
        following = False
    context = {
        'page_obj': page_obj,
        'profile': profile_post_list,
        'username': username,
        'number_of_posts': number_of_posts,
        'is_profile': is_profile,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    username = get_object_or_404(User, id=post.author_id)
    number_of_posts = Post.objects.filter(author=username).count()
    group = post.group
    title = post.text[:30]
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post=post)
    context = {
        'post': post,
        'username': username,
        'title': title,
        'number_of_posts': number_of_posts,
        'group': group,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', post.author.username)
        else:
            print(form.errors)
            return render(request, 'posts/create_post.html', {'form': form})
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
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
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page_obj')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = User.objects.get(username=username)
    is_follower = Follow.objects.filter(user=user, author=author)
    if user != author and not is_follower.exists():
        Follow.objects.create(user=user, author=author)
    return redirect(reverse('posts:profile', args=[username]))


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    is_follower = Follow.objects.filter(user=request.user, author=author)
    if is_follower.exists():
        is_follower.delete()
    return redirect('posts:profile', username=author)
