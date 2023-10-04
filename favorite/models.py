from django.db import models

from user.models import User


# Create your models here.

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def info(self):
        return {
            'id': self.id,
            'title': self.title,
            'items': [item.info() for item in self.favoriteitem_set.all().order_by('-created_at')],
        }


class FavoriteItem(models.Model):
    favorite = models.ForeignKey(Favorite, on_delete=models.CASCADE)
    work = models.CharField(max_length=100)
    title = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def info(self):
        return {
            'id': self.id,
            'work': self.work,
            'title': self.title,
        }