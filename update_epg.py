import os
import re
import gzip
import requests
import xml.etree.ElementTree as ET

M3U_URL = os.environ.get('M3U_URL', '')
OUTPUT_DIR = 'epgs'
OUTPUT_FILE_GZ = os.path.join(OUTPUT_DIR, 'light-epg.xml.gz')
OUTPUT_FILE_XML = os.path.join(OUTPUT_DIR, 'light-epg.xml')

EPG_URLS = [
    'https://epgshare01.' + 'online/epgshare01/epg_ripper_FR1.xml.gz',
    'https://epgshare01.' + 'online/epgshare01/epg_ripper_BE1.xml.gz',
    'https://epgshare01.' + 'online/epgshare01/epg_ripper_PT1.xml.gz',
    'https://github.' + 'com/matthuisman/i.mjh.nz/raw/refs/heads/master/PlutoTV/all.xml.gz',
]

def get_m3u_tvg_ids(url):
    if not url:
        print("M3U_URL is empty.")
        return set()
    print(f"Fetching M3U from {url}...")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    ids = set(re.findall(r'tvg-id="([^"]+)"', resp.text))
    print(f"Found {len(ids)} unique tvg-ids in M3U.")
    return ids

def fetch_epg(url):
    print(f"Downloading EPG from {url}...")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    content = resp.content
    if url.endswith('.gz') or content[:2] == b'\x1f\x8b':
        content = gzip.decompress(content)
    return ET.fromstring(content)

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    valid_ids = get_m3u_tvg_ids(M3U_URL)
    if not valid_ids:
        print("No valid tvg-ids found. Exiting.")
        return

    master_root = ET.Element('tv')
    added_channels = set()

    for url in EPG_URLS:
        try:
            epg_data = fetch_epg(url)
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            continue

        for ch in epg_data.findall('channel'):
            ch_id = ch.get('id')
            if ch_id in valid_ids and ch_id not in added_channels:
                master_root.append(ch)
                added_channels.add(ch_id)

        for prog in epg_data.findall('programme'):
            if prog.get('channel') in valid_ids:
                title = prog.find('title')
                if title is not None and title.text in ['NHL Hockey', 'Live: NFL Football']:
                    sub = prog.find('sub-title')
                    if sub is not None and sub.text:
                        title.text = f"{title.text} {sub.text}"
                master_root.append(prog)

    tree = ET.ElementTree(master_root)
    with gzip.open(OUTPUT_FILE_GZ, 'wb') as f:
        tree.write(f, encoding='utf-8', xml_declaration=True)
    with open(OUTPUT_FILE_XML, 'wb') as f:
        tree.write(f, encoding='utf-8', xml_declaration=True)

    print("EPG generation complete.")

if __name__ == "__main__":
    main()
