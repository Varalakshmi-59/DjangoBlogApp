from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from django.template.defaultfilters import slugify
# Create your models here.

class Article(models.Model):
    author = models.ForeignKey("auth.User", on_delete=models.CASCADE, verbose_name="Author")
    title = models.CharField(max_length=50, verbose_name="Title")
    content = CKEditor5Field('Text', config_name='extends')
    created_date = models.DateTimeField(auto_now_add=True, verbose_name="Creation Date")
    article_image = models.FileField(blank=True, null=True, verbose_name="Add Photo to the Article")
    slug = models.SlugField(unique=True, max_length=100)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        return super(Article, self).save(*args, **kwargs)        

    class Meta:
        ordering = ['-created_date']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['author']),
            models.Index(fields=['created_date']),
        ]

class Comment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, verbose_name="Article", related_name="comments")
    comment_author = models.CharField(max_length=50, verbose_name="Name")
    comment_content = models.CharField(max_length=200, verbose_name="Comment")
    comment_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.comment_content
    
    class Meta:
        ordering = ['-comment_date']