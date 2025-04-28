import requests
from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import redirect
from .models import Alert
from django.db.models import Q
from django.urls import reverse
import openai
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

def index(request):
    zip_code = request.GET.get('zip_code')
    unit = request.GET.get('unit', 'imperial')
    weather_data = None
    error_message = None
    lat = lon = None
    owm_key = settings.WEATHER_API_KEY
    alerts_data = []

    if zip_code:
        api_key = settings.WEATHER_API_KEY
        url = f"http://api.openweathermap.org/data/2.5/weather?zip={zip_code},us&appid={api_key}&units={unit}"
        resp = requests.get(url)

        if resp.status_code == 200:
            weather_data = resp.json()
            lat = weather_data['coord']['lat']
            lon = weather_data['coord']['lon']

            # NOAA alerts
            alerts_url = f"https://api.weather.gov/alerts/active?point={lat},{lon}"
            try:
                alert_resp = requests.get(alerts_url, headers={'User-Agent': 'weather-app/1.0'})
                if alert_resp.status_code == 200:
                    alert_json = alert_resp.json()
                    noaa_alerts = alert_json['features'] if alert_json['features'] else []
                    alerts_data += noaa_alerts
            except Exception:
                pass

            # Saved alerts
            if request.user.is_authenticated:
                saved_alerts = Alert.objects.filter(Q(public=True) | Q(user=request.user),zip_code=zip_code)
                alerts_data += list(saved_alerts)
            else:
                error_message = "Invalid ZIP code—could not retrieve weather."

    return render(request, 'weather/index.html', {
        'weather_data':  weather_data,
        'error_message': error_message,
        'zip_code':      zip_code,
        'unit':          unit,
        'lat':           lat,
        'lon':           lon,
        'owm_key':       owm_key,
        'alerts_data':   alerts_data,
    })


def forecast(request):
    """
    7-day forecast via weather.gov (no key needed).
    """
    zip_code      = request.GET.get('zip_code')
    unit          = request.GET.get('unit', 'imperial')  # preserves your buttons/links
    forecast_data = None
    error_message = None

    if zip_code:
        # 1) Geocode ZIP → lat,lon with OpenStreetMap
        geo_url = (
            "https://nominatim.openstreetmap.org/search"
            f"?postalcode={zip_code}&country=USA&format=json"
        )
        geo = requests.get(geo_url, headers={'User-Agent': 'weather-app/1.0'})
        if geo.status_code != 200 or not geo.json():
            error_message = "Could not geocode that ZIP code."
        else:
            loc = geo.json()[0]
            lat, lon = loc['lat'], loc['lon']

            # 2) Ask NOAA for the “points” metadata
            pts_url = f"https://api.weather.gov/points/{lat},{lon}"
            pts = requests.get(pts_url)
            if pts.status_code != 200:
                error_message = "Could not find forecast area for those coordinates."
            else:
                # 3) Fetch the 7-day forecast URL
                fc_url = pts.json()['properties']['forecast']
                fc    = requests.get(fc_url)
                if fc.status_code != 200:
                    error_message = "Error fetching forecast data."
                else:
                    periods = fc.json()['properties']['periods']
                    # grab the first 7 daytime entries
                    forecast_data = [p for p in periods if p['isDaytime']][:7]

    return render(request, 'weather/forecast.html', {
        'zip_code'     : zip_code,
        'unit'         : unit,
        'forecast_data': forecast_data,
        'error_message': error_message,
    })

@require_POST
@login_required
def add_alert(request):
    city_name = request.POST.get("city_name")
    zip_code = request.POST.get("zip_code")
    alert_text = request.POST.get("alert_text")

    if city_name and zip_code and alert_text:
        Alert.objects.create(
            user=request.user,
            city_name=city_name,
            zip_code=zip_code,
            alert_text=alert_text,
            public=request.user.is_staff
        )
    return redirect(f"{reverse('weather.summary')}?zip_code={zip_code}&unit=imperial")


from django.views.decorators.http import require_POST

@require_POST
@login_required
def delete_alert(request, alert_id):
    try:
        alert = Alert.objects.get(id=alert_id)
    except Alert.DoesNotExist:
        return redirect('weather.alerts')

    if alert.public:
        if request.user.is_staff:
            alert.delete()
    else:
        if alert.user == request.user:
            alert.delete()

    return redirect('weather.alerts')

