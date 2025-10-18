import wikipedia as w
import os
from flask import *
from flask import request, render_template
from prometheus_client import generate_latest, Counter, Histogram, Gauge, REGISTRY
import time
import threading

app = Flask(__name__, static_folder="ico", template_folder=os.getcwd())

# Prometheus Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status_code'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration in seconds', ['endpoint'])
WIKIPEDIA_SEARCHES = Counter('wikipedia_searches_total', 'Total Wikipedia searches', ['status'])
WIKIPEDIA_SEARCH_DURATION = Histogram('wikipedia_search_duration_seconds', 'Wikipedia search duration in seconds')
ACTIVE_REQUESTS = Gauge('active_requests', 'Currently active requests')
APP_ERRORS = Counter('app_errors_total', 'Total application errors', ['error_type'])

@app.before_request
def before_request():
    request.start_time = time.time()
    ACTIVE_REQUESTS.inc()

@app.after_request
def after_request(response):
    ACTIVE_REQUESTS.dec()
    duration = time.time() - request.start_time
    REQUEST_DURATION.labels(endpoint=request.endpoint).observe(duration)
    REQUEST_COUNT.labels(method=request.method, endpoint=request.endpoint, status_code=response.status_code)
    return response

@app.route("/", methods=["POST", "GET"])
def mn():
    if request.method == "GET":
        return render_template("index.html", info="")
    else:
        search_start = time.time()
        try:
            search_term = request.form["search"]
            info = w.summary(request.form["search"])
            search_duration = time.time() - search_start
            WIKIPEDIA_SEARCH_DURATION.observe(search_duration)
            WIKIPEDIA_SEARCHES.labels(status="success").inc()
            return render_template("index.html", info=info)
        except Exception as e:
            search_duration = time.time() - search_start
            WIKIPEDIA_SEARCH_DURATION.observe(search_duration)
            WIKIPEDIA_SEARCHES.labels(status="error").inc()
            APP_ERRORS.labels(error_type="wikipedia_search").inc()
            return render_template("index.html", info="Information not found")

# Prometheus Metrics Endpoint
@app.route('/metrics')
def metrics():
    return generate_latest(REGISTRY), 200, {'Content-Type': 'text/plain'}

# Health Check Endpoint
@app.route('/health')
def health():
    return {'status': 'healthy', 'timestamp': time.time()}

if "__main__" == __name__:
    # Start Prometheus metrics server on port 8000
    from prometheus_client import start_http_server
    start_http_server(8000)
    
    # Start Flask app on all interfaces
    app.run(host='0.0.0.0', port=5000)
