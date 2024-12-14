from django.shortcuts import render, HttpResponse, redirect, get_object_or_404, reverse
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_protect
from django.utils.html import escape
from django.db.models import Count, Prefetch
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.core.validators import validate_slug
from django.conf import settings
from .forms import ArticleForm
from .models import Article, Comment
from django.contrib import messages
from django.template.defaultfilters import slugify
from django.contrib.auth.decorators import login_required
import bleach
from django.core.mail import send_mail

@cache_page(settings.CACHE_TTL)
def articles(request):
    keyword = bleach.clean(request.GET.get("keyword", ""))

    if keyword:
        cache_key = f'articles_search_{keyword}'
        articles = cache.get(cache_key)
        
        if articles is None:
            articles = Article.objects.filter(title__icontains=keyword)\
                .select_related('author')\
                .prefetch_related('comments')\
                .annotate(comment_count=Count('comments'))
            cache.set(cache_key, articles, timeout=300)
    else:
        cache_key = 'all_articles'
        articles = cache.get(cache_key)
        
        if articles is None:
            articles = Article.objects.all()\
                .select_related('author')\
                .prefetch_related('comments')\
                .annotate(comment_count=Count('comments'))
            cache.set(cache_key, articles, timeout=300)

    return render(request, "articles.html", {"articles": articles})

def index(request):
    cache_key = 'index_articles'
    articles = cache.get(cache_key)
    
    if articles is None:
        articles = Article.objects.all()\
            .select_related('author')\
            .prefetch_related('comments')[:4]
        cache.set(cache_key, articles, timeout=300)
    
    return render(request, "index.html", {"articles": articles})

@cache_page(settings.CACHE_TTL * 4)  # Cache for 1 hour
def about(request):
    return render(request, "about.html")

@login_required(login_url="users:login")
def dashboard(request):
    cache_key = f'user_dashboard_{request.user.id}'
    articles = cache.get(cache_key)
    
    if articles is None:
        articles = Article.objects.filter(author=request.user)\
            .select_related('author')\
            .prefetch_related('comments')\
            .annotate(comment_count=Count('comments'))
        cache.set(cache_key, articles, timeout=300)
    
    return render(request, "dashboard.html", {"articles": articles})

@login_required(login_url="users:login")
@csrf_protect
@require_http_methods(["GET", "POST"])
def addArticle(request):
    if request.method == "POST":
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                article = form.save(commit=False)
                article.slug = slugify(bleach.clean(article.title))
                article.author = request.user
                article.save()
                
                send_mail(
                    'New Article Published',
                    f'Your article titled {article.title} has been published',
                    settings.EMAIL_HOST_USER,
                    [request.user.email,],
                    fail_silently=False,
                )
                
                # Invalidate relevant caches
                cache.delete('all_articles')
                cache.delete(f'user_dashboard_{request.user.id}')
                cache.delete('index_articles')

                messages.success(request, "Article successfully created and confirmation email has been sent.")
                return redirect("article:dashboard")
            except ValidationError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ArticleForm()

    return render(request, "addarticle.html", {"form": form})

def detail(request, slug):
    try:
        validate_slug(slug)
        cache_key = f'article_detail_{slug}'
        article_data = cache.get(cache_key)
        
        if article_data is None:
            article = get_object_or_404(
                Article.objects.select_related('author')
                .prefetch_related(
                    Prefetch('comments', queryset=Comment.objects.select_related('article'))
                ),
                slug=slug
            )
            comments = list(article.comments.all())  # Convert to list for caching
            article_data = {
                'article': article,
                'comments': comments
            }
            cache.set(cache_key, article_data, timeout=300)
        
        return render(request, "detail.html", article_data)
    except ValidationError:
        messages.error(request, "Invalid article URL")
        return redirect("article:articles")

@login_required(login_url="users:login")
@csrf_protect
@require_http_methods(["GET", "POST"])
def updateArticle(request, slug):
    try:
        validate_slug(slug)
        article = get_object_or_404(Article, slug=slug, author=request.user)
        
        if request.method == "POST":
            form = ArticleForm(request.POST, request.FILES, instance=article)
            if form.is_valid():
                article = form.save(commit=False)
                article.slug = slugify(bleach.clean(article.title))
                article.save()
                
                # Invalidate relevant caches
                cache.delete(f'article_detail_{slug}')
                cache.delete('all_articles')
                cache.delete(f'user_dashboard_{request.user.id}')
                cache.delete('index_articles')
                
                messages.success(request, "Article successfully updated")
                return redirect("article:dashboard")
        else:
            form = ArticleForm(instance=article)
        
        return render(request, "update.html", {"form": form})
    except ValidationError:
        messages.error(request, "Invalid article URL")
        return redirect("article:dashboard")

@login_required(login_url="users:login")
@csrf_protect
@require_http_methods(["POST"])
def deleteArticle(request, slug):
    try:
        validate_slug(slug)
        article = get_object_or_404(Article, slug=slug, author=request.user)
        article_title = article.title
        article.delete()
                
        send_mail(
            'Article Deleted',
            f'Your article titled {article_title} has been deleted.',
            settings.EMAIL_HOST_USER,
            [request.user.email,],
            fail_silently=False,
        )
        
        # Invalidate relevant caches
        cache.delete(f'article_detail_{slug}')
        cache.delete('all_articles')
        cache.delete(f'user_dashboard_{request.user.id}')
        cache.delete('index_articles')
        
        messages.success(request, "Article successfully deleted")
        return redirect("article:dashboard")
    except ValidationError:
        messages.error(request, "Invalid article URL")
        return redirect("article:dashboard")

@login_required(login_url="users:login")
@csrf_protect
@require_http_methods(["POST"])
def addComment(request, slug):
    try:
        validate_slug(slug)
        article = get_object_or_404(Article, slug=slug)
        
        comment_author = bleach.clean(request.POST.get("comment_author", ""))
        comment_content = bleach.clean(request.POST.get("comment_content", ""))
        
        if comment_author and comment_content:
            Comment.objects.create(
                comment_author=comment_author,
                comment_content=comment_content,
                article=article
            )
            
            # Invalidate article detail cache
            cache.delete(f'article_detail_{slug}')
            
            messages.success(request, "Comment added successfully")
        else:
            messages.error(request, "Comment author and content are required")
            
        return redirect(reverse("article:detail", kwargs={"slug": slug}))
    except ValidationError:
        messages.error(request, "Invalid article URL")
        return redirect("article:articles")
