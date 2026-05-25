#!/usr/bin/env python3
import sys
import subprocess
import argparse
from HdRezkaApi import HdRezkaApi


def choose_option(options, prompt_text):
    print(f"\n--- {prompt_text} ---")
    for idx, opt in enumerate(options, 1):
        print(f"[{idx}] {opt}")
    
    while True:
        try:
            choice = int(input("Select an option number: ")) - 1
            if 0 <= choice < len(options):
                return options[choice]
        except ValueError:
            pass
        print("Invalid choice. Try again.")

def get_safe_stream_url(stream, quality):
    if not stream or not stream.videos:
        return None
    
    if quality not in stream.videos:
        quality = list(stream.videos.keys())[0]
        
    url = stream.videos[quality]
    if isinstance(url, list):
        url = url[0]
    return url

def main():
    parser = argparse.ArgumentParser(description="Stream or download media from HDRezka using MPV")
    parser.add_argument("url", help="The full HDRezka page URL")
    args = parser.parse_args()

    print("[*] Fetching media details...")
    try:
        rezka = HdRezkaApi(args.url)
    except Exception as e:
        print(f"[-] Failed to initialize wrapper: {e}")
        sys.exit(1)

    if not getattr(rezka, 'ok', True):
        print(f"[-] Wrapper Error: {getattr(rezka, 'exception', 'Unknown extraction error')}")
        sys.exit(1)

    title = getattr(rezka, 'name', 'HDRezka Media')

    translators_dict = getattr(rezka, 'translators_names', {})
    if not translators_dict:
        print("[-] No translators found for this media.")
        sys.exit(1)
        
    voiceover_names = list(translators_dict.keys())
    selected_voiceover = choose_option(voiceover_names, "Available Voiceovers")
    selected_translator_id = translators_dict[selected_voiceover]['id']

    if hasattr(rezka, 'translators_priority'):
        rezka.translators_priority = [selected_translator_id]

    is_series = getattr(rezka, 'type', '') == 'tv_series'

    if is_series:
        series_info = getattr(rezka, 'seriesInfo', {})
        t_info = None
        for key, value in series_info.items():
            if str(key) == str(selected_translator_id):
                t_info = value
                break
                
        if not t_info and series_info:
            t_info = list(series_info.values())[0]
        elif not t_info:
            print("[-] Could not parse season data for the selected voiceover.")
            sys.exit(1)
            
        seasons = sorted(list(t_info['seasons']), key=lambda x: int(x) if str(x).isdigit() else 0)
        season_options = [f"Season {s}" for s in seasons]
        chosen_season_str = choose_option(season_options, "Select Season")
        selected_season = seasons[season_options.index(chosen_season_str)]
        
        episodes_dict = t_info.get('episodes', {})
        episodes_list = []
        for skey, evals in episodes_dict.items():
            if str(skey) == str(selected_season):
                episodes_list = evals
                break
                
        if not episodes_list:
            print(f"[-] No episodes found for Season {selected_season}.")
            sys.exit(1)
            
        episodes = sorted(list(episodes_list), key=lambda x: int(x) if str(x).isdigit() else 0)
        
        print("[*] Probing resolution choices from first episode...")
        try:
            first_stream = rezka.getStream(selected_season, episodes[0], translation=selected_translator_id)
        except TypeError:
            first_stream = rezka.getStream(selected_season, episodes[0])
            
        qualities = list(first_stream.videos.keys())
        selected_quality = choose_option(qualities, "Select Quality Resolution")

        playlist_lines = ["#EXTM3U"]
        print(f"\n[*] Decrypting links for {len(episodes)} episodes. Please wait...")
        
        for ep in episodes:
            sys.stdout.write(f"\r\033[K[*] Processing Episode {ep}/{episodes[-1]}...")
            sys.stdout.flush()
            try:
                stream = rezka.getStream(selected_season, ep, translation=selected_translator_id)
            except TypeError:
                stream = rezka.getStream(selected_season, ep)
                
            url = get_safe_stream_url(stream, selected_quality)
            if url:
                # Add an M3U header track naming line before the stream payload
                # Format: #EXTINF:<duration>,<display_name> (-1 signifies a live stream/undetermined runtime length)
                playlist_lines.append(f"#EXTINF:-1,Episode {ep} (S{selected_season})")
                playlist_lines.append(url)
                
        print("\n[*] Playlist generated successfully.")

        if len(playlist_lines) <= 1:
            print("[-] Failed to extract any valid streaming URLs.")
            sys.exit(1)

        playlist_content = "\n".join(playlist_lines)

        print(f"[*] Launching MPV with playlist...")
        mpv_cmd = [
            "mpv",
            "--playlist=-",  
            f"--title={title} - {selected_voiceover}"
        ]
        subprocess.run(mpv_cmd, input=playlist_content, text=True)

    else:
        print("[*] Decrypting movie streams...")
        try:
            stream = rezka.getStream(translation=selected_translator_id)
        except TypeError:
            stream = rezka.getStream()
            
        qualities = list(stream.videos.keys())
        selected_quality = choose_option(qualities, "Select Quality Resolution")
        selected_stream_url = get_safe_stream_url(stream, selected_quality)

        print(f"\n[*] Launching MPV for movie playback...")
        mpv_cmd = [
            "mpv.com",
            selected_stream_url,
            f"--title={title} - {selected_voiceover}"
        ]
        subprocess.run(mpv_cmd)

if __name__ == "__main__":
    main()