import os
import re
import json
import urllib.request
import urllib.parse

# Klucz API do serwisu The Movie Database (TMDb)
# Możesz wpisać go tutaj na stałe lub podać w konsoli podczas pierwszego uruchomienia
TMDB_API_KEY = ""

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

def get_tmdb_api_key():
    return TMDB_API_KEY or os.environ.get("TMDB_API_KEY")

def translate_text(text, sl="en", tl="pl"):
    if not text:
        return ""
    clean_text = re.sub(r'<[^>]+>', '', text).strip()
    encoded_text = urllib.parse.quote(clean_text)
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={sl}&tl={tl}&dt=t&q={encoded_text}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
        translated = "".join([part[0] for part in res[0] if part and part[0]])
        return translated
    except Exception as e:
        return clean_text

def find_movie(title, year, api_key):
    query = urllib.parse.quote(title)
    # Najpierw szukamy z precyzyjnym uwzględnieniem roku premiery
    url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={query}&primary_release_year={year}&language=pl-PL"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
        results = res.get('results', [])
        
        # Jeśli nie znaleziono, próbujemy bez filtru roku
        if not results:
            url_no_year = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={query}&language=pl-PL"
            req = urllib.request.Request(url_no_year, headers=HEADERS)
            with urllib.request.urlopen(req) as response:
                res = json.loads(response.read().decode('utf-8'))
            results = res.get('results', [])
            
        return results[0] if results else None
    except Exception as e:
        print(f"Błąd wyszukiwania TMDb dla '{title}': {e}")
        return None

def fetch_movie_details(movie_id, api_key, lang="pl-PL"):
    # append_to_response=credits pobiera dodatkowe informacje, w tym reżysera
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language={lang}&append_to_response=credits"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Błąd pobierania szczegółów TMDb dla ID {movie_id}: {e}")
        return None

def detect_html_file():
    if os.path.exists("index_updated.html"):
        return "index_updated.html"
    elif os.path.exists("index.html"):
        return "index.html"
    return None

def get_next_index(html_content):
    numbers = re.findall(r'<h2 class="card-title">(\d+)\.', html_content)
    if not numbers:
        return 1
    return max(int(n) for n in numbers) + 1

def append_to_html(file_path, card_html):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    grid_end_pattern = r'</div>\s*</main>'
    replacement = f"{card_html}\n</div>\n</main>"
    new_content = re.sub(grid_end_pattern, replacement, content, flags=re.IGNORECASE)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)

def build_search_buttons(query_title):
    encoded_query_plus = urllib.parse.quote_plus(query_title)
    query_lower = query_title.lower()
    encoded_query_upflix = urllib.parse.quote_plus(query_lower)
    encoded_query_filmweb = urllib.parse.quote(query_lower)
    
    return f"""<div class="search-buttons-grid">
<a class="btn-search btn-tmdb" href="https://www.themoviedb.org/search?query={encoded_query_plus}" target="_blank">TMDb</a>
<a class="btn-search btn-imdb" href="https://www.imdb.com/find?q={encoded_query_plus}" target="_blank">IMDb</a>
<a class="btn-search btn-tropes" href="https://tvtropes.org/pmwiki/search_result.php?q={encoded_query_plus}" target="_blank">Tropes</a>
<a class="btn-search btn-filmweb" href="https://www.filmweb.pl/search#/all?query={encoded_query_filmweb}" target="_blank">Filmweb</a>
<a class="btn-search btn-upflix" href="https://upflix.pl/{encoded_query_upflix}" target="_blank">Upflix</a>
</div>"""

