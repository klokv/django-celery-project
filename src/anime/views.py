from django.views import generic 
from .models import Anime

SORTING_CHOICES = {
    "recommended": "popular",
    "not recommended": "unpopular",
    "popular": "-rating_count",
    "not popular": "rating_count",
    "top rated": "-rating_avg",
    "low rated": "rating_avg",
    "recent": "-release_date",
    "old": "release_date"
}

class AnimeListView(generic.ListView):
    paginate_by = 50

    def get_queryset(self):
        request = self.request
        sort = request.GET.get('sort') or request.session.get('anime_sort_order') or 'popular'
        qs = Anime.objects.all()
        if sort is not None:
            request.session['anime_sort_order'] = sort
            if sort == 'popular':
                return qs.popular()
            elif sort == 'unpopular':
                return qs.popular(reverse=True)
            qs = qs.order_by(sort)
        return qs

    def get_template_names(self):
        request = self.request
        if request.htmx:
            return ['anime/snippet/list.html']
        return ['anime/list-view.html']

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        request = self.request
        user = request.user
        context['sorting_choices'] = SORTING_CHOICES
        if user.is_authenticated:
            object_list = context['object_list']
            object_ids = [x.id for x in object_list]
            my_ratings = user.rating_set.anime().as_object_dict(object_ids=object_ids)
            context['my_ratings'] = my_ratings
        return context

anime_list_view = AnimeListView.as_view()

class AnimeDetailView(generic.DetailView):
    template_name = 'anime/detail.html'
    queryset = Anime.objects.all()
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        request = self.request
        user = request.user
        if user.is_authenticated:
            object = context['object']
            object_ids = [object.id]
            my_ratings = user.rating_set.anime().as_object_dict(object_ids=object_ids)
            context['my_ratings'] = my_ratings
        return context

anime_detail_view = AnimeDetailView.as_view()


class AnimeInfiniteRatingView(AnimeDetailView):
    def get_object(self):
        user = self.request.user
        return Anime.objects.all().order_by("?").first()
    
    def get_template_names(self):
        request = self.request
        if request.htmx:
            return ['anime/snippet/infinite.html']
        return ['anime/infinite-view.html']  

anime_infinite_rating_view = AnimeInfiniteRatingView.as_view()



class AnimePopularView(AnimeDetailView):
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['endless_path'] = '/anime/popular/'
        return context
    
    def get_object(self):
        user = self.request.user
        exclude_ids = []
        if user.is_authenticated:
            exclude_ids = [x.object_id for x in user.rating_set.filter(active=True)]
        anime_id_options = Anime.objects.all().popular().exclude(id__in=exclude_ids).values_list('id', flat=True)[:100]
        return Anime.objects.filter(id__in=anime_id_options).order_by("?").first()
    
    def get_template_names(self):
        request = self.request
        if request.htmx:
            return ['anime/snippet/infinite.html']
        return ['anime/infinite-view.html']   

anime_popular_view = AnimePopularView.as_view()