from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import AbstractUser
from django.db.models import Sum

class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

# Create your models here.
class CommonProperty(models.Model):
    created_by = models.ForeignKey(User,null=True,on_delete=models.CASCADE,related_name="%(class)s_created_by")
    updated_by = models.ForeignKey(User,null=True,on_delete=models.CASCADE,related_name="%(class)s_updated_by")
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def updatedby(self,user):
        updated_by = user
    class Meta:
        abstract = True

class Company(CommonProperty):
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name

class Depot(CommonProperty):
    code = models.CharField(max_length=10,primary_key=True)
    name = models.CharField(max_length=150)
    company = models.ForeignKey(Company,on_delete=models.RESTRICT)
    map_coordinates = models.TextField()

    def __str__(self):
        return self.name

class DepotAssetId(models.Model):
    depot = models.ForeignKey(Depot,on_delete=models.CASCADE)
    next_id = models.IntegerField(default=1)

class AssetClass(CommonProperty):
    name = models.CharField(max_length=150)

class Asset(CommonProperty):

    ASSET_STATUSES = (
        ('A','Active'),
        ('IA','Inactive'),
        ('D','Disposed'),
        ('I','Idle'),
        ('IN','Installed'),
        ('R','Reclass')
        )

    asset_no = models.CharField(max_length=150)
    date_acquired = models.DateField()
    asset_class = models.ForeignKey(AssetClass,on_delete=models.RESTRICT)
    description = models.CharField(max_length=150)
    location = models.CharField(max_length=150)
    depot = models.ForeignKey(Depot,on_delete=models.RESTRICT)
    quantity = models.IntegerField()
    unit = models.CharField(max_length=10)
    remarks = models.TextField(max_length=1000)
    serial_number = models.CharField(max_length=150)
    status = models.CharField(max_length=3,choices=ASSET_STATUSES,default='A')
    asset_tagability = models.CharField(max_length=150,blank=True)
    cost = models.DecimalField(max_digits=16,decimal_places=2)
    life = models.DecimalField(max_digits=16,decimal_places=2)
    accum_depreciation = models.DecimalField(max_digits=16,decimal_places=2)

    @property
    def monthly_depreciation_expense(self):
        return self.cost / self.life

    @property
    def net_book_value(self):
        return self.cost - self.accum_depreciation

    @property
    def accum_depreciation(self):
        return MonthlyDepreciation.objects.filter(asset=self).aggregate(Sum('expense'))

    def __str__(self):
        return self.description

    class Meta:
        permissions = [('can_dispose_asset','Can Dispose Asset'),
                       ('can_transfer_asset','Can Transfer Asset')]
    
class MonthlyDepreciation(models.Model):
    asset = models.ForeignKey(Asset,on_delete=models.CASCADE)
    date_added = models.DateField(auto_now_add=True)
    expense = models.DecimalField(max_digits=16,decimal_places=2)