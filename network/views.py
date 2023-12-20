from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.core.paginator import Paginator
import json
from django import template
from django.db.models import Count


from .models import User, Post, Follow,Like


from django.template.defaultfilters import register

@register.filter
def get_dict_value(dictionary, key):
    return dictionary.get(key, "")


def edit(request, post_id):
    if request.method == "POST":
        data = json.loads(request.body)
        edit_post = Post.objects.get(pk=post_id)
        edit_post.content = data['content']
        edit_post.save()
        return JsonResponse({"message": "Change successful", "data": data["content"]})


register = template.Library()

@register.simple_tag
def contains(list, element):
    return element in list


def index(request):
    allPosts = Post.objects.annotate(like_count=Count('likes')).order_by("id").reverse()

    # Pagination
    paginator = Paginator(allPosts, 10)
    page_number = request.GET.get('page')
    posts_of_the_page = paginator.get_page(page_number)

    likedByWhom = {}
    for post in allPosts:
        users_liked_post = User.objects.filter(user_like__post=post)
        likedByWhom[post.id] = {
            'like_count': users_liked_post.count()  
        }
    likedByWhom_json = json.dumps(likedByWhom)

    whoYouliked = []
    if request.user.is_authenticated:
        whoYouliked = Like.objects.filter(user=request.user).values_list('post__id', flat=True)
        whoYouliked = list(whoYouliked)

    context = {
        "allPosts": allPosts,
        "posts_of_the_page": posts_of_the_page,
        "likedByWhom": likedByWhom_json,
        "whoYouliked": whoYouliked
    }

    return render(request, "network/index.html", context)


def toggle_like(request, post_id):
    post = Post.objects.get(pk=post_id)
    user = User.objects.get(pk=request.user.id)

    try:
        like = Like.objects.get(user=user, post=post)
        like.delete()
        liked = False
    except Like.DoesNotExist:
        new_like = Like(user=user, post=post)
        new_like.save()
        liked = True

    like_count = post.likes.count()
    post_data = {
        "liked": liked,
        "like_count": like_count,
    }

    return JsonResponse(post_data)


def newPost(request):
    if request.method == "POST":
        content = request.POST["content"]
        user = User.objects.get(pk=request.user.id)
        post = Post(content=content, user=user)
        post.save()
        return HttpResponseRedirect(reverse(index))
    

def delete_post(request, post_id):
    if request.method == "DELETE":
        post = Post.objects.get(pk=post_id)
        post.delete()
        return JsonResponse({"message": "Post deleted successfully"})


def profile(request, user_id):
    user = User.objects.get(pk=user_id)
    allPosts = Post.objects.filter(user=user).order_by("id").reverse()
    allPost = Post.objects.annotate(like_count=Count('likes')).order_by("id").reverse()
    following = Follow.objects.filter(user=user)
    followers = Follow.objects.filter(user_follower=user)

    likedByWhom = {}
    for post in allPost:
        users_liked_post = User.objects.filter(user_like__post=post)
        likedByWhom[post.id] = {
            'like_count': users_liked_post.count()  
        }
    likedByWhom_json = json.dumps(likedByWhom)

    whoYouliked = []
    if request.user.is_authenticated:
        whoYouliked = Like.objects.filter(user=request.user).values_list('post__id', flat=True)
        whoYouliked = list(whoYouliked)

    try:
        checkFollow = followers.filter(user_follower=user)
        if len(checkFollow) != 0:
            isFollowing = True
        else:
            isFollowing = False
    except:
        isFollowing = False

    # Pagination
    paginator = Paginator(allPosts, 10)
    page_number = request.GET.get('page')
    posts_of_the_page = paginator.get_page(page_number)

    return render(request, "network/profile.html", {
        "allPosts": allPosts,
        "posts_of_the_page": posts_of_the_page,
        "username": user.username,
        "following": following,
        "followers": followers,
        "isFollowing": isFollowing,
        "user_profile": user,
        "likedByWhom": likedByWhom_json,
        "whoYouliked": whoYouliked
    })


def following(request):
    currentUser = User.objects.get(pk=request.user.id)
    followingPeople = Follow.objects.filter(user=currentUser)
    allPosts = Post.objects.all().order_by('id').reverse()
    allPost = Post.objects.annotate(like_count=Count('likes')).order_by("id").reverse()

    likedByWhom = {}
    for post in allPost:
        users_liked_post = User.objects.filter(user_like__post=post)
        likedByWhom[post.id] = {
            'like_count': users_liked_post.count()  
        }
    likedByWhom_json = json.dumps(likedByWhom)

    whoYouliked = []
    if request.user.is_authenticated:
        whoYouliked = Like.objects.filter(user=request.user).values_list('post__id', flat=True)
        whoYouliked = list(whoYouliked)

    followingPosts = []
    for post in allPosts:
        for person in followingPeople:
            if person.user_follower == post.user:
                followingPosts.append(post)
    # Pagination
    paginator = Paginator(followingPosts, 10)
    page_number = request.GET.get('page')
    posts_of_the_page = paginator.get_page(page_number)

    return render(request, "network/following.html", {
        "allPosts": allPosts,
        "posts_of_the_page": posts_of_the_page,
        "likedByWhom": likedByWhom_json,
        "whoYouliked": whoYouliked
    })



def follow(request):
    userfollow = request.POST['userfollow']  
    currentUser = User.objects.get(pk=request.user.id)
    userfollowData = User.objects.get(username=userfollow)
    f = Follow(user=currentUser, user_follower=userfollowData)  
    f.save()
    user_id = userfollowData.id
    return HttpResponseRedirect(reverse(profile, kwargs={'user_id': user_id}))


def unfollow(request):
    userfollow = request.POST['userfollow']
    currentUser = User.objects.get(pk=request.user.id)
    userfollowData = User.objects.get(username=userfollow)
    f = Follow.objects.get(user=currentUser, user_follower=userfollowData)
    f.delete()
    user_id = userfollowData.id
    return HttpResponseRedirect(reverse(profile, kwargs={'user_id': user_id}))


def login_view(request):
    if request.method == "POST":

        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")

#==============================================#
#   Superuser :-
#   Username:- Admin
#   Email:- sharmarajatraj1@gmail.com
#   Password:- Admin   
#   Rajat - rajat@gmail.com - rajat
#   Amit - amit@gmail.com - amit
# hello I am Rajat raj Sharma , i am a 3rd year student doing enginearing. 