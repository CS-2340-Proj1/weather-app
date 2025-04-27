import requests
from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required
import openai

def index(request):
    """
    Home view: shows current weather for a ZIP code.
    """
    zip_code      = request.GET.get('zip_code')
    unit          = request.GET.get('unit', 'imperial')
    weather_data  = None
    error_message = None
    lat           = None
    lon           = None
    owm_key       = settings.WEATHER_API_KEY

    if zip_code:
        api_key = settings.WEATHER_API_KEY
        url = (
            f"http://api.openweathermap.org/data/2.5/weather"
            f"?zip={zip_code},us&appid={api_key}&units={unit}"
        )
        resp = requests.get(url)

        if resp.status_code == 200:
            weather_data = resp.json()
            lat = weather_data['coord']['lat']
            lon = weather_data['coord']['lon']
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
                f"The current weather is {desc}, {temp}{unit_label}, "
                f"humidity {hum}%, and wind at {wind} {speed_unit}. "
                "Provide two short bullet points: "
                "one recommendation on what to wear, "
                "and one warning about what to watch out for. "
                "Do NOT restate the weather."
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
    })