@login_required
def alerts_view(request):
    all_alerts = Alert.objects.all()

    alerts = [
        alert for alert in all_alerts
        if (not alert.public and alert.user == request.user) or
           (alert.public and not alert.is_dismissed_for(request.user))
    ]

    return render(request, 'weather/alerts.html', {
        'alerts': alerts
    })

@require_POST
@login_required
def dismiss_alert(request, alert_id):
    alert = get_object_or_404(Alert, id=alert_id)

    if alert.public:
        alert.dismissed_by.add(request.user)
    elif alert.user == request.user:
        alert.delete()

    return redirect('weather.alerts')

@login_required
def summary(request):
    """
    Shows a one-sentence AI summary plus clothing/safety suggestions based on a ZIP code.
    """
    zip_code      = request.GET.get('zip_code')
    unit          = request.GET.get('unit', 'imperial')
    weather_data  = None
    summary_text  = None
    suggestions   = None
    error_message = None
    alerts_data = []

    if zip_code:
        api_key = settings.WEATHER_API_KEY

        # Fetch current weather
        url = (
            f"http://api.openweathermap.org/data/2.5/weather"
            f"?zip={zip_code},us&appid={api_key}&units={unit}"
        )
        resp = requests.get(url)

        if resp.status_code == 200:
            weather_data = resp.json()
            desc       = weather_data['weather'][0]['description']
            temp       = weather_data['main']['temp']
            hum        = weather_data['main']['humidity']
            wind       = weather_data['wind']['speed']
            unit_label = 'F' if unit == 'imperial' else 'C'
            speed_unit = 'mph' if unit == 'imperial' else 'm/s'

            # 1) AI one-sentence summary
            prompt = (
                f"Summarize today's weather in one sentence: "
                f"{desc}, temp {temp}{unit_label}, "
                f"humidity {hum}%, wind {wind} {speed_unit}."
            )
            openai.api_key = settings.OPENAI_API_KEY
            try:
                chat = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a concise assistant that summarizes weather in one sentence."
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=60,
                    temperature=0.5,
                )
                summary_text = chat.choices[0].message.content.strip()
            except Exception:
                summary_text = (
                    f"{desc.capitalize()} with temp {temp}{unit_label}, "
                    f"humidity {hum}%, wind {wind} {speed_unit}."
                )

            # 2) AI clothing & safety suggestions
            suggestion_prompt = (
                f"The current weather in ZIP code {zip_code} is {desc}, with a temperature of {temp}{unit_label}, "
                f"humidity at {hum}%, and wind speed of {wind} {speed_unit}. "
                "Please provide two helpful bullet points:\n"
                "• One recommendation on what the user should wear.\n"
                "• One warning or suggestion on what the user should be aware of."
            )
            try:
                chat2 = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": "You provide concise clothing and safety advice based on weather."
                        },
                        {"role": "user", "content": suggestion_prompt},
                    ],
                    max_tokens=80,
                    temperature=0.7,
                )
                suggestions = chat2.choices[0].message.content.strip()
            except Exception:
                # Fallback
                if 'rain' in desc:
                    suggestions = (
                        "• Wear a waterproof jacket or carry an umbrella.\n"
                        "• Watch out for slippery surfaces."
                    )
                elif 'snow' in desc or 'sleet' in desc:
                    suggestions = (
                        "• Bundle up in warm layers and insulated boots.\n"
                        "• Watch out for icy sidewalks."
                    )
                elif temp <= 50:
                    suggestions = (
                        "• Wear extra warm layers.\n"
                        "• Be cautious of the cold wind."
                    )
                elif temp >= 85:
                    suggestions = (
                        "• Wear light, breathable clothing.\n"
                        "• Stay hydrated and seek shade."
                    )
                else:
                    suggestions = (
                        "• Dress comfortably for mild weather.\n"
                        "• Enjoy your day!"
                    )
        else:
            error_message = "Invalid ZIP code—could not retrieve weather."


    return render(request, 'weather/summary.html', {
        'weather_data':  weather_data,
        'summary':       summary_text,
        'suggestions':   suggestions,
        'error_message': error_message,
        'zip_code':      zip_code,
        'unit':          unit,
        'alerts_data':   alerts_data,
    })