def create_card_string(index_num, custom_title, show_year, meta_info, director_info, genres_pl, description_pl, show_name, img_src_path):
    buttons_html = build_search_buttons(show_name)
    encoded_query_plus = urllib.parse.quote_plus(show_name)
    trailer_url = f"https://www.youtube.com/results?search_query={encoded_query_plus}+{show_year}+Official+Trailer"
    
    return f"""<!-- {index_num}. {custom_title} -->
<article class="card">
<div class="card-image-container">
<img alt="{custom_title}" class="card-image" loading="lazy" src="data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==" data-src="{img_src_path}"/>
</div>
<div class="card-content">
<div class="card-header">
<div class="title-wrapper">
<div>
<h2 class="card-title">{index_num}. {custom_title}</h2>
<span class="years">({show_year})</span>
</div>
</div>
<div class="meta-info">{meta_info}</div>
<div class="director-info">{director_info}</div>
<div class="genre-info">{genres_pl}</div>
</div>
<p class="description">{description_pl}</p>
</div>
<div class="card-footer">
<a class="btn-trailer" href="{trailer_url}" target="_blank">
<svg viewbox="0 0 24 24"><path d="M8 5v14l11-7z"></path></svg> Zwiastun na YouTube
</a>
{buttons_html}
</div>
</article>"""

def add_single_movie(html_file, title, year, api_key, is_bulk=False):
    """Przetwarza i dodaje pojedynczy film na podstawie nazwy i roku."""
    search_titles = [title]
    if "/" in title:
        parts = [p.strip() for p in title.split("/")]
        if len(parts) >= 2:
            # Pierwsza próba po nazwie oryginalnej, druga po polskiej
            search_titles = [parts[1], parts[0]]

    movie_data = None
    used_title = None
    for t in search_titles:
        movie_data = find_movie(t, year, api_key)
        if movie_data:
            used_title = t
            break

    if not movie_data:
        print(f"[Błąd] Nie znaleziono filmu dla '{title}' ({year}) w bazie TMDb.")
        return False
        
    details = fetch_movie_details(movie_data['id'], api_key, lang="pl-PL")
    if not details:
        print(f"[Błąd] Nie udało się pobrać szczegółowych danych dla '{used_title}' z TMDb.")
        return False
        
    movie_name = details.get('title', used_title)
    release_date = details.get('release_date', '')
    movie_year = release_date[:4] if release_date else str(year)
    
    # Pobieranie gatunków
    genres_list = details.get('genres', [])
    genres_pl = ", ".join([g['name'] for g in genres_list]) if genres_list else "Brak gatunku"
    
    # Czas trwania
    runtime = details.get('runtime')
    meta_info = f"{runtime} min" if runtime else "Brak danych o czasie trwania"
    
    # Reżyseria
    credits = details.get('credits', {})
    crew = credits.get('crew', [])
    directors = [member['name'] for member in crew if member.get('job') == 'Director']
    director_name = ", ".join(directors) if directors else "Nieznany"
    director_info = f"Reżyseria: {director_name}"

    # Przygotowanie opisów
    description_tmdb_pl = details.get('overview', '').strip()
    
    # Jeżeli brak polskiego opisu, pobierz i przetłumacz angielski
    description_tmdb_translated = ""
    if not description_tmdb_pl:
        details_en = fetch_movie_details(movie_data['id'], api_key, lang="en-US")
        if details_en:
            overview_en = details_en.get('overview', '').strip()
            if overview_en:
                description_tmdb_translated = translate_text(overview_en)

    description_pl = ""
    
    if not is_bulk:
        print("\n" + "-"*35)
        print(f"ZNALEZIONO: {movie_name} ({movie_year})")
        print(f"{director_info} | Czas trwania: {meta_info}")
        print(f"Gatunki: {genres_pl}")
        print("-"*35)
        
        # Wybór opisu
        if description_tmdb_pl:
            print(f"\n[1] Znaleziono polski opis w bazie TMDb:")
            print(f"--------------------------------------------------\n{description_tmdb_pl}\n--------------------------------------------------")
            print("Co chcesz zrobić?")
            print("[1] Zaakceptuj ten opis")
            print("[2] Pozostaw opis pusty")
            
            choice = input("Wybór [1, 2 - Domyślnie: 1]: ").strip()
            if choice == "2":
                print("Opis pozostanie pusty.")
            else:
                description_pl = description_tmdb_pl
        elif description_tmdb_translated:
            print(f"\n[1] Znaleziono opis angielski, przetłumaczony automatycznie:")
            print(f"--------------------------------------------------\n{description_tmdb_translated}\n--------------------------------------------------")
            print("Czy akceptujesz ten opis?")
            print("[1] Tak, zaakceptuj")
            print("[2] Nie, pozostaw opis pusty")
            
            choice = input("Wybór [1, 2 - Domyślnie: 1]: ").strip()
            if choice == "2":
                print("Opis pozostanie pusty.")
            else:
                description_pl = description_tmdb_translated
        else:
            print("\n[!] Nie odnaleziono opisu filmu.")
        
        confirm = input("\nCzy chcesz dodać ten film? (T/N): ").strip().lower()
        if confirm not in ('t', 'tak', ''):
            print("Pominięto.")
            return False
            
        custom_title = input(f"Wyświetlana nazwa w katalogu [Domyślnie: '{title}']: ").strip()
        if not custom_title:
            custom_title = title
    else:
        # Masowo = automatyczny wybór
        custom_title = title
        print(f"[Masowy] Przetwarzanie: {movie_name} ({movie_year})...")
        if description_tmdb_pl:
            description_pl = description_tmdb_pl
            print(f"   [Masowy] Wybrano polski opis z TMDb")
        elif description_tmdb_translated:
            description_pl = description_tmdb_translated
            print("   [Masowy] Wybrano przetłumaczony opis")
        else:
            print("   [Masowy] Brak opisu")

    with open(html_file, "r", encoding="utf-8") as f:
        html_content = f.read()
    next_index = get_next_index(html_content)
    
    # Obsługa grafiki (plakatu)
    poster_path_suffix = details.get('poster_path')
    ext = ".jpg"
    img_src_path = f"{next_index}{ext}" 
    
    # Zapisz w folderze 'img' jeśli takowy istnieje
    if os.path.exists("img") and os.path.isdir("img"):
        img_src_path = f"img/{next_index}{ext}"
    
    if poster_path_suffix:
        image_url = f"https://image.tmdb.org/t/p/w500{poster_path_suffix}"
        try:
            img_req = urllib.request.Request(image_url, headers=HEADERS)
            with urllib.request.urlopen(img_req) as img_response:
                with open(img_src_path, "wb") as img_file:
                    img_file.write(img_response.read())
        except Exception as e:
            print(f"   [Ostrzeżenie] Nie pobrano grafiki dla nr {next_index}: {e}")
            
    # Zapis karty w strukturze HTML
    card_html = create_card_string(next_index, custom_title, movie_year, meta_info, director_info, genres_pl, description_pl, movie_name, img_src_path)
    append_to_html(html_file, card_html)
    
    print(f"   [Sukces] Dodano pomyślnie jako pozycję nr {next_index} ({img_src_path})")
    return True

