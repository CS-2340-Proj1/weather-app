from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import FavoriteZip

@login_required
def index(request):
    zips = request.user.favorite_zips.all()
    return render(request, 'favorites/index.html', {'zips': zips})

@login_required
def add(request):
    if request.method == 'POST':
        FavoriteZip.objects.get_or_create(
            user=request.user,
            zip_code=request.POST.get('zip_code', '').strip(),
            defaults={'city_name': request.POST.get('city_name', '').strip()}
        )
    return redirect('favorites.index')

@login_required
def delete(request, id):
    fav = get_object_or_404(FavoriteZip, pk=id, user=request.user)
    fav.delete()
    return redirect('favorites.index')