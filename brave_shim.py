import time
import random
import yaml
import uvicorn
import logging
import os
import ssl
from fastapi import FastAPI, Query
from ddgs import DDGS
from pathlib import Path

# 1. Caricamento configurazione
config_file = Path("brave_shim.conf")
if not config_file.exists():
    raise FileNotFoundError("Errore: Il file 'brave_shim.conf' non esiste.")

with open(config_file, "r") as f:
    config = yaml.safe_load(f)

# 2. Configurazione Logging (Solo su file, rimosso StreamHandler per il Journal)
logging.basicConfig(
    level=config['logging']['level'],
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(config['logging']['file_path'])]
)
logger = logging.getLogger("brave_shim")

# 3. Gestione SSL e Variabili d'Ambiente
ssl_cfg = config.get('ssl', {})
verify_ssl = ssl_cfg.get('verify_ssl', True)
custom_ca_status = "System Default"

if ssl_cfg.get('use_custom_ca'):
    ca_path = ssl_cfg['ca_bundle_path']
    if os.path.exists(ca_path):
        # Imposta variabili per i backend HTTP (Requests, HTTpx, Rust/Reqwest)
        os.environ["SSL_CERT_FILE"] = ca_path
        os.environ["REQUESTS_CA_BUNDLE"] = ca_path
        os.environ["CURL_CA_BUNDLE"] = ca_path
        
        if not verify_ssl:
            # Bypass totale della verifica SSL in Python
            ssl._create_default_https_context = ssl._create_unverified_context
            custom_ca_status = f"Active (Verify=OFF, Path={ca_path})"
            logger.warning("SSL: Verifica disabilitata. Accetto certificati self-signed.")
        else:
            try:
                context = ssl.create_default_context(cafile=ca_path)
                ssl._create_default_https_context = lambda: context
                custom_ca_status = f"Active (Path={ca_path})"
            except Exception as e:
                logger.error(f"SSL: Errore nel caricamento del bundle: {e}")
    else:
        logger.error(f"SSL: File CA Bundle non trovato a {ca_path}")
        custom_ca_status = "Error: File not found"

app = FastAPI(title="Brave Search API Shim for OpenClaw (DuckDuckGo)", docs_url=None, redoc_url=None)

search_cache = {}

# --- FUNZIONI DI SUPPORTO ---
def get_from_cache(q):
    expiration = config['bot_protection']['cache_expiration']
    if q in search_cache:
        timestamp, data = search_cache[q]
        if time.time() - timestamp < expiration:
            return data
    return None

# --- ENDPOINTS ---

@app.get("/status")
async def health_check():
    return {
        "status": "online",
        "cache_entries": len(search_cache),
        "ssl_verify": verify_ssl,
        "ca_bundle": custom_ca_status
    }

@app.get("/res/v1/web/search")
async def search_proxy(q: str = Query(...), count: int = None):
    res_count = count or config['search']['default_count']
    
    cached_res = get_from_cache(q)
    if cached_res:
        logger.info(f"CACHE HIT: {q}")
        return cached_res

    # Anti-Ban Delay
    time.sleep(random.uniform(config['bot_protection']['min_delay'], config['bot_protection']['max_delay']))
    
    logger.info(f"FETCH WEB: {q}")
    try:
        # Passiamo verify=False se configurato nel file conf
        with DDGS(verify=verify_ssl) as ddgs:
            results = []
            for r in ddgs.text(q, max_results=res_count):
                results.append({
                    "title": r.get("title"),
                    "url": r.get("href"),
                    "description": r.get("body"),
                    "meta_url": {"path": r.get("href")}
                })
        
        response_data = {"web": {"results": results}}
        search_cache[q] = (time.time(), response_data)
        return response_data
    except Exception as e:
        logger.error(f"Errore ricerca WEB per '{q}': {e}")
        return {"web": {"results": []}, "error": str(e)}

@app.get("/res/v1/local/pois")
async def local_proxy(q: str = Query(...), count: int = None):
    res_count = count or config['search']['local_count']
    logger.info(f"FETCH LOCAL: {q}")
    try:
        with DDGS(verify=verify_ssl) as ddgs:
            res = [
                {
                    "id": str(i), 
                    "name": r["title"], 
                    "address": r["body"][:100],
                    "phone": "", 
                    "coordinates": {"latitude": 0.0, "longitude": 0.0}
                } 
                for i, r in enumerate(ddgs.text(f"place {q}", max_results=res_count))
            ]
        return {"results": res}
    except Exception as e:
        logger.error(f"Errore ricerca LOCAL per '{q}': {e}")
        return {"results": []}

@app.get("/res/v1/local/descriptions")
async def local_descriptions(id: str = Query(...)):
    return {"descriptions": {id: "Dati via DDG Proxy."}}

@app.get("/res/v1/summarizer/summary")
async def summarizer_proxy(key: str = Query(...)):
    return {"summary": "Sintesi pronta.", "status": "complete"}

if __name__ == "__main__":
    logger.info(f"Avvio Brave-Shim su {config['server']['host']}:{config['server']['port']}")
    uvicorn.run(
        app, 
        host=config['server']['host'], 
        port=config['server']['port'], 
        access_log=False,
        log_level="critical"
    )

