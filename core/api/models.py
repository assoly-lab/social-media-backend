from django.db import models
from django.contrib.auth.models import AbstractBaseUser,BaseUserManager,PermissionsMixin
from PIL import Image
import os
import uuid
from django.core.files.base import ContentFile
from io import BytesIO






class CustomUserManager(BaseUserManager):
    def create_user(self,username,password=None,**extra_fields):
        if not username:
            raise ValueError('an username must be set')
        user = self.model(username=username,**extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self,username,password,**extra_fields):
        extra_fields.setdefault('is_staff',True)
        extra_fields.setdefault('is_superuser',True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have staff privilege.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have superuser privilege ')
        self.create_user(username=username,password=password,**extra_fields)




class CustomUser(AbstractBaseUser,PermissionsMixin):
    email = models.EmailField(unique=True,blank=False)
    username = models.CharField(max_length=35,unique=True,blank=False)
    first_name= models.CharField(max_length=35,blank=False)
    last_name= models.CharField(max_length=35,blank=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    
    objects = CustomUserManager()
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name','last_name','email']

    def __str__(self):
        return self.username




class UserProfile(models.Model):
    user  = models.OneToOneField(CustomUser,on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/',default='avatars/user.jpg', blank=False,null=False)

    def __str__(self) -> str:
        return self.user.username
    
    def save(self, *args, **kwargs):
        if self.avatar and hasattr(self.avatar, 'file'):
            try:
                old_avatar = UserProfile.objects.get(pk=self.pk).avatar
            except UserProfile.DoesNotExist:
                old_avatar = None

            # Only proceed if the avatar is new or different
            if not old_avatar or old_avatar.name != self.avatar.name:
                # Open the image using Pillow
                img = Image.open(self.avatar)

                # Resize the image to 400x400
                img = img.resize((400, 400), Image.LANCZOS)

                # Save the resized image to an in-memory file
                img_io = BytesIO()

                # Get the format from the original image or set a default
                image_format = img.format if img.format else 'png'

                # Save the image in the specified format
                img.save(img_io, format=image_format)
                img_io.seek(0)

                # Generate a new image name by appending a UUID to it
                original_image_name = self.avatar.name
                image_name, extension = os.path.splitext(original_image_name)
                new_image_name = f"{image_name}_{uuid.uuid4()}{extension}"

                # Replace the avatar with the new image
                self.avatar.save(new_image_name, ContentFile(img_io.read()), save=False)

        # Call the parent's save method to continue saving the model instance
        super().save(*args, **kwargs)



class Post(models.Model):
    author = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    content = models.TextField(null=True,blank=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self) -> str:
        return f'{self.author.username} - {self.created_at}'  




class PostMedia(models.Model):

    MEDIA_TYPE_CHOICES = [
        ('image','Image'),
        ('video','Video')
    ]

    post = models.ForeignKey(Post,related_name='media',on_delete=models.CASCADE)
    media_type = models.CharField(max_length=5,choices=MEDIA_TYPE_CHOICES)
    file = models.FileField(upload_to="post_media/")
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.media_type.capitalize()} for {self.post.author.username}'s post"





class Follow(models.Model):
    following = models.ForeignKey(CustomUser,related_name='followers',on_delete=models.CASCADE)
    follower = models.ForeignKey(CustomUser,related_name="following",on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f'{self.follower} follows {self.following}'





class PostLike(models.Model):
    post = models.ForeignKey(Post,related_name='likes',on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post','user')




class Comment(models.Model):
    author = models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='comments')
    post = models.ForeignKey(Post,on_delete=models.CASCADE,related_name='comments')
    content = models.TextField(blank=False,null=False)
    parent = models.ForeignKey('self',blank=True,null=True,related_name='replies', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


    def is_top_level(self):
        return self.parent is None




class CommentLike(models.Model):
    comment = models.ForeignKey(Comment,on_delete=models.CASCADE,related_name='likes')
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('comment','user')