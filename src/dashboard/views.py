from django.shortcuts import render
from anime.models import Anime
from suggestions.models import Suggestion
from django.shortcuts import redirect

def home_view(request):
    context = {}
    user = request.user
    if not user.is_authenticated:
        return render(request, 'home.html', context)
    context['endless_path'] = '/'
    suggestion_qs = Suggestion.objects.filter(user=user, did_rate=False)
    max_anime = 25
    request.session['total-new-suggestions'] = suggestion_qs.count()
    if suggestion_qs.exists():
        anime_ids = suggestion_qs.order_by("-value").values_list('object_id', flat=True)
        qs = Anime.objects.by_id_order(anime_ids)
        context['object_list'] = qs[:max_anime]
    else:
        return redirect('anime/popular')
    if request.htmx:
        return render(request, "anime/snippet/infinite.html", context)
    return render(request, "dashboard/main.html", context)
