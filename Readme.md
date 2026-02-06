# Brave Search API Shim for OpenClaw (DuckDuckGo)

This project is a local proxy (shim) that emulates **Brave Search APIs** by redirecting requests to **DuckDuckGo**. It is specifically designed to allow [OpenClaw](https://github.com) (or similar agents) to operate for free, eliminating the need for official Brave API keys.

## 🚀 Features

* **Web Search**: Complete mapping of DuckDuckGo results into Brave's JSON format.
* **Local Search**: Point of Interest (POI) search simulation.
* **Summarizer**: Placeholder for RAG pipeline compatibility.
* **Systemd Ready**: Pre-configured scripts to run the proxy as a background service.

---

## 🛠️ Installation

### 1. Prerequisites

Ensure you have **Python 3.8+** installed. Clone the repository:

```bash
cd /opt
git clone https://github.com/asoraruf/brave_shim

```

### 2. Virtual Environment & Dependencies

Create an isolated environment and install the required packages:

```bash
cd /opt/brave_shim
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn ddgs pyyaml

```

### 3. Service Configuration

#### ⚙️ Systemd Setup

To run the proxy automatically at server startup:

1. **Copy the unit file**:
```bash
sudo cp /opt/brave_shim/configs/systemd/openclaw-proxy.service /etc/systemd/system/

```

2. **Enable and start the service**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now openclaw-proxy
sudo systemctl start openclaw-proxy
sudo journalctl -u openclaw-proxy -f

```

---

## 🧪 Verification Tests

You can verify the proxy is working by simulating OpenClaw's REST calls using `curl`:

**Web Search Test**

```bash
curl -G "http://localhost:8000/res/v1/web/search" --data-urlencode "q=OpenAI news"

```

**Local Search Test**

```bash
curl -G "http://localhost:8000/res/v1/local/pois" --data-urlencode "q=pizza in Naples"

```

---

## 🔗 OpenClaw Integration

Apply the patch to redirect OpenClaw traffic to the local shim:

```bash
sudo sh /opt/brave_shim/scripts/patch_openclaw.sh

```
