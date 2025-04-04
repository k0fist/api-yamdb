from django.contrib import admin
from .models import User, Genre, Category, Title, Review, Comment


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'email',
        'bio',
        'role',
        'first_name',
        'last_name'
    )
    list_editable = (
        'email',
        'bio',
        'role',
        'first_name',
        'last_name'
    )
    search_fields = ('username',)
    list_filter = ('username',)
    list_display_links = ('username',)


class FirstBaseAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug'
    )
    list_editable = ('slug',)
    search_fields = ('name',)
    list_filter = ('name',)
    list_display_links = ('name',)


class GenreAdmin(FirstBaseAdmin):
    pass


class CategoryAdmin(FirstBaseAdmin):
    pass


class TitleAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'category',
        'year',
        'description'
    )
    list_editable = (
        'category',
        'description'
    )
    search_fields = ('name',)
    list_filter = ('name',)
    list_display_links = ('name',)
    filter_horizontal = ('genre',)


class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        'author',
        'text',
        'pub_date',
        'title',
        'score'
    )
    list_editable = (
        'author',
        'text',
        'pub_date',
        'score'
    )
    search_fields = ('title',)
    list_filter = ('title',)
    list_display_links = ('title',)


class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'author',
        'text',
        'pub_date',
        'review'
    )
    list_editable = (
        'author',
        'text',
        'pub_date',
        'review'
    )
    search_fields = ('title',)
    list_filter = ('title',)
    list_display_links = ('title',)


admin.site.register(User, UserAdmin)
admin.site.register(Genre, GenreAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Title, TitleAdmin)
admin.site.register(Review)
admin.site.register(Comment)
admin.site.empty_value_display = 'Не задано'