def safe_read_lines(file_path):
    """Próbuje bezpiecznie odczytać plik z najpopularniejszymi kodowaniami na systemie Windows."""
    encodings = ['utf-8', 'cp1250', 'windows-1250', 'iso-8859-2']
    
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                return f.readlines()
        except UnicodeDecodeError:
            continue
            
    print(f"[!] Nie udało się odczytać pliku {file_path}. Zapisz go w notatniku jako UTF-8.")
    return []

def main():
    global TMDB_API_KEY
    html_file = detect_html_file()
    if not html_file:
        print("Błąd: Nie odnaleziono pliku HTML (np. index.html) w tym folderze!")
        input("\nNaciśnij Enter, aby zamknąć program...")
        return

    print(f"Wykryto plik katalogu: '{html_file}'")
    
    # Sprawdzenie obecności klucza TMDb
    api_key = get_tmdb_api_key()
    if not api_key:
        print("\n[!] Wymagany jest klucz TMDB_API_KEY do działania wyszukiwania filmów.")
        print("Klucz można uzyskać za darmo po rejestracji na stronie https://www.themoviedb.org")
        key_input = input("Wprowadź swój klucz TMDb: ").strip()
        if key_input:
            TMDB_API_KEY = key_input
            api_key = key_input
            print("[+] Klucz TMDb został ustawiony dla tej sesji.")
        else:
            print("[Błąd] Brak klucza TMDb uniemożliwia działanie. Zamykanie...")
            input("\nNaciśnij Enter, aby zamknąć...")
            return

    print("\nWybierz tryb pracy:")
    print("[1] Interaktywny (ręczne wpisywanie krok po kroku)")
    print("[2] Masowy z pliku (automatyczne pobieranie z listy w pliku 'filmy.txt')")
    
    choice = input("Wybierz tryb [1 lub 2, Domyślnie: 1]: ").strip()
    
    if choice == "2":
        import_file = "filmy.txt"
        if not os.path.exists(import_file):
            with open(import_file, "w", encoding="utf-8") as f:
                f.write("# Wpisz tu filmy w formacie: Tytuł, Rok lub Tytuł (Rok)\n# Przykłady:\n# Incepcja, 2010\n# Gladiator (2000)\n")
            print(f"\n[!] Utworzono pusty plik '{import_file}'.")
            print("Wpisz do niego pożądane filmy, zapisz plik i uruchom skrypt ponownie.")
            input("\nNaciśnij Enter, aby zakończyć...")
            return
            
        print(f"\nWczytywanie listy z '{import_file}'...")
        # Zastępujemy zwykłe odczytywanie bezpieczną funkcją fall-back'ującą
        lines = safe_read_lines(import_file)
        if not lines:
            return
            
        to_process = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            # Formaty "Gladiator, 2000" lub "Gladiator, (2000)"
            if "," in line:
                parts = line.split(",")
                title = ",".join(parts[:-1]).strip()
                # Usuwamy nawiasy z roku, jeśli ktoś wpisał po przecinku w nawiasach
                year = parts[-1].replace("(", "").replace(")", "").strip()
                if title and year.isdigit():
                    to_process.append((title, int(year)))
            # Format "Gladiator (2000)" bez przecinka
            else:
                match = re.search(r'^(.*?)\s*\((\d{4})\)$', line)
                if match:
                    to_process.append((match.group(1).strip(), int(match.group(2))))
                    
        if not to_process:
            print("Plik 'filmy.txt' nie zawiera poprawnych wpisów. Upewnij się, że wpisano np. 'Gladiator (2000)'")
            return
            
        print(f"Odnaleziono {len(to_process)} pozycji. Rozpoczynanie importu masowego...")
        success_count = 0
        for title, year in to_process:
            if add_single_movie(html_file, title, year, api_key, is_bulk=True):
                success_count += 1
        print(f"\nUkończono! Pomyślnie dodano {success_count} z {len(to_process)} filmów.")
        
    else:
        while True:
            print("\n" + "="*50)
            title_input = input("Wprowadź tytuł filmu (lub naciśnij Enter, aby zakończyć): ").strip()
            if not title_input:
                print("Zamykanie programu.")
                break
                
            # Wykrywanie czy użytkownik podał "Tytuł (Rok)" od razu w pierwszym pytaniu
            match = re.search(r'^(.*?)\s*\((\d{4})\)$', title_input)
            if match:
                title = match.group(1).strip()
                year = match.group(2).strip()
                print(f"[*] Rozpoznano tytuł: '{title}' oraz rok: {year}")
            else:
                title = title_input
                year_input = input("Wprowadź rok produkcji (np. 2010 lub (2010)): ").strip()
                # Jeśli użytkownik wpisze w nawiasach, np. (2010) - usuniemy je.
                year = year_input.replace("(", "").replace(")", "").strip()
                
            if not year.isdigit() or len(year) != 4:
                print("[Błąd] Rok musi składać się z 4 cyfr!")
                continue
                
            add_single_movie(html_file, title, year, api_key, is_bulk=False)

if __name__ == "__main__":
    main()