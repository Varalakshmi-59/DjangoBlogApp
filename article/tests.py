from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from article.models import Article, Comment
from article.forms import ArticleForm
from django.core.files.uploadedfile import SimpleUploadedFile

class ArticleViewsTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create a test article
        self.article = Article.objects.create(
            title='Test Article',
            content='Test Content',
            author=self.user,
            slug='test-article'
        )
        
        # Create a test client
        self.client = Client()

    def test_articles_list_view(self):
        """Test the articles list view"""
        # Test without keyword
        response = self.client.get(reverse('article:articles'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'articles.html')
        self.assertIn('articles', response.context)
        
        # Test with keyword
        response = self.client.get(f"{reverse('article:articles')}?keyword=Test")
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.article, response.context['articles'])

    def test_index_view(self):
        """Test the index view"""
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        self.assertIn('articles', response.context)

    def test_about_view(self):
        """Test the about view"""
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'about.html')

    def test_dashboard_view(self):
        """Test the dashboard view"""
        # Test without login
        response = self.client.get(reverse('article:dashboard'))
        self.assertEqual(response.status_code, 302)  # Should redirect to login
        
        # Test with login
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('article:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')
        self.assertIn('articles', response.context)

    def test_add_article(self):
        """Test adding a new article"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test GET request
        response = self.client.get(reverse('article:addarticle'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'addarticle.html')
        
        # Test POST request
        article_data = {
            'title': 'New Test Article',
            'content': 'New Test Content',
        }
        response = self.client.post(reverse('article:addarticle'), article_data)
        self.assertEqual(response.status_code, 302)  # Should redirect to dashboard
        self.assertTrue(Article.objects.filter(title='New Test Article').exists())

    def test_article_detail(self):
        """Test article detail view"""
        response = self.client.get(
            reverse('article:detail', kwargs={'slug': self.article.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'detail.html')
        self.assertEqual(response.context['article'], self.article)

    def test_update_article(self):
        """Test updating an article"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test GET request
        response = self.client.get(
            reverse('article:update', kwargs={'slug': self.article.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'update.html')
        
        # Test POST request
        updated_data = {
            'title': 'Updated Test Article',
            'content': 'Updated Test Content',
        }
        response = self.client.post(
            reverse('article:update', kwargs={'slug': self.article.slug}),
            updated_data
        )
        self.assertEqual(response.status_code, 302)  # Should redirect to dashboard
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, 'Updated Test Article')

    def test_delete_article(self):
        """Test deleting an article"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('article:delete', kwargs={'slug': self.article.slug})
        )
        self.assertEqual(response.status_code, 302)  # Should redirect to dashboard
        self.assertFalse(Article.objects.filter(slug=self.article.slug).exists())

    def test_add_comment(self):
        """Test adding a comment to an article"""
        comment_data = {
            'comment_author': 'Test Commenter',
            'comment_content': 'Test Comment Content'
        }
        response = self.client.post(
            reverse('article:comment', kwargs={'slug': self.article.slug}),
            comment_data
        )
        self.assertEqual(response.status_code, 302)  # Should redirect to article detail
        self.assertTrue(
            Comment.objects.filter(
                article=self.article,
                comment_author='Test Commenter'
            ).exists()
        )

class ArticleFormTest(TestCase):
    def test_article_form_valid(self):
        """Test article form with valid data"""
        form_data = {
            'title': 'Test Article',
            'content': 'Test Content'
        }
        form = ArticleForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_article_form_invalid(self):
        """Test article form with invalid data"""
        form_data = {
            'title': '',  # Title is required
            'content': 'Test Content'
        }
        form = ArticleForm(data=form_data)
        self.assertFalse(form.is_valid())